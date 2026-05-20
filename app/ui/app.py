from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from app.modules.visualization.palette import apply_dark_style

from .main_window import MainWindow

RESOURCES = Path(__file__).resolve().parent.parent / "resources"
STYLE_PATH = RESOURCES / "styles" / "dark.qss"
FONTS_DIR = RESOURCES / "fonts"


def _load_app_fonts() -> str:
    """Подгружает встроенные TTF и возвращает имя семейства для применения."""
    if not FONTS_DIR.exists():
        return "Segoe UI"
    loaded_families: set[str] = set()
    for ttf in FONTS_DIR.glob("*.ttf"):
        fid = QFontDatabase.addApplicationFont(str(ttf))
        if fid >= 0:
            for fam in QFontDatabase.applicationFontFamilies(fid):
                loaded_families.add(fam)
    for preferred in ("IBM Plex Sans", "Inter", "Source Sans 3"):
        if preferred in loaded_families:
            return preferred
    return "Segoe UI"


def run() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ОСХ-Аналитик")
    app.setApplicationDisplayName("ОСХ-Аналитик")
    app.setOrganizationName("ОСХ-Аналитик")
    family = _load_app_fonts()
    app.setFont(QFont(family, 10))

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
