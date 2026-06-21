"""자동 업데이트 시스템 — GitHub Releases 기반"""

import json
import logging
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from datetime import datetime

from src.config.settings import BASE_DIR

logger = logging.getLogger(__name__)

VERSION_FILE = BASE_DIR / "version.json"
UPDATE_URL_DEFAULT = "https://api.github.com/repos/matahari999/medicerti-vision/releases/latest"

CURRENT_VERSION = "0.1.0"


def get_current_version() -> str:
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE) as f:
                data = json.load(f)
                return data.get("version", CURRENT_VERSION)
        except (json.JSONDecodeError, KeyError):
            pass
    return CURRENT_VERSION


def check_for_updates(update_url: str | None = None,
                      silent: bool = False) -> dict:
    url = update_url or UPDATE_URL_DEFAULT
    current = get_current_version()
    result = {
        "current_version": current,
        "latest_version": None,
        "update_available": False,
        "download_url": None,
        "release_notes": "",
        "error": None,
    }

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "medicerti-vision/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            release = json.loads(resp.read())
    except Exception as e:
        result["error"] = str(e)
        if not silent:
            logger.warning(f"Update check failed: {e}")
        return result

    latest = release.get("tag_name", "").lstrip("v")
    result["latest_version"] = latest

    if latest and _compare_versions(latest, current) > 0:
        result["update_available"] = True
        result["download_url"] = _find_asset_url(release)
        result["release_notes"] = release.get("body", "")[:500]
        if not silent:
            logger.info(f"Update available: {current} -> {latest}")
    else:
        if not silent:
            logger.info(f"Already up-to-date ({current})")

    return result


def _find_asset_url(release: dict) -> str | None:
    assets = release.get("assets", [])
    for asset in assets:
        name = asset.get("name", "")
        if name.endswith((".exe", ".msi", ".zip")):
            return asset.get("browser_download_url")
    return release.get("zipball_url")


def _compare_versions(v1: str, v2: str) -> int:
    parts1 = [int(x) for x in v1.split(".")]
    parts2 = [int(x) for x in v2.split(".")]
    for a, b in zip(parts1, parts2):
        if a > b:
            return 1
        if a < b:
            return -1
    return len(parts1) - len(parts2)


def apply_update(download_url: str, silent: bool = False) -> bool:
    if not download_url:
        logger.error("No download URL provided.")
        return False

    tmp_dir = Path(tempfile.mkdtemp(prefix="medicerti_update_"))
    archive_path = tmp_dir / "update.zip"

    try:
        if not silent:
            logger.info(f"Downloading update from {download_url}...")
        urllib.request.urlretrieve(download_url, archive_path)

        backup_dir = BASE_DIR / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        import zipfile
        with zipfile.ZipFile(archive_path, "r") as zf:
            extract_dir = tmp_dir / "extracted"
            extract_dir.mkdir()
            zf.extractall(extract_dir)

        _backup_and_swap(extract_dir, backup_dir, silent)

        version = get_current_version()
        logger.info(f"Update applied: {version}")
        return True

    except Exception as e:
        logger.error(f"Update failed: {e}")
        return False

    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _backup_and_swap(src_dir: Path, backup_dir: Path, silent: bool = False):
    for item in src_dir.iterdir():
        dest = BASE_DIR / item.name
        if dest.exists():
            backup_path = backup_dir / item.name
            if dest.is_file():
                shutil.copy2(dest, backup_path)
            else:
                shutil.copytree(dest, backup_path, dirs_exist_ok=True)

        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    if not silent:
        logger.info(f"Backup saved to {backup_dir}")
