import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class PoseEstimator:
    LANDMARK_NAMES = [
        "nose", "left_eye_inner", "left_eye", "left_eye_outer",
        "right_eye_inner", "right_eye", "right_eye_outer",
        "left_ear", "right_ear", "mouth_left", "mouth_right",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_pinky", "right_pinky",
        "left_index", "right_index", "left_thumb", "right_thumb",
        "left_hip", "right_hip", "left_knee", "right_knee",
        "left_ankle", "right_ankle", "left_heel", "right_heel",
        "left_foot_index", "right_foot_index",
    ]

    SKELETON_CONNECTIONS = [
        (11, 12), (12, 14), (14, 16), (11, 13), (13, 15),
        (11, 23), (12, 24), (23, 24),
        (23, 25), (25, 27), (27, 29), (29, 31),
        (24, 26), (26, 28), (28, 30), (30, 32),
    ]

    def __init__(self, model_complexity: int = 1, min_detection_confidence: float = 0.5):
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self._pose = None

    def _lazy_init(self):
        if self._pose is not None:
            return
        import mediapipe as mp
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=0.5,
        )
        self._mp_drawing = mp.solutions.drawing_utils
        self._mp_pose = mp.solutions.pose
        logger.info(f"PoseEstimator initialized (complexity={self.model_complexity})")

    def process(self, frame: cv2.Mat) -> tuple[list[dict] | None, cv2.Mat | None]:
        self._lazy_init()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._pose.process(rgb)

        if not results.pose_landmarks:
            return None, frame

        h, w = frame.shape[:2]
        landmarks = []
        for lm in results.pose_landmarks.landmark:
            landmarks.append({
                "x": lm.x * w,
                "y": lm.y * h,
                "z": lm.z,
                "visibility": lm.visibility,
            })

        return landmarks, frame

    def draw_skeleton(self, frame: cv2.Mat, landmarks: list[dict]) -> cv2.Mat:
        overlay = frame.copy()
        h, w = frame.shape[:2]

        for idx, lm in enumerate(landmarks):
            if lm["visibility"] < 0.5:
                continue
            cx, cy = int(lm["x"]), int(lm["y"])
            cv2.circle(overlay, (cx, cy), 4, (0, 255, 0), -1)

        for connection in self._pose.PoseConnections if hasattr(self, '_pose') and self._pose else []:
            pass

        for (i, j) in self.SKELETON_CONNECTIONS:
            if i >= len(landmarks) or j >= len(landmarks):
                continue
            if landmarks[i]["visibility"] < 0.5 or landmarks[j]["visibility"] < 0.5:
                continue
            pt1 = (int(landmarks[i]["x"]), int(landmarks[i]["y"]))
            pt2 = (int(landmarks[j]["x"]), int(landmarks[j]["y"]))
            cv2.line(overlay, pt1, pt2, (0, 255, 0), 2)

        return cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)

    def close(self):
        if self._pose:
            self._pose.close()
            self._pose = None
