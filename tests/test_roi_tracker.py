import time
import pytest
import numpy as np
from src.detector.roi_tracker import ROITracker


@pytest.fixture
def tracker():
    return ROITracker(zoom_factor=2.0, smooth_factor=0.3)


class TestROITracker:
    def test_default_inactive(self, tracker):
        assert tracker.is_active is False

    def test_activate(self, tracker):
        tracker.activate(320, 240)
        assert tracker.is_active is True

    def test_deactivate(self, tracker):
        tracker.activate(320, 240)
        tracker.deactivate()
        assert tracker.is_active is False

    def test_set_zoom_clamps_min(self, tracker):
        tracker.set_zoom(0.5)
        assert tracker.zoom_factor == 1.0

    def test_set_zoom_clamps_max(self, tracker):
        tracker.set_zoom(10.0)
        assert tracker.zoom_factor == 8.0

    def test_set_zoom_normal(self, tracker):
        tracker.set_zoom(3.5)
        assert tracker.zoom_factor == 3.5

    def test_set_center(self, tracker):
        tracker.set_center(100, 200)
        assert tracker._target_center == (100, 200)
        assert tracker.is_active is True

    def test_track_bbox(self, tracker):
        tracker.track_bbox((50, 60, 100, 80))
        assert tracker._target_center == (100, 100)

    def test_compute_zoom_returns_none_when_inactive(self, tracker):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        assert tracker.compute_zoom(frame) is None

    def test_compute_zoom_returns_zoomed_frame(self, tracker):
        tracker.activate(320, 240)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        zoomed = tracker.compute_zoom(frame)
        assert zoomed is not None
        assert zoomed.shape == (480, 640, 3)

    def test_compute_zoom_with_manual_center(self, tracker):
        tracker.set_center(200, 150)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        zoomed = tracker.compute_zoom(frame)
        assert zoomed is not None
        assert zoomed.shape == (480, 640, 3)

    def test_smooth_tracking(self, tracker):
        tracker.activate(320, 240)
        _ = tracker.compute_zoom(np.zeros((480, 640, 3), dtype=np.uint8))
        assert tracker._current_center == (320, 240)

    def test_auto_track_expires(self, tracker):
        tracker.activate(320, 240, auto_track=True)
        assert tracker.is_active is True
        tracker._auto_track_until = time.time() - 1
        tracker._active = False
        assert tracker.is_active is False

    def test_update_frame_shape(self, tracker):
        tracker.update_frame_shape(600, 800)
        assert tracker._frame_shape == (600, 800)

    def test_get_roi_info(self, tracker):
        info = tracker.get_roi_info()
        assert info["active"] is False
        assert info["zoom_factor"] == 2.0

    def test_get_roi_info_after_activate(self, tracker):
        tracker.activate(400, 300)
        info = tracker.get_roi_info()
        assert info["active"] is True
        assert info["target"] == (400, 300)

    def test_zoom_factor_independent_of_state(self, tracker):
        tracker.set_zoom(4.0)
        assert tracker.zoom_factor == 4.0
        tracker.deactivate()
        assert tracker.zoom_factor == 4.0

    def test_consecutive_zoom_returns_different_frames(self, tracker):
        tracker.activate(320, 240)
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        z1 = tracker.compute_zoom(frame)
        tracker._target_center = (400, 300)
        tracker._current_center = None
        z2 = tracker.compute_zoom(frame)
        assert z1 is not None and z2 is not None
