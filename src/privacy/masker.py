import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class PrivacyMasker:
    def __init__(self, blur_face: bool = True, silhouette_mode: bool = True):
        self.blur_face = blur_face
        self.silhouette_mode = silhouette_mode
        self._unmasked = False

    def set_unmasked(self, state: bool):
        self._unmasked = state

    def apply(self, frame: np.ndarray, landmarks: list[dict] | None = None) -> np.ndarray:
        if self._unmasked or landmarks is None:
            return frame

        if self.silhouette_mode:
            return self._render_silhouette(frame, landmarks)

        return self._apply_blur(frame, landmarks)

    def _render_silhouette(self, frame: np.ndarray, landmarks: list[dict]) -> np.ndarray:
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)

        head_idx = 0
        shoulder_l = 11
        shoulder_r = 12
        hip_l = 23
        hip_r = 24

        if any(l["visibility"] < 0.5 for l in [landmarks[i] for i in [head_idx, shoulder_l, shoulder_r, hip_l, hip_r] if i < len(landmarks)]):
            skeleton_overlay = self._draw_skeleton(frame, landmarks)
            return cv2.addWeighted(frame, 0.3, skeleton_overlay, 0.7, 0)

        body_contour = np.array([
            (landmarks[head_idx]["x"], landmarks[head_idx]["y"]),
            (landmarks[shoulder_l]["x"], landmarks[shoulder_l]["y"]),
            (landmarks[hip_l]["x"], landmarks[hip_l]["y"]),
            (landmarks[hip_r]["x"], landmarks[hip_r]["y"]),
            (landmarks[shoulder_r]["x"], landmarks[shoulder_r]["y"]),
        ], dtype=np.int32)

        cv2.fillPoly(mask, [body_contour], 255)

        result = frame.copy()
        result[mask == 255] = (50, 50, 50)

        skeleton = self._draw_skeleton(frame, landmarks)
        result = cv2.addWeighted(result, 1.0, skeleton, 1.0, 0)

        return result

    def _draw_skeleton(self, frame: np.ndarray, landmarks: list[dict]) -> np.ndarray:
        overlay = np.zeros_like(frame)
        SKELETON_CONNECTIONS = [
            (11, 12), (12, 14), (14, 16), (11, 13), (13, 15),
            (11, 23), (12, 24), (23, 24),
            (23, 25), (25, 27), (27, 29), (29, 31),
            (24, 26), (26, 28), (28, 30), (30, 32),
        ]

        for i, j in SKELETON_CONNECTIONS:
            if i >= len(landmarks) or j >= len(landmarks):
                continue
            if landmarks[i]["visibility"] < 0.5 or landmarks[j]["visibility"] < 0.5:
                continue
            pt1 = (int(landmarks[i]["x"]), int(landmarks[i]["y"]))
            pt2 = (int(landmarks[j]["x"]), int(landmarks[j]["y"]))
            cv2.line(overlay, pt1, pt2, (0, 255, 0), 2)

        for lm in landmarks:
            if lm["visibility"] >= 0.5:
                cv2.circle(overlay, (int(lm["x"]), int(lm["y"])), 3, (0, 255, 0), -1)

        return overlay

    def _apply_blur(self, frame: np.ndarray, landmarks: list[dict]) -> np.ndarray:
        result = frame.copy()
        if not self.blur_face:
            return result
        if len(landmarks) < 1:
            return result
        nose = landmarks[0]
        if nose["visibility"] < 0.5:
            return result

        x, y = int(nose["x"]), int(nose["y"])
        face_size = 60
        x1 = max(0, x - face_size)
        y1 = max(0, y - face_size)
        x2 = min(frame.shape[1], x + face_size)
        y2 = min(frame.shape[0], y + face_size)

        roi = result[y1:y2, x1:x2]
        if roi.size > 0:
            blurred = cv2.GaussianBlur(roi, (35, 35), 10)
            result[y1:y2, x1:x2] = blurred

        return result
