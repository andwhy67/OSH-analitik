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
            NavItem("analysis", "Анализ", "analysis.svg"),
            NavItem("optimization", "Оптимизация", "optimization.svg"),
            NavItem("expert", "Эксперты", "expert.svg"),
            NavItem("visualization", "Визуализация", "visualization.svg"),
        ]
        self.sidebar = Sidebar(items)
        self.sidebar.navigated.connect(self._navigate)

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

        self.sidebar.select("dashboard")
        self.stack.setCurrentWidget(self.pages["dashboard"])

    def _navigate(self, key: str) -> None:
        page = self.pages.get(key)
        if page is not None:
            self.stack.setCurrentWidget(page)
