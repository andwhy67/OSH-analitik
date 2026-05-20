from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

ICONS_DIR = Path(__file__).resolve().parent.parent / "resources" / "icons"


@dataclass
class NavItem:
    key: str
    label: str
    icon: str
    requires: tuple[str, ...] = field(default_factory=tuple)
    locked_hint: str = ""


class _NavRow(QWidget):
    """Кнопка пункта + опциональный значок-замок справа, в одном ряду."""

    clicked = Signal(str)

    def __init__(self, item: NavItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setObjectName("NavRow")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.button = QPushButton(f"  {item.label}")
        self.button.setObjectName("NavButton")
        self.button.setCheckable(True)
        self.button.setCursor(Qt.PointingHandCursor)
        icon_path = ICONS_DIR / item.icon
        if icon_path.exists():
            self.button.setIcon(QIcon(str(icon_path)))
            self.button.setIconSize(QSize(18, 18))
        self.button.clicked.connect(lambda _checked=False: self.clicked.emit(item.key))
        lay.addWidget(self.button, 1)

        self.lock = QLabel("\U0001F512")
        self.lock.setObjectName("NavLock")
        self.lock.setStyleSheet("color: #4a526a; padding-right: 18px;")
        self.lock.hide()
        lay.addWidget(self.lock)

    def set_locked(self, locked: bool, hint: str = "") -> None:
        self.button.setEnabled(not locked)
        if locked:
            self.lock.show()
            self.button.setCursor(Qt.ForbiddenCursor)
            self.button.setToolTip(hint)
            self.lock.setToolTip(hint)
        else:
            self.lock.hide()
            self.button.setCursor(Qt.PointingHandCursor)
            self.button.setToolTip("")
            self.lock.setToolTip("")


class Sidebar(QFrame):
    """Левая навигационная панель с гейтингом пунктов по доступности данных."""

    navigated = Signal(str)

    def __init__(self, items: list[NavItem], parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(248)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        brand = QLabel("ОСХ-Аналитик")
        brand.setObjectName("SidebarBrand")
        subtitle = QLabel("Оптимизация состава характеристик · СППР")
        subtitle.setObjectName("SidebarSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(brand)
        layout.addWidget(subtitle)

        section_main = QLabel("Навигация")
        section_main.setObjectName("SectionHeader")
        layout.addWidget(section_main)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._rows: dict[str, _NavRow] = {}
        self._items: dict[str, NavItem] = {}
        for item in items:
            row = _NavRow(item)
            row.clicked.connect(self.navigated.emit)
            self._group.addButton(row.button)
            self._rows[item.key] = row
            self._items[item.key] = item
            layout.addWidget(row)

        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        footer = QLabel("v0.1 · метод Г. Н. Хубаева")
        footer.setObjectName("SidebarFooter")
        footer.setAlignment(Qt.AlignLeft)
        layout.addWidget(footer)

    def select(self, key: str) -> None:
        row = self._rows.get(key)
        if row is not None and row.button.isEnabled():
            row.button.setChecked(True)

    def set_availability(self, available: dict[str, bool]) -> None:
        """Включает/выключает пункты по словарю флагов доступности."""
        for key, row in self._rows.items():
            ok = available.get(key, True)
            row.set_locked(not ok, hint=self._items[key].locked_hint if not ok else "")

    def first_available(self) -> str | None:
        for key, row in self._rows.items():
            if row.button.isEnabled():
                return key
        return None

    def is_available(self, key: str) -> bool:
        row = self._rows.get(key)
        return bool(row and row.button.isEnabled())
