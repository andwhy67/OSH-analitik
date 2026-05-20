from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
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

RESOURCES = Path(__file__).resolve().parent.parent / "resources"

_NEEDS_MATRIX = "Сначала загрузите бинарную матрицу в разделе «Матрица объектов»."


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ОСХ-Аналитик — оптимизация состава характеристик объектов")
        self.resize(1440, 900)
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

        self.stack = QStackedWidget()
        self.pages = {
            "dashboard": DashboardPage(self.state),
            "matrix": MatrixPage(self.state),
            "analysis": AnalysisPage(self.state),
            "optimization": OptimizationPage(self.state),
            "expert": ExpertPage(self.state),
            "visualization": VisualizationPage(self.state),
        }
        for key in ("dashboard", "matrix", "analysis", "optimization", "expert", "visualization"):
            self.stack.addWidget(self.pages[key])

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        status = QStatusBar()
        self.setStatusBar(status)
        self.state.status_message.connect(lambda msg: status.showMessage(msg, 6000))

        self.state.matrix_changed.connect(self._refresh_availability)
        self.state.experts_changed.connect(self._refresh_availability)
        self._refresh_availability()

        self.sidebar.select("dashboard")
        self.stack.setCurrentWidget(self.pages["dashboard"])

    def _navigate(self, key: str) -> None:
        page = self.pages.get(key)
        if page is not None and self.sidebar.is_available(key):
            self.stack.setCurrentWidget(page)

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
