"""
Zopi Guard - System Tray Icon
Shows service status in the Windows system tray.
"""

import os
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QSize


def _make_tray_icon(active: bool) -> QIcon:
    """
    Draw a simple shield icon in green (active) or red (stopped).
    Falls back to a coloured circle if drawing fails.
    """
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    colour = QColor("#00E87A") if active else QColor("#FF3030")

    # Outer shield shape (simplified as rounded rect + triangle point)
    p.setBrush(QBrush(colour))
    p.setPen(Qt.PenStyle.NoPen)

    # Body
    p.drawRoundedRect(8, 4, 48, 44, 8, 8)

    # Point at bottom
    from PyQt6.QtGui import QPolygon
    from PyQt6.QtCore import QPoint
    triangle = QPolygon([
        QPoint(8,  40),
        QPoint(56, 40),
        QPoint(32, 60),
    ])
    p.drawPolygon(triangle)

    # Inner Z letter
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("#0D0F14")))
    # Simple Z using rectangles
    bar_h = 5
    p.drawRect(18, 16, 28, bar_h)   # top bar
    p.drawRect(18, 38, 28, bar_h)   # bottom bar
    # Diagonal — approximate with a parallelogram
    from PyQt6.QtGui import QPolygonF
    from PyQt6.QtCore import QPointF
    diag = QPolygonF([
        QPointF(42, 21),
        QPointF(46, 21),
        QPointF(22, 38),
        QPointF(18, 38),
    ])
    p.drawPolygon(diag)

    p.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, main_window):
        super().__init__()
        self._window = main_window
        self._active = False

        self.set_status(False)
        self._build_menu()

        self.activated.connect(self._on_activated)
        self.show()

    def _build_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0D1017;
                border: 1px solid #1A2233;
                color: #D8E4F0;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 4px;
            }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background-color: #1A2535; }
            QMenu::separator { background: #1A2233; height: 1px; margin: 4px 0; }
        """)

        self._status_action = menu.addAction("● Service Stopped")
        self._status_action.setEnabled(False)
        menu.addSeparator()

        show_action = menu.addAction("Open Zopi Guard")
        show_action.triggered.connect(self._show_window)

        menu.addSeparator()

        self._start_action = menu.addAction("▶  Start Service")
        self._start_action.triggered.connect(self._window._start_monitor)

        self._stop_action = menu.addAction("■  Stop Service")
        self._stop_action.triggered.connect(self._window._stop_monitor)
        self._stop_action.setEnabled(False)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)

        self.setContextMenu(menu)

    def set_status(self, active: bool):
        self._active = active
        self.setIcon(_make_tray_icon(active))
        tooltip = "Zopi Guard — Service Running" if active else "Zopi Guard — Service Stopped"
        self.setToolTip(tooltip)
        if hasattr(self, '_status_action'):
            dot = "●" if active else "●"
            colour_hint = " (Active)" if active else " (Stopped)"
            self._status_action.setText(f"{dot} Service{colour_hint}")
        if hasattr(self, '_start_action'):
            self._start_action.setEnabled(not active)
            self._stop_action.setEnabled(active)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self):
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _quit(self):
        self._window._stop_monitor()
        QSystemTrayIcon.hide(self)
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
