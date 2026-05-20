from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout

from app.modules.core.matrix import BinaryMatrix
from app.modules.core.optimization import OptimizationResult
from app.modules.visualization.canvas import MplCanvas
from app.modules.visualization.charts import plot_richness
from app.modules.visualization.heatmaps import plot_binary_matrix
from app.ui.widgets import InfoNote, Placeholder, ResultSummary, StatCard

from .base import BasePage


class DashboardPage(BasePage):
    title = "Дашборд"
    subtitle = (
        "Сводка по текущему набору объектов и характеристик: состояние данных, "
        "базовые показатели и итог последней оптимизации."
    )

    def build(self) -> None:
        intro = InfoNote(
            "Эта страница показывает <b>текущий контекст работы</b>: сколько объектов "
            "и признаков загружено, насколько плотна матрица и был ли уже выполнен расчёт. "
            "Дальнейшие шаги — слева в навигации, разделы становятся активными по мере появления данных."
        )
        self._root.addWidget(intro)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        self.card_objects = StatCard("Объекты", "—", "строки бинарной матрицы")
        self.card_features = StatCard("Характеристики", "—", "столбцы бинарной матрицы")
        self.card_density = StatCard("Плотность", "—", "доля единиц во всей матрице")
        self.card_optimized = StatCard("Оптимизация", "не выполнялась", "перейдите в раздел «Оптимизация»")
        for c in (self.card_objects, self.card_features, self.card_density, self.card_optimized):
            cards_row.addWidget(c, 1)
        self._root.addLayout(cards_row)

        self._next_step = ResultSummary(
            "Следующий шаг: загрузите CSV/XLSX или сгенерируйте пример в разделе «Матрица объектов»."
        )
        self._root.addWidget(self._next_step)

        body = QGridLayout()
        body.setSpacing(14)

        self._matrix_canvas = MplCanvas(width=6.5, height=4.5)
        self._richness_canvas = MplCanvas(width=6.5, height=4.5)
        self._matrix_canvas.setMinimumHeight(360)
        self._richness_canvas.setMinimumHeight(360)

        self._placeholder = Placeholder(
            "Данные ещё не загружены",
            "Перейдите в раздел «Матрица объектов» и загрузите CSV / XLSX "
            "либо нажмите «Сгенерировать случайный набор», чтобы попробовать на демо.",
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
            self._next_step.setText(
                "Следующий шаг: загрузите данные в разделе «Матрица объектов»."
            )
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

        if self.state.optimization is None:
            self._next_step.setText(
                f"Данные загружены ({matrix.n_objects} × {matrix.n_features}). "
                "Дальше — посмотрите попарные сходства в «Анализе» "
                "или сразу запустите расчёт в «Оптимизации»."
            )

    def _on_optimization(self, opt: OptimizationResult | None) -> None:
        if opt is None:
            self.card_optimized.set_value("не выполнялась")
            self.card_optimized.set_caption("перейдите в раздел «Оптимизация»")
            if self.state.matrix is not None:
                m = self.state.matrix
                self._next_step.setText(
                    f"Данные загружены ({m.n_objects} × {m.n_features}). "
                    "Дальше — «Анализ» или «Оптимизация»."
                )
        else:
            kept = len(opt.kept_features)
            removed = len(opt.removed_features)
            self.card_optimized.set_value(f"{kept} призн.")
            self.card_optimized.set_caption(f"исключено {removed}, шагов {len(opt.history)}")
            total = kept + removed
            share = removed / total if total else 0.0
            self._next_step.setText(
                f"Оптимизация выполнена: <b>сохранено {kept}</b> из {total} признаков "
                f"(исключено {removed}, это {share:.0%}). "
                "Можно перейти в «Визуализацию», чтобы сравнить структуру до и после, "
                "или вернуться к «Матрице объектов» и применить сокращённый состав."
            )
