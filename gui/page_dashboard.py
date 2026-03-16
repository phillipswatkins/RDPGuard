"""
RDP Guard - Dashboard Page
Shows stat cards, activity chart, and live event feed.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QFrame, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
import datetime


class MiniBarChart(QWidget):
    """Simple custom bar chart for hourly attempt data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = [0] * 24
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, hourly: list):
        self.data = hourly[-24:] if len(hourly) >= 24 else hourly
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        padding_bottom = 24
        padding_top = 8
        chart_h = h - padding_bottom - padding_top

        # Background
        painter.fillRect(0, 0, w, h, QColor("#0D1117"))

        # Grid lines
        painter.setPen(QPen(QColor("#1E2530"), 1))
        for i in range(4):
            y = padding_top + (chart_h // 3) * i
            painter.drawLine(0, y, w, y)

        max_val = max(self.data) if self.data and max(self.data) > 0 else 1
        bar_count = len(self.data)
        if bar_count == 0:
            return

        bar_width = (w - 2) / bar_count
        gap = max(1, bar_width * 0.15)

        for i, val in enumerate(self.data):
            bar_h = int((val / max_val) * chart_h)
            x = int(i * bar_width + gap / 2)
            bw = int(bar_width - gap)
            y = padding_top + chart_h - bar_h

            # Bar fill
            alpha = min(255, 100 + int((val / max_val) * 155))
            painter.fillRect(x, y, bw, bar_h, QColor(255, 59, 59, alpha))

            # Top highlight
            if bar_h > 3:
                painter.fillRect(x, y, bw, 2, QColor(255, 100, 100, 200))

        # X-axis labels (every 6 hours)
        painter.setPen(QColor("#2A3A4A"))
        font = QFont("Consolas", 8)
        painter.setFont(font)
        now_hour = datetime.datetime.utcnow().hour
        for i in range(0, 24, 6):
            x = int(i * bar_width)
            hour = (now_hour - 23 + i) % 24
            painter.drawText(x, h - 4, f"{hour:02d}h")


class StatCard(QWidget):
    def __init__(self, label: str, value: str = "0", card_type: str = "info", parent=None):
        super().__init__(parent)
        self.setObjectName(f"stat_card_{card_type}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("stat_value")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.text_label = QLabel(label.upper())
        self.text_label.setObjectName("stat_label")

        layout.addWidget(self.value_label)
        layout.addWidget(self.text_label)
        self.setObjectName("stat_card")
        # Re-apply type class for color
        self._type = card_type

    def set_value(self, v):
        self.value_label.setText(str(v))


class DashboardPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(20)

        # ── Title ──
        title_row = QHBoxLayout()
        left_title = QVBoxLayout()
        t = QLabel("DASHBOARD")
        t.setObjectName("page_title")
        s = QLabel("REAL-TIME THREAT OVERVIEW")
        s.setObjectName("page_subtitle")
        left_title.addWidget(t)
        left_title.addWidget(s)

        self.time_label = QLabel()
        self.time_label.setObjectName("status_text")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        title_row.addLayout(left_title)
        title_row.addStretch()
        title_row.addWidget(self.time_label)
        root.addLayout(title_row)

        div = QFrame(); div.setObjectName("section_divider")
        root.addWidget(div)

        # ── Stat cards ──
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_today    = StatCard("Today's Attempts", "0", "danger")
        self.card_total    = StatCard("Total Attempts",   "0", "info")
        self.card_temp     = StatCard("Temp Blocked",     "0", "warning")
        self.card_perm     = StatCard("Perm Blocked",     "0", "danger")
        self.card_unique   = StatCard("Unique IPs Seen",  "0", "info")
        for card in [self.card_today, self.card_total, self.card_temp,
                     self.card_perm, self.card_unique]:
            cards_row.addWidget(card)
        root.addLayout(cards_row)

        # ── Chart + Live log ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # Chart panel
        chart_panel = QVBoxLayout()
        chart_title = QLabel("ATTEMPTS — LAST 24 HOURS")
        chart_title.setObjectName("section_title")
        self.chart = MiniBarChart()
        chart_panel.addWidget(chart_title)
        chart_panel.addWidget(self.chart)
        chart_panel.addStretch()

        chart_container = QWidget()
        chart_container.setObjectName("stat_card")
        inner = QVBoxLayout(chart_container)
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(10)
        label2 = QLabel("ATTEMPTS — LAST 24 HOURS")
        label2.setObjectName("section_title")
        inner.addWidget(label2)
        inner.addWidget(self.chart)
        inner.addStretch()

        # Live event log
        log_panel = QWidget()
        log_panel.setObjectName("stat_card")
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(16, 14, 16, 14)
        log_layout.setSpacing(8)

        log_header = QHBoxLayout()
        log_title = QLabel("LIVE EVENT LOG")
        log_title.setObjectName("section_title")
        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setObjectName("btn_neutral")
        self.clear_btn.setFixedWidth(70)
        self.clear_btn.clicked.connect(self._clear_log)
        log_header.addWidget(log_title)
        log_header.addStretch()
        log_header.addWidget(self.clear_btn)
        log_layout.addLayout(log_header)

        self.event_log = QTextEdit()
        self.event_log.setObjectName("event_log")
        self.event_log.setReadOnly(True)
        self.event_log.setMinimumHeight(180)
        log_layout.addWidget(self.event_log)

        bottom_row.addWidget(chart_container, 55)
        bottom_row.addWidget(log_panel, 45)

        root.addLayout(bottom_row, 1)

        # Clock timer
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._update_clock)
        self._clock.start(1000)
        self._update_clock()

    def _update_clock(self):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d  %H:%M:%S UTC")
        self.time_label.setText(now)

    def _clear_log(self):
        self.event_log.clear()

    def refresh(self):
        stats = self.db.get_stats()
        self.card_today.set_value(stats["today_attempts"])
        self.card_total.set_value(stats["total_attempts"])
        self.card_temp.set_value(stats["temp_blocks"])
        self.card_perm.set_value(stats["perm_blocks"])
        self.card_unique.set_value(stats["unique_ips"])
        self.chart.set_data(stats["hourly"])

    def append_event(self, text: str, color: str = "#6A8FAF"):
        ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
        line = f'<span style="color:#2A4060">[{ts}]</span> <span style="color:{color}">{text}</span>'
        self.event_log.append(line)
        # Auto-scroll
        sb = self.event_log.verticalScrollBar()
        sb.setValue(sb.maximum())
