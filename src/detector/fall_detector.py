import logging
from collections import deque

import numpy as np

from src.config.settings import FALL_CONFIRM_FRAMES, FALL_CONFIRMATION_THRESHOLD

logger = logging.getLogger(__name__)


class FallDetector:
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    NOSE = 0

    def __init__(self, velocity_threshold: float = 20.0, angle_threshold: float = 45.0):
        self.velocity_threshold = velocity_threshold
        self.angle_threshold = angle_threshold
        self._history: deque = deque(maxlen=FALL_CONFIRM_FRAMES)
        self._frame_count = 0
        self._prev_hip_center: np.ndarray | None = None

    def detect(self, landmarks: list[dict]) -> dict:
        result = {"fall": False, "confidence": 0.0, "reasons": []}
        self._frame_count += 1

        hip_center = self._get_hip_center(landmarks)
        if hip_center is None:
            self._prev_hip_center = None
            return result

        hip_angle = self._compute_hip_angle(landmarks)
        vertical_velocity = 0.0

        if self._prev_hip_center is not None:
            vertical_velocity = hip_center[1] - self._prev_hip_center[1]

        self._prev_hip_center = hip_center
        is_horizontal = hip_angle is not None and hip_angle > self.angle_threshold
        is_fast_drop = vertical_velocity > self.velocity_threshold

        ground_proximity = self._check_ground_proximity(landmarks)

        confidence = 0.0
        reasons = []

        if is_horizontal:
            confidence += 0.4
            reasons.append(f"hip_angle={hip_angle:.1f}deg")

        if is_fast_drop:
            confidence += 0.3
            reasons.append(f"velocity={vertical_velocity:.1f}")

        if ground_proximity:
            confidence += 0.3
            reasons.append("near_ground")

        self._history.append(confidence)

        if len(self._history) >= FALL_CONFIRM_FRAMES:
            mean_conf = np.mean(self._history)
            if mean_conf > FALL_CONFIRMATION_THRESHOLD:
                result["fall"] = True
                result["confidence"] = float(mean_conf)

        result["reasons"] = reasons
        return result

    def _get_hip_center(self, landmarks: list[dict]) -> np.ndarray | None:
        if self.LEFT_HIP >= len(landmarks) or self.RIGHT_HIP >= len(landmarks):
            return None
        lh = np.array([landmarks[self.LEFT_HIP]["x"], landmarks[self.LEFT_HIP]["y"]])
        rh = np.array([landmarks[self.RIGHT_HIP]["x"], landmarks[self.RIGHT_HIP]["y"]])
        return (lh + rh) / 2

    def _compute_hip_angle(self, landmarks: list[dict]) -> float | None:
        if (self.LEFT_SHOULDER >= len(landmarks) or self.RIGHT_SHOULDER >= len(landmarks)
                or self.LEFT_HIP >= len(landmarks) or self.RIGHT_HIP >= len(landmarks)):
            return None

        shoulder_center = np.array([
            (landmarks[self.LEFT_SHOULDER]["x"] + landmarks[self.RIGHT_SHOULDER]["x"]) / 2,
            (landmarks[self.LEFT_SHOULDER]["y"] + landmarks[self.RIGHT_SHOULDER]["y"]) / 2,
        ])
        hip_center = np.array([
            (landmarks[self.LEFT_HIP]["x"] + landmarks[self.RIGHT_HIP]["x"]) / 2,
            (landmarks[self.LEFT_HIP]["y"] + landmarks[self.RIGHT_HIP]["y"]) / 2,
        ])

        vertical = np.array([0, 1])
        body_vec = hip_center - shoulder_center
        norm = np.linalg.norm(body_vec)
        if norm < 1e-6:
            return None

        body_vec = body_vec / norm
        angle = np.degrees(np.arccos(np.clip(np.dot(body_vec, vertical), -1.0, 1.0)))
        return angle

    def _check_ground_proximity(self, landmarks: list[dict]) -> bool:
        required = [self.LEFT_SHOULDER, self.RIGHT_SHOULDER, self.LEFT_HIP, self.RIGHT_HIP]
        if any(i >= len(landmarks) for i in required):
            return False

        shoulder_y = (landmarks[self.LEFT_SHOULDER]["y"] + landmarks[self.RIGHT_SHOULDER]["y"]) / 2
        hip_center = self._get_hip_center(landmarks)
        if hip_center is None:
            return False

        torso_height = max(hip_center[1] - shoulder_y, 1)
        return torso_height < 60
