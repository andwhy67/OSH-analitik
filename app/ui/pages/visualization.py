from __future__ import annotations

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QWidget,
)

from app.modules.core.clustering import cluster_objects
from app.modules.core.matrix import BinaryMatrix
from app.modules.core.similarity import jaccard_matrix
from app.modules.visualization.canvas import MplCanvas
from app.modules.visualization.clusters import plot_cluster_scatter, plot_dendrogram
from app.modules.visualization.graphs import plot_object_graph
from app.modules.visualization.heatmaps import plot_binary_matrix, plot_similarity_matrix
from app.ui.widgets import Placeholder

from .base import BasePage


class VisualizationPage(BasePage):
    title = "Визуализация"
    subtitle = (
        "Сводное представление: тепловые карты, граф связей, "
        "иерархическая кластеризация и MDS-проекция объектов."
    )

    def build(self) -> None:
        controls = QGroupBox("Параметры визуализации")
        cl = QHBoxLayout(controls)

        self._sp_threshold = QDoubleSpinBox()
        self._sp_threshold.setRange(0.0, 1.0)
        self._sp_threshold.setSingleStep(0.05)
        self._sp_threshold.setDecimals(2)
        self._sp_threshold.setValue(0.4)
        self._sp_threshold.valueChanged.connect(self._refresh)

        self._sp_clusters = QSpinBox()
        self._sp_clusters.setRange(1, 20)
        self._sp_clusters.setValue(3)
        self._sp_clusters.valueChanged.connect(self._refresh)

        cl.addWidget(QLabel("Порог связи в графе:"))
        cl.addWidget(self._sp_threshold)
        cl.addSpacing(20)
        cl.addWidget(QLabel("Кластеров объектов:"))
        cl.addWidget(self._sp_clusters)
        cl.addStretch(1)

        self._btn = QPushButton("Обновить")
        self._btn.setObjectName("Primary")
        self._btn.clicked.connect(self._refresh)
        cl.addWidget(self._btn)

        self._root.addWidget(controls)
        self._controls = controls

        self._tabs = QTabWidget()
        self._root.addWidget(self._tabs, 1)

        self._canvas_heat = MplCanvas(width=6.0, height=5.0)
        self._canvas_sim = MplCanvas(width=6.0, height=5.0)
        heat_w = QWidget()
        heat_l = QHBoxLayout(heat_w)
        heat_l.setContentsMargins(0, 0, 0, 0)
        heat_l.addWidget(self._canvas_heat)
        heat_l.addWidget(self._canvas_sim)
        self._tabs.addTab(heat_w, "Тепловые карты")

        self._canvas_graph = MplCanvas(width=7.0, height=6.0)
        self._tabs.addTab(self._canvas_graph, "Граф связей объектов")

        self._canvas_dendro = MplCanvas(width=6.0, height=5.0)
        self._canvas_scatter = MplCanvas(width=6.0, height=5.0)
        cl_w = QWidget()
        cl_l = QHBoxLayout(cl_w)
        cl_l.setContentsMargins(0, 0, 0, 0)
        cl_l.addWidget(self._canvas_dendro)
        cl_l.addWidget(self._canvas_scatter)
        self._tabs.addTab(cl_w, "Кластеризация объектов")

        self._placeholder = Placeholder(
            "Нет данных",
            "Загрузите матрицу на странице 'Матрица объектов'.",
        )
        self._root.addWidget(self._placeholder)
        self._tabs.hide()
        controls.setEnabled(False)

        self.state.matrix_changed.connect(self._on_matrix)

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
