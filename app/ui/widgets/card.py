from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


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
        self._value = QLabel(value)
        self._value.setObjectName("CardValue")
        self._caption = QLabel(caption)
        self._caption.setObjectName("CardCaption")
        self._caption.setWordWrap(True)

        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._caption)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self._value.setText(value)

    def set_caption(self, caption: str) -> None:
        self._caption.setText(caption)
