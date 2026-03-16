"""
Zopi Guard - Blocked IPs Page
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QFrame, QLineEdit, QHeaderView, QMessageBox,
    QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QFont, QPen, QBrush


class UnblockButton(QPushButton):
    """Custom drawn button that bypasses the global stylesheet completely."""
    def __init__(self, text="UNBLOCK", parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(90, 28)
        self.setMaximumHeight(32)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._hovered = False

    def enterEvent(self, e):
        self._hovered = True
        self.update()

    def leaveEvent(self, e):
        self._hovered = False
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        bg = QColor("#1A3A5A") if self._hovered else QColor("#0D1A2D")
        p.setBrush(QBrush(bg))
        pen_col = QColor("#4A9ADF") if self._hovered else QColor("#2A5A8F")
        p.setPen(QPen(pen_col, 2))
        p.drawRoundedRect(2, 2, w - 4, h - 4, 3, 3)

        # Text
        p.setPen(QColor("#80D8FF") if self._hovered else QColor("#5AC8FA"))
        font = QFont("Consolas", 9)
        font.setBold(True)
        p.setFont(font)
        p.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()


class BlockedIPsPage(QWidget):
    unblock_requested = pyqtSignal(str)

    def __init__(self, db, firewall, parent=None):
        super().__init__(parent)
        self.db = db
        self.fw = firewall
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        left = QVBoxLayout()
        t = QLabel("BLOCKED IPs")
        t.setObjectName("page_title")
        s = QLabel("ACTIVE FIREWALL RULES")
        s.setObjectName("page_subtitle")
        left.addWidget(t)
        left.addWidget(s)

        right = QHBoxLayout()
        right.setSpacing(8)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter by IP...")
        self.search_box.setFixedWidth(200)
        self.search_box.textChanged.connect(self._filter)

        self.refresh_btn = QPushButton("↻  REFRESH")
        self.refresh_btn.setObjectName("btn_neutral")
        self.refresh_btn.clicked.connect(self.refresh)

        right.addWidget(self.search_box)
        right.addWidget(self.refresh_btn)

        title_row.addLayout(left)
        title_row.addStretch()
        title_row.addLayout(right)
        root.addLayout(title_row)

        div = QFrame(); div.setObjectName("section_divider")
        root.addWidget(div)

        # Summary labels
        summary_row = QHBoxLayout()
        self.lbl_perm = QLabel()
        self.lbl_temp = QLabel()
        self.lbl_perm.setObjectName("section_title")
        self.lbl_temp.setObjectName("section_title")
        summary_row.addWidget(self.lbl_perm)
        summary_row.addSpacing(24)
        summary_row.addWidget(self.lbl_temp)
        summary_row.addStretch()
        root.addLayout(summary_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "IP ADDRESS", "TYPE", "ATTEMPTS", "BLOCKED AT", "EXPIRES AT", "ACTION"
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 100)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 80)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 160)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 160)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 130)
        root.addWidget(self.table, 1)

        # Bottom — manual block
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.manual_ip = QLineEdit()
        self.manual_ip.setPlaceholderText("Enter IP to manually block...")
        self.manual_ip.setFixedWidth(260)
        self.manual_ip.returnPressed.connect(self._manual_block)
        self.manual_block_btn = QPushButton("BLOCK IP")
        self.manual_block_btn.setObjectName("btn_danger")
        self.manual_block_btn.clicked.connect(self._manual_block)
        action_row.addWidget(self.manual_ip)
        action_row.addWidget(self.manual_block_btn)
        action_row.addStretch()
        root.addLayout(action_row)

    def refresh(self):
        self._all_rows = self.db.get_blocked_ips()
        self._render(self._all_rows)
        perm = sum(1 for r in self._all_rows if r["block_type"] == "PERMANENT")
        temp = len(self._all_rows) - perm
        self.lbl_perm.setText(f"● {perm}  PERMANENT")
        self.lbl_temp.setText(f"● {temp}  TEMPORARY")

    def _filter(self, text: str):
        filtered = [r for r in self._all_rows if text.lower() in r["ip"].lower()]
        self._render(filtered)

    def _render(self, rows: list):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 40)
            is_perm = row["block_type"] == "PERMANENT"

            ip_item = QTableWidgetItem(row["ip"])
            ip_item.setForeground(QColor("#E0E8F0"))
            self.table.setItem(r, 0, ip_item)

            type_item = QTableWidgetItem(row["block_type"])
            type_item.setForeground(QColor("#FF3B3B") if is_perm else QColor("#FF9500"))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 1, type_item)

            attempts_item = QTableWidgetItem(str(row["attempt_count"]))
            attempts_item.setForeground(QColor("#8090A0"))
            attempts_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 2, attempts_item)

            blocked_at = (row["blocked_at"] or "")[:19].replace("T", " ")
            ba_item = QTableWidgetItem(blocked_at)
            ba_item.setForeground(QColor("#6A8090"))
            self.table.setItem(r, 3, ba_item)

            expires = (row.get("expires_at") or "—")
            if expires != "—":
                expires = expires[:19].replace("T", " ")
            exp_item = QTableWidgetItem(expires)
            exp_item.setForeground(QColor("#6A8090"))
            self.table.setItem(r, 4, exp_item)

            # Clean inline unblock button — no wrapper widget
            btn = QPushButton("UNBLOCK")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0D1A2D;
                    border: 1px solid #1E3A5F;
                    color: #5AC8FA;
                    font-family: 'Consolas', monospace;
                    font-size: 10px;
                    letter-spacing: 1px;
                    border-radius: 3px;
                    padding: 5px 10px;
                    margin: 5px 6px;
                    min-width: 70px;
                }
                QPushButton:hover { background-color: #152438; }
                QPushButton:pressed { background-color: #0A1020; }
            """)
            ip = row["ip"]
            btn.clicked.connect(lambda _, x=ip: self._unblock(x))
            self.table.setCellWidget(r, 5, btn)

    def _unblock(self, ip: str):
        reply = QMessageBox.question(
            self, "Confirm Unblock",
            f"Unblock {ip} and remove all attempt records?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.fw.unblock_ip(ip)
            self.db.unblock_ip(ip)
            self.unblock_requested.emit(ip)
            self.refresh()

    def _manual_block(self):
        ip = self.manual_ip.text().strip()
        if not ip:
            return
        self.fw.block_ip(ip, permanent=True)
        self.db.manual_block(ip)
        self.manual_ip.clear()
        self.refresh()
