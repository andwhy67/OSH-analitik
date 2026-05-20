from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.modules.core.matrix import BinaryMatrix
from app.modules.core.ranking import (
    missing_characteristics,
    rank_objects_by_dominance,
    rank_objects_by_richness,
)
from app.modules.core.similarity import (
    cosine_similarity_binary,
    inclusion_matrix,
    jaccard_matrix,
    sorensen_dice_matrix,
)
from app.modules.visualization.canvas import MplCanvas
from app.modules.visualization.heatmaps import plot_similarity_matrix
from app.ui.widgets import DataFrameTable, Placeholder

from .base import BasePage

_SIMILARITIES = {
    "Жаккар": jaccard_matrix,
    "Сёренсен-Дайс": sorensen_dice_matrix,
    "Косинусная": cosine_similarity_binary,
    "Включение (асимметрично)": inclusion_matrix,
}


class AnalysisPage(BasePage):
    title = "Анализ сходства и ранжирование"
    subtitle = (
        "Попарные коэффициенты сходства и включения, ранжирование объектов "
        "по богатству и доминированию, поиск недостающих характеристик."
    )

    def build(self) -> None:
        controls = QGroupBox("Параметры")
        cl = QHBoxLayout(controls)
        self._cmb_metric = QComboBox()
        for name in _SIMILARITIES:
            self._cmb_metric.addItem(name)
        self._cmb_metric.currentIndexChanged.connect(self._refresh)
        cl.addWidget(QLabel("Мера сходства:"))
        cl.addWidget(self._cmb_metric)
        cl.addStretch(1)
        self._btn_recalc = QPushButton("Пересчитать")
        self._btn_recalc.setObjectName("Primary")
        self._btn_recalc.clicked.connect(self._refresh)
        cl.addWidget(self._btn_recalc)
        self._root.addWidget(controls)

        self._tabs = QTabWidget()
        self._root.addWidget(self._tabs, 1)

        self._canvas_sim = MplCanvas(width=6.5, height=5.5)
        self._table_sim = DataFrameTable()
        sim_tab = QSplitter(Qt.Horizontal)
        sim_tab.addWidget(self._canvas_sim)
        sim_tab.addWidget(self._table_sim)
        sim_tab.setSizes([500, 400])
        self._tabs.addTab(sim_tab, "Матрица сходства")

        self._table_rich = DataFrameTable()
        self._table_dom = DataFrameTable()
        rank_tab = QSplitter(Qt.Horizontal)
        rich_box = self._wrap("По числу характеристик", self._table_rich)
        dom_box = self._wrap("По доминированию (включение)", self._table_dom)
        rank_tab.addWidget(rich_box)
        rank_tab.addWidget(dom_box)
        self._tabs.addTab(rank_tab, "Ранжирование объектов")

        self._table_missing = DataFrameTable()
        self._tabs.addTab(self._wrap("Кандидаты на добавление", self._table_missing), "Недостающие характеристики")

        self._placeholder = Placeholder(
            "Данных нет",
            "Загрузите матрицу объектов в разделе 'Матрица объектов'.",
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
            return
        self._placeholder.hide()
        self._tabs.show()
        self._controls.setEnabled(True)
        self._refresh()

    def _refresh(self) -> None:
        matrix = self.state.matrix
        if matrix is None:
            return
        metric_name = self._cmb_metric.currentText()
        sim = _SIMILARITIES[metric_name](matrix)
        plot_similarity_matrix(
            self._canvas_sim.figure, sim, matrix.objects,
            title=f"Сходство ({metric_name})",
        )
        self._canvas_sim.draw_idle()
        df_sim = pd.DataFrame(sim, index=matrix.objects, columns=matrix.objects)
        self._table_sim.set_dataframe(df_sim.round(4))

        self._table_rich.set_dataframe(rank_objects_by_richness(matrix))
        self._table_dom.set_dataframe(rank_objects_by_dominance(matrix).round(4))

        missing = missing_characteristics(matrix, min_coverage=self.state.config.missing_coverage_threshold)
        self._table_missing.set_dataframe(missing.round(3))
