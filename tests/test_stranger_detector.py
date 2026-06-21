import os
import tempfile
import pytest
import numpy as np


@pytest.fixture
def detector(monkeypatch):
    tmp = tempfile.TemporaryDirectory()
    db_path = os.path.join(tmp.name, "whitelist.db")
    monkeypatch.setattr("src.detector.stranger_detector.WHITELIST_DB_PATH", db_path)
    from src.detector.stranger_detector import StrangerDetector
    d = StrangerDetector(match_threshold=0.6, restricted_hours=(22, 6))
    yield d
    tmp.cleanup()


@pytest.fixture
def detector_with_face(detector):
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    detector.register_face("doctor_kim", img, role="의사")
    return detector


class TestWhitelist:
    def test_empty_list(self, detector):
        assert detector.get_whitelist() == []

    def test_register_and_list(self, detector):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        detector.register_face("nurse_lee", img)
        wl = detector.get_whitelist()
        assert len(wl) == 1
        assert wl[0]["name"] == "nurse_lee"

    def test_remove_face(self, detector_with_face):
        assert len(detector_with_face.get_whitelist()) == 1
        detector_with_face.remove_face("doctor_kim")
        assert len(detector_with_face.get_whitelist()) == 0

    def test_remove_nonexistent(self, detector):
        detector.remove_face("nobody")

    def test_double_register(self, detector):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        detector.register_face("dup", img)
        detector.register_face("dup", img)
        assert len(detector.get_whitelist()) == 2

    def test_whitelist_cache_after_register(self, detector):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        detector.register_face("n1", img)
        assert "n1" in detector._whitelist_cache

    def test_whitelist_cache_after_remove(self, detector_with_face):
        detector_with_face.remove_face("doctor_kim")
        assert "doctor_kim" not in detector_with_face._whitelist_cache


class TestEncoding:
    def test_extract_encoding(self, detector):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        enc = detector._extract_encoding(img)
        assert enc is not None
        assert enc.dtype == np.float32
        assert enc.shape == (10000,)

    def test_extract_encoding_small(self, detector):
        img = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        enc = detector._extract_encoding(img)
        assert enc is not None

    def test_invalid_image(self, detector):
        ok = detector.register_face("bad", np.array([]))
        assert ok is False

    def test_match_face_empty_cache(self, detector):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        assert detector._match_face(img) is None


class TestRecognizer:
    def test_train_no_data(self, detector):
        assert detector.train_recognizer() is False

    def test_train_with_data(self, detector):
        detector._whitelist_cache["test"] = np.random.rand(10000).astype(np.float32)
        detector._lazy_init()
        assert detector._recognizer is not None
        assert detector.train_recognizer() is True

    def test_stranger_events_empty(self, detector):
        assert detector.get_stranger_events() == []


class TestRestrictedHours:
    def test_night_hours(self, detector):
        from datetime import datetime
        h = datetime.now().hour
        expected = (22 <= h) or (h <= 6)
        assert detector._is_restricted_hour() == expected

    def test_always_restricted(self, monkeypatch):
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        monkeypatch.setattr("src.detector.stranger_detector.WHITELIST_DB_PATH", os.path.join(tmp.name, "w.db"))
        from src.detector.stranger_detector import StrangerDetector
        d = StrangerDetector(restricted_hours=(0, 23))
        assert d._is_restricted_hour() is True
        tmp.cleanup()


class TestYoloPose:
    def test_model_exists(self):
        from src.detector.yolo_pose import MODEL_PATH
        assert MODEL_PATH.exists(), f"Model not found: {MODEL_PATH}"

    def test_estimator_initializes(self):
        import numpy as np
        from src.detector.yolo_pose import YoloPoseEstimator
        est = YoloPoseEstimator()
        est._lazy_init()
        assert est._session is not None

    def test_inference_on_noise_returns_none(self):
        import numpy as np
        from src.detector.yolo_pose import YoloPoseEstimator
        est = YoloPoseEstimator()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        lm, _ = est.process(frame)
        assert lm is None


class TestDetection:
    def test_no_mediapipe_returns_no_stranger(self, detector):
        detector._face_detector = None
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        r = detector.detect(frame, camera_id="cam0")
        assert r["stranger"] is False
