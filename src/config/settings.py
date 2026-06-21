import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    _DATA_ROOT = Path(os.environ.get("APPDATA", "C:\\ProgramData")) / "medicerti-vision"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    _DATA_ROOT = BASE_DIR

DATA_DIR = _DATA_ROOT / "data"
EVENTS_DIR = DATA_DIR / "events"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

RTSP_RECONNECT_DELAYS = [1, 2, 4, 8, 15]
RTSP_MAX_RECONNECTS = 5
FRAME_QUEUE_MAXSIZE = 3
FALL_CONFIRM_FRAMES = 2
FALL_CONFIRMATION_THRESHOLD = 0.6
LOITERING_SECONDS = 30

SQLITE_PATH = str(EVENTS_DIR / "events.db")
REPORT_OUTPUT_DIR = DATA_DIR / "reports"

FACE_ENCRYPTION_KEY_PATH = BASE_DIR / ".face_key"
WHITELIST_DB_PATH = str(DATA_DIR / "whitelist.db")

NOTIFY_CONFIG_PATH = DATA_DIR / "notify_config.json"
