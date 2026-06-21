import logging
import time

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ROITracker:
    def __init__(self, zoom_factor: float = 2.0, smooth_factor: float = 0.3):
        self.zoom_factor = zoom_factor
        self.smooth_factor = smooth_factor
        self._active = False
        self._target_center: tuple[int, int] | None = None
        self._current_center: tuple[int, int] | None = None
        self._auto_track_until: float = 0.0
        self._auto_track_duration = 5.0
        self._frame_shape: tuple[int, int] = (640, 480)
        self._manual_center: tuple[int, int] | None = None

    @property
    def is_active(self) -> bool:
        now = time.time()
        if self._auto_track_until > now:
            return True
        return self._active

    def activate(self, center_x: int, center_y: int, auto_track: bool = False):
        self._active = True
        self._target_center = (center_x, center_y)
        if self._current_center is None:
            self._current_center = (center_x, center_y)
        if auto_track:
            self._auto_track_until = time.time() + self._auto_track_duration

    def deactivate(self):
        self._active = False
        self._target_center = None
        self._auto_track_until = 0.0

    def set_zoom(self, factor: float):
        self.zoom_factor = max(1.0, min(8.0, factor))

    def set_center(self, x: int, y: int):
        self._manual_center = (x, y)
        self.activate(x, y)

    def track_bbox(self, bbox: tuple[int, int, int, int], auto_track: bool = True):
        x, y, w, h = bbox
        cx, cy = x + w // 2, y + h // 2
        self.activate(cx, cy, auto_track=auto_track)

    def update_frame_shape(self, h: int, w: int):
        self._frame_shape = (h, w)

    def compute_zoom(self, frame: np.ndarray) -> np.ndarray | None:
        if not self.is_active:
            return None

        h, w = frame.shape[:2]
        self._frame_shape = (h, w)

        target = self._manual_center or self._target_center
        if target is None:
            return None

        cx, cy = target
        if self._current_center is None:
            self._current_center = (cx, cy)
        else:
            sx = self._current_center[0] + (cx - self._current_center[0]) * self.smooth_factor
            sy = self._current_center[1] + (cy - self._current_center[1]) * self.smooth_factor
            self._current_center = (int(sx), int(sy))

        cx, cy = self._current_center
        zoom = self.zoom_factor

        crop_w = int(w / zoom)
        crop_h = int(h / zoom)

        x1 = max(0, cx - crop_w // 2)
        y1 = max(0, cy - crop_h // 2)
        x2 = min(w, x1 + crop_w)
        y2 = min(h, y1 + crop_h)

        if x2 - x1 < 10 or y2 - y1 < 10:
            return None

        cropped = frame[y1:y2, x1:x2]
        zoomed = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LANCZOS4)

        cv2.rectangle(zoomed, (0, 0), (w-1, h-1), (0, 255, 255), 2)
        cv2.putText(zoomed, f"{zoom:.1f}x", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        return zoomed

    def get_roi_info(self) -> dict:
        return {
            "active": self.is_active,
            "zoom_factor": self.zoom_factor,
            "center": self._current_center,
            "target": self._target_center,
            "frame_shape": self._frame_shape,
        }
