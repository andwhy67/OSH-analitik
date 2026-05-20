from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

ICONS_DIR = Path(__file__).resolve().parent.parent / "resources" / "icons"


@dataclass
class NavItem:
    key: str
    label: str
    icon: str


class Sidebar(QFrame):
    """Левая навигационная панель."""

    navigated = Signal(str)

    def __init__(self, items: list[NavItem], parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        brand = QLabel("ОСХ-Аналитик")
        brand.setObjectName("SidebarBrand")
        subtitle = QLabel("Оптимизация состава характеристик · СППР")
        subtitle.setObjectName("SidebarSubtitle")
        layout.addWidget(brand)
        layout.addWidget(subtitle)

        section_main = QLabel("Навигация")
        section_main.setObjectName("SectionHeader")
        layout.addWidget(section_main)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}
        for item in items:
            btn = QPushButton(f"  {item.label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            icon_path = ICONS_DIR / item.icon
            if icon_path.exists():
                btn.setIcon(QIcon(str(icon_path)))
                btn.setIconSize(QSize(18, 18))
            btn.clicked.connect(lambda _checked=False, k=item.key: self.navigated.emit(k))
            self._buttons[item.key] = btn
            self._group.addButton(btn)
            layout.addWidget(btn)

        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        footer = QLabel("v0.1 · реализация метода Г. Н. Хубаева")
        footer.setStyleSheet("color: #4a526a; padding: 14px 22px;")
        footer.setAlignment(Qt.AlignLeft)
        layout.addWidget(footer)

    def select(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn is not None:
            btn.setChecked(True)
