import json
import shutil
from pathlib import Path
import pytest
from src.accreditation.report_gen import (
    AccreditationReport,
    NightSecurityReport,
    HighRiskObservationReport,
    AccessControlReport,
)
from src.config.settings import REPORT_OUTPUT_DIR


SAMPLE_EVENTS = [
    {"timestamp": "2026-06-21T03:15:00", "camera_id": "cam1", "event_type": "fall",
     "confidence": 0.85, "details": {"velocity": 25.0, "angle": 50.0}},
    {"timestamp": "2026-06-21T10:30:00", "camera_id": "cam2", "event_type": "elopement",
     "confidence": 0.72, "details": {"zone": "exit_a"}},
    {"timestamp": "2026-06-21T14:45:00", "camera_id": "cam1", "event_type": "loitering",
     "confidence": 0.65, "details": {"zone": "ward_b", "seconds": 35}},
    {"timestamp": "2026-06-21T23:00:00", "camera_id": "cam3", "event_type": "stranger",
     "confidence": 0.90, "details": {"face_label": "unknown"}},
    {"timestamp": "2026-06-21T02:00:00", "camera_id": "cam1", "event_type": "fall",
     "confidence": 0.78, "details": {"velocity": 30.0}},
]


@pytest.fixture(autouse=True)
def clean_reports():
    yield
    for f in REPORT_OUTPUT_DIR.glob("test_*.pdf"):
        f.unlink(missing_ok=True)
    for f in REPORT_OUTPUT_DIR.glob("test_*.html"):
        f.unlink(missing_ok=True)


class TestAccreditationReport:
    def test_generates_pdf(self):
        gen = AccreditationReport()
        path = gen.generate(SAMPLE_EVENTS, facility_name="test")
        assert path.endswith(".pdf")
        assert Path(path).exists()
        assert Path(path).stat().st_size > 1000

    def test_generates_html_fallback_when_no_reportlab(self, monkeypatch):
        monkeypatch.setattr("src.accreditation.report_gen.HAS_REPORTLAB", False)
        gen = AccreditationReport()
        path = gen.generate(SAMPLE_EVENTS, facility_name="test")
        assert path.endswith(".html")
        assert Path(path).exists()

    def test_empty_events(self):
        gen = AccreditationReport()
        path = gen.generate([], facility_name="test")
        assert Path(path).exists()

    def test_event_type_kor(self):
        t = AccreditationReport._event_type_kor
        assert t("fall") == "낙상"
        assert t("elopement") == "이탈"
        assert t("loitering") == "배회"
        assert t("stranger") == "미등록 외부인"
        assert t("unknown") == "unknown"


class TestNightSecurityReport:
    def test_generates_pdf(self):
        gen = NightSecurityReport()
        path = gen.generate(SAMPLE_EVENTS, facility_name="test")
        assert path.endswith(".pdf")
        assert Path(path).exists()

    def test_filters_night_events(self):
        gen = NightSecurityReport()
        path = gen.generate(SAMPLE_EVENTS, facility_name="test", night_start=22, night_end=6)
        assert Path(path).exists()

    def test_no_night_events(self):
        gen = NightSecurityReport()
        day_events = [e for e in SAMPLE_EVENTS if "10:" in e["timestamp"] or "14:" in e["timestamp"]]
        path = gen.generate(day_events, facility_name="test", night_start=22, night_end=6)
        assert Path(path).exists()

    def test_is_night_hour(self):
        assert NightSecurityReport._is_night_hour("2026-06-21T23:00:00", 22, 6) is True
        assert NightSecurityReport._is_night_hour("2026-06-21T03:00:00", 22, 6) is True
        assert NightSecurityReport._is_night_hour("2026-06-21T10:00:00", 22, 6) is False
        assert NightSecurityReport._is_night_hour("bad", 22, 6) is False

    def test_wrap_around_hours(self):
        assert NightSecurityReport._is_night_hour("2026-06-21T23:00:00", 22, 6) is True
        assert NightSecurityReport._is_night_hour("2026-06-21T05:00:00", 22, 6) is True
        assert NightSecurityReport._is_night_hour("2026-06-21T12:00:00", 22, 6) is False


class TestHighRiskObservationReport:
    def test_generates_pdf(self):
        gen = HighRiskObservationReport()
        path = gen.generate(SAMPLE_EVENTS, facility_name="test")
        assert path.endswith(".pdf")
        assert Path(path).exists()

    def test_filters_to_target_types(self):
        gen = HighRiskObservationReport()
        path = gen.generate(SAMPLE_EVENTS, facility_name="test", target_types=["fall"])
        assert Path(path).exists()

    def test_empty_filtered(self):
        gen = HighRiskObservationReport()
        path = gen.generate(SAMPLE_EVENTS, facility_name="test", target_types=["unknown_type"])
        assert Path(path).exists()


class TestAccessControlReport:
    def test_generates_pdf(self):
        gen = AccessControlReport()
        path = gen.generate(SAMPLE_EVENTS, facility_name="test")
        assert path.endswith(".pdf")
        assert Path(path).exists()

    def test_filters_stranger_and_elopement(self):
        gen = AccessControlReport()
        path = gen.generate(SAMPLE_EVENTS, facility_name="test")
        assert Path(path).exists()

    def test_no_access_events(self):
        gen = AccessControlReport()
        safe = [e for e in SAMPLE_EVENTS if e["event_type"] == "loitering"]
        path = gen.generate(safe, facility_name="test")
        assert Path(path).exists()
