"""
Zopi Guard - Attempts & Statistics Page
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QFrame, QLineEdit, QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor


class AttemptsPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._all_rows = []
        self._build_ui()
        self.refresh()

        # Auto-refresh every 5 seconds so new attempts appear without manual refresh
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(5000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        # ── Title row ──
        title_row = QHBoxLayout()
        left = QVBoxLayout()
        t = QLabel("ATTEMPT LOG")
        t.setObjectName("page_title")
        s = QLabel("ALL TRACKED IP ADDRESSES")
        s.setObjectName("page_subtitle")
        left.addWidget(t)
        left.addWidget(s)

        right = QHBoxLayout()
        right.setSpacing(8)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter by IP or username...")
        self.search_box.setFixedWidth(220)
        self.search_box.textChanged.connect(self._filter)

        self.refresh_btn = QPushButton("↻  REFRESH")
        self.refresh_btn.setObjectName("btn_neutral")
        self.refresh_btn.clicked.connect(self.refresh)

        self.clear_selected_btn = QPushButton("CLEAR SELECTED")
        self.clear_selected_btn.setObjectName("btn_danger")
        self.clear_selected_btn.setToolTip("Reset attempt counter for the selected IP")
        self.clear_selected_btn.clicked.connect(self._clear_selected)

        right.addWidget(self.search_box)
        right.addWidget(self.refresh_btn)
        right.addWidget(self.clear_selected_btn)
        title_row.addLayout(left)
        title_row.addStretch()
        title_row.addLayout(right)
        root.addLayout(title_row)

        div = QFrame(); div.setObjectName("section_divider")
        root.addWidget(div)

        # ── Summary + risk legend ──
        info_row = QHBoxLayout()
        self.lbl_summary = QLabel()
        self.lbl_summary.setObjectName("section_title")
        info_row.addWidget(self.lbl_summary)
        info_row.addStretch()

        legend_title = QLabel("RISK:")
        legend_title.setStyleSheet("color:#4A6080; font-size:9px; letter-spacing:2px;")
        lo_box = QFrame(); lo_box.setFixedSize(10, 10)
        lo_box.setStyleSheet("background:#FF9500; border-radius:1px;")
        lo_lbl = QLabel("LOW (1–4)")
        lo_lbl.setStyleSheet("color:#4A6080; font-size:9px;")
        hi_box = QFrame(); hi_box.setFixedSize(10, 10)
        hi_box.setStyleSheet("background:#FF3B3B; border-radius:1px;")
        hi_lbl = QLabel("HIGH (5+)")
        hi_lbl.setStyleSheet("color:#4A6080; font-size:9px;")

        for w in [legend_title, lo_box, lo_lbl, hi_box, hi_lbl]:
            info_row.addWidget(w)
            if w in (lo_lbl,):
                info_row.addSpacing(8)
        root.addLayout(info_row)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "IP ADDRESS", "ATTEMPTS", "LAST USERNAME", "STATUS",
            "FIRST SEEN", "LAST SEEN", "RISK", "ACTION"
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(1, 75)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(2, 130)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(3, 85)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(4, 140)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(5, 140)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(6, 95)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(7, 80)

        root.addWidget(self.table, 1)

        # ── Help text ──
        help_lbl = QLabel(
            "Tip: Select a row and click CLEAR SELECTED (or use the row button) to reset "
            "that IP's attempt counter. This does not remove any active firewall blocks."
        )
        help_lbl.setStyleSheet("color:#2A4060; font-size:10px;")
        help_lbl.setWordWrap(True)
        root.addWidget(help_lbl)

    # ── Data ──────────────────────────────────────────────────────────
    def refresh(self):
        # Remember scroll position and selected IP
        scroll_pos = self.table.verticalScrollBar().value()
        selected_ip = None
        if self.table.currentRow() >= 0:
            item = self.table.item(self.table.currentRow(), 0)
            if item:
                selected_ip = item.text()

        self._all_rows = self.db.get_all_attempts()
        search = self.search_box.text()
        if search:
            self._render([r for r in self._all_rows
                          if search.lower() in r["ip"].lower()
                          or search.lower() in (r.get("last_username") or "").lower()])
        else:
            self._render(self._all_rows)

        total = sum(r["attempt_count"] for r in self._all_rows)
        self.lbl_summary.setText(
            f"{len(self._all_rows)} IPs tracked  ·  {total} total attempts"
        )

        # Restore scroll and selection
        self.table.verticalScrollBar().setValue(scroll_pos)
        if selected_ip:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item and item.text() == selected_ip:
                    self.table.selectRow(row)
                    break

    def _filter(self, text: str):
        filtered = [
            r for r in self._all_rows
            if text.lower() in r["ip"].lower()
            or text.lower() in (r.get("last_username") or "").lower()
        ]
        self._render(filtered)

    def _render(self, rows: list):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 38)

            count    = row["attempt_count"]
            status   = row["block_status"]
            username = row.get("last_username") or "—"

            # IP
            ip_item = QTableWidgetItem(row["ip"])
            ip_item.setForeground(QColor("#E0E8F0"))
            self.table.setItem(r, 0, ip_item)

            # Attempts
            cnt_item = QTableWidgetItem(str(count))
            cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cnt_item.setForeground(
                QColor("#FF3B3B") if count >= 10 else
                QColor("#FF9500") if count >= 5  else
                QColor("#8090A0")
            )
            self.table.setItem(r, 1, cnt_item)

            # Username
            user_item = QTableWidgetItem(username)
            user_item.setForeground(
                QColor("#C0A060") if username != "—" else QColor("#2A3A4A")
            )
            self.table.setItem(r, 2, user_item)

            # Status
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(
                QColor("#FF3B3B") if status == "PERMANENT" else
                QColor("#FF9500") if status == "TEMP"      else
                QColor("#4A6080")
            )
            self.table.setItem(r, 3, status_item)

            # Timestamps
            fs = (row["first_seen"] or "")[:19].replace("T", " ")
            ls = (row["last_seen"]  or "")[:19].replace("T", " ")
            for col, val in [(4, fs), (5, ls)]:
                item = QTableWidgetItem(val)
                item.setForeground(QColor("#6A8090"))
                self.table.setItem(r, col, item)

            # Risk bar
            self.table.setCellWidget(r, 6, self._make_risk_bar(count))

            # Clear button
            btn = QPushButton("CLEAR")
            btn.setStyleSheet(
                "background-color:#2A0A0A; border:2px solid #6A2020; color:#FF6060;"
                "font-size:11px; font-weight:bold; border-radius:3px;"
                "padding:5px 10px; min-width:60px;"
            )
            btn.setToolTip(f"Clear attempt history for {row['ip']}")
            ip = row["ip"]
            btn.clicked.connect(lambda _, x=ip: self._clear_ip(x))
            self.table.setCellWidget(r, 7, btn)

    def _make_risk_bar(self, count: int) -> QWidget:
        w = QWidget()
        w.setToolTip(
            f"{count} failed attempt(s)\n"
            "Orange = low risk (attempts 1–4)\n"
            "Red    = high risk (attempts 5+)\n"
            "Each segment represents 1 attempt (max shown: 10)"
        )
        layout = QHBoxLayout(w)
        layout.setContentsMargins(6, 10, 6, 10)
        layout.setSpacing(2)
        filled = min(10, count)
        for i in range(10):
            seg = QFrame()
            seg.setFixedSize(6, 16)
            if i < filled:
                colour = "#FF9500" if i < 4 else "#FF3B3B"
                seg.setStyleSheet(f"background:{colour}; border-radius:1px;")
            else:
                seg.setStyleSheet("background:#1E2530; border-radius:1px;")
            layout.addWidget(seg)
        layout.addStretch()
        return w

    # ── Actions ───────────────────────────────────────────────────────
    def _clear_selected(self):
        if self.table.currentRow() < 0:
            QMessageBox.information(self, "No Selection", "Please click a row to select it first.")
            return
        item = self.table.item(self.table.currentRow(), 0)
        if item:
            self._clear_ip(item.text())

    def _clear_ip(self, ip: str):
        reply = QMessageBox.question(
            self, "Clear Attempts",
            f"Clear all attempt records for  {ip}?\n\n"
            "This resets the counter but does NOT remove any active firewall blocks.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.unblock_ip(ip)
            self.refresh()
