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
from src.api.event_logger import EventLogger
from src.config.settings import SNAPSHOTS_DIR, BASE_DIR

logger = logging.getLogger(__name__)

event_logger = EventLogger()
active_connections: list[WebSocket] = []
pipeline_state = {"running": False, "cameras": {}}
stranger_detector = StrangerDetector()
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

dashboard_dir = BASE_DIR / "src" / "dashboard"
if dashboard_dir.exists():
    app.mount("/", StaticFiles(directory=str(dashboard_dir), html=True), name="dashboard")


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
