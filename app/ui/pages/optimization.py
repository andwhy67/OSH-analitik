from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.modules.core.matrix import BinaryMatrix
from app.modules.core.optimization import (
    KhubaevOptimizer,
    OptimizationConfig,
    OptimizationResult,
)
from app.modules.visualization.canvas import MplCanvas
from app.modules.visualization.charts import plot_feature_importance, plot_object_ranking
from app.modules.visualization.heatmaps import plot_similarity_matrix

from .base import BasePage
from app.ui.widgets import DataFrameTable, Placeholder


class OptimizationPage(BasePage):
    title = "Оптимизация состава характеристик"
    subtitle = (
        "Универсальный метод Хубаева: итеративное удаление "
        "малоинформативных характеристик и выявление кандидатов на добавление."
    )

    def build(self) -> None:
        controls = QGroupBox("Параметры алгоритма")
        layout = QHBoxLayout(controls)

        form = QFormLayout()
        self._cmb_sim = QComboBox()
        self._cmb_sim.addItem("Жаккар", "jaccard")
        self._cmb_sim.addItem("Включение", "inclusion")
        form.addRow("Мера сходства:", self._cmb_sim)

        self._sp_min_freq = QDoubleSpinBox()
        self._sp_min_freq.setRange(0.0, 1.0)
        self._sp_min_freq.setSingleStep(0.01)
        self._sp_min_freq.setDecimals(3)
        self._sp_min_freq.setValue(0.05)
        form.addRow("Мин. частота признака:", self._sp_min_freq)

        self._sp_max_freq = QDoubleSpinBox()
        self._sp_max_freq.setRange(0.0, 1.0)
        self._sp_max_freq.setSingleStep(0.01)
        self._sp_max_freq.setDecimals(3)
        self._sp_max_freq.setValue(0.98)
        form.addRow("Макс. частота признака:", self._sp_max_freq)

        self._sp_info = QDoubleSpinBox()
        self._sp_info.setRange(0.0, 10.0)
        self._sp_info.setDecimals(5)
        self._sp_info.setSingleStep(0.0001)
        self._sp_info.setValue(0.0001)
        form.addRow("Порог информативности:", self._sp_info)

        self._sp_missing = QDoubleSpinBox()
        self._sp_missing.setRange(0.0, 1.0)
        self._sp_missing.setSingleStep(0.05)
        self._sp_missing.setDecimals(2)
        self._sp_missing.setValue(0.60)
        form.addRow("Порог 'недостающих' (доля):", self._sp_missing)

        self._sp_iter = QSpinBox()
        self._sp_iter.setRange(1, 200)
        self._sp_iter.setValue(25)
        form.addRow("Макс. итераций:", self._sp_iter)

        layout.addLayout(form, 1)

        right = QVBoxLayout()
        self._btn_run = QPushButton("Запустить оптимизацию")
        self._btn_run.setObjectName("Primary")
        self._btn_run.clicked.connect(self._run)
        self._btn_apply = QPushButton("Применить оптимизированный состав к матрице")
        self._btn_apply.clicked.connect(self._apply)
        self._btn_apply.setEnabled(False)
        right.addStretch(1)
        right.addWidget(self._btn_run)
        right.addWidget(self._btn_apply)
        layout.addLayout(right)

        self._root.addWidget(controls)

        self._tabs = QTabWidget()
        self._root.addWidget(self._tabs, 1)

        self._canvas_imp = MplCanvas(width=6.0, height=5.0)
        self._table_imp = DataFrameTable()
        imp_split = QSplitter(Qt.Horizontal)
        imp_split.addWidget(self._canvas_imp)
        imp_split.addWidget(self._table_imp)
        imp_split.setSizes([520, 380])
        self._tabs.addTab(imp_split, "Информативность характеристик")

        self._canvas_rank = MplCanvas(width=6.0, height=5.0)
        self._table_rank = DataFrameTable()
        rank_split = QSplitter(Qt.Horizontal)
        rank_split.addWidget(self._canvas_rank)
        rank_split.addWidget(self._table_rank)
        rank_split.setSizes([520, 380])
        self._tabs.addTab(rank_split, "Ранжирование объектов")

        self._canvas_before = MplCanvas(width=5.0, height=5.0)
        self._canvas_after = MplCanvas(width=5.0, height=5.0)
        sim_w = QWidget()
        sim_l = QHBoxLayout(sim_w)
        sim_l.setContentsMargins(0, 0, 0, 0)
        sim_l.addWidget(self._canvas_before)
        sim_l.addWidget(self._canvas_after)
        self._tabs.addTab(sim_w, "Сходство: до / после")

        self._table_missing = DataFrameTable()
        self._tabs.addTab(self._wrap("Кандидаты на добавление", self._table_missing), "Недостающие характеристики")

        self._lbl_history = QLabel("Шаги оптимизации:")
        self._lbl_history.setStyleSheet("color: #8a93a6;")
        self._tab_history = DataFrameTable()
        hist_w = QWidget()
        hist_l = QVBoxLayout(hist_w)
        hist_l.addWidget(self._lbl_history)
        hist_l.addWidget(self._tab_history)
        self._tabs.addTab(hist_w, "Журнал шагов")

        self._placeholder = Placeholder(
            "Нет матрицы",
            "Загрузите бинарную матрицу на странице 'Матрица объектов'.",
        )
        self._root.addWidget(self._placeholder)
        self._tabs.hide()
        controls.setEnabled(False)
        self._controls = controls

        self.state.matrix_changed.connect(self._on_matrix)

    @staticmethod
    def _wrap(title: str, widget: QWidget) -> QWidget:
        box = QGroupBox(title)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 18, 10, 10)
        lay.addWidget(widget)
        return box

    def _on_matrix(self, matrix: BinaryMatrix | None) -> None:
        if matrix is None:
            self._tabs.hide()
            self._placeholder.show()
            self._controls.setEnabled(False)
            self._btn_apply.setEnabled(False)
            return
        self._placeholder.hide()
        self._tabs.show()
        self._controls.setEnabled(True)

    def _current_config(self) -> OptimizationConfig:
        return OptimizationConfig(
            similarity=self._cmb_sim.currentData(),
            min_feature_frequency=self._sp_min_freq.value(),
            max_feature_frequency=self._sp_max_freq.value(),
            informativeness_threshold=self._sp_info.value(),
            missing_coverage_threshold=self._sp_missing.value(),
            max_iterations=self._sp_iter.value(),
        )

    def _run(self) -> None:
        matrix = self.state.matrix
        if matrix is None:
            return
        cfg = self._current_config()
        self.state.update_config(cfg)
        result = KhubaevOptimizer(cfg).run(matrix)
        self.state.set_optimization(result)
        self._render(result)
        self._btn_apply.setEnabled(True)
        self.state.status_message.emit(
            f"Оптимизация выполнена: оставлено {len(result.kept_features)} из {matrix.n_features}"
        )

    def _apply(self) -> None:
        opt = self.state.optimization
        if opt is None:
            return
        self.state.set_matrix(
            opt.optimized_matrix, source="<optimized>", preserve_optimization=True
        )
        self.state.status_message.emit("Оптимизированный состав применён к рабочей матрице")
        self._btn_apply.setEnabled(False)

    def _render(self, opt: OptimizationResult) -> None:
        plot_feature_importance(self._canvas_imp.figure, opt.feature_importance)
        self._canvas_imp.draw_idle()
        self._table_imp.set_dataframe(opt.feature_importance.round(5))

        plot_object_ranking(self._canvas_rank.figure, opt.object_ranking)
        self._canvas_rank.draw_idle()
        self._table_rank.set_dataframe(opt.object_ranking.round(4))

        plot_similarity_matrix(
            self._canvas_before.figure,
            opt.similarity_before,
            self.state.matrix.objects if self.state.matrix else [],
            title="Сходство до оптимизации",
        )
        self._canvas_before.draw_idle()
        plot_similarity_matrix(
            self._canvas_after.figure,
            opt.similarity_after,
            opt.optimized_matrix.objects,
            title="Сходство после оптимизации",
        )
        self._canvas_after.draw_idle()

        self._table_missing.set_dataframe(opt.missing.round(3) if not opt.missing.empty else opt.missing)

        hist_df = pd.DataFrame(opt.history)
        if hist_df.empty:
            hist_df = pd.DataFrame({"info": ["оптимизация не нашла признаков для удаления"]})
        else:
            hist_df["dropped"] = hist_df["dropped"].map(lambda xs: ", ".join(xs))
        self._tab_history.set_dataframe(hist_df)
