import logging
import time
from collections import defaultdict

import cv2
import numpy as np

from src.config.settings import LOITERING_SECONDS

logger = logging.getLogger(__name__)


class GeoFenceDetector:
    def __init__(self):
        self._polygons: dict[str, list[list[tuple[int, int]]]] = {}
        self._entry_times: dict[str, dict[int, float]] = defaultdict(dict)

    def set_polygon(self, zone_id: str, vertices: list[tuple[int, int]]):
        self._polygons[zone_id] = vertices
        logger.info(f"GeoFence zone '{zone_id}' set with {len(vertices)} vertices")

    def remove_polygon(self, zone_id: str):
        self._polygons.pop(zone_id, None)
        self._entry_times.pop(zone_id, None)

    def get_polygons(self) -> dict:
        return dict(self._polygons)

    def detect_elopement(self, landmarks: list[dict]) -> dict:
        result = {"elopement": False, "zone": None, "loitering": False}
        if not landmarks:
            return result

        hip_center = self._get_hip_center(landmarks)
        if hip_center is None:
            return result

        hip_pt = tuple(hip_center.astype(int))

        for zone_id, vertices in self._polygons.items():
            pts = np.array(vertices, dtype=np.int32)
            inside = cv2.pointPolygonTest(pts, hip_pt, measureDist=False) >= 0

            if inside:
                loiter_seconds = self._update_loiter(zone_id, id(landmarks))
                result["zone"] = zone_id
                result["loitering"] = loiter_seconds > LOITERING_SECONDS
                result["elopement"] = True
                result["loiter_seconds"] = loiter_seconds
                break

        return result

    def _update_loiter(self, zone_id: str, person_id: int) -> float:
        now = time.time()
        if person_id not in self._entry_times[zone_id]:
            self._entry_times[zone_id][person_id] = now
        return now - self._entry_times[zone_id][person_id]

    def _get_hip_center(self, landmarks: list[dict]) -> np.ndarray | None:
        if len(landmarks) < 25:
            return None
        lh = np.array([landmarks[23]["x"], landmarks[23]["y"]])
        rh = np.array([landmarks[24]["x"], landmarks[24]["y"]])
        return (lh + rh) / 2

    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        for zone_id, vertices in self._polygons.items():
            pts = np.array(vertices, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
            label_pos = tuple(vertices[0])
            cv2.putText(frame, zone_id, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        return frame
