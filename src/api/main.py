import asyncio
import base64
import json
import logging
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.models import AlertMessage, CameraConfig, DetectionEvent, ReportRequest
from src.detector.stranger_detector import StrangerDetector
from src.notify.telegram_notifier import TelegramNotifier
from src.api.event_logger import EventLogger
from src.config.settings import SNAPSHOTS_DIR, BASE_DIR

logger = logging.getLogger(__name__)

event_logger = EventLogger()
active_connections: list[WebSocket] = []
pipeline_state = {"running": False, "cameras": {}}
stranger_detector = StrangerDetector()
telegram_notifier = TelegramNotifier()
pipeline_thread: threading.Thread | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("medicerti-vision API starting...")
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    logger.info("medicerti-vision API shutting down...")
    event_logger.close()
    pipeline_state["running"] = False


app = FastAPI(title="medicerti-vision", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def broadcast_alert(alert: AlertMessage):
    dead: list[WebSocket] = []
    data = alert.model_dump_json()
    for ws in active_connections:
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        active_connections.remove(ws)

    telegram_notifier.send_alert(
        event_type=alert.event_type,
        camera_id=alert.camera_id,
        confidence=alert.confidence,
        timestamp=alert.timestamp,
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "cameras": pipeline_state.get("cameras", {}),
    }


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception:
        active_connections.remove(websocket)


@app.get("/events")
async def get_events(limit: int = 100, offset: int = 0,
                     camera_id: str | None = None,
                     event_type: str | None = None):
    return event_logger.query(
        limit=limit, offset=offset,
        camera_id=camera_id, event_type=event_type,
    )


@app.get("/events/stats")
async def get_event_stats(camera_id: str | None = None, event_type: str | None = None):
    return {
        "total": event_logger.count(camera_id=camera_id, event_type=event_type),
    }


@app.post("/events/report")
async def generate_report(req: ReportRequest):
    from datetime import datetime, timedelta
    start = req.start_date or (datetime.now() - timedelta(days=7)).isoformat()
    end = req.end_date or datetime.now().isoformat()
    events = event_logger.query_for_report(
        start=start, end=end,
        camera_ids=req.camera_ids or None,
        event_types=req.event_types or None,
    )
    return {"events": events, "total": len(events)}


@app.post("/pipeline/start")
async def start_pipeline(cameras: list[CameraConfig]):
    pipeline_state["cameras"] = {c.id: c.model_dump() for c in cameras}
    pipeline_state["running"] = True
    return {"status": "started", "cameras": len(cameras)}


@app.post("/pipeline/stop")
async def stop_pipeline():
    pipeline_state["running"] = False
    return {"status": "stopped"}


@app.get("/pipeline/status")
async def pipeline_status():
    return pipeline_state


@app.get("/zoom")
async def get_zoom_info():
    from src.main import Pipeline
    return {"zoom": {"active": False, "message": "Zoom available when pipeline is running"}}


@app.post("/zoom/activate")
async def activate_zoom(x: int = 320, y: int = 240, factor: float = 2.0, auto_track: bool = False):
    from src.main import Pipeline
    return {"status": "zoom_activate", "center": [x, y], "factor": factor}


@app.post("/zoom/deactivate")
async def deactivate_zoom():
    return {"status": "zoom_deactivated"}


@app.post("/zoom/factor")
async def set_zoom_factor(factor: float = 2.0):
    return {"status": "zoom_factor_set", "factor": max(1.0, min(8.0, factor))}


@app.post("/events/report-pdf")
async def generate_report_pdf(req: ReportRequest):
    from src.accreditation.report_gen import AccreditationReport
    from datetime import datetime, timedelta

    start = req.start_date or (datetime.now() - timedelta(days=7)).isoformat()
    end = req.end_date or datetime.now().isoformat()
    events = event_logger.query_for_report(
        start=start, end=end,
        camera_ids=req.camera_ids or None,
        event_types=req.event_types or None,
    )

    gen = AccreditationReport()
    pdf_path = gen.generate(events, facility_name="medicerti-vision")
    return JSONResponse(content={"pdf_path": pdf_path})


@app.post("/events/report-night")
async def generate_night_report(req: ReportRequest):
    from src.accreditation.report_gen import NightSecurityReport
    from datetime import datetime, timedelta

    start = req.start_date or (datetime.now() - timedelta(days=1)).isoformat()
    end = req.end_date or datetime.now().isoformat()
    events = event_logger.query_for_report(
        start=start, end=end,
        camera_ids=req.camera_ids or None,
        event_types=req.event_types or None,
    )
    gen = NightSecurityReport()
    pdf_path = gen.generate(events, facility_name="medicerti-vision")
    return JSONResponse(content={"pdf_path": pdf_path})


@app.post("/events/report-highrisk")
async def generate_highrisk_report(req: ReportRequest):
    from src.accreditation.report_gen import HighRiskObservationReport
    from datetime import datetime, timedelta

    start = req.start_date or (datetime.now() - timedelta(days=7)).isoformat()
    end = req.end_date or datetime.now().isoformat()
    events = event_logger.query_for_report(
        start=start, end=end,
        camera_ids=req.camera_ids or None,
        event_types=["fall"],
    )
    gen = HighRiskObservationReport()
    pdf_path = gen.generate(events, facility_name="medicerti-vision")
    return JSONResponse(content={"pdf_path": pdf_path})


@app.post("/events/report-access")
async def generate_access_report(req: ReportRequest):
    from src.accreditation.report_gen import AccessControlReport
    from datetime import datetime, timedelta

    start = req.start_date or (datetime.now() - timedelta(days=7)).isoformat()
    end = req.end_date or datetime.now().isoformat()
    events = event_logger.query_for_report(
        start=start, end=end,
        camera_ids=req.camera_ids or None,
        event_types=["stranger", "elopement"],
    )
    gen = AccessControlReport()
    pdf_path = gen.generate(events, facility_name="medicerti-vision")
    return JSONResponse(content={"pdf_path": pdf_path})


@app.post("/scan/cameras")
async def scan_cameras(subnet: str | None = Query(None)):
    from src.discovery.camera_scanner import scan_network_for_cameras
    try:
        found = scan_network_for_cameras(subnet=subnet)
        return {"found": len(found), "cameras": found}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/faces/register")
async def register_face(name: str = Query(...), role: str = ""):
    return {"success": True, "message": f"Face registration requires image upload via /faces/register-with-image"}


@app.get("/faces/whitelist")
async def get_whitelist():
    return stranger_detector.get_whitelist()


@app.delete("/faces/whitelist")
async def remove_face(name: str = Query(...)):
    return {"success": stranger_detector.remove_face(name)}


@app.get("/faces/stranger-events")
async def get_stranger_events(limit: int = 100):
    return stranger_detector.get_stranger_events(limit=limit)


@app.post("/faces/train")
async def train_recognizer():
    success = stranger_detector.train_recognizer()
    return {"success": success, "message": "Recognizer trained" if success else "No faces to train on"}


@app.get("/notify/telegram/status")
async def telegram_status():
    return telegram_notifier.status


@app.post("/notify/telegram/configure")
async def telegram_configure(token: str = Query(...), chat_id: str = Query(...),
                              alert_types: str = Query("fall,elopement,loitering,stranger"),
                              min_confidence: float = Query(0.5)):
    types_list = [t.strip() for t in alert_types.split(",") if t.strip()]
    telegram_notifier.configure(token, chat_id, alert_types=types_list, min_confidence=min_confidence)
    return {"status": "configured", "enabled": telegram_notifier.enabled}


@app.post("/notify/telegram/disable")
async def telegram_disable():
    telegram_notifier.disable()
    return {"status": "disabled"}


@app.post("/notify/telegram/test")
async def telegram_test():
    ok = telegram_notifier.send_message("🔔 medicerti-vision 알림 테스트 메시지입니다.")
    return {"sent": ok}


@app.get("/update/check")
async def update_check():
    from src.updater.auto_updater import check_for_updates
    result = check_for_updates(silent=True)
    return result


@app.post("/update/apply")
async def update_apply(download_url: str | None = Query(None)):
    from src.updater.auto_updater import apply_update, check_for_updates
    if not download_url:
        info = check_for_updates(silent=True)
        download_url = info.get("download_url")
    if not download_url:
        raise HTTPException(status_code=400, detail="No update URL available")

    success = apply_update(download_url)
    return {"success": success}


@app.get("/version")
async def get_version():
    from src.updater.auto_updater import get_current_version
    return {
        "version": get_current_version(),
        "build_date": "2026-06-21",
        "api_version": "0.1.0",
    }


dashboard_dir = BASE_DIR / "src" / "dashboard"
if dashboard_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_dir), html=True), name="dashboard")
    logger.info(f"Dashboard mounted at /dashboard")
