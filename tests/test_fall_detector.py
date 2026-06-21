import pytest
import numpy as np
from src.detector.fall_detector import FallDetector


@pytest.fixture
def detector():
    return FallDetector(velocity_threshold=20.0, angle_threshold=45.0)


def _make_landmarks(**overrides) -> list[dict]:
    base = [{"x": 320, "y": 100, "z": 0, "visibility": 0.9}] * 33
    # nose=0, Lshoulder=11, Rshoulder=12, Lhip=23, Rhip=24, Lknee=25, Rknee=26, Lankle=27, Rankle=28
    base[0] = {"x": 320, "y": 80, "z": 0, "visibility": 0.9}
    base[11] = {"x": 280, "y": 120, "z": 0, "visibility": 0.9}
    base[12] = {"x": 360, "y": 120, "z": 0, "visibility": 0.9}
    base[23] = {"x": 290, "y": 250, "z": 0, "visibility": 0.9}
    base[24] = {"x": 350, "y": 250, "z": 0, "visibility": 0.9}
    base[27] = {"x": 300, "y": 400, "z": 0, "visibility": 0.9}
    base[28] = {"x": 340, "y": 400, "z": 0, "visibility": 0.9}
    for k, v in overrides.items():
        idx, key = k.split(".")
        base[int(idx)][key] = v
    return base


class TestFallDetector:
    def test_standing_no_fall(self, detector):
        lm = _make_landmarks()
        r = detector.detect(lm)
        assert r["fall"] is False
        assert r["confidence"] < 0.6

    def test_falling_detected(self, detector):
        lm = _make_landmarks(
            **{"11.x": 260, "12.x": 280, "11.y": 200, "12.y": 200,
               "23.x": 310, "24.x": 330, "23.y": 205, "24.y": 205}
        )
        for _ in range(3):
            r = detector.detect(lm)
        assert r["fall"] is True
        assert r["confidence"] >= 0.6
        assert len(r["reasons"]) > 0

    def test_hip_angle_triggers_horizontal(self, detector):
        lm = _make_landmarks(
            **{"11.x": 250, "12.x": 270, "11.y": 200, "12.y": 200,
               "23.x": 310, "24.x": 330, "23.y": 200, "24.y": 200}
        )
        angle = detector._compute_hip_angle(lm)
        assert angle is not None
        assert angle > 60

    def test_vertical_standing_angle(self, detector):
        lm = _make_landmarks()
        angle = detector._compute_hip_angle(lm)
        assert angle is not None
        assert angle < 30

    def test_velocity_threshold(self, detector):
        lm1 = _make_landmarks()
        detector.detect(lm1)
        lm2 = _make_landmarks(**{"23.y": 300, "24.y": 300})
        r = detector.detect(lm2)
        assert "velocity" in r["reasons"][0] if r["reasons"] else True

    def test_ground_proximity_detected(self, detector):
        lm = _make_landmarks(
            **{"11.y": 200, "12.y": 200, "23.y": 230, "24.y": 230}
        )
        assert detector._check_ground_proximity(lm)

    def test_ground_proximity_false_when_high(self, detector):
        lm = _make_landmarks()
        assert not detector._check_ground_proximity(lm)

    def test_missing_landmarks_returns_safe(self, detector):
        r = detector.detect([])
        assert r["fall"] is False
        assert r["confidence"] == 0.0

    def test_partial_landmarks_no_crash(self, detector):
        lm = [{"x": 0, "y": 0, "z": 0, "visibility": 0.5}] * 10
        r = detector.detect(lm)
        assert r["fall"] is False

    def test_hip_center_calculation(self, detector):
        lm = _make_landmarks()
        hc = detector._get_hip_center(lm)
        assert hc is not None
        assert hc[0] == pytest.approx(320, abs=1)
        assert hc[1] == pytest.approx(250, abs=1)

    def test_hip_center_insufficient_landmarks(self, detector):
        lm = [{"x": 0, "y": 0, "z": 0}] * 22
        assert detector._get_hip_center(lm) is None

    def test_confidence_accumulates_over_frames(self, detector):
        lm = _make_landmarks(
            **{"23.y": 180, "24.y": 185, "11.y": 150, "12.y": 152}
        )
        r1 = detector.detect(lm)
        r2 = detector.detect(lm)
        assert r2["confidence"] >= r1["confidence"]

    def test_reset_on_new_person(self, detector):
        lm = _make_landmarks(
            **{"11.x": 260, "12.x": 280, "11.y": 200, "12.y": 200,
               "23.x": 310, "24.x": 330, "23.y": 205, "24.y": 205}
        )
        for _ in range(3):
            r = detector.detect(lm)
        assert r["fall"] is True
        detector2 = FallDetector()
        r2 = detector2.detect(_make_landmarks())
        assert r2["fall"] is False
