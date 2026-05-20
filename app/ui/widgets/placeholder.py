from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class Placeholder(QFrame):
    """Карточка-заглушка с подсказкой, что нужно сделать."""

    def __init__(self, title: str, hint: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        t = QLabel(title)
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("font-size: 14pt; font-weight: 600;")
        t.setWordWrap(True)
        h = QLabel(hint)
        h.setAlignment(Qt.AlignCenter)
        h.setStyleSheet("color: #8a93a6;")
        h.setWordWrap(True)
        layout.addWidget(t)
        layout.addWidget(h)
