import logging
import os
import urllib.request
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n-pose.onnx"
MODEL_PATH = MODEL_DIR / "yolov8n-pose.onnx"

INPUT_SIZE = 640
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45

COCO_TO_BLAZEPOSE = {
    0: 0, 1: None, 2: None, 3: None, 4: None,
    5: 11, 6: 12, 7: None, 8: None, 9: None, 10: None,
    11: 23, 12: 24, 13: 25, 14: 26, 15: 27, 16: 28,
}

NUM_KPTS = 17
COCO_SKELETON = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16),
]


class YoloPoseEstimator:
    def __init__(self, model_path: str | None = None, conf_threshold: float = CONFIDENCE_THRESHOLD):
        self.conf_threshold = conf_threshold
        self._session = None
        self._model_path = model_path or str(MODEL_PATH)
        self._input_name = None
        self._output_name = None

    def _lazy_init(self):
        if self._session is not None:
            return
        try:
            import onnxruntime as ort
        except ImportError:
            logger.warning("onnxruntime not installed, falling back")
            return

        if not os.path.exists(self._model_path):
            self._download_model()

        if not os.path.exists(self._model_path):
            logger.error(f"Model not found at {self._model_path}")
            return

        try:
            self._session = ort.InferenceSession(
                self._model_path,
                providers=["CPUExecutionProvider"],
            )
            self._input_name = self._session.get_inputs()[0].name
            self._output_name = self._session.get_outputs()[0].name
            logger.info(f"YOLO-Pose model loaded: {self._model_path}")
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            self._session = None

    def _download_model(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        try:
            logger.info(f"Downloading YOLO-Pose model from {MODEL_URL}...")
            urllib.request.urlretrieve(MODEL_URL, self._model_path)
            logger.info(f"Model downloaded: {self._model_path}")
            return
        except Exception as e:
            logger.warning(f"Direct download failed: {e}")

        try:
            logger.info("Falling back to ultralytics export...")
            from ultralytics import YOLO
            model = YOLO("yolov8n-pose.pt")
            model.export(format="onnx", imgsz=INPUT_SIZE, simplify=True)
            src = Path("yolov8n-pose.onnx")
            if src.exists():
                import shutil
                shutil.move(str(src), self._model_path)
                logger.info(f"Model exported: {self._model_path}")
        except Exception as e:
            logger.error(f"Ultralytics export failed: {e}")

    def _preprocess(self, frame: np.ndarray) -> tuple[np.ndarray, float, float, float, float]:
        h, w = frame.shape[:2]
        scale = min(INPUT_SIZE / w, INPUT_SIZE / h)
        nw, nh = int(w * scale), int(h * scale)
        pad_x = (INPUT_SIZE - nw) // 2
        pad_y = (INPUT_SIZE - nh) // 2

        resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.zeros((INPUT_SIZE, INPUT_SIZE, 3), dtype=np.uint8)
        canvas[pad_y:pad_y + nh, pad_x:pad_x + nw] = resized

        blob = canvas.astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))
        blob = np.expand_dims(blob, axis=0)
        return blob, scale, pad_x, pad_y, w, h

    def process(self, frame: np.ndarray) -> tuple[list[dict] | None, np.ndarray | None]:
        self._lazy_init()
        if self._session is None:
            logger.debug("ONNX session not available, returning None")
            return None, frame

        try:
            blob, scale, pad_x, pad_y, orig_w, orig_h = self._preprocess(frame)
            outputs = self._session.run([self._output_name], {self._input_name: blob})
            preds = outputs[0][0]

            landmarks = self._postprocess(preds, scale, pad_x, pad_y, orig_w, orig_h)
            return landmarks, frame
        except Exception as e:
            logger.error(f"YOLO-Pose inference error: {e}")
            return None, frame

    def _postprocess(self, preds: np.ndarray, scale: float,
                     pad_x: int, pad_y: int, orig_w: int, orig_h: int) -> list[dict] | None:
        preds = np.transpose(preds, (1, 0))
        bboxes = preds[:, :4]
        scores = preds[:, 4:5]
        kpts = preds[:, 5:].reshape(-1, NUM_KPTS, 3)

        mask = scores.flatten() > self.conf_threshold
        if not mask.any():
            return None

        bboxes = bboxes[mask]
        scores = scores[mask]
        kpts = kpts[mask]

        keep = self._nms(bboxes, scores.flatten(), IOU_THRESHOLD)
        if not len(keep):
            return None

        best = keep[0]
        landmarks = [{"x": 0, "y": 0, "z": 0, "visibility": 0}] * 33

        for coco_idx, blaze_idx in COCO_TO_BLAZEPOSE.items():
            if blaze_idx is None:
                continue
            x_raw = kpts[best, coco_idx, 0]
            y_raw = kpts[best, coco_idx, 1]
            conf = kpts[best, coco_idx, 2]

            x = (float(x_raw) - pad_x) / scale
            y = (float(y_raw) - pad_y) / scale
            x = max(0, min(orig_w - 1, x))
            y = max(0, min(orig_h - 1, y))

            landmarks[blaze_idx] = {
                "x": x, "y": y, "z": 0,
                "visibility": float(conf),
            }

        nose_kpt = kpts[best, 0]
        nose_x = (float(nose_kpt[0]) - pad_x) / scale
        nose_y = (float(nose_kpt[1]) - pad_y) / scale
        landmarks[0] = {
            "x": max(0, min(orig_w - 1, nose_x)),
            "y": max(0, min(orig_h - 1, nose_y)),
            "z": 0,
            "visibility": float(nose_kpt[2]),
        }

        return landmarks

    def _nms(self, bboxes: np.ndarray, scores: np.ndarray, iou_thresh: float) -> list[int]:
        x1 = bboxes[:, 0] - bboxes[:, 2] / 2
        y1 = bboxes[:, 1] - bboxes[:, 3] / 2
        x2 = bboxes[:, 0] + bboxes[:, 2] / 2
        y2 = bboxes[:, 1] + bboxes[:, 3] / 2

        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        keep = []

        while len(order) > 0:
            i = order[0]
            keep.append(i)
            if len(order) == 1:
                break

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            order = order[1:][iou <= iou_thresh]

        return keep

    def draw_skeleton(self, frame: np.ndarray, landmarks: list[dict]) -> np.ndarray:
        overlay = frame.copy()
        h, w = frame.shape[:2]

        for idx, lm in enumerate(landmarks):
            vis = lm.get("visibility", 0)
            if vis < 0.3:
                continue
            cx, cy = int(lm["x"]), int(lm["y"])
            if 0 <= cx < w and 0 <= cy < h:
                cv2.circle(overlay, (cx, cy), 4, (0, 255, 0), -1)

        for (i, j) in COCO_SKELETON:
            bi = COCO_TO_BLAZEPOSE.get(i)
            bj = COCO_TO_BLAZEPOSE.get(j)
            if bi is None or bj is None:
                continue
            if bi >= len(landmarks) or bj >= len(landmarks):
                continue
            if landmarks[bi].get("visibility", 0) < 0.3 or landmarks[bj].get("visibility", 0) < 0.3:
                continue
            pt1 = (int(landmarks[bi]["x"]), int(landmarks[bi]["y"]))
            pt2 = (int(landmarks[bj]["x"]), int(landmarks[bj]["y"]))
            cv2.line(overlay, pt1, pt2, (0, 255, 0), 2)

        return cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)

    def close(self):
        self._session = None
