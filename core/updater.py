"""
RDP Guard - Auto Updater
Checks GitHub releases for newer versions and downloads/applies updates.
"""

import os
import sys
import json
import shutil
import logging
import zipfile
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

log = logging.getLogger(__name__)

# ── Change these to match your GitHub repo ────────────────────────────────
GITHUB_OWNER = "your-github-username"
GITHUB_REPO  = "rdp-guard"
# ─────────────────────────────────────────────────────────────────────────

CURRENT_VERSION = "1.0.0"   # bumped on each release
API_URL  = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
APP_DIR  = Path(__file__).parent.parent.resolve()


def parse_version(v: str) -> tuple:
    """Convert '1.2.3' → (1, 2, 3) for comparison."""
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except Exception:
        return (0, 0, 0)


def get_latest_release() -> dict | None:
    """
    Fetch the latest release info from GitHub API.
    Returns dict with keys: tag_name, body, assets  — or None on failure.
    """
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"User-Agent": f"RDPGuard/{CURRENT_VERSION}",
                     "Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        log.warning(f"Update check failed (network): {exc}")
    except Exception as exc:
        log.warning(f"Update check failed: {exc}")
    return None


def is_newer(remote_tag: str) -> bool:
    return parse_version(remote_tag) > parse_version(CURRENT_VERSION)


def download_and_apply(asset_url: str, progress_cb=None) -> bool:
    """
    Download the zip asset from GitHub and extract it over the current install.
    progress_cb(pct: int) is called with 0-100 during download.
    Returns True on success.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="rdpguard_update_"))
    zip_path = tmp_dir / "update.zip"
    try:
        # ── Download ──
        req = urllib.request.Request(
            asset_url,
            headers={"User-Agent": f"RDPGuard/{CURRENT_VERSION}"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk = 8192
            with open(zip_path, "wb") as f:
                while True:
                    data = resp.read(chunk)
                    if not data:
                        break
                    f.write(data)
                    downloaded += len(data)
                    if progress_cb and total:
                        progress_cb(int(downloaded / total * 90))

        # ── Extract ──
        with zipfile.ZipFile(zip_path, "r") as zf:
            # GitHub zips have a top-level folder — find it
            top = {p.split("/")[0] for p in zf.namelist() if "/" in p}
            prefix = (top.pop() + "/") if len(top) == 1 else ""

            for member in zf.namelist():
                if not member.startswith(prefix):
                    continue
                rel = member[len(prefix):]
                if not rel or rel.endswith("/"):
                    continue
                dest = APP_DIR / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)

        if progress_cb:
            progress_cb(100)
        log.info("Update applied successfully.")
        return True

    except Exception as exc:
        log.error(f"Update failed: {exc}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── Background worker thread ──────────────────────────────────────────────
class UpdateChecker(QThread):
    """Runs the update check off the main thread so the UI stays responsive."""

    # (tag, release_notes, asset_url)
    update_available = pyqtSignal(str, str, str)
    no_update        = pyqtSignal()
    check_failed     = pyqtSignal(str)
    # download progress 0-100
    progress         = pyqtSignal(int)
    update_done      = pyqtSignal(bool)   # True = success

    def __init__(self, mode: str = "check", asset_url: str = ""):
        """
        mode:
          'check'    — just check for a newer version
          'download' — download and apply asset_url
        """
        super().__init__()
        self.mode = mode
        self.asset_url = asset_url

    def run(self):
        if self.mode == "check":
            self._do_check()
        elif self.mode == "download":
            ok = download_and_apply(self.asset_url, self.progress.emit)
            self.update_done.emit(ok)

    def _do_check(self):
        release = get_latest_release()
        if release is None:
            self.check_failed.emit("Could not reach GitHub. Check your internet connection.")
            return
        tag   = release.get("tag_name", "")
        notes = release.get("body", "No release notes.")
        # Find the zip asset
        asset_url = ""
        for asset in release.get("assets", []):
            if asset.get("name", "").endswith(".zip"):
                asset_url = asset["browser_download_url"]
                break
        # Fall back to source zip
        if not asset_url:
            asset_url = release.get("zipball_url", "")

        if is_newer(tag):
            self.update_available.emit(tag, notes, asset_url)
        else:
            self.no_update.emit()
