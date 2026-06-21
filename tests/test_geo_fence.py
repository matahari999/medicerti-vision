import time
import pytest
from src.detector.geo_fence import GeoFenceDetector


def _make_landmarks(hip_x: float = 320, hip_y: float = 250) -> list[dict]:
    lm = [{"x": 320, "y": 100, "z": 0, "visibility": 0.9}] * 33
    lm[23] = {"x": hip_x - 30, "y": hip_y, "z": 0, "visibility": 0.9}
    lm[24] = {"x": hip_x + 30, "y": hip_y, "z": 0, "visibility": 0.9}
    return lm


class TestGeoFenceDetector:
    def test_no_polygon_no_detection(self):
        g = GeoFenceDetector()
        r = g.detect_elopement(_make_landmarks())
        assert r["elopement"] is False
        assert r["zone"] is None

    def test_inside_polygon_detected(self):
        g = GeoFenceDetector()
        g.set_polygon("zone_a", [(0, 0), (640, 0), (640, 480), (0, 480)])
        r = g.detect_elopement(_make_landmarks(320, 250))
        assert r["elopement"] is True
        assert r["zone"] == "zone_a"

    def test_outside_polygon_no_detection(self):
        g = GeoFenceDetector()
        g.set_polygon("zone_a", [(10, 10), (100, 10), (100, 100), (10, 100)])
        r = g.detect_elopement(_make_landmarks(500, 400))
        assert r["elopement"] is False

    def test_loitering_after_threshold(self):
        g = GeoFenceDetector()
        g.set_polygon("zone_a", [(0, 0), (640, 0), (640, 480), (0, 480)])
        lm = _make_landmarks(320, 250)
        r1 = g.detect_elopement(lm)
        assert r1["loitering"] is False
        time.sleep(0.01)
        from src.config.settings import LOITERING_SECONDS
        saved = g._entry_times["zone_a"].get(id(lm), 0)
        g._entry_times["zone_a"][id(lm)] = time.time() - LOITERING_SECONDS - 1
        r2 = g.detect_elopement(lm)
        assert r2["loitering"] is True

    def test_multiple_zones_first_match(self):
        g = GeoFenceDetector()
        g.set_polygon("big", [(0, 0), (640, 0), (640, 480), (0, 480)])
        g.set_polygon("small", [(10, 10), (100, 10), (100, 100), (10, 100)])
        r = g.detect_elopement(_make_landmarks(320, 250))
        assert r["zone"] == "big"

    def test_remove_polygon(self):
        g = GeoFenceDetector()
        g.set_polygon("z", [(0, 0), (10, 0), (10, 10), (0, 10)])
        g.remove_polygon("z")
        assert "z" not in g.get_polygons()

    def test_empty_landmarks_no_detection(self):
        g = GeoFenceDetector()
        g.set_polygon("z", [(0, 0), (640, 0), (640, 480), (0, 480)])
        r = g.detect_elopement([])
        assert r["elopement"] is False

    def test_insufficient_landmarks(self):
        g = GeoFenceDetector()
        r = g.detect_elopement([{"x": 0, "y": 0, "z": 0}] * 20)
        assert r["elopement"] is False

    def test_draw_zones_no_crash(self):
        import numpy as np
        g = GeoFenceDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        g.draw_zones(frame)
        g.set_polygon("z", [(10, 10), (100, 10), (100, 100), (10, 100)])
        result = g.draw_zones(frame)
        assert result.shape == (480, 640, 3)

    def test_get_polygons_returns_copy(self):
        g = GeoFenceDetector()
        g.set_polygon("z", [(0, 0), (10, 0), (10, 10), (0, 10)])
        d = g.get_polygons()
        d["new"] = []
        assert "new" not in g.get_polygons()
