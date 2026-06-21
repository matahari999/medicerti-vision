#!/usr/bin/env python3
"""medicerti-vision - 통합 실행 스크립트"""

import argparse
import logging
import sys
import threading

import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("medicerti-vision")


def run_pipeline(args):
    from src.main import Pipeline
    from src.api.models import CameraConfig

    cameras = []
    if args.mock:
        cameras.append(CameraConfig(id="mock_cam", rtsp_url="0"))
    for arg in args.cameras or []:
        if "=" in arg:
            cam_id, url = arg.split("=", 1)
            cameras.append(CameraConfig(id=cam_id, rtsp_url=url))

    if not cameras:
        logger.warning("No cameras specified. Use --mock or --cameras.")
        return

    pipeline = Pipeline(cameras, mock_mode=args.mock)
    pipeline.start()
    from src.api.main import pipeline_state
    pipeline_state["running"] = True
    pipeline_state["cameras"] = {c.id: c.model_dump() for c in cameras}

    import asyncio
    from src.main import run_pipeline_async
    try:
        asyncio.run(run_pipeline_async(pipeline))
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()


def main():
    parser = argparse.ArgumentParser(description="medicerti-vision 실행")
    parser.add_argument("--cameras", "-c", type=str, nargs="*", default=[],
                        help="Camera configs: id=rtsp_url (e.g. cam0=rtsp://...)")
    parser.add_argument("--mock", action="store_true",
                        help="로컬 웹캠으로 테스트")
    parser.add_argument("--auto-scan", action="store_true",
                        help="네트워크에서 RTSP 카메라 자동 탐지")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="대시보드 서버 호스트")
    parser.add_argument("--port", type=int, default=8111,
                        help="대시보드 서버 포트")
    parser.add_argument("--no-pipeline", action="store_true",
                        help="API 서버만 실행 (파이프라인 없음)")
    parser.add_argument("--no-dashboard", action="store_true",
                        help="파이프라인만 실행 (대시보드 없음)")
    parser.add_argument("--update-check", action="store_true",
                        help="시작 전 업데이트 확인")
    args = parser.parse_args()

    if args.update_check:
        from src.updater.auto_updater import check_for_updates
        check_for_updates()

    if args.auto_scan and not args.cameras and not args.mock:
        from src.discovery.camera_scanner import scan_network_for_cameras
        logger.info("Auto-scanning network for RTSP cameras...")
        found = scan_network_for_cameras()
        if found:
            logger.info(f"Found {len(found)} camera(s): {[c['id'] for c in found]}")
            from src.api.main import pipeline_state
            pipeline_state["cameras"] = {c["id"]: c for c in found}
            import json
            cam_config_path = type('obj', (object,), {'cameras': []})
            from src.api.models import CameraConfig
            args.cameras = [f"{c['id']}={c['rtsp_url']}" for c in found]
        else:
            logger.warning("No cameras found. Falling back to mock mode.")
            args.mock = True

    if not args.no_pipeline:
        logger.info("Starting video pipeline...")
        t = threading.Thread(target=run_pipeline, args=(args,), daemon=True)
        t.start()

    if not args.no_dashboard:
        logger.info(f"Starting dashboard server at http://{args.host}:{args.port}")
        uvicorn.run(
            "src.api.main:app",
            host=args.host,
            port=args.port,
            log_level="info",
        )
    else:
        while True:
            import time
            time.sleep(1)


if __name__ == "__main__":
    main()
