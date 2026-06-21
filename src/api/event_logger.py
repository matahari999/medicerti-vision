import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterator

from src.config.settings import SQLITE_PATH

logger = logging.getLogger(__name__)


class EventLogger:
    def __init__(self):
        self._lock = threading.Lock()
        Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    snapshot_path TEXT,
                    details TEXT DEFAULT '{}'
                )
            """)
            self._conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)
            """)
            self._conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)
            """)
            self._conn.commit()

    def insert(self, camera_id: str, event_type: str, confidence: float,
               snapshot_path: str | None = None, details: dict | None = None):
        with self._lock:
            self._conn.execute(
                "INSERT INTO events (timestamp, camera_id, event_type, confidence, snapshot_path, details) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.now().isoformat(),
                    camera_id,
                    event_type,
                    confidence,
                    snapshot_path,
                    json.dumps(details or {}),
                ),
            )
            self._conn.commit()

    def query(self, limit: int = 100, offset: int = 0,
              camera_id: str | None = None,
              event_type: str | None = None,
              start: str | None = None,
              end: str | None = None) -> list[dict]:
        sql = "SELECT * FROM events WHERE 1=1"
        params = []

        if camera_id:
            sql += " AND camera_id = ?"
            params.append(camera_id)
        if event_type:
            sql += " AND event_type = ?"
            params.append(event_type)
        if start:
            sql += " AND timestamp >= ?"
            params.append(start)
        if end:
            sql += " AND timestamp <= ?"
            params.append(end)

        sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
            cols = [d[0] for d in self._conn.execute("PRAGMA table_info(events)").fetchall()]

        results = []
        for row in rows:
            event = dict(zip(cols, row))
            event["details"] = json.loads(event.get("details", "{}"))
            results.append(event)
        return results

    def count(self, camera_id: str | None = None,
              event_type: str | None = None,
              start: str | None = None,
              end: str | None = None) -> int:
        sql = "SELECT COUNT(*) FROM events WHERE 1=1"
        params = []

        if camera_id:
            sql += " AND camera_id = ?"
            params.append(camera_id)
        if event_type:
            sql += " AND event_type = ?"
            params.append(event_type)
        if start:
            sql += " AND timestamp >= ?"
            params.append(start)
        if end:
            sql += " AND timestamp <= ?"
            params.append(end)

        with self._lock:
            return self._conn.execute(sql, params).fetchone()[0]

    def query_for_report(self, start: str, end: str,
                         camera_ids: list[str] | None = None,
                         event_types: list[str] | None = None) -> list[dict]:
        sql = "SELECT * FROM events WHERE timestamp >= ? AND timestamp <= ?"
        params = [start, end]

        if camera_ids:
            placeholders = ",".join("?" for _ in camera_ids)
            sql += f" AND camera_id IN ({placeholders})"
            params.extend(camera_ids)
        if event_types:
            placeholders = ",".join("?" for _ in event_types)
            sql += f" AND event_type IN ({placeholders})"
            params.extend(event_types)

        sql += " ORDER BY timestamp DESC"

        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
            cols = [d[0] for d in self._conn.execute("PRAGMA table_info(events)").fetchall()]

        results = []
        for row in rows:
            event = dict(zip(cols, row))
            event["details"] = json.loads(event.get("details", "{}"))
            results.append(event)
        return results

    def get_recent_events(self, seconds: int = 30) -> list[dict]:
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(seconds=seconds)).isoformat()
        return self.query(start=cutoff, limit=50)

    def close(self):
        self._conn.close()
