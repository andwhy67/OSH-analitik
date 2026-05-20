from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from .animations import CountUp


class StatCard(QFrame):
    """Карточка KPI на дашборде."""

    def __init__(self, title: str, value: str = "—", caption: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._title = QLabel(title)
        self._title.setObjectName("CardTitle")
        self._title.setWordWrap(True)
        self._value = QLabel(value)
        self._value.setObjectName("CardValue")
        self._value.setWordWrap(True)
        self._caption = QLabel(caption)
        self._caption.setObjectName("CardCaption")
        self._caption.setWordWrap(True)

        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._caption)
        layout.addStretch(1)

        self._counter = CountUp(self._value, duration_ms=320)

    def set_value(self, value: str) -> None:
        self._counter.animate_to(value)

    def set_caption(self, caption: str) -> None:
        self._caption.setText(caption)
