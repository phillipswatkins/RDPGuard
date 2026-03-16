"""
RDP Guard - Settings Page
All settings are saved to the database.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QSpinBox,
    QCheckBox, QScrollArea, QMessageBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.updater import UpdateChecker, CURRENT_VERSION
import sys, os


class SettingsPage(QWidget):
    settings_saved = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._build_ui()
        self._load()

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setObjectName("form_label")
        return lbl

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(f"── {text.upper()}")
        lbl.setObjectName("section_title")
        return lbl

    def _divider(self) -> QFrame:
        d = QFrame(); d.setObjectName("section_divider")
        return d

    def _build_ui(self):
        # Scrollable container
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        root = QVBoxLayout(container)
        root.setContentsMargins(28, 24, 48, 24)
        root.setSpacing(12)

        # Page title
        t = QLabel("SETTINGS")
        t.setObjectName("page_title")
        s = QLabel("CONFIGURE PROTECTION RULES")
        s.setObjectName("page_subtitle")
        root.addWidget(t)
        root.addWidget(s)
        root.addWidget(self._divider())

        # ── Detection thresholds ──────────────────────────────────────
        root.addWidget(self._section("Detection Thresholds"))

        thresh_row = QHBoxLayout()
        thresh_row.setSpacing(24)

        t1 = QVBoxLayout()
        t1.addWidget(self._label("Temp Block After (attempts)"))
        self.spin_temp_thresh = QSpinBox()
        self.spin_temp_thresh.setRange(1, 100)
        self.spin_temp_thresh.setFixedWidth(120)
        t1.addWidget(self.spin_temp_thresh)
        thresh_row.addLayout(t1)

        t2 = QVBoxLayout()
        t2.addWidget(self._label("Perm Block After (attempts)"))
        self.spin_perm_thresh = QSpinBox()
        self.spin_perm_thresh.setRange(1, 1000)
        self.spin_perm_thresh.setFixedWidth(120)
        t2.addWidget(self.spin_perm_thresh)
        thresh_row.addLayout(t2)

        t3 = QVBoxLayout()
        t3.addWidget(self._label("Temp Block Duration (minutes)"))
        self.spin_temp_mins = QSpinBox()
        self.spin_temp_mins.setRange(1, 1440)
        self.spin_temp_mins.setFixedWidth(120)
        t3.addWidget(self.spin_temp_mins)
        thresh_row.addLayout(t3)

        thresh_row.addStretch()
        root.addLayout(thresh_row)

        root.addSpacing(8)
        root.addWidget(self._divider())

        # ── Whitelist ─────────────────────────────────────────────────
        root.addWidget(self._section("IP Whitelist"))
        lbl_wl = QLabel("IPs and subnets in this list will never be blocked (e.g. 192.168.1.0/24)")
        lbl_wl.setObjectName("form_label")
        root.addWidget(lbl_wl)

        wl_row = QHBoxLayout()
        wl_left = QVBoxLayout()

        self.whitelist_widget = QListWidget()
        self.whitelist_widget.setFixedHeight(130)
        self.whitelist_widget.setObjectName("event_log")
        wl_left.addWidget(self.whitelist_widget)

        add_row = QHBoxLayout()
        self.wl_input = QLineEdit()
        self.wl_input.setPlaceholderText("e.g. 203.0.113.10 or 192.168.1.0/24")
        add_btn = QPushButton("ADD")
        add_btn.setObjectName("btn_action")
        add_btn.setFixedWidth(70)
        add_btn.clicked.connect(self._add_whitelist)
        self.wl_input.returnPressed.connect(self._add_whitelist)
        rm_btn = QPushButton("REMOVE SELECTED")
        rm_btn.setObjectName("btn_neutral")
        rm_btn.clicked.connect(self._remove_whitelist)
        add_row.addWidget(self.wl_input)
        add_row.addWidget(add_btn)
        add_row.addWidget(rm_btn)
        add_row.addStretch()
        wl_left.addLayout(add_row)

        wl_row.addLayout(wl_left)
        root.addLayout(wl_row)

        root.addSpacing(8)
        root.addWidget(self._divider())

        # ── Email alerts ──────────────────────────────────────────────
        root.addWidget(self._section("Email Alerts"))

        self.chk_email = QCheckBox("Enable email alerts on permanent block")
        self.chk_email.stateChanged.connect(self._toggle_email)
        root.addWidget(self.chk_email)

        self.email_frame = QWidget()
        email_layout = QVBoxLayout(self.email_frame)
        email_layout.setContentsMargins(0, 8, 0, 0)
        email_layout.setSpacing(10)

        row1 = QHBoxLayout(); row1.setSpacing(16)
        c1 = QVBoxLayout()
        c1.addWidget(self._label("SMTP Host"))
        self.smtp_host = QLineEdit(); c1.addWidget(self.smtp_host)
        c2 = QVBoxLayout()
        c2.addWidget(self._label("SMTP Port"))
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setFixedWidth(100)
        c2.addWidget(self.smtp_port)
        c3 = QVBoxLayout()
        self.chk_tls = QCheckBox("Use TLS")
        c3.addSpacing(18); c3.addWidget(self.chk_tls)
        row1.addLayout(c1, 3); row1.addLayout(c2, 1); row1.addLayout(c3, 1)
        row1.addStretch()
        email_layout.addLayout(row1)

        row2 = QHBoxLayout(); row2.setSpacing(16)
        c4 = QVBoxLayout()
        c4.addWidget(self._label("SMTP Username"))
        self.smtp_user = QLineEdit(); c4.addWidget(self.smtp_user)
        c5 = QVBoxLayout()
        c5.addWidget(self._label("SMTP Password"))
        self.smtp_pass = QLineEdit()
        self.smtp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        c5.addWidget(self.smtp_pass)
        row2.addLayout(c4, 1); row2.addLayout(c5, 1)
        email_layout.addLayout(row2)

        row3 = QHBoxLayout(); row3.setSpacing(16)
        c6 = QVBoxLayout()
        c6.addWidget(self._label("Alert Recipient"))
        self.alert_to = QLineEdit(); c6.addWidget(self.alert_to)
        c7 = QVBoxLayout()
        c7.addWidget(self._label("Sender Name / Address"))
        self.alert_from = QLineEdit(); c7.addWidget(self.alert_from)
        row3.addLayout(c6, 1); row3.addLayout(c7, 1)
        email_layout.addLayout(row3)

        test_btn = QPushButton("SEND TEST EMAIL")
        test_btn.setObjectName("btn_neutral")
        test_btn.setFixedWidth(180)
        test_btn.clicked.connect(self._test_email)
        email_layout.addWidget(test_btn)

        root.addWidget(self.email_frame)

        root.addSpacing(8)
        root.addWidget(self._divider())

        # ── Updates ───────────────────────────────────────────────────
        root.addWidget(self._section("Software Updates"))

        ver_row = QHBoxLayout()
        self._ver_label = QLabel(f"Current version:  v{CURRENT_VERSION}")
        self._ver_label.setObjectName("form_label")
        self._update_status = QLabel("")
        self._update_status.setObjectName("form_label")

        self._check_btn = QPushButton("CHECK FOR UPDATES")
        self._check_btn.setObjectName("btn_neutral")
        self._check_btn.setFixedWidth(200)
        self._check_btn.clicked.connect(self._check_updates)

        ver_row.addWidget(self._ver_label)
        ver_row.addSpacing(20)
        ver_row.addWidget(self._update_status)
        ver_row.addStretch()
        ver_row.addWidget(self._check_btn)
        root.addLayout(ver_row)

        root.addSpacing(8)
        root.addWidget(self._divider())

        # ── Startup ───────────────────────────────────────────────────
        root.addWidget(self._section("Windows Startup"))

        startup_row = QHBoxLayout()
        self.chk_startup = QCheckBox("Launch Zopi Guard automatically when Windows starts")
        self.chk_startup.setToolTip(
            "Adds Zopi Guard to the Windows registry run key so it starts with Windows"
        )
        startup_row.addWidget(self.chk_startup)
        startup_row.addStretch()
        root.addLayout(startup_row)

        startup_note = QLabel(
            "Note: Zopi Guard will start minimised to the system tray. "
            "The service must be started manually or set to auto-start."
        )
        startup_note.setObjectName("form_label")
        startup_note.setWordWrap(True)
        root.addWidget(startup_note)

        root.addSpacing(16)
        root.addWidget(self._divider())

        # ── Save button ───────────────────────────────────────────────
        save_row = QHBoxLayout()
        self.save_btn = QPushButton("SAVE SETTINGS")
        self.save_btn.setObjectName("btn_start")
        self.save_btn.setFixedWidth(180)
        self.save_btn.clicked.connect(self._save)
        save_row.addStretch()
        save_row.addWidget(self.save_btn)
        root.addLayout(save_row)

        root.addStretch()
        self._update_worker = None

    def _toggle_email(self):
        enabled = self.chk_email.isChecked()
        self.email_frame.setEnabled(enabled)

    def _add_whitelist(self):
        ip = self.wl_input.text().strip()
        if ip:
            self.whitelist_widget.addItem(ip)
            self.wl_input.clear()

    def _remove_whitelist(self):
        for item in self.whitelist_widget.selectedItems():
            self.whitelist_widget.takeItem(self.whitelist_widget.row(item))

    # ── Startup registry helpers ──────────────────────────────────────
    _RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    _APP_NAME = "ZopiGuard"

    def _is_startup_enabled(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._RUN_KEY)
            winreg.QueryValueEx(key, self._APP_NAME)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def _set_startup(self, enable: bool):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, self._RUN_KEY, 0,
                winreg.KEY_SET_VALUE
            )
            if enable:
                exe = sys.executable
                script = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '..', 'main.py')
                )
                winreg.SetValueEx(
                    key, self._APP_NAME, 0, winreg.REG_SZ,
                    f'"{exe}" "{script}" --minimised'
                )
            else:
                try:
                    winreg.DeleteValue(key, self._APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            return False

    def _load(self):
        cfg = self.config
        self.spin_temp_thresh.setValue(cfg.TEMP_BLOCK_THRESHOLD)
        self.spin_perm_thresh.setValue(cfg.PERM_BLOCK_THRESHOLD)
        self.spin_temp_mins.setValue(cfg.TEMP_BLOCK_MINUTES)

        self.whitelist_widget.clear()
        for ip in cfg.WHITELIST:
            self.whitelist_widget.addItem(ip)

        self.chk_email.setChecked(cfg.EMAIL_ENABLED)
        self.smtp_host.setText(cfg.SMTP_HOST)
        self.smtp_port.setValue(cfg.SMTP_PORT)
        self.chk_tls.setChecked(cfg.SMTP_USE_TLS)
        self.smtp_user.setText(cfg.SMTP_USER)
        self.smtp_pass.setText(cfg.SMTP_PASSWORD)
        self.alert_to.setText(cfg.ALERT_RECIPIENT)
        self.alert_from.setText(cfg.ALERT_FROM)
        self._toggle_email()
        self.chk_startup.setChecked(self._is_startup_enabled())

    def _save(self):
        cfg = self.config
        cfg.TEMP_BLOCK_THRESHOLD = self.spin_temp_thresh.value()
        cfg.PERM_BLOCK_THRESHOLD = self.spin_perm_thresh.value()
        cfg.TEMP_BLOCK_MINUTES   = self.spin_temp_mins.value()

        wl = [self.whitelist_widget.item(i).text()
              for i in range(self.whitelist_widget.count())]
        cfg.WHITELIST = wl

        cfg.EMAIL_ENABLED   = self.chk_email.isChecked()
        cfg.SMTP_HOST       = self.smtp_host.text().strip()
        cfg.SMTP_PORT       = self.smtp_port.value()
        cfg.SMTP_USE_TLS    = self.chk_tls.isChecked()
        cfg.SMTP_USER       = self.smtp_user.text().strip()
        cfg.SMTP_PASSWORD   = self.smtp_pass.text()
        cfg.ALERT_RECIPIENT = self.alert_to.text().strip()
        cfg.ALERT_FROM      = self.alert_from.text().strip()

        # Handle startup registry
        startup_ok = self._set_startup(self.chk_startup.isChecked())
        if not startup_ok and self.chk_startup.isChecked():
            QMessageBox.warning(
                self, "Startup",
                "Could not write to the Windows registry.\n"
                "Try running Zopi Guard as Administrator to enable startup."
            )

        self.settings_saved.emit()
        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    def _test_email(self):
        self._save()
        try:
            from core.emailer import send_permanent_block_alert
            send_permanent_block_alert(self.config, "TEST-IP-0.0.0.0", 0)
            QMessageBox.information(self, "Success", "Test email sent successfully!")
        except Exception as exc:
            QMessageBox.critical(self, "Email Error", f"Failed to send test email:\n\n{exc}")

    def _check_updates(self):
        self._check_btn.setEnabled(False)
        self._check_btn.setText("CHECKING...")
        self._update_status.setText("")
        self._update_status.setStyleSheet("")

        self._update_worker = UpdateChecker(mode="check")
        self._update_worker.update_available.connect(self._on_update_available)
        self._update_worker.no_update.connect(self._on_no_update)
        self._update_worker.check_failed.connect(self._on_check_failed)
        self._update_worker.start()

    def _on_update_available(self, tag: str, notes: str, asset_url: str):
        self._check_btn.setEnabled(True)
        self._check_btn.setText("CHECK FOR UPDATES")
        from gui.update_dialog import UpdateDialog
        dlg = UpdateDialog(tag, notes, asset_url, parent=self)
        dlg.exec()

    def _on_no_update(self):
        self._check_btn.setEnabled(True)
        self._check_btn.setText("CHECK FOR UPDATES")
        self._update_status.setText("✓  You are on the latest version.")
        self._update_status.setStyleSheet("color: #00E87A; font-size: 11px;")

    def _on_check_failed(self, msg: str):
        self._check_btn.setEnabled(True)
        self._check_btn.setText("CHECK FOR UPDATES")
        self._update_status.setText(f"✗  {msg}")
        self._update_status.setStyleSheet("color: #FF3030; font-size: 11px;")
