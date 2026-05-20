from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class HintBadge(QPushButton):
    """Маленькая круглая иконка-вопрос с подсказкой в тултипе."""

    def __init__(self, hint: str, parent=None):
        super().__init__("?", parent)
        self.setObjectName("HintBadge")
        self.setCursor(Qt.WhatsThisCursor)
        self.setFlat(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setToolTip(hint)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(18, 18)


class LabeledField(QWidget):
    """Строка вида: подпись + иконка-подсказка + поле ввода справа."""

    def __init__(self, label: str, field: QWidget, hint: str = "", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lbl = QLabel(label)
        lbl.setMinimumWidth(0)
        lay.addWidget(lbl)
        if hint:
            lay.addWidget(HintBadge(hint))
        lay.addStretch(1)
        lay.addWidget(field)
        self.field = field


class InfoNote(QFrame):
    """Карточка-заметка с пояснением «о чём эта страница / что делать»."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("InfoNote")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.RichText)
        lbl.setObjectName("InfoNoteText")
        lay.addWidget(lbl)


class ResultSummary(QLabel):
    """Однострочный/многострочный текстовый вывод-интерпретация результата."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("ResultSummary")
        self.setWordWrap(True)
        self.setTextFormat(Qt.RichText)
        self.setStyleSheet(
            "QLabel#ResultSummary {"
            "color: #b4bbcc; padding: 8px 10px;"
            "background-color: #131722; border: 1px solid #1f2330;"
            "border-radius: 6px;"
            "}"
        )
