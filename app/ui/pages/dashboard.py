from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.modules.core.matrix import BinaryMatrix
from app.modules.core.optimization import OptimizationResult
from app.modules.visualization.canvas import MplCanvas
from app.modules.visualization.charts import plot_richness
from app.modules.visualization.heatmaps import plot_binary_matrix

from .base import BasePage
from app.ui.widgets import Placeholder, StatCard


class DashboardPage(BasePage):
    title = "Дашборд"
    subtitle = (
        "Сводка по текущему набору объектов и характеристик. Здесь видно "
        "состояние данных, базовые показатели и результат последней оптимизации."
    )

    def build(self) -> None:
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        self.card_objects = StatCard("Объекты", "—", "загрузите данные на странице 'Матрица объектов'")
        self.card_features = StatCard("Характеристики", "—", "столбцов в бинарной матрице")
        self.card_density = StatCard("Плотность", "—", "доля единиц в матрице")
        self.card_optimized = StatCard("Оптимизация", "не выполнялась", "перейдите на страницу 'Оптимизация'")
        for c in (self.card_objects, self.card_features, self.card_density, self.card_optimized):
            cards_row.addWidget(c, 1)
        self._root.addLayout(cards_row)

        body = QGridLayout()
        body.setSpacing(14)

        self._matrix_canvas = MplCanvas(width=6.5, height=4.5)
        self._richness_canvas = MplCanvas(width=6.5, height=4.5)
        self._matrix_canvas.setMinimumHeight(360)
        self._richness_canvas.setMinimumHeight(360)

        self._placeholder = Placeholder(
            "Данные ещё не загружены",
            "Перейдите в раздел 'Матрица объектов' и загрузите CSV/XLSX.",
        )

        body.addWidget(self._placeholder, 0, 0, 1, 2)
        body.addWidget(self._matrix_canvas, 1, 0)
        body.addWidget(self._richness_canvas, 1, 1)
        body.setRowStretch(1, 1)
        body.setColumnStretch(0, 1)
        body.setColumnStretch(1, 1)
        self._root.addLayout(body, 1)

        self._matrix_canvas.hide()
        self._richness_canvas.hide()

        self.state.matrix_changed.connect(self._on_matrix)
        self.state.optimization_changed.connect(self._on_optimization)

    def _on_matrix(self, matrix: BinaryMatrix | None) -> None:
        if matrix is None:
            self.card_objects.set_value("—")
            self.card_features.set_value("—")
            self.card_density.set_value("—")
            self._matrix_canvas.hide()
            self._richness_canvas.hide()
            self._placeholder.show()
            return
        self._placeholder.hide()
        self._matrix_canvas.show()
        self._richness_canvas.show()

        self.card_objects.set_value(str(matrix.n_objects))
        self.card_features.set_value(str(matrix.n_features))
        density = matrix.data.sum() / max(matrix.n_objects * matrix.n_features, 1)
        self.card_density.set_value(f"{density:.1%}")
        self.card_density.set_caption(
            f"единиц: {int(matrix.data.sum())} из {matrix.n_objects * matrix.n_features}"
        )

        plot_binary_matrix(self._matrix_canvas.figure, matrix)
        self._matrix_canvas.draw_idle()
        plot_richness(self._richness_canvas.figure, matrix)
        self._richness_canvas.draw_idle()

    def _on_optimization(self, opt: OptimizationResult | None) -> None:
        if opt is None:
            self.card_optimized.set_value("не выполнялась")
            self.card_optimized.set_caption("перейдите на страницу 'Оптимизация'")
        else:
            kept = len(opt.kept_features)
            removed = len(opt.removed_features)
            self.card_optimized.set_value(f"{kept} призн.")
            self.card_optimized.set_caption(f"исключено {removed}, шагов {len(opt.history)}")
