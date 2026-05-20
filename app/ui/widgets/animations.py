"""Аккуратные служебные анимации: count-up, fade, wipe, pulse."""
from __future__ import annotations

import re

from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QLabel,
    QWidget,
)

_NUM_RE = re.compile(r"^-?\d+(?:[\.,]\d+)?$")


def _parse_number(text: str) -> float | None:
    t = text.strip().replace(" ", "").replace(" ", "").replace(",", ".").rstrip("%")
    return float(t) if _NUM_RE.fullmatch(t) else None


class CountUp(QObject):
    """Быстрый плавный пересчёт числа в QLabel."""

    finished = Signal()

    def __init__(self, label: QLabel, duration_ms: int = 180):
        super().__init__(label)
        self._label = label
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(duration_ms)
        self._anim.setEasingCurve(QEasingCurve.OutExpo)
        self._anim.valueChanged.connect(self._on_step)
        self._anim.finished.connect(self.finished)
        self._suffix = ""
        self._decimals = 0
        self._final_text: str | None = None

    def animate_to(self, new_text: str) -> None:
        target = _parse_number(new_text)
        current = _parse_number(self._label.text())
        if target is None or current is None or target == current:
            self._label.setText(new_text)
            return
        suffix = "%" if new_text.strip().endswith("%") else ""
        m = re.search(r"\.(\d+)", new_text)
        self._decimals = len(m.group(1)) if m else 0
        self._suffix = suffix
        self._final_text = new_text
        self._anim.stop()
        self._anim.setStartValue(float(current))
        self._anim.setEndValue(float(target))
        self._anim.start()

    def _on_step(self, value: float) -> None:
        if self._final_text is None:
            return
        if self._suffix == "%":
            txt = f"{value:.{self._decimals}f}{self._suffix}"
        else:
            txt = (
                f"{value:.{self._decimals}f}" if self._decimals else f"{int(round(value))}"
            )
        self._label.setText(txt)


class Fader:
    """Лёгкая обёртка для эффекта прозрачности на виджете."""

    def __init__(self, widget: QWidget):
        self._widget = widget
        self._effect = QGraphicsOpacityEffect(widget)
        self._effect.setOpacity(1.0)
        widget.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", widget)
        self._anim.setEasingCurve(QEasingCurve.OutExpo)

    def fade_in(self, duration_ms: int = 90, start: float = 0.0) -> None:
        self._anim.stop()
        self._effect.setOpacity(start)
        self._anim.setDuration(duration_ms)
        self._anim.setStartValue(start)
        self._anim.setEndValue(1.0)
        self._anim.start()


class WipeOverlay(QWidget):
    """Полупрозрачная «шторка», бегущая слева направо поверх родителя.

    Используется для «проявления» свежеотрисованного содержимого
    (графика matplotlib, например). 110–140 мс — мгновенно по ощущениям,
    но даёт ясный визуальный «удар» обновления.
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._progress = 0.0
        self.hide()
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.OutExpo)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.valueChanged.connect(self._on_step)
        self._anim.finished.connect(self.hide)

    def play(self) -> None:
        p = self.parentWidget()
        if p is None:
            return
        self.setGeometry(p.rect())
        self.raise_()
        self.show()
        self._progress = 0.0
        self._anim.stop()
        self._anim.start()

    def _on_step(self, v: float) -> None:
        self._progress = float(v)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        if self._progress >= 1.0:
            return
        w = self.width()
        h = self.height()
        x = int(w * self._progress)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        # тёмная маска позади края «шторки»
        mask = QColor(14, 17, 23)  # совпадает с фоном приложения
        mask.setAlpha(int(255 * (1.0 - self._progress)))
        painter.fillRect(QRect(x, 0, w - x, h), mask)
        # узкий световой край у фронта шторки
        edge_w = max(24, int(w * 0.04))
        grad = QLinearGradient(QPoint(x - edge_w, 0), QPoint(x, 0))
        c0 = QColor(124, 138, 176, 0)        # #7c8ab0 → 0 alpha
        c1 = QColor(152, 168, 200, int(120 * (1.0 - self._progress)))  # #98a8c8
        grad.setColorAt(0.0, c0)
        grad.setColorAt(1.0, c1)
        painter.fillRect(QRect(x - edge_w, 0, edge_w, h), grad)
        painter.end()

    def resizeEvent(self, _event) -> None:  # noqa: N802
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())


class GlowPulse(QObject):
    """Мягкая «дышащая» подсветка CTA через QGraphicsDropShadowEffect.

    Не дёргает раскладку (тень не отбирает место). Останавливается на hover
    или после явного `stop()`. Цикл ~1100 мс — заметно, но не назойливо.
    """

    def __init__(self, widget: QWidget):
        super().__init__(widget)
        self._widget = widget
        self._effect = QGraphicsDropShadowEffect(widget)
        self._effect.setColor(QColor(152, 168, 200, 0))
        self._effect.setBlurRadius(0)
        self._effect.setOffset(0, 0)
        widget.setGraphicsEffect(self._effect)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(1100)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(self._on_step)
        self._running = False
        widget.installEventFilter(self)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._anim.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._anim.stop()
        self._running = False
        self._effect.setBlurRadius(0)
        self._effect.setColor(QColor(152, 168, 200, 0))

    def _on_step(self, v: float) -> None:
        # треугольная огибающая: 0→1→0
        env = 1.0 - abs(2.0 * float(v) - 1.0)
        self._effect.setBlurRadius(4 + 22 * env)
        c = QColor(152, 168, 200)
        c.setAlpha(int(180 * env))
        self._effect.setColor(c)

    def eventFilter(self, obj, ev):  # noqa: N802
        from PySide6.QtCore import QEvent
        if obj is self._widget and ev.type() in (QEvent.Enter, QEvent.FocusIn):
            if self._running:
                self.stop()
        return False


class RailIndicator(QWidget):
    """Тонкий акцентный «рейл», скользящий к выбранному пункту меню."""

    def __init__(self, parent: QWidget, width: int = 3, color: str = "#7c8ab0"):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._color = QColor(color)
        self._width = width
        self.resize(QSize(width, 0))
        self._anim_pos = QPropertyAnimation(self, b"pos", self)
        self._anim_pos.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_pos.setDuration(160)
        self._anim_size = QPropertyAnimation(self, b"size", self)
        self._anim_size.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_size.setDuration(160)
        self.hide()

    def move_to(self, target: QWidget) -> None:
        if target is None:
            return
        if target.height() <= 1:
            QTimer.singleShot(0, lambda: self.move_to(target))
            return
        top_left = target.mapTo(self.parentWidget(), QPoint(0, 0))
        new_pos = QPoint(0, top_left.y())
        new_size = QSize(self._width, target.height())
        if not self.isVisible():
            self.move(new_pos)
            self.resize(new_size)
            self.show()
            return
        self._anim_pos.stop()
        self._anim_pos.setStartValue(self.pos())
        self._anim_pos.setEndValue(new_pos)
        self._anim_pos.start()
        self._anim_size.stop()
        self._anim_size.setStartValue(self.size())
        self._anim_size.setEndValue(new_size)
        self._anim_size.start()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.fillRect(self.rect(), self._color)
        p.end()
