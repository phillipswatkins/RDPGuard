"""
RDP Guard - Update Dialog
Shown when a newer version is available on GitHub.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt
from core.updater import CURRENT_VERSION, UpdateChecker


class UpdateDialog(QDialog):
    def __init__(self, tag: str, notes: str, asset_url: str, parent=None):
        super().__init__(parent)
        self.tag       = tag
        self.notes     = notes
        self.asset_url = asset_url
        self._worker   = None

        self.setWindowTitle("Update Available")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        # Header
        hdr = QLabel("🆕  UPDATE AVAILABLE")
        hdr.setStyleSheet("font-size:15px; font-weight:bold; color:#00E87A; letter-spacing:2px;")
        layout.addWidget(hdr)

        ver_row = QHBoxLayout()
        cur = QLabel(f"Current:  v{CURRENT_VERSION}")
        cur.setStyleSheet("color:#4A6080; font-size:12px;")
        new = QLabel(f"Latest:   {self.tag}")
        new.setStyleSheet("color:#E0E8F0; font-size:12px;")
        ver_row.addWidget(cur)
        ver_row.addSpacing(24)
        ver_row.addWidget(new)
        ver_row.addStretch()
        layout.addLayout(ver_row)

        div = QFrame(); div.setStyleSheet("background:#1A2233; max-height:1px; min-height:1px;")
        layout.addWidget(div)

        # Release notes
        notes_label = QLabel("RELEASE NOTES")
        notes_label.setStyleSheet("font-size:9px; color:#4A6080; letter-spacing:3px;")
        layout.addWidget(notes_label)

        self.notes_box = QTextEdit()
        self.notes_box.setReadOnly(True)
        self.notes_box.setPlainText(self.notes)
        self.notes_box.setFixedHeight(130)
        self.notes_box.setStyleSheet("""
            background:#080A0E; border:1px solid #1A2233;
            color:#8090A8; font-size:11px; padding:6px;
        """)
        layout.addWidget(self.notes_box)

        # Progress bar (hidden until download starts)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("Downloading... %p%")
        self.progress.setFixedHeight(22)
        self.progress.setStyleSheet("""
            QProgressBar {
                background:#080A0E; border:1px solid #1A2233;
                border-radius:2px; color:#00E87A; font-size:10px; text-align:center;
            }
            QProgressBar::chunk { background:#005528; border-radius:2px; }
        """)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color:#4A6080; font-size:11px;")
        self.status_label.hide()
        layout.addWidget(self.status_label)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_skip = QPushButton("SKIP")
        self.btn_skip.setStyleSheet("""
            background:#131C28; border:1px solid #1E2D40; color:#8090A0;
            padding:8px 20px; font-size:11px; letter-spacing:1px; border-radius:3px;
        """)
        self.btn_skip.clicked.connect(self.reject)

        self.btn_update = QPushButton("DOWNLOAD & INSTALL")
        self.btn_update.setStyleSheet("""
            background:#002E18; border:1px solid #005528; color:#00E87A;
            padding:8px 20px; font-size:11px; letter-spacing:1px; border-radius:3px; font-weight:bold;
        """)
        self.btn_update.clicked.connect(self._start_download)

        btn_row.addWidget(self.btn_skip)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_update)
        layout.addLayout(btn_row)

    def _start_download(self):
        self.btn_update.setEnabled(False)
        self.btn_update.setText("DOWNLOADING...")
        self.btn_skip.setEnabled(False)
        self.progress.show()
        self.status_label.show()
        self.status_label.setText("Downloading update from GitHub...")

        self._worker = UpdateChecker(mode="download", asset_url=self.asset_url)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.update_done.connect(self._on_done)
        self._worker.start()

    def _on_done(self, success: bool):
        if success:
            self.progress.setValue(100)
            self.status_label.setText(
                "✓ Update installed! Please restart RDP Guard to use the new version."
            )
            self.status_label.setStyleSheet("color:#00E87A; font-size:11px;")
            self.btn_skip.setText("CLOSE")
            self.btn_skip.setEnabled(True)
            self.btn_update.hide()
        else:
            self.status_label.setText(
                "✗ Update failed. Check your internet connection or update manually from GitHub."
            )
            self.status_label.setStyleSheet("color:#FF3030; font-size:11px;")
            self.btn_skip.setEnabled(True)
            self.btn_update.setEnabled(True)
            self.btn_update.setText("RETRY")
