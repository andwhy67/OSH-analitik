from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.modules.core.clustering import cluster_objects
from app.modules.core.matrix import BinaryMatrix
from app.modules.core.similarity import jaccard_matrix
from app.modules.visualization.canvas import MplCanvas
from app.modules.visualization.clusters import plot_cluster_scatter, plot_dendrogram
from app.modules.visualization.graphs import plot_object_graph
from app.modules.visualization.heatmaps import plot_binary_matrix, plot_similarity_matrix
from app.ui.widgets import HintBadge, Placeholder, ResultSummary, SectionTitle

from .base import BasePage


class VisualizationPage(BasePage):
    title = "Визуализация"
    subtitle = "Тепловые карты, граф связей, дендрограмма и MDS-проекция объектов."
    info_title = "О разделе"
    info_body = (
        "Раздел <b>не выполняет новых расчётов</b>. Он показывает структуру набора под "
        "разными углами: где скопления, где изоляты, где видна неоднородность. "
        "Подкручивайте порог и число кластеров в правой панели."
    )

    def build(self) -> None:
        self._build_parameters()

        self._summary = ResultSummary("")
        self._summary.hide()
        self._root.addWidget(self._summary)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._root.addWidget(self._tabs, 1)

        self._canvas_heat = MplCanvas(width=6.0, height=5.0)
        self._canvas_sim = MplCanvas(width=6.0, height=5.0)
        heat_split = QSplitter(Qt.Horizontal)
        heat_split.addWidget(self._canvas_heat)
        heat_split.addWidget(self._canvas_sim)
        heat_split.setSizes([520, 520])
        self._tabs.addTab(heat_split, "Тепловые карты")

        self._canvas_graph = MplCanvas(width=7.0, height=6.0)
        self._tabs.addTab(self._canvas_graph, "Граф связей объектов")

        self._canvas_dendro = MplCanvas(width=6.0, height=5.0)
        self._canvas_scatter = MplCanvas(width=6.0, height=5.0)
        cl_split = QSplitter(Qt.Horizontal)
        cl_split.addWidget(self._canvas_dendro)
        cl_split.addWidget(self._canvas_scatter)
        cl_split.setSizes([520, 520])
        self._tabs.addTab(cl_split, "Кластеризация объектов")

        self._placeholder = Placeholder(
            "Нет данных",
            "Загрузите матрицу на странице «Матрица объектов».",
        )
        self._root.addWidget(self._placeholder)
        self._tabs.hide()

        self.state.matrix_changed.connect(self._on_matrix)

    def _build_parameters(self) -> None:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 6, 12, 12)
        lay.setSpacing(10)

        lay.addWidget(SectionTitle("Граф связей"))

        row1 = QHBoxLayout()
        row1.setSpacing(6)
        row1.addWidget(QLabel("Порог связи:"))
        row1.addWidget(HintBadge(
            "Только пары со сходством Жаккара ≥ порога соединяются ребром. "
            "Выше порог — реже связи."
        ))
        row1.addStretch(1)
        lay.addLayout(row1)

        self._sp_threshold = QDoubleSpinBox()
        self._sp_threshold.setRange(0.0, 1.0)
        self._sp_threshold.setSingleStep(0.05)
        self._sp_threshold.setDecimals(2)
        self._sp_threshold.setValue(0.4)
        self._sp_threshold.valueChanged.connect(self._refresh)
        lay.addWidget(self._sp_threshold)

        lay.addSpacing(6)
        lay.addWidget(SectionTitle("Кластеризация"))

        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addWidget(QLabel("Кластеров:"))
        row2.addWidget(HintBadge(
            "На сколько групп разбить объекты в дендрограмме и MDS-проекции."
        ))
        row2.addStretch(1)
        lay.addLayout(row2)

        self._sp_clusters = QSpinBox()
        self._sp_clusters.setRange(1, 20)
        self._sp_clusters.setValue(3)
        self._sp_clusters.valueChanged.connect(self._refresh)
        lay.addWidget(self._sp_clusters)

        lay.addSpacing(8)
        self._btn = QPushButton("Обновить")
        self._btn.setObjectName("Primary")
        self._btn.clicked.connect(self._refresh)
        lay.addWidget(self._btn)

        lay.addStretch(1)
        self._params = panel

    def _on_matrix(self, matrix: BinaryMatrix | None) -> None:
        if matrix is None:
            self._tabs.hide()
            self._placeholder.show()
            self._params.setEnabled(False)
            self._summary.hide()
            return
        self._placeholder.hide()
        self._tabs.show()
        self._params.setEnabled(True)
        self._summary.show()
        self._refresh()

    def _refresh(self) -> None:
        matrix = self.state.matrix
        if matrix is None:
            return
        plot_binary_matrix(self._canvas_heat.figure, matrix)
        self._canvas_heat.draw_idle()

        sim = jaccard_matrix(matrix)
        plot_similarity_matrix(
            self._canvas_sim.figure, sim, matrix.objects,
            title="Матрица сходства (Жаккар)",
        )
        self._canvas_sim.draw_idle()

        plot_object_graph(
            self._canvas_graph.figure, sim, matrix.objects,
            threshold=self._sp_threshold.value(),
        )
        self._canvas_graph.draw_idle()

        n_clusters = min(self._sp_clusters.value(), matrix.n_objects)
        clusters = cluster_objects(matrix, n_clusters=n_clusters)
        plot_dendrogram(self._canvas_dendro.figure, clusters)
        self._canvas_dendro.draw_idle()
        plot_cluster_scatter(self._canvas_scatter.figure, clusters)
        self._canvas_scatter.draw_idle()

        try:
            import numpy as np
            iu = np.triu_indices_from(sim, k=1)
            edges = int((sim[iu] >= self._sp_threshold.value()).sum()) if iu[0].size else 0
            total_pairs = iu[0].size
            self._summary.setText(
                f"Объектов: <b>{matrix.n_objects}</b>, кластеров: <b>{n_clusters}</b>. "
                f"При пороге {self._sp_threshold.value():.2f} в графе остаётся "
                f"<b>{edges}</b> из {total_pairs} возможных связей."
            )
        except Exception:
            pass
