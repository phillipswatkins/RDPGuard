"""
Zopi Guard - Main Entry Point
Run this file to launch the GUI application.
Requires Administrator privileges for firewall management.
"""

import sys
import os

# Ensure the app directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow


def main():
    # Enable high DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("Zopi Guard")
    app.setOrganizationName("ZopiGuard")
    app.setStyle("Fusion")

    window = MainWindow()
    # If launched with --minimised (e.g. from Windows startup), go to tray silently
    if "--minimised" in sys.argv:
        window.hide()
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
