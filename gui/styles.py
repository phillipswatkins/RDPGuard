"""
Zopi Guard - Application Stylesheet
Dark industrial security aesthetic.
"""

STYLESHEET = """
/* ── Global ──────────────────────────────────────────────────────────── */
* {
    font-family: 'Consolas', 'Courier New', monospace;
    color: #E0E0E0;
}

QMainWindow, QDialog, QWidget {
    background-color: #0D0F14;
}

QStackedWidget, QFrame {
    background-color: transparent;
}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
#sidebar {
    background-color: #080A0E;
    border-right: 1px solid #1E2530;
    min-width: 200px;
    max-width: 200px;
}

#logo_label {
    color: #FF3B3B;
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 3px;
    padding: 8px 0px;
}

#logo_sub {
    color: #4A5568;
    font-size: 9px;
    letter-spacing: 4px;
    padding-bottom: 4px;
}

#nav_button {
    background-color: transparent;
    border: none;
    border-left: 3px solid transparent;
    color: #4A6080;
    font-size: 12px;
    letter-spacing: 1px;
    padding: 12px 20px;
    text-align: left;
    font-weight: normal;
}

#nav_button:hover {
    background-color: #111520;
    color: #A0B4CC;
    border-left: 3px solid #2A4060;
}

#nav_button[active="true"] {
    background-color: #131A24;
    color: #E0E8F0;
    border-left: 3px solid #FF3B3B;
    font-weight: bold;
}

/* ── Status bar ──────────────────────────────────────────────────────── */
#status_bar {
    background-color: #080A0E;
    border-top: 1px solid #1E2530;
    padding: 4px 16px;
}

#status_dot_running {
    color: #00FF88;
    font-size: 10px;
}

#status_dot_stopped {
    color: #FF3B3B;
    font-size: 10px;
}

#status_text {
    color: #4A6080;
    font-size: 11px;
}

/* ── Page titles ─────────────────────────────────────────────────────── */
#page_title {
    color: #FFFFFF;
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 2px;
    padding-bottom: 4px;
}

#page_subtitle {
    color: #4A6080;
    font-size: 10px;
    letter-spacing: 3px;
}

#section_divider {
    background-color: #1E2530;
    max-height: 1px;
    min-height: 1px;
}

/* ── Stat cards ──────────────────────────────────────────────────────── */
#stat_card {
    background-color: #0D1117;
    border: 1px solid #1E2530;
    border-radius: 4px;
    padding: 16px;
}

#stat_value {
    font-size: 36px;
    font-weight: bold;
    color: #FFFFFF;
    letter-spacing: -1px;
}

#stat_label {
    font-size: 9px;
    color: #4A6080;
    letter-spacing: 3px;
}

#stat_card_danger #stat_value  { color: #FF3B3B; }
#stat_card_warning #stat_value { color: #FF9500; }
#stat_card_info #stat_value    { color: #5AC8FA; }
#stat_card_ok #stat_value      { color: #00FF88; }

/* ── Service control buttons ─────────────────────────────────────────── */
#btn_start {
    background-color: #003D1F;
    border: 1px solid #00602F;
    color: #00FF88;
    font-size: 12px;
    letter-spacing: 2px;
    padding: 10px 28px;
    border-radius: 3px;
    font-weight: bold;
}
#btn_start:hover { background-color: #005228; }
#btn_start:disabled { background-color: #1A1A1A; border-color: #2A2A2A; color: #444; }

#btn_stop {
    background-color: #3D0000;
    border: 1px solid #600000;
    color: #FF3B3B;
    font-size: 12px;
    letter-spacing: 2px;
    padding: 10px 28px;
    border-radius: 3px;
    font-weight: bold;
}
#btn_stop:hover { background-color: #520000; }
#btn_stop:disabled { background-color: #1A1A1A; border-color: #2A2A2A; color: #444; }

/* ── Tables ──────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #0D1117;
    border: 1px solid #1E2530;
    gridline-color: #161C24;
    border-radius: 4px;
    font-size: 12px;
}

QTableWidget::item {
    padding: 8px 12px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #1A2535;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #080A0E;
    color: #4A6080;
    font-size: 10px;
    letter-spacing: 2px;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #1E2530;
    border-right: 1px solid #1E2530;
    font-weight: bold;
}

QHeaderView::section:last { border-right: none; }

/* ── Event log ───────────────────────────────────────────────────────── */
#event_log {
    background-color: #080A0E;
    border: 1px solid #1E2530;
    border-radius: 4px;
    font-size: 12px;
    padding: 8px;
    color: #6A8FAF;
}

/* ── Buttons (general) ───────────────────────────────────────────────── */
#btn_danger {
    background-color: #3D0000;
    border: 1px solid #600000;
    color: #FF3B3B;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 6px 16px;
    border-radius: 3px;
}
#btn_danger:hover { background-color: #520000; }

#btn_action {
    background-color: #0D1A2D;
    border: 1px solid #1E3A5F;
    color: #5AC8FA;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 6px 16px;
    border-radius: 3px;
}
#btn_action:hover { background-color: #152438; }

#btn_neutral {
    background-color: #151C26;
    border: 1px solid #1E2D40;
    color: #8090A0;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 6px 16px;
    border-radius: 3px;
}
#btn_neutral:hover { background-color: #1C2535; }

/* ── Input fields ────────────────────────────────────────────────────── */
QLineEdit, QSpinBox, QComboBox {
    background-color: #0D1117;
    border: 1px solid #1E2D40;
    border-radius: 3px;
    color: #C0D0E0;
    font-size: 12px;
    padding: 7px 10px;
    selection-background-color: #1A3A5F;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #2A5080;
    background-color: #0F1520;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #1E2D40;
    border: none;
    width: 18px;
}

QSpinBox::up-arrow  { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 5px solid #5AC8FA; margin: 3px; }
QSpinBox::down-arrow{ image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #5AC8FA; margin: 3px; }

QCheckBox {
    color: #8090A0;
    font-size: 12px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px; height: 16px;
    background-color: #0D1117;
    border: 1px solid #1E2D40;
    border-radius: 2px;
}
QCheckBox::indicator:checked {
    background-color: #1A3A5F;
    border-color: #2A5080;
}

QLabel {
    background-color: transparent;
}

/* ── Settings form labels ────────────────────────────────────────────── */
#form_label {
    color: #4A6080;
    font-size: 10px;
    letter-spacing: 2px;
}

#section_title {
    color: #8090A0;
    font-size: 11px;
    letter-spacing: 3px;
    font-weight: bold;
    padding-top: 8px;
}

/* ── Scrollbars ──────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background-color: #0D0F14;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #1E2D40;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background-color: #2A4060; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background-color: #0D0F14;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background-color: #1E2D40;
    border-radius: 4px;
}

/* ── Tab widget ──────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #1E2530;
    background-color: #0D1117;
    border-radius: 0px 4px 4px 4px;
}
QTabBar::tab {
    background-color: #080A0E;
    color: #4A6080;
    padding: 8px 20px;
    border: 1px solid #1E2530;
    border-bottom: none;
    font-size: 10px;
    letter-spacing: 2px;
}
QTabBar::tab:selected {
    background-color: #0D1117;
    color: #E0E8F0;
    border-top: 2px solid #FF3B3B;
}
QTabBar::tab:hover:!selected { background-color: #0D1117; color: #8090A0; }

/* ── Table cell buttons ─────────────────────────────────────────────── */
QPushButton[class="cell-unblock"] {
    background-color: #0D1A2D;
    border: 2px solid #2A5A8F;
    color: #5AC8FA;
    font-size: 11px;
    font-weight: bold;
    border-radius: 3px;
    padding: 5px 12px;
    min-width: 80px;
}
QPushButton[class="cell-unblock"]:hover { background-color: #1A3A5A; color: #80D8FF; }

QPushButton[class="cell-clear"] {
    background-color: #2A0A0A;
    border: 2px solid #6A2020;
    color: #FF6060;
    font-size: 11px;
    font-weight: bold;
    border-radius: 3px;
    padding: 5px 10px;
    min-width: 60px;
}
QPushButton[class="cell-clear"]:hover { background-color: #3D1010; color: #FF8080; border-color: #AA3030; }

/* ── Tooltip ─────────────────────────────────────────────────────────── */
QToolTip {
    background-color: #0D1117;
    border: 1px solid #2A4060;
    color: #C0D0E0;
    padding: 4px 8px;
    font-size: 11px;
}

/* ── Message box ─────────────────────────────────────────────────────── */
QMessageBox {
    background-color: #0D1117;
}
QMessageBox QPushButton {
    background-color: #151C26;
    border: 1px solid #1E2D40;
    color: #8090A0;
    padding: 6px 20px;
    border-radius: 3px;
    min-width: 80px;
}
QMessageBox QPushButton:hover { background-color: #1C2535; }
"""
