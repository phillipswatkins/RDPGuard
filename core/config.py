"""
RDP Guard - Config Manager
Reads and writes all settings to the SQLite database.
"""

import ipaddress
import json


DEFAULTS = {
    "temp_block_threshold": "5",
    "perm_block_threshold": "20",
    "temp_block_minutes": "15",
    "poll_interval_seconds": "5",
    "whitelist": json.dumps(["127.0.0.1", "::1"]),
    "email_enabled": "false",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": "587",
    "smtp_use_tls": "true",
    "smtp_user": "",
    "smtp_password": "",
    "alert_recipient": "",
    "alert_from": "",
}


class Config:
    def __init__(self, db):
        self._db = db
        # Seed defaults for any missing keys
        for key, val in DEFAULTS.items():
            if self._db.get_setting(key) is None:
                self._db.set_setting(key, val)

    def _get(self, key):
        return self._db.get_setting(key, DEFAULTS.get(key, ""))

    def _set(self, key, value):
        self._db.set_setting(key, value)

    # ── Thresholds ────────────────────────────────────────────────────
    @property
    def TEMP_BLOCK_THRESHOLD(self) -> int:
        return int(self._get("temp_block_threshold"))

    @TEMP_BLOCK_THRESHOLD.setter
    def TEMP_BLOCK_THRESHOLD(self, v):
        self._set("temp_block_threshold", str(v))

    @property
    def PERM_BLOCK_THRESHOLD(self) -> int:
        return int(self._get("perm_block_threshold"))

    @PERM_BLOCK_THRESHOLD.setter
    def PERM_BLOCK_THRESHOLD(self, v):
        self._set("perm_block_threshold", str(v))

    @property
    def TEMP_BLOCK_MINUTES(self) -> int:
        return int(self._get("temp_block_minutes"))

    @TEMP_BLOCK_MINUTES.setter
    def TEMP_BLOCK_MINUTES(self, v):
        self._set("temp_block_minutes", str(v))

    @property
    def POLL_INTERVAL_SECONDS(self) -> int:
        return int(self._get("poll_interval_seconds"))

    # ── Whitelist ─────────────────────────────────────────────────────
    @property
    def WHITELIST(self) -> list:
        raw = self._get("whitelist")
        try:
            return json.loads(raw)
        except Exception:
            return []

    @WHITELIST.setter
    def WHITELIST(self, v: list):
        self._set("whitelist", json.dumps(v))

    def is_whitelisted(self, ip: str) -> bool:
        try:
            addr = ipaddress.ip_address(ip)
            for entry in self.WHITELIST:
                try:
                    if addr in ipaddress.ip_network(entry, strict=False):
                        return True
                except ValueError:
                    if ip == entry:
                        return True
        except ValueError:
            pass
        return False

    # ── Email ─────────────────────────────────────────────────────────
    @property
    def EMAIL_ENABLED(self) -> bool:
        return self._get("email_enabled").lower() == "true"

    @EMAIL_ENABLED.setter
    def EMAIL_ENABLED(self, v: bool):
        self._set("email_enabled", "true" if v else "false")

    @property
    def SMTP_HOST(self) -> str:
        return self._get("smtp_host")

    @SMTP_HOST.setter
    def SMTP_HOST(self, v):
        self._set("smtp_host", v)

    @property
    def SMTP_PORT(self) -> int:
        return int(self._get("smtp_port"))

    @SMTP_PORT.setter
    def SMTP_PORT(self, v):
        self._set("smtp_port", str(v))

    @property
    def SMTP_USE_TLS(self) -> bool:
        return self._get("smtp_use_tls").lower() == "true"

    @SMTP_USE_TLS.setter
    def SMTP_USE_TLS(self, v: bool):
        self._set("smtp_use_tls", "true" if v else "false")

    @property
    def SMTP_USER(self) -> str:
        return self._get("smtp_user")

    @SMTP_USER.setter
    def SMTP_USER(self, v):
        self._set("smtp_user", v)

    @property
    def SMTP_PASSWORD(self) -> str:
        return self._get("smtp_password")

    @SMTP_PASSWORD.setter
    def SMTP_PASSWORD(self, v):
        self._set("smtp_password", v)

    @property
    def ALERT_RECIPIENT(self) -> str:
        return self._get("alert_recipient")

    @ALERT_RECIPIENT.setter
    def ALERT_RECIPIENT(self, v):
        self._set("alert_recipient", v)

    @property
    def ALERT_FROM(self) -> str:
        return self._get("alert_from")

    @ALERT_FROM.setter
    def ALERT_FROM(self, v):
        self._set("alert_from", v)
