"""
Zopi Guard - Main Window
"""

import os
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap

from core.database import Database
from core.config import Config
from core.firewall import FirewallManager
from core.monitor import MonitorWorker
from core.updater import UpdateChecker
from gui.update_dialog import UpdateDialog
from gui.tray import TrayIcon
from gui.styles import STYLESHEET
from gui.page_dashboard import DashboardPage
from gui.page_blocked import BlockedIPsPage
from gui.page_attempts import AttemptsPage
from gui.page_settings import SettingsPage

log = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "zopi_guard.db")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zopi Guard")
        self.resize(1180, 760)
        self.setMinimumSize(960, 640)

        # Core components
        self.db = Database(DB_PATH)
        self.config = Config(self.db)
        self.fw = FirewallManager()
        self.monitor: MonitorWorker | None = None

        self.setStyleSheet(STYLESHEET)
        self._build_ui()

        # Tray icon
        self.tray = TrayIcon(self)


        # Refresh timer (every 30s)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._on_tick)
        self._refresh_timer.start(30_000)

        # Startup update check (slight delay so window appears first)
        QTimer.singleShot(3000, self._startup_update_check)

    # ── UI construction ────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Content area (sidebar + pages)
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        content.addWidget(self._build_sidebar())

        # Pages
        self.stack = QStackedWidget()
        self.dash_page     = DashboardPage(self.db)
        self.blocked_page  = BlockedIPsPage(self.db, self.fw)
        self.attempts_page = AttemptsPage(self.db)
        self.settings_page = SettingsPage(self.config)
        self.settings_page.settings_saved.connect(self._on_settings_saved)
        self.blocked_page.unblock_requested.connect(
            lambda ip: self.dash_page.append_event(f"Unblocked: {ip}", "#5AC8FA")
        )

        for page in [self.dash_page, self.blocked_page,
                     self.attempts_page, self.settings_page]:
            self.stack.addWidget(page)

        content.addWidget(self.stack, 1)

        main_layout.addLayout(content, 1)
        main_layout.addWidget(self._build_status_bar())

        self._nav_to(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo_area = QWidget()
        logo_area.setStyleSheet("padding: 20px 16px 16px 16px;")
        logo_layout = QVBoxLayout(logo_area)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(6)

        # Try to load Zopi logo image
        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
        logo_img = QLabel()
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(140, Qt.TransformationMode.SmoothTransformation)
            logo_img.setPixmap(pixmap)
            logo_img.setAlignment(Qt.AlignmentFlag.AlignLeft)
            logo_layout.addWidget(logo_img)
        else:
            # Fallback text logo if image not found
            name = QLabel("ZOPI GUARD")
            name.setObjectName("logo_label")
            logo_layout.addWidget(name)

        sub = QLabel("BRUTE FORCE PROTECTION")
        sub.setObjectName("logo_sub")
        logo_layout.addWidget(sub)
        layout.addWidget(logo_area)

        # Divider
        div = QFrame(); div.setObjectName("section_divider")
        layout.addWidget(div)

        # Nav buttons
        nav_items = [
            ("⬛  DASHBOARD",   0),
            ("⬛  BLOCKED IPs",  1),
            ("⬛  ATTEMPTS",     2),
            ("⬛  SETTINGS",     3),
        ]
        self._nav_buttons = []
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav_button")
            btn.setCheckable(False)
            btn.clicked.connect(lambda _, i=idx: self._nav_to(i))
            layout.addWidget(btn)
            self._nav_buttons.append(btn)

        layout.addStretch()

        # Service controls
        svc_area = QWidget()
        svc_area.setStyleSheet("padding: 16px 16px;")
        svc_layout = QVBoxLayout(svc_area)
        svc_layout.setContentsMargins(0, 0, 0, 0)
        svc_layout.setSpacing(8)

        svc_label = QLabel("SERVICE")
        svc_label.setObjectName("form_label")
        svc_layout.addWidget(svc_label)

        self.btn_start = QPushButton("▶  START")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.clicked.connect(self._start_monitor)

        self.btn_stop = QPushButton("■  STOP")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_monitor)

        svc_layout.addWidget(self.btn_start)
        svc_layout.addWidget(self.btn_stop)
        layout.addWidget(svc_area)

        return sidebar

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("status_bar")
        bar.setFixedHeight(32)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)

        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("status_dot_stopped")

        self.status_label = QLabel("Service stopped")
        self.status_label.setObjectName("status_text")

        layout.addWidget(self.status_dot)
        layout.addWidget(self.status_label)
        layout.addStretch()

        ver = QLabel("ZOPI GUARD  v1.0")
        ver.setObjectName("status_text")
        layout.addWidget(ver)

        return bar

    # ── Navigation ─────────────────────────────────────────────────────
    def _nav_to(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", "true" if i == idx else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ── Monitor control ────────────────────────────────────────────────
    def _start_monitor(self):
        if self.monitor and self.monitor.isRunning():
            return
        self.monitor = MonitorWorker(self.db, self.config, self.fw)
        self.monitor.failed_login.connect(self._on_failed_login)
        self.monitor.ip_blocked.connect(self._on_ip_blocked)
        self.monitor.ip_unblocked.connect(self._on_ip_unblocked)
        self.monitor.status_message.connect(self._on_status_msg)
        self.monitor.tick.connect(self._on_tick)
        self.monitor.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.tray.set_status(True)
        self.status_dot.setObjectName("status_dot_running")
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)
        self.status_label.setText("Service running — monitoring event log")

    def _stop_monitor(self):
        if self.monitor:
            self.monitor.stop()
            self.monitor.wait(3000)
            self.monitor = None
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.tray.set_status(False)
        self.status_dot.setObjectName("status_dot_stopped")
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)
        self.status_label.setText("Service stopped")

    # ── Signal handlers ────────────────────────────────────────────────
    def _on_failed_login(self, ip: str, count: int):
        self.dash_page.append_event(
            f"Failed login from <b>{ip}</b> — {count} attempt(s)", "#E0A030"
        )
        self.dash_page.refresh()

    def _on_ip_blocked(self, ip: str, block_type: str):
        if block_type == "perm":
            color = "#FF3B3B"
            msg = f"PERMANENT block issued for <b>{ip}</b>"
        else:
            color = "#FF9500"
            msg = f"TEMPORARY block issued for <b>{ip}</b> ({self.config.TEMP_BLOCK_MINUTES} min)"
        self.dash_page.append_event(msg, color)
        self.dash_page.refresh()
        self.blocked_page.refresh()

    def _on_ip_unblocked(self, ip: str):
        self.dash_page.append_event(f"Temp block expired: {ip}", "#5AC8FA")
        self.blocked_page.refresh()
        self.dash_page.refresh()

    def _on_status_msg(self, msg: str):
        self.status_label.setText(msg)
        self.dash_page.append_event(msg, "#4A8090")

    def _on_tick(self):
        self.dash_page.refresh()

    def _on_settings_saved(self):
        self.status_label.setText("Settings saved.")

    # ── Update check ───────────────────────────────────────────────────
    def _startup_update_check(self):
        self._update_worker = UpdateChecker(mode="check")
        self._update_worker.update_available.connect(self._on_update_available)
        self._update_worker.no_update.connect(lambda: None)
        self._update_worker.check_failed.connect(lambda msg: log.warning(f"Startup update check: {msg}"))
        self._update_worker.start()

    def _on_update_available(self, tag: str, notes: str, asset_url: str):
        dlg = UpdateDialog(tag, notes, asset_url, parent=self)
        dlg.exec()

    # ── Cleanup ────────────────────────────────────────────────────────
    def closeEvent(self, event):
        self._stop_monitor()
        event.accept()
