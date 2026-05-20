from __future__ import annotations

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.modules.core.clustering import cluster_experts
from app.modules.core.expert import (
    consensus_matrix,
    kendall_w,
    median_ranking,
)
from app.modules.data.samples import sample_file
from app.modules.visualization.canvas import MplCanvas
from app.modules.visualization.clusters import plot_cluster_scatter, plot_dendrogram
from app.modules.visualization.heatmaps import plot_similarity_matrix
from app.ui.state import ExpertSession
from app.ui.widgets import (
    DataFrameTable,
    HintBadge,
    InfoNote,
    Placeholder,
    ResultSummary,
)

from .base import BasePage


def _w_interpretation(w: float) -> str:
    if w >= 0.7:
        return "сильная согласованность"
    if w >= 0.5:
        return "умеренная согласованность"
    if w >= 0.3:
        return "слабая согласованность"
    return "согласованность практически отсутствует"


class ExpertPage(BasePage):
    title = "Экспертный анализ"
    subtitle = (
        "Агрегация ранжирований экспертов: матрица консенсуса, медиана Кемени, "
        "коэффициент конкордации Кендалла, кластеризация экспертов."
    )

    def build(self) -> None:
        intro = InfoNote(
            "Каждая строка файла — это один <b>эксперт</b>, столбцы — <b>объекты</b>, "
            "а значения — присвоенные ранги (1 — самый приоритетный). "
            "Раздел показывает, насколько эксперты согласны между собой и какое усреднённое ранжирование "
            "лучше всего описывает их совокупное мнение."
        )
        self._root.addWidget(intro)

        controls = QGroupBox("Данные экспертов")
        layout = QHBoxLayout(controls)
        layout.setSpacing(10)

        self._btn_load = QPushButton("Загрузить ранжирования…")
        self._btn_load.setObjectName("Primary")
        self._btn_load.clicked.connect(self._on_load)

        self._btn_open_sample = QPushButton("Открыть пример")
        self._btn_open_sample.setToolTip("samples/experts_rankings.csv")
        self._btn_open_sample.clicked.connect(self._on_open_sample)

        self._btn_sample = QPushButton("Случайный пример")
        self._btn_sample.clicked.connect(self._on_sample)

        self._sp_clusters = QSpinBox()
        self._sp_clusters.setRange(1, 12)
        self._sp_clusters.setValue(2)
        self._sp_clusters.valueChanged.connect(self._refresh)

        self._btn_calc = QPushButton("Пересчитать")
        self._btn_calc.clicked.connect(self._refresh)

        clusters_hint = HintBadge(
            "На сколько групп разбить экспертов по близости их ранжирований. "
            "Помогает увидеть, расходятся ли эксперты на несколько лагерей."
        )

        layout.addWidget(self._btn_load)
        layout.addWidget(self._btn_open_sample)
        layout.addWidget(self._btn_sample)
        layout.addStretch(1)
        layout.addWidget(QLabel("Кластеров экспертов:"))
        layout.addWidget(clusters_hint)
        layout.addWidget(self._sp_clusters)
        layout.addWidget(self._btn_calc)

        self._root.addWidget(controls)

        self._summary = ResultSummary(
            "Загрузите файл с ранжированиями экспертов (строки — эксперты, столбцы — объекты, "
            "значения — ранги)."
        )
        self._root.addWidget(self._summary)

        self._tabs = QTabWidget()
        self._root.addWidget(self._tabs, 1)

        self._table_data = DataFrameTable()
        self._tabs.addTab(self._wrap("Ранжирования экспертов", self._table_data), "Данные")

        self._canvas_cons = MplCanvas(width=6.0, height=5.0)
        self._table_cons = DataFrameTable()
        cons_split = QSplitter(Qt.Horizontal)
        cons_split.addWidget(self._canvas_cons)
        cons_split.addWidget(self._table_cons)
        cons_split.setSizes([520, 380])
        self._tabs.addTab(cons_split, "Матрица консенсуса")

        self._table_median = DataFrameTable()
        self._lbl_w = QLabel("—")
        self._lbl_w.setStyleSheet("color: #b4bbcc; padding: 8px; font-size: 10pt;")
        self._lbl_w.setWordWrap(True)
        med_w = QWidget()
        med_l = QVBoxLayout(med_w)
        med_l.addWidget(self._lbl_w)
        med_l.addWidget(self._table_median)
        self._tabs.addTab(med_w, "Медиана Кемени")

        self._canvas_dendro = MplCanvas(width=6.0, height=5.0)
        self._canvas_scatter = MplCanvas(width=6.0, height=5.0)
        clus_w = QWidget()
        clus_l = QHBoxLayout(clus_w)
        clus_l.setContentsMargins(0, 0, 0, 0)
        clus_l.addWidget(self._canvas_dendro)
        clus_l.addWidget(self._canvas_scatter)
        self._tabs.addTab(clus_w, "Кластеризация экспертов")

        self._placeholder = Placeholder(
            "Экспертные данные не загружены",
            "Загрузите CSV / XLSX с ранжированиями или используйте демонстрационный пример.",
        )
        self._root.addWidget(self._placeholder)
        self._tabs.hide()

        self.state.experts_changed.connect(self._on_experts)

    @staticmethod
    def _wrap(title: str, widget: QWidget) -> QWidget:
        box = QGroupBox(title)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 18, 10, 10)
        lay.addWidget(widget)
        return box

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузка ранжирований", "",
            "Таблицы (*.csv *.tsv *.xlsx);;CSV (*.csv *.tsv);;Excel (*.xlsx)",
        )
        if not path:
            return
        try:
            if path.lower().endswith((".xlsx", ".xls", ".xlsm")):
                df = pd.read_excel(path, index_col=0)
            else:
                df = pd.read_csv(path, index_col=0, engine="python")
            df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        self._set_session(df)

    def _on_open_sample(self) -> None:
        path = sample_file("experts_rankings.csv")
        if path is None:
            QMessageBox.warning(
                self,
                "Пример не найден",
                "Файл samples/experts_rankings.csv не найден.",
            )
            return
        try:
            df = pd.read_csv(path, index_col=0, engine="python")
            df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки примера", str(e))
            return
        self._set_session(df)
        self.state.status_message.emit(f"Загружен пример: {path.name}")

    def _on_sample(self) -> None:
        rng = np.random.default_rng(11)
        n_obj = 6
        n_exp = 5
        true_order = rng.permutation(n_obj) + 1
        ranks = []
        for _ in range(n_exp):
            noise = rng.normal(0.0, 1.0, size=n_obj)
            order = np.argsort(true_order + noise)
            r = np.empty(n_obj, dtype=int)
            r[order] = np.arange(1, n_obj + 1)
            ranks.append(r)
        df = pd.DataFrame(
            ranks,
            index=[f"Эксперт {i+1}" for i in range(n_exp)],
            columns=[f"Объект {j+1}" for j in range(n_obj)],
        )
        self._set_session(df)

    def _set_session(self, df: pd.DataFrame) -> None:
        session = ExpertSession(rankings=df)
        self.state.set_experts(session)

    def _on_experts(self, session: ExpertSession) -> None:
        if session.rankings is None or session.rankings.empty:
            self._tabs.hide()
            self._placeholder.show()
            return
        self._placeholder.hide()
        self._tabs.show()
        self._refresh()

    def _refresh(self) -> None:
        session = self.state.experts
        if session.rankings is None or session.rankings.empty:
            return
        df = session.rankings
        self._table_data.set_dataframe(df)

        cons = consensus_matrix(df)
        plot_similarity_matrix(
            self._canvas_cons.figure, cons, list(df.columns),
            title="Матрица консенсуса",
        )
        self._canvas_cons.draw_idle()
        self._table_cons.set_dataframe(
            pd.DataFrame(cons, index=df.columns, columns=df.columns).round(3)
        )

        med = median_ranking(df)
        med_df = med.to_frame().reset_index().rename(columns={"index": "object"})
        med_df = med_df.sort_values("median_rank")
        self._table_median.set_dataframe(med_df)
        w = kendall_w(df)
        self._lbl_w.setText(
            f"<b>Коэффициент конкордации Кендалла W = {w:.3f}</b> &nbsp; "
            f"({_w_interpretation(w)}; 0 — полный разнобой, 1 — полное согласие)."
            "<br>В таблице ниже — усреднённое ранжирование объектов (медиана Кемени), "
            "минимизирующее суммарное расстояние до всех экспертов."
        )
        self._lbl_w.setTextFormat(Qt.RichText)

        n_clusters = min(self._sp_clusters.value(), df.shape[0])
        clusters = cluster_experts(df, n_clusters=n_clusters)
        plot_dendrogram(self._canvas_dendro.figure, clusters, title="Дендрограмма экспертов")
        self._canvas_dendro.draw_idle()
        plot_cluster_scatter(self._canvas_scatter.figure, clusters, title="Кластеры экспертов")
        self._canvas_scatter.draw_idle()

        leader = med_df.iloc[0]["object"] if not med_df.empty else "—"
        self._summary.setText(
            f"Экспертов: <b>{df.shape[0]}</b>, объектов: <b>{df.shape[1]}</b>. "
            f"Согласованность W = <b>{w:.3f}</b> ({_w_interpretation(w)}). "
            f"Текущий лидер по медиане Кемени: <b>{leader}</b>. "
        )
