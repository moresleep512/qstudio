"""Entry point for Qlib Studio Pro (qstudio) Desktop Application."""

from __future__ import annotations

import ctypes
from pathlib import Path
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from qstudio import __app_name__, __version__
from qstudio.ui.main_window import QlibStudioMainWindow


def main() -> int:
    """Launch the Qlib Studio GUI workstation."""
    # Ensure Windows taskbar displays our custom application icon instead of python.exe icon
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                f"quantlab.qstudio.studio.{__version__}"
            )
        except Exception:
            pass

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("QuantResearchLab")
    app.setFont(QFont("Segoe UI", 10))

    icon_path = Path(__file__).resolve().parent / "assets" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = QlibStudioMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
