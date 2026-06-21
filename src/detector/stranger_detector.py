import logging
import sqlite3
import json
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from src.config.settings import WHITELIST_DB_PATH, FACE_ENCRYPTION_KEY_PATH

logger = logging.getLogger(__name__)


class StrangerDetector:
    def __init__(self, match_threshold: float = 0.6, restricted_hours: tuple = (22, 6)):
        self.match_threshold = match_threshold
        self.restricted_hours = restricted_hours
        self._lock = threading.Lock()
        self._face_detector = None
        self._recognizer = None
        self._whitelist_cache: dict[str, np.ndarray] = {}
        Path(WHITELIST_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _lazy_init(self):
        if self._face_detector is not None:
            return
        try:
            import mediapipe as mp
            self._face_detector = mp.solutions.face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.5
            )
            logger.info("MediaPipe Face Detection initialized")
        except Exception as e:
            logger.warning(f"MediaPipe face detection init failed: {e}")
            self._face_detector = None

        self._recognizer = cv2.face.LBPHFaceRecognizer_create()
        self._load_whitelist_cache()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(WHITELIST_DB_PATH)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT DEFAULT '',
                    face_encoding BLOB NOT NULL,
                    registered_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stranger_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    restricted_hour INTEGER DEFAULT 0,
                    restricted_zone INTEGER DEFAULT 0,
                    snapshot_path TEXT,
                    details TEXT DEFAULT '{}'
                )
            """)
            conn.commit()
            conn.close()

    def _load_whitelist_cache(self):
        try:
            conn = sqlite3.connect(WHITELIST_DB_PATH)
            rows = conn.execute("SELECT name, face_encoding FROM whitelist").fetchall()
            conn.close()
            for name, blob in rows:
                arr = np.frombuffer(blob, dtype=np.float32).copy()
                self._whitelist_cache[name] = arr
            logger.info(f"Loaded {len(self._whitelist_cache)} whitelist entries")
        except Exception as e:
            logger.warning(f"Failed to load whitelist cache: {e}")

    def register_face(self, name: str, face_image: np.ndarray, role: str = "") -> bool:
        self._lazy_init()
        encoding = self._extract_encoding(face_image)
        if encoding is None:
            logger.warning(f"Failed to extract face encoding for {name}")
            return False

        blob = encoding.astype(np.float32).tobytes()
        now = datetime.now().isoformat()
        with self._lock:
            conn = sqlite3.connect(WHITELIST_DB_PATH)
            conn.execute(
                "INSERT INTO whitelist (name, role, face_encoding, registered_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (name, role, blob, now, now),
            )
            conn.commit()
            conn.close()
        self._whitelist_cache[name] = encoding
        logger.info(f"Registered face: {name} ({role})")
        return True

    def remove_face(self, name: str) -> bool:
        with self._lock:
            conn = sqlite3.connect(WHITELIST_DB_PATH)
            conn.execute("DELETE FROM whitelist WHERE name = ?", (name,))
            conn.commit()
            conn.close()
        self._whitelist_cache.pop(name, None)
        logger.info(f"Removed face: {name}")
        return True

    def get_whitelist(self) -> list[dict]:
        conn = sqlite3.connect(WHITELIST_DB_PATH)
        rows = conn.execute("SELECT id, name, role, registered_at, updated_at FROM whitelist").fetchall()
        conn.close()
        return [
            {"id": r[0], "name": r[1], "role": r[2], "registered_at": r[3], "updated_at": r[4]}
            for r in rows
        ]

    def detect(self, frame: np.ndarray, camera_id: str = "cam0",
               zone_restricted: bool = False) -> dict:
        self._lazy_init()
        result = {"stranger": False, "confidence": 0.0, "matched_name": None, "faces": [], "reasons": []}

        if self._face_detector is None:
            return result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detections = self._face_detector.process(rgb)

        if not detections.detections:
            return result

        is_restricted_hour = self._is_restricted_hour()
        h, w = frame.shape[:2]
        faces_info = []

        for detection in detections.detections:
            bbox = detection.location_data.relative_bounding_box
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            bw = int(bbox.width * w)
            bh = int(bbox.height * h)
            x = max(0, x); y = max(0, y)
            bw = min(bw, w - x); bh = min(bh, h - y)

            score = detection.score[0] if detection.score else 0.0
            face_roi = frame[y:y+bh, x:x+bw]

            matched_name = self._match_face(face_roi) if face_roi.size > 0 else None

            face_info = {
                "bbox": [x, y, bw, bh],
                "score": float(score),
                "matched_name": matched_name,
            }
            faces_info.append(face_info)

            if matched_name is None:
                reasons = []
                if is_restricted_hour:
                    reasons.append("restricted_hours")
                if zone_restricted:
                    reasons.append("restricted_zone")
                if not reasons:
                    reasons.append("unregistered")

                result["stranger"] = True
                result["confidence"] = max(result["confidence"], float(score))
                result["matched_name"] = None
                result["reasons"] = reasons

        result["faces"] = faces_info

        if result["stranger"]:
            self._log_stranger_event(camera_id, result)

        return result

    def _match_face(self, face_roi: np.ndarray) -> str | None:
        if not self._whitelist_cache:
            return None

        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (100, 100))

        best_name = None
        best_conf = float("inf")

        for name, _ in self._whitelist_cache.items():
            try:
                label, conf = self._recognizer.predict(gray)
                if conf < best_conf:
                    best_conf = conf
                    best_name = name
            except Exception:
                continue

        if best_name and best_conf < (1.0 - self.match_threshold) * 100:
            return best_name
        return None

    def _extract_encoding(self, face_image: np.ndarray) -> np.ndarray | None:
        try:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (100, 100))
            return gray.flatten().astype(np.float32) / 255.0
        except Exception as e:
            logger.warning(f"Encoding extraction failed: {e}")
            return None

    def _is_restricted_hour(self) -> bool:
        hour = datetime.now().hour
        start, end = self.restricted_hours
        if start <= end:
            return start <= hour <= end
        return hour >= start or hour <= end

    def _log_stranger_event(self, camera_id: str, detection: dict):
        now = datetime.now().isoformat()
        details = {
            "reasons": detection["reasons"],
            "faces": [
                {"bbox": f["bbox"], "score": f["score"]}
                for f in detection["faces"] if f["matched_name"] is None
            ],
        }
        is_restricted = "restricted_hours" in detection["reasons"]
        is_zone = "restricted_zone" in detection["reasons"]

        with self._lock:
            conn = sqlite3.connect(WHITELIST_DB_PATH)
            conn.execute(
                "INSERT INTO stranger_events (timestamp, camera_id, confidence, restricted_hour, restricted_zone, details) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (now, camera_id, detection["confidence"], int(is_restricted), int(is_zone), json.dumps(details)),
            )
            conn.commit()
            conn.close()

    def get_stranger_events(self, limit: int = 100) -> list[dict]:
        conn = sqlite3.connect(WHITELIST_DB_PATH)
        rows = conn.execute(
            "SELECT * FROM stranger_events ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        cols = [d[0] for d in conn.execute("PRAGMA table_info(stranger_events)").fetchall()]
        conn.close()
        results = []
        for row in rows:
            event = dict(zip(cols, row))
            event["details"] = json.loads(event.get("details", "{}"))
            results.append(event)
        return results

    def train_recognizer(self):
        if len(self._whitelist_cache) < 1:
            logger.warning("No whitelist entries to train on")
            return False

        faces = []
        labels = []
        label_map = {}

        for idx, (name, encoding) in enumerate(self._whitelist_cache.items()):
            img = (encoding * 255.0).astype(np.uint8).reshape(100, 100)
            faces.append(img)
            labels.append(idx)
            label_map[idx] = name

        self._recognizer.train(faces, np.array(labels))
        self._label_map = label_map
        logger.info(f"Recognizer trained on {len(faces)} faces")
        return True
