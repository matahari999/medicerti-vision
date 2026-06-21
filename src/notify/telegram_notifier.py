import logging
import os
import urllib.request
import urllib.parse
import json
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "notify_config.json"

EVENT_TYPE_LABELS = {
    "fall": "낙상 감지",
    "elopement": "이탈 감지",
    "loitering": "배회 감지",
    "stranger": "미등록 외부인",
}

EVENT_TYPE_EMOJIS = {
    "fall": "⚠️",
    "elopement": "🚶",
    "loitering": "👀",
    "stranger": "🔴",
}


class TelegramNotifier:
    def __init__(self):
        self._token: str = ""
        self._chat_id: str = ""
        self._enabled: bool = False
        self._alert_types: list[str] = ["fall", "elopement", "loitering", "stranger"]
        self._min_confidence: float = 0.5
        self._load_config()

    def _load_config(self):
        try:
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH) as f:
                    cfg = json.load(f)
                self._token = cfg.get("token", "")
                self._chat_id = cfg.get("chat_id", "")
                self._enabled = cfg.get("enabled", False) and bool(self._token and self._chat_id)
                self._alert_types = cfg.get("alert_types", self._alert_types)
                self._min_confidence = cfg.get("min_confidence", self._min_confidence)
                if self._enabled:
                    logger.info("Telegram notifier loaded (enabled)")
                else:
                    logger.info("Telegram notifier loaded (disabled)")
        except Exception as e:
            logger.warning("Failed to load Telegram config: %s", e)

    def _save_config(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        cfg = {
            "token": self._token,
            "chat_id": self._chat_id,
            "enabled": self._enabled,
            "alert_types": self._alert_types,
            "min_confidence": self._min_confidence,
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)

    def configure(self, token: str, chat_id: str,
                  alert_types: list[str] | None = None,
                  min_confidence: float = 0.5):
        self._token = token
        self._chat_id = chat_id
        self._alert_types = alert_types or ["fall", "elopement", "loitering", "stranger"]
        self._min_confidence = min_confidence
        self._enabled = bool(token and chat_id)
        self._save_config()
        logger.info("Telegram configured: chat=%s, types=%s, min_conf=%.2f",
                     chat_id, self._alert_types, min_confidence)

    def disable(self):
        self._enabled = False
        self._save_config()
        logger.info("Telegram notifier disabled")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def status(self) -> dict:
        return {
            "enabled": self._enabled,
            "chat_id": self._chat_id[:8] + "..." if self._chat_id else "",
            "has_token": bool(self._token),
            "alert_types": self._alert_types,
            "min_confidence": self._min_confidence,
        }

    def send_alert(self, event_type: str, camera_id: str,
                   confidence: float, timestamp: str,
                   snapshot_path: str | None = None,
                   details: dict | None = None) -> bool:
        if not self._enabled:
            return False
        if event_type not in self._alert_types:
            return False
        if confidence < self._min_confidence:
            return False

        emoji = EVENT_TYPE_EMOJIS.get(event_type, "")
        label = EVENT_TYPE_LABELS.get(event_type, event_type)
        text = (
            f"{emoji} <b>{label}</b>\n"
            f"카메라: <code>{camera_id}</code>\n"
            f"신뢰도: {confidence:.0%}\n"
            f"시간: {timestamp[:19]}"
        )
        if details:
            for k, v in details.items():
                if isinstance(v, list):
                    v = ", ".join(str(x) for x in v)
                text += f"\n{k}: {v}"

        ok = self._send_message(text)
        if ok and snapshot_path:
            try:
                self._send_photo(snapshot_path, caption=f"{emoji} {label} - {camera_id}")
            except Exception as e:
                logger.warning("Failed to send photo: %s", e)
        return ok

    def send_message(self, text: str) -> bool:
        if not self._enabled:
            return False
        return self._send_message(text)

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        if not self._enabled or not photo_path:
            return False
        try:
            return self._send_photo(photo_path, caption)
        except Exception as e:
            logger.warning("Failed to send photo: %s", e)
            return False

    def _send_message(self, text: str) -> bool:
        if not self._token or not self._chat_id:
            return False
        try:
            url = f"https://api.telegram.org/bot{self._token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": "HTML",
            }).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                return result.get("ok", False)
        except Exception as e:
            logger.warning("Telegram sendMessage failed: %s", e)
            return False

    def _send_photo(self, photo_path: str, caption: str = "") -> bool:
        import mimetypes
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        filename = Path(photo_path).name

        with open(photo_path, "rb") as f:
            file_bytes = f.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
            f"{self._chat_id}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + file_bytes + (
            f"\r\n--{boundary}\r\n"
            f'Content-Disposition: form-data; name="caption"\r\n\r\n'
            f"{caption}\r\n"
            f"--{boundary}--\r\n"
        ).encode("utf-8")

        url = f"https://api.telegram.org/bot{self._token}/sendPhoto"
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
