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
from app.ui.widgets import (
    DataFrameTable,
    HintBadge,
    Placeholder,
    ResultSummary,
    SectionTitle,
)

from .base import BasePage

_SIMILARITIES = {
    "Жаккар": jaccard_matrix,
    "Сёренсен-Дайс": sorensen_dice_matrix,
    "Косинусная": cosine_similarity_binary,
    "Включение (асимметрично)": inclusion_matrix,
}

_METRIC_HINTS = {
    "Жаккар": "J(A,B) = |A∩B| / |A∪B|. Симметрично, не учитывает совпадение нулей.",
    "Сёренсен-Дайс": "Dice = 2·|A∩B| / (|A|+|B|). Похоже на Жаккара, выше для пересекающихся наборов.",
    "Косинусная": "Угловое сходство бинарных векторов; учитывает только единицы.",
    "Включение (асимметрично)": "P(A⊂B) = |A∩B| / |A|. Показывает, насколько A вложен в B.",
}


class AnalysisPage(BasePage):
    title = "Анализ сходства и ранжирование"
    subtitle = "Попарные сходства, ранжирование объектов и недостающие характеристики."
    info_title = "Зачем этот раздел"
    info_body = (
        "Помогает <b>понять структуру набора до оптимизации</b>: где «двойники», "
        "кто лидер по богатству, какие признаки системно отсутствуют. "
        "Выберите меру сходства справа и нажмите «Пересчитать»."
    )

    def build(self) -> None:
        self._build_parameters()

        self._summary = ResultSummary("Выберите меру сходства и нажмите «Пересчитать».")
        self._root.addWidget(self._summary)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._root.addWidget(self._tabs, 1)

        self._canvas_sim = MplCanvas(width=6.5, height=5.5)
        self._table_sim = DataFrameTable()
        sim_tab = QSplitter(Qt.Horizontal)
        sim_tab.addWidget(self._canvas_sim)
        sim_tab.addWidget(self._table_sim)
        sim_tab.setSizes([600, 360])
        sim_tab.setChildrenCollapsible(False)
        self._tabs.addTab(sim_tab, "Матрица сходства")

        self._table_rich = DataFrameTable()
        self._table_dom = DataFrameTable()
        rank_tab = QSplitter(Qt.Horizontal)
        rich_box = self._wrap(
            "По числу характеристик",
            self._table_rich,
            "Сколько единиц у объекта; чем больше — тем «богаче» по составу.",
        )
        dom_box = self._wrap(
            "По доминированию (включение)",
            self._table_dom,
            "Доля объектов, чьи признаки целиком содержатся в данном объекте.",
        )
        rank_tab.addWidget(rich_box)
        rank_tab.addWidget(dom_box)
        rank_tab.setChildrenCollapsible(False)
        self._tabs.addTab(rank_tab, "Ранжирование объектов")

        self._table_missing = DataFrameTable()
        self._tabs.addTab(
            self._wrap(
                "Кандидаты на добавление",
                self._table_missing,
                "Характеристики, отсутствующие у большой доли объектов — потенциальные пропуски.",
            ),
            "Недостающие характеристики",
        )

        self._placeholder = Placeholder(
            "Данных нет",
            "Загрузите матрицу объектов в разделе «Матрица объектов».",
        )
        self._root.addWidget(self._placeholder)
        self._tabs.hide()

        self.state.matrix_changed.connect(self._on_matrix)

    def _build_parameters(self) -> None:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 6, 12, 12)
        lay.setSpacing(10)

        lay.addWidget(SectionTitle("Параметры"))

        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(QLabel("Мера сходства:"))
        self._metric_hint = HintBadge(_METRIC_HINTS["Жаккар"])
        row.addWidget(self._metric_hint)
        row.addStretch(1)
        lay.addLayout(row)

        self._cmb_metric = QComboBox()
        for name in _SIMILARITIES:
            self._cmb_metric.addItem(name)
        self._cmb_metric.currentIndexChanged.connect(self._on_metric_changed)
        lay.addWidget(self._cmb_metric)

        lay.addSpacing(8)
        self._btn_recalc = QPushButton("Пересчитать")
        self._btn_recalc.setObjectName("Primary")
        self._btn_recalc.clicked.connect(self._refresh)
        lay.addWidget(self._btn_recalc)

        lay.addStretch(1)
        self._params = panel

    @staticmethod
    def _wrap(title: str, widget: QWidget, hint: str = "") -> QWidget:
        box = QGroupBox(title)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 16, 10, 10)
        if hint:
            note = QLabel(hint)
            note.setWordWrap(True)
            note.setStyleSheet("color: #8a93a6; padding: 0 0 6px 0;")
            lay.addWidget(note)
        lay.addWidget(widget)
        return box

    def _on_metric_changed(self) -> None:
        name = self._cmb_metric.currentText()
        self._metric_hint.setToolTip(_METRIC_HINTS.get(name, ""))
        self._refresh()

    def _on_matrix(self, matrix: BinaryMatrix | None) -> None:
        if matrix is None:
            self._tabs.hide()
            self._placeholder.show()
            self._params.setEnabled(False)
            return
        self._placeholder.hide()
        self._tabs.show()
        self._params.setEnabled(True)
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

        try:
            import numpy as np
            iu = np.triu_indices_from(sim, k=1)
            if iu[0].size:
                avg_sim = float(sim[iu].mean())
                self._summary.setText(
                    f"Мера: <b>{metric_name}</b>. Среднее попарное сходство = <b>{avg_sim:.3f}</b>. "
                    f"Кандидатов на добавление: <b>{len(missing)}</b>. "
                    "Высокое сходство — повод запустить оптимизацию."
                )
            else:
                self._summary.setText("Объектов слишком мало для попарного сравнения.")
        except Exception:
            self._summary.setText("Расчёт выполнен.")
