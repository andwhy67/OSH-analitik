from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.state import AppState
from app.ui.widgets import InfoButton


class BasePage(QWidget):
    """Базовая страница: шапка с «i»-поповером и контентом.

    Параметры раздела не лежат внутри страницы — они отдаются через
    `parameters_widget()` и помещаются MainWindow в правый док.
    """

    title: str = ""
    subtitle: str = ""
    info_title: str = ""
    info_body: str = ""

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self._params: QWidget | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 18, 24, 18)
        outer.setSpacing(8)

        header = QWidget()
        header.setObjectName("PageHeader")
        h = QVBoxLayout(header)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        if self.title:
            t = QLabel(self.title)
            t.setObjectName("PageTitle")
            t.setWordWrap(True)
            title_row.addWidget(t)
        if self.info_body:
            self._info_btn = InfoButton(self.info_title or self.title, self.info_body)
            title_row.addWidget(self._info_btn, 0, Qt.AlignVCenter)
        title_row.addStretch(1)
        h.addLayout(title_row)
        if self.subtitle:
            s = QLabel(self.subtitle)
            s.setObjectName("PageSubtitle")
            s.setWordWrap(True)
            h.addWidget(s)
        outer.addWidget(header)

        self._root = QVBoxLayout()
        self._root.setContentsMargins(0, 6, 0, 0)
        self._root.setSpacing(10)
        outer.addLayout(self._root, 1)

        self.build()

    def build(self) -> None:
        raise NotImplementedError

    def parameters_widget(self) -> QWidget | None:
        """Возвращает виджет параметров для правого дока. None — параметров нет."""
        return self._params
