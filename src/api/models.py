from datetime import datetime
from pydantic import BaseModel


class DetectionEvent(BaseModel):
    id: int | None = None
    timestamp: str
    camera_id: str
    event_type: str
    confidence: float
    snapshot_path: str | None = None
    details: dict = {}


class AlertMessage(BaseModel):
    type: str
    camera_id: str
    event_type: str
    confidence: float
    timestamp: str
    snapshot_b64: str | None = None


class CameraConfig(BaseModel):
    id: str
    rtsp_url: str
    label: str = ""
    enabled: bool = True
    zones: list[list[tuple[int, int]]] = []


class ReportRequest(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    camera_ids: list[str] = []
    event_types: list[str] = ["fall", "elopement", "loitering", "stranger"]


class NightReportRequest(ReportRequest):
    night_start: int = 22
    night_end: int = 6


class HighRiskReportRequest(ReportRequest):
    target_types: list[str] = ["fall"]
