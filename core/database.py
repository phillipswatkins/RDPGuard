"""
Zopi Guard - Database Layer (SQLite)
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

log = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()
        self._migrate()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS attempts (
                    ip              TEXT PRIMARY KEY,
                    attempt_count   INTEGER NOT NULL DEFAULT 0,
                    last_username   TEXT,
                    first_seen      TEXT NOT NULL,
                    last_seen       TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS temp_blocks (
                    ip          TEXT PRIMARY KEY,
                    blocked_at  TEXT NOT NULL,
                    expires_at  TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS permanent_blocks (
                    ip              TEXT PRIMARY KEY,
                    blocked_at      TEXT NOT NULL,
                    attempt_count   INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS event_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          TEXT NOT NULL,
                    ip          TEXT NOT NULL,
                    event_type  TEXT NOT NULL,
                    notes       TEXT
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key     TEXT PRIMARY KEY,
                    value   TEXT NOT NULL
                );
            """)

    def _migrate(self):
        """Add new columns to existing databases without breaking them."""
        with self._conn() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(attempts)").fetchall()]
            if "last_username" not in cols:
                conn.execute("ALTER TABLE attempts ADD COLUMN last_username TEXT")
                log.info("DB migration: added last_username column to attempts.")

    # ── Attempts ──────────────────────────────────────────────────────
    def record_attempt(self, ip: str, username: str = "") -> int:
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO attempts (ip, attempt_count, last_username, first_seen, last_seen)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(ip) DO UPDATE SET
                    attempt_count = attempt_count + 1,
                    last_username = excluded.last_username,
                    last_seen     = excluded.last_seen
            """, (ip, username or None, now, now))
            row = conn.execute(
                "SELECT attempt_count FROM attempts WHERE ip = ?", (ip,)
            ).fetchone()
            count = row["attempt_count"]
            conn.execute(
                "INSERT INTO event_log (ts, ip, event_type, notes) VALUES (?, ?, 'attempt', ?)",
                (now, ip, f"user:{username}" if username else None)
            )
        return count

    def get_attempt_count(self, ip: str) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT attempt_count FROM attempts WHERE ip = ?", (ip,)
            ).fetchone()
            return row["attempt_count"] if row else 0

    # ── Temp blocks ───────────────────────────────────────────────────
    def set_temp_block(self, ip: str, minutes: int):
        now = datetime.utcnow()
        expires = now + timedelta(minutes=minutes)
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO temp_blocks (ip, blocked_at, expires_at)
                VALUES (?, ?, ?)
            """, (ip, now.isoformat(), expires.isoformat()))
            conn.execute(
                "INSERT INTO event_log (ts, ip, event_type, notes) VALUES (?, ?, 'temp_block', ?)",
                (now.isoformat(), ip, f"expires {expires.isoformat()}")
            )

    def is_temp_blocked(self, ip: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT expires_at FROM temp_blocks WHERE ip = ?", (ip,)
            ).fetchone()
            if not row:
                return False
            return datetime.utcnow() < datetime.fromisoformat(row["expires_at"])

    def get_expired_temp_blocks(self) -> list:
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT ip FROM temp_blocks WHERE expires_at <= ?", (now,)
            ).fetchall()
            return [r["ip"] for r in rows]

    def clear_temp_block(self, ip: str):
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute("DELETE FROM temp_blocks WHERE ip = ?", (ip,))
            conn.execute(
                "INSERT INTO event_log (ts, ip, event_type, notes) VALUES (?, ?, 'unblock', 'temp block expired')",
                (now, ip)
            )

    # ── Permanent blocks ──────────────────────────────────────────────
    def set_permanent_block(self, ip: str):
        now = datetime.utcnow().isoformat()
        count = self.get_attempt_count(ip)
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO permanent_blocks (ip, blocked_at, attempt_count)
                VALUES (?, ?, ?)
            """, (ip, now, count))
            conn.execute("DELETE FROM temp_blocks WHERE ip = ?", (ip,))
            conn.execute(
                "INSERT INTO event_log (ts, ip, event_type, notes) VALUES (?, ?, 'perm_block', ?)",
                (now, ip, f"after {count} attempts")
            )

    def is_permanently_blocked(self, ip: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM permanent_blocks WHERE ip = ?", (ip,)
            ).fetchone()
            return row is not None

    def get_permanent_blocks(self) -> list:
        with self._conn() as conn:
            rows = conn.execute("SELECT ip FROM permanent_blocks").fetchall()
            return [r["ip"] for r in rows]

    # ── Admin helpers ─────────────────────────────────────────────────
    def unblock_ip(self, ip: str):
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute("DELETE FROM temp_blocks WHERE ip = ?", (ip,))
            conn.execute("DELETE FROM permanent_blocks WHERE ip = ?", (ip,))
            conn.execute("DELETE FROM attempts WHERE ip = ?", (ip,))
            conn.execute(
                "INSERT INTO event_log (ts, ip, event_type, notes) VALUES (?, ?, 'unblock', 'manual unblock')",
                (now, ip)
            )

    def manual_block(self, ip: str):
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO attempts (ip, attempt_count, first_seen, last_seen)
                VALUES (?, 0, ?, ?)
            """, (ip, now, now))
            conn.execute("""
                INSERT OR REPLACE INTO permanent_blocks (ip, blocked_at, attempt_count)
                VALUES (?, ?, 0)
            """, (ip, now))
            conn.execute(
                "INSERT INTO event_log (ts, ip, event_type, notes) VALUES (?, ?, 'perm_block', 'manual block')",
                (now, ip)
            )

    def get_all_attempts(self) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT a.ip, a.attempt_count, a.last_username, a.first_seen, a.last_seen,
                       CASE WHEN pb.ip IS NOT NULL THEN 'PERMANENT'
                            WHEN tb.ip IS NOT NULL THEN 'TEMP'
                            ELSE 'NONE' END AS block_status,
                       tb.expires_at
                FROM attempts a
                LEFT JOIN temp_blocks tb ON a.ip = tb.ip
                LEFT JOIN permanent_blocks pb ON a.ip = pb.ip
                ORDER BY a.attempt_count DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def get_blocked_ips(self) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT a.ip, a.attempt_count, a.last_seen,
                       CASE WHEN pb.ip IS NOT NULL THEN 'PERMANENT'
                            ELSE 'TEMP' END AS block_type,
                       COALESCE(pb.blocked_at, tb.blocked_at) AS blocked_at,
                       tb.expires_at
                FROM attempts a
                LEFT JOIN temp_blocks tb ON a.ip = tb.ip
                LEFT JOIN permanent_blocks pb ON a.ip = pb.ip
                WHERE pb.ip IS NOT NULL OR tb.ip IS NOT NULL
                ORDER BY blocked_at DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def get_recent_events(self, limit: int = 100) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT ts, ip, event_type, notes
                FROM event_log
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        with self._conn() as conn:
            total_attempts = conn.execute(
                "SELECT COALESCE(SUM(attempt_count), 0) FROM attempts"
            ).fetchone()[0]
            unique_ips = conn.execute(
                "SELECT COUNT(*) FROM attempts"
            ).fetchone()[0]
            temp_blocks = conn.execute(
                "SELECT COUNT(*) FROM temp_blocks WHERE expires_at > ?",
                (datetime.utcnow().isoformat(),)
            ).fetchone()[0]
            perm_blocks = conn.execute(
                "SELECT COUNT(*) FROM permanent_blocks"
            ).fetchone()[0]
            today = datetime.utcnow().date().isoformat()
            today_attempts = conn.execute(
                "SELECT COUNT(*) FROM event_log WHERE event_type='attempt' AND ts >= ?",
                (today,)
            ).fetchone()[0]
            hourly = []
            for h in range(23, -1, -1):
                start = (datetime.utcnow() - timedelta(hours=h+1)).isoformat()
                end   = (datetime.utcnow() - timedelta(hours=h)).isoformat()
                count = conn.execute(
                    "SELECT COUNT(*) FROM event_log WHERE event_type='attempt' AND ts BETWEEN ? AND ?",
                    (start, end)
                ).fetchone()[0]
                hourly.append(count)
            return {
                "total_attempts": total_attempts,
                "unique_ips": unique_ips,
                "temp_blocks": temp_blocks,
                "perm_blocks": perm_blocks,
                "today_attempts": today_attempts,
                "hourly": hourly,
            }

    # ── Settings ──────────────────────────────────────────────────────
    def get_setting(self, key: str, default=None):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            """, (key, str(value)))

    def get_all_settings(self) -> dict:
        with self._conn() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {r["key"]: r["value"] for r in rows}
