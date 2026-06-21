#!/usr/bin/env python3
"""medicerti-vision: Medical Edge Vision AI SaaS - Entry Point"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

from src.api.event_logger import EventLogger
from src.api.main import active_connections, broadcast_alert, event_logger, pipeline_state
from src.api.models import AlertMessage, CameraConfig
from src.config.settings import SNAPSHOTS_DIR
from src.detector.fall_detector import FallDetector
from src.detector.geo_fence import GeoFenceDetector
from src.detector.yolo_pose import YoloPoseEstimator
from src.detector.stranger_detector import StrangerDetector
from src.detector.roi_tracker import ROITracker
from src.ingest.rtsp_reader import RTSPStreamReader
from src.privacy.masker import PrivacyMasker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("medicerti-vision")


class Pipeline:
    def __init__(self, cameras: list[CameraConfig], mock_mode: bool = False):
        self.cameras = cameras
        self.mock_mode = mock_mode
        self.readers: dict[str, RTSPStreamReader] = {}
        self.estimator = YoloPoseEstimator()
        self.fall_detector = FallDetector()
        self.geo_fence = GeoFenceDetector()
        self.stranger_detector = StrangerDetector()
        self.roi_tracker = ROITracker()
        self.masker = PrivacyMasker()
        self.logger = EventLogger()
        self._running = False
        self._frame_count = 0

    def start(self):
        self._running = True
        if self.mock_mode:
            logger.info("Starting in MOCK mode (local webcam)")
            for cam in self.cameras:
                reader = RTSPStreamReader("0", name=cam.id)
                reader.fps = 30.0
                reader.resolution = (640, 480)
                self.readers[cam.id] = reader
        else:
            for cam in self.cameras:
                reader = RTSPStreamReader(cam.rtsp_url, name=cam.id)
                reader.start()
                self.readers[cam.id] = reader

        for zone_id, vertices in getattr(self, '_zones', {}).items():
            self.geo_fence.set_polygon(zone_id, vertices)

    def stop(self):
        self._running = False
        for reader in self.readers.values():
            reader.stop()
        self.estimator.close()
        self.logger.close()

    def process_frame(self, camera_id: str, frame):
        if frame is None:
            return None, None

        landmarks, _ = self.estimator.process(frame)
        if landmarks is None:
            return None, None

        fall_result = self.fall_detector.detect(landmarks)
        geo_result = self.geo_fence.detect_elopement(landmarks)
        stranger_result = self.stranger_detector.detect(
            frame, camera_id=camera_id,
            zone_restricted=bool(geo_result.get("zone")),
        )

        masked = self.masker.apply(frame, landmarks)
        
        if geo_result.get("zone"):
            masked = self.geo_fence.draw_zones(masked)

        self.roi_tracker.update_frame_shape(frame.shape[0], frame.shape[1])
        zoomed_frame = self.roi_tracker.compute_zoom(frame)

        events = []

        if fall_result["fall"]:
            event_type = "fall"
            snapshot = self._save_snapshot(camera_id, frame, event_type)
            self.roi_tracker.track_bbox(self._estimate_bbox(landmarks), auto_track=True)
            self.logger.insert(
                camera_id=camera_id,
                event_type=event_type,
                confidence=fall_result["confidence"],
                snapshot_path=snapshot,
                details={"reasons": fall_result["reasons"]},
            )
            events.append(AlertMessage(
                type="alert",
                camera_id=camera_id,
                event_type=event_type,
                confidence=fall_result["confidence"],
                timestamp=datetime.now().isoformat(),
            ))

        if geo_result.get("elopement"):
            event_type = "elopement" if not geo_result.get("loitering") else "loitering"
            snapshot = self._save_snapshot(camera_id, frame, event_type)
            self.roi_tracker.track_bbox(self._estimate_bbox(landmarks), auto_track=True)
            self.logger.insert(
                camera_id=camera_id,
                event_type=event_type,
                confidence=1.0,
                snapshot_path=snapshot,
                details={"zone": geo_result.get("zone"), "loiter_seconds": geo_result.get("loiter_seconds", 0)},
            )
            events.append(AlertMessage(
                type="alert",
                camera_id=camera_id,
                event_type=event_type,
                confidence=1.0,
                timestamp=datetime.now().isoformat(),
            ))

        if stranger_result["stranger"]:
            event_type = "stranger"
            snapshot = self._save_snapshot(camera_id, frame, event_type)
            for face in stranger_result.get("faces", []):
                bbox = face.get("bbox")
                if bbox and face["matched_name"] is None:
                    self.roi_tracker.track_bbox(tuple(bbox), auto_track=True)
                    break
            self.logger.insert(
                camera_id=camera_id,
                event_type=event_type,
                confidence=stranger_result["confidence"],
                snapshot_path=snapshot,
                details={"reasons": stranger_result["reasons"], "faces": len(stranger_result.get("faces", []))},
            )
            events.append(AlertMessage(
                type="alert",
                camera_id=camera_id,
                event_type=event_type,
                confidence=stranger_result["confidence"],
                timestamp=datetime.now().isoformat(),
            ))

        return masked, zoomed_frame, events

    def _estimate_bbox(self, landmarks: list[dict]) -> tuple[int, int, int, int]:
        xs = [lm["x"] for lm in landmarks[:25] if lm["visibility"] > 0.5]
        ys = [lm["y"] for lm in landmarks[:25] if lm["visibility"] > 0.5]
        if not xs or not ys:
            return (0, 0, 100, 100)
        x, y = int(min(xs)), int(min(ys))
        x2, y2 = int(max(xs)), int(max(ys))
        return (x, y, x2 - x, y2 - y)

    def _save_snapshot(self, camera_id: str, frame, event_type: str) -> str | None:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{camera_id}_{event_type}_{ts}.jpg"
            path = SNAPSHOTS_DIR / filename
            cv2.imwrite(str(path), frame)
            return str(path)
        except Exception as e:
            logger.warning(f"Snapshot save failed: {e}")
            return None


async def run_pipeline_async(pipeline: Pipeline):
    loop = asyncio.get_event_loop()

    while pipeline._running:
        for cam_id, reader in pipeline.readers.items():
            frame = reader.read(timeout=0.5)
            if frame is None:
                continue

            masked, zoomed, events = await loop.run_in_executor(None, pipeline.process_frame, cam_id, frame)
            if masked is None:
                continue

            for alert in events:
                await broadcast_alert(alert)

            if masked is not None:
                display = zoomed if zoomed is not None else masked
                cv2.imshow(f"medicerti-vision: {cam_id}", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            pipeline._running = False
            break


def main():
    parser = argparse.ArgumentParser(description="medicerti-vision Edge AI Pipeline")
    parser.add_argument("--cameras", "-c", type=str, nargs="*", default=[],
                        help="Camera configs: id=rtsp_url (e.g. cam0=rtsp://...)")
    parser.add_argument("--mock", action="store_true",
                        help="Use local webcam for testing")
    parser.add_argument("--show", action="store_true", default=True,
                        help="Show video windows")
    args = parser.parse_args()

    cameras = []
    if args.mock:
        cameras.append(CameraConfig(id="mock_cam", rtsp_url="0"))
    for arg in args.cameras:
        if "=" in arg:
            cam_id, url = arg.split("=", 1)
            cameras.append(CameraConfig(id=cam_id, rtsp_url=url))

    if not cameras:
        logger.warning("No cameras specified. Use --mock for webcam or --cameras for RTSP.")
        cameras.append(CameraConfig(id="mock_cam", rtsp_url="0"))

    pipeline = Pipeline(cameras, mock_mode=args.mock)
    pipeline.start()
    pipeline_state["running"] = True
    pipeline_state["cameras"] = {c.id: c.model_dump() for c in cameras}

    try:
        asyncio.run(run_pipeline_async(pipeline))
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        logger.info("Pipeline stopped.")


if __name__ == "__main__":
    main()
