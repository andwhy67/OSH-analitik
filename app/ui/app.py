from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.modules.visualization.palette import apply_dark_style

from .main_window import MainWindow


STYLE_PATH = Path(__file__).resolve().parent.parent / "resources" / "styles" / "dark.qss"


def run() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ОСХ-Аналитик")
    app.setApplicationDisplayName("ОСХ-Аналитик")
    app.setOrganizationName("ОСХ-Аналитик")
    app.setFont(QFont("Segoe UI", 10))

    apply_dark_style()
    if STYLE_PATH.exists():
        app.setStyleSheet(STYLE_PATH.read_text(encoding="utf-8"))

    window = MainWindow()
    window.show()

    # дымовой режим для CI: запустить, прожить N секунд, корректно выйти
    smoke_ms = os.environ.get("SYSAN_SMOKE_EXIT_MS")
    if smoke_ms:
        try:
            delay = max(0, int(smoke_ms))
        except ValueError:
            delay = 3000
        QTimer.singleShot(delay, app.quit)

    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
