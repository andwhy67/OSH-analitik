from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPoint, Qt, QVariantAnimation
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
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


class _PopoverFrame(QFrame):
    def __init__(self, title: str, body: str, parent=None):
        super().__init__(parent)
        self.setObjectName("InfoPopover")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)
        if title:
            t = QLabel(title)
            t.setObjectName("InfoPopoverTitle")
            lay.addWidget(t)
        b = QLabel(body)
        b.setWordWrap(True)
        b.setTextFormat(Qt.RichText)
        b.setMinimumWidth(360)
        b.setMaximumWidth(420)
        lay.addWidget(b)


class InfoButton(QToolButton):
    """Маленькая «i»-кнопка, открывающая поповер с пояснением."""

    def __init__(self, title: str, body: str, parent=None):
        super().__init__(parent)
        self.setObjectName("InfoButton")
        self.setText("i")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setToolTip("Показать описание раздела")
        self._title = title
        self._body = body
        self.clicked.connect(self._show_popover)

    def update_content(self, title: str, body: str) -> None:
        self._title, self._body = title, body

    def _show_popover(self) -> None:
        menu = QMenu(self)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        act = QWidgetAction(menu)
        act.setDefaultWidget(_PopoverFrame(self._title, self._body))
        menu.addAction(act)
        pos = self.mapToGlobal(QPoint(0, self.height() + 4))
        menu.exec(pos)


class ResultSummary(QLabel):
    """Текст-интерпретация результата с подсветкой при обновлении.

    При смене текста цвет проявляется из акцентного `#98a8c8` к спокойному
    `#b4bbcc` за ~220 мс. Не использует QGraphicsEffect, поэтому
    корректно работает внутри страницы с собственным fade-эффектом.
    """

    _START = QColor("#98a8c8")
    _END = QColor("#b4bbcc")

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("ResultSummary")
        self.setWordWrap(True)
        self.setTextFormat(Qt.RichText)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutExpo)
        self._anim.setStartValue(self._START)
        self._anim.setEndValue(self._END)
        self._anim.valueChanged.connect(self._apply_color)
        self._apply_color(self._END)

    def setText(self, text: str) -> None:  # type: ignore[override]
        if text == self.text():
            super().setText(text)
            return
        super().setText(text)
        self._anim.stop()
        self._apply_color(self._START)
        self._anim.start()

    def _apply_color(self, c: QColor) -> None:
        rgb = f"rgb({c.red()},{c.green()},{c.blue()})"
        self.setStyleSheet(
            "QLabel#ResultSummary {"
            f" color: {rgb};"
            " padding: 8px 12px;"
            " background-color: #131722;"
            " border: 1px solid #1f2330;"
            " border-radius: 6px;"
            "}"
        )


class SectionTitle(QLabel):
    """Маленький заголовок секции в доке/боковой колонке."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("SectionHeader")
