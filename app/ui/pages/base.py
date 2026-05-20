from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.ui.state import AppState


class BasePage(QWidget):
    """Базовая страница: единое оформление шапки + ссылка на AppState."""

    title: str = ""
    subtitle: str = ""

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(28, 24, 28, 24)
        self._root.setSpacing(10)

        if self.title:
            t = QLabel(self.title)
            t.setObjectName("PageTitle")
            t.setWordWrap(True)
            self._root.addWidget(t)
        if self.subtitle:
            s = QLabel(self.subtitle)
            s.setObjectName("PageSubtitle")
            s.setWordWrap(True)
            s.setMinimumWidth(0)
            self._root.addWidget(s)

        self.build()

    def build(self) -> None:
        """Переопределяется в наследниках."""
        raise NotImplementedError
