"""
Zopi Guard - Monitor Worker
Background QThread that tails the Windows Security Event Log.
"""

import logging
import os
import re
from PyQt6.QtCore import QThread, pyqtSignal

# ── File logging setup ────────────────────────────────────────────────────
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "zopi_guard.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)

# ── pywin32 import ────────────────────────────────────────────────────────
WIN32_AVAILABLE = False
try:
    import win32evtlog
    WIN32_AVAILABLE = True
    log.info("pywin32 loaded OK — real mode enabled.")
except ImportError as e:
    log.warning(f"pywin32 not available ({e}) — DEMO mode.")
except Exception as e:
    log.warning(f"pywin32 load error ({e}) — DEMO mode.")


class MonitorWorker(QThread):
    failed_login   = pyqtSignal(str, int)
    ip_blocked     = pyqtSignal(str, str)
    ip_unblocked   = pyqtSignal(str)
    status_message = pyqtSignal(str)
    tick           = pyqtSignal()

    def __init__(self, db, config, firewall):
        super().__init__()
        self.db = db
        self.config = config
        self.fw = firewall
        self._running = False

    def run(self):
        self._running = True
        self._restore_permanent_blocks()
        if WIN32_AVAILABLE:
            log.info("Starting real event log monitor...")
            self.status_message.emit("Monitor started — watching Security Event Log.")
            self._run_real()
        else:
            log.warning("Starting DEMO mode.")
            self.status_message.emit("DEMO MODE — pywin32 not available.")
            self._run_demo()

    def stop(self):
        self._running = False
        self.status_message.emit("Monitor stopped.")

    # ── Real monitoring ───────────────────────────────────────────────
    def _run_real(self):
        try:
            handle = win32evtlog.OpenEventLog("localhost", "Security")
        except Exception as e:
            msg = f"Cannot open Security Event Log: {e} — run as Administrator."
            log.error(msg)
            self.status_message.emit(f"ERROR: {msg}")
            return

        flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

        # Drain existing events so we only catch new ones
        try:
            drained = 0
            while True:
                events = win32evtlog.ReadEventLog(handle, flags, 0)
                if not events:
                    break
                drained += len(events)
            log.info(f"Drained {drained} existing events. Watching for new ones...")
            self.status_message.emit(f"Ready — watching for new failed logins...")
        except Exception as e:
            log.error(f"Error draining log: {e}")

        tick_counter = 0
        while self._running:
            try:
                events = win32evtlog.ReadEventLog(handle, flags, 0)
                if events:
                    log.debug(f"Read {len(events)} new event(s).")
                    for event in events:
                        self._process_event(event)
            except Exception as e:
                log.error(f"Error reading event log: {e}")

            tick_counter += 1
            if tick_counter >= max(1, 60 // self.config.POLL_INTERVAL_SECONDS):
                self._expire_temp_blocks()
                self.tick.emit()
                tick_counter = 0

            self.msleep(self.config.POLL_INTERVAL_SECONDS * 1000)

        try:
            win32evtlog.CloseEventLog(handle)
        except Exception:
            pass

    def _process_event(self, event):
        try:
            event_id = event.EventID & 0xFFFF
            if event_id != 4625:
                return
            log.debug(f"4625 event found. StringInserts: {event.StringInserts}")
            ip       = self._extract_ip(event)
            username = self._extract_username(event)
            if ip:
                log.info(f"Failed login from: {ip}  user: {username}")
                self._handle_failed_login(ip, username)
            else:
                log.debug("4625 event — could not extract IP.")
        except Exception as e:
            log.error(f"Error processing event: {e}")

    @staticmethod
    def _extract_ip(event):
        try:
            strings = event.StringInserts
            if not strings:
                return None
            # Primary: index 19 is IpAddress in 4625 events
            if len(strings) > 19:
                ip = strings[19].strip()
                if ip and ip not in ("-", "", "::1", "127.0.0.1"):
                    return ip
            # Fallback: scan all fields for an IP pattern
            ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
            for field in strings:
                if field:
                    match = ip_pattern.search(field.strip())
                    if match:
                        candidate = match.group()
                        if candidate not in ("0.0.0.0", "127.0.0.1"):
                            return candidate
        except Exception as e:
            log.debug(f"IP extraction error: {e}")
        return None

    @staticmethod
    def _extract_username(event) -> str:
        """Extract attempted username from a 4625 event (field index 5)."""
        try:
            strings = event.StringInserts
            if strings and len(strings) > 5:
                username = strings[5].strip()
                if username and username not in ("-", "", "ANONYMOUS LOGON"):
                    return username
        except Exception:
            pass
        return ""

    # ── Demo mode ─────────────────────────────────────────────────────
    def _run_demo(self):
        import random, time
        demo_ips = [
            "185.234.218.42", "91.240.118.172", "45.33.32.156",
            "203.0.113.99",   "198.51.100.14",  "192.0.2.200",
        ]
        tick_counter = 0
        while self._running:
            time.sleep(2)
            if random.random() < 0.6:
                self._handle_failed_login(random.choice(demo_ips))
            tick_counter += 1
            if tick_counter >= 15:
                self._expire_temp_blocks()
                self.tick.emit()
                tick_counter = 0

    # ── Core logic ────────────────────────────────────────────────────
    def _handle_failed_login(self, ip: str, username: str = ""):
        if self.config.is_whitelisted(ip):
            log.debug(f"Whitelisted, ignoring: {ip}")
            return
        if self.db.is_permanently_blocked(ip):
            log.debug(f"Already permanently blocked: {ip}")
            return

        attempts = self.db.record_attempt(ip, username)
        log.info(f"Attempt #{attempts} from {ip}  user: {username}")
        self.failed_login.emit(ip, attempts)

        if attempts >= self.config.PERM_BLOCK_THRESHOLD:
            log.warning(f"PERMANENT BLOCK: {ip}")
            self.fw.block_ip(ip, permanent=True)
            self.db.set_permanent_block(ip)
            self.ip_blocked.emit(ip, "perm")
            try:
                from core.emailer import send_permanent_block_alert
                send_permanent_block_alert(self.config, ip, attempts)
            except Exception as exc:
                log.error(f"Email alert failed: {exc}")

        elif attempts >= self.config.TEMP_BLOCK_THRESHOLD:
            if not self.db.is_temp_blocked(ip):
                log.warning(f"TEMP BLOCK: {ip}")
                self.fw.block_ip(ip, permanent=False)
                self.db.set_temp_block(ip, self.config.TEMP_BLOCK_MINUTES)
                self.ip_blocked.emit(ip, "temp")

    def _expire_temp_blocks(self):
        for ip in self.db.get_expired_temp_blocks():
            log.info(f"Temp block expired: {ip}")
            self.fw.unblock_ip(ip)
            self.db.clear_temp_block(ip)
            self.ip_unblocked.emit(ip)

    def _restore_permanent_blocks(self):
        blocks = self.db.get_permanent_blocks()
        log.info(f"Restoring {len(blocks)} permanent block(s).")
        for ip in blocks:
            if not self.fw.is_blocked(ip):
                self.fw.block_ip(ip, permanent=True)
        self.status_message.emit(f"Restored {len(blocks)} permanent firewall rule(s).")
