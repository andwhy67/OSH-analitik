from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .pages import (
    AnalysisPage,
    DashboardPage,
    ExpertPage,
    MatrixPage,
    OptimizationPage,
    VisualizationPage,
)
from .sidebar import NavItem, Sidebar
from .state import AppState
from .widgets import Fader

RESOURCES = Path(__file__).resolve().parent.parent / "resources"

_NEEDS_MATRIX = "Сначала загрузите бинарную матрицу в разделе «Матрица объектов»."

_PAGE_ORDER = ("dashboard", "matrix", "analysis", "optimization", "expert", "visualization")


class _EmptyParams(QWidget):
    """Заглушка для пунктов без параметров (например, Дашборда)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 20, 16, 20)
        lay.setSpacing(6)
        t = QLabel("Параметры для этого раздела не требуются.")
        t.setStyleSheet("color: #8a93a6;")
        t.setWordWrap(True)
        lay.addWidget(t)
        lay.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("ОСХ-Аналитик — оптимизация состава характеристик объектов")
        self.resize(1480, 920)
        self.setDockOptions(
            QMainWindow.AnimatedDocks
            | QMainWindow.AllowNestedDocks
            | QMainWindow.AllowTabbedDocks
        )

        ico = RESOURCES / "icons" / "osh-analitik.ico"
        self.setWindowIcon(QIcon(str(ico if ico.exists() else RESOURCES / "icons" / "logo.svg")))

        self.state = AppState()

        items = [
            NavItem("dashboard", "Дашборд", "dashboard.svg"),
            NavItem("matrix", "Матрица объектов", "matrix.svg"),
            NavItem(
                "analysis", "Анализ", "analysis.svg",
                requires=("matrix",), locked_hint=_NEEDS_MATRIX,
            ),
            NavItem(
                "optimization", "Оптимизация", "optimization.svg",
                requires=("matrix",), locked_hint=_NEEDS_MATRIX,
            ),
            NavItem("expert", "Эксперты", "expert.svg"),
            NavItem(
                "visualization", "Визуализация", "visualization.svg",
                requires=("matrix",), locked_hint=_NEEDS_MATRIX,
            ),
        ]
        self.sidebar = Sidebar(items)
        self.sidebar.navigated.connect(self._navigate)
        self._nav_items = {it.key: it for it in items}

        # центральная зона: сайдбар + стек страниц
        self.stack = QStackedWidget()
        self.pages = {
            "dashboard": DashboardPage(self.state),
            "matrix": MatrixPage(self.state),
            "analysis": AnalysisPage(self.state),
            "optimization": OptimizationPage(self.state),
            "expert": ExpertPage(self.state),
            "visualization": VisualizationPage(self.state),
        }
        self._page_fader: dict[str, Fader] = {}
        for key in _PAGE_ORDER:
            self.stack.addWidget(self.pages[key])
            self._page_fader[key] = Fader(self.pages[key])

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        # правый док с параметрами
        self.params_dock = QDockWidget("Параметры раздела", self)
        self.params_dock.setObjectName("ParametersDock")
        self.params_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.params_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        self.params_stack = QStackedWidget()
        self.params_stack.setMinimumWidth(260)
        self._params_indices: dict[str, int] = {}
        for key in _PAGE_ORDER:
            page = self.pages[key]
            w = page.parameters_widget() or _EmptyParams()
            self._params_indices[key] = self.params_stack.addWidget(w)
        self.params_dock.setWidget(self.params_stack)
        self.addDockWidget(Qt.RightDockWidgetArea, self.params_dock)
        self.resizeDocks([self.params_dock], [320], Qt.Horizontal)

        # статусбар
        status = QStatusBar()
        self.setStatusBar(status)
        self.state.status_message.connect(lambda msg: status.showMessage(msg, 6000))

        self.state.matrix_changed.connect(self._refresh_availability)
        self.state.experts_changed.connect(self._refresh_availability)
        self._refresh_availability()

        # восстановление геометрии
        self._settings = QSettings("OSH-Analitik", "ui")
        geom = self._settings.value("main/geometry")
        state = self._settings.value("main/windowState")
        last_page = self._settings.value("main/page", "dashboard")
        if geom is not None:
            self.restoreGeometry(geom)
        if state is not None:
            self.restoreState(state)

        if not isinstance(last_page, str) or last_page not in self.pages:
            last_page = "dashboard"
        if not self.sidebar.is_available(last_page):
            last_page = self.sidebar.first_available() or "dashboard"
        self.sidebar.select(last_page)
        self._activate(last_page)

    def _activate(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        self._page_fader[key].fade_in(duration_ms=90, start=0.35)
        self.params_stack.setCurrentIndex(self._params_indices[key])
        has_params = page.parameters_widget() is not None
        self.params_dock.setVisible(has_params)

    def _navigate(self, key: str) -> None:
        if not self.sidebar.is_available(key):
            return
        self._activate(key)
        self._settings.setValue("main/page", key)

    def _refresh_availability(self, *_args) -> None:
        has_matrix = self.state.matrix is not None
        has_experts = (
            self.state.experts is not None
            and self.state.experts.rankings is not None
            and not self.state.experts.rankings.empty
        )
        ctx = {"matrix": has_matrix, "experts": has_experts}
        available = {}
        for key, item in self._nav_items.items():
            available[key] = all(ctx.get(req, True) for req in item.requires)
        self.sidebar.set_availability(available)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._settings.setValue("main/geometry", self.saveGeometry())
        self._settings.setValue("main/windowState", self.saveState())
        super().closeEvent(event)
