from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
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
from app.ui.widgets import (
    DataFrameTable,
    GlowPulse,
    HintBadge,
    Placeholder,
    ResultSummary,
    SectionTitle,
)

from .base import BasePage


def _param_row(label: str, field: QWidget, hint: str) -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)
    head = QHBoxLayout()
    head.setSpacing(6)
    lbl = QLabel(label)
    head.addWidget(lbl)
    head.addWidget(HintBadge(hint))
    head.addStretch(1)
    lay.addLayout(head)
    lay.addWidget(field)
    return w


class OptimizationPage(BasePage):
    title = "Оптимизация состава характеристик"
    subtitle = "Метод Хубаева: итеративное отсечение малоинформативных признаков."
    info_title = "Как работает метод"
    info_body = (
        "На каждой итерации оценивается <b>вклад признака</b> в попарные сходства. "
        "Слишком частые (общие почти для всех) и слишком редкие признаки сразу отсекаются по "
        "порогам частот; остальные удаляются по очереди, пока их вклад ниже порога информативности. "
        "Параллельно выявляются <b>кандидаты на добавление</b> — признаки, которых системно не хватает."
    )

    def build(self) -> None:
        self._build_parameters()

        self._summary = ResultSummary(
            "Параметры подобраны под средние наборы. Скорректируйте справа и запустите расчёт."
        )
        self._root.addWidget(self._summary)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._root.addWidget(self._tabs, 1)

        self._canvas_imp = MplCanvas(width=6.0, height=5.0)
        self._table_imp = DataFrameTable()
        imp_split = QSplitter(Qt.Horizontal)
        imp_split.addWidget(self._canvas_imp)
        imp_split.addWidget(self._table_imp)
        imp_split.setSizes([600, 360])
        imp_split.setChildrenCollapsible(False)
        self._tabs.addTab(imp_split, "Информативность")

        self._canvas_rank = MplCanvas(width=6.0, height=5.0)
        self._table_rank = DataFrameTable()
        rank_split = QSplitter(Qt.Horizontal)
        rank_split.addWidget(self._canvas_rank)
        rank_split.addWidget(self._table_rank)
        rank_split.setSizes([600, 360])
        rank_split.setChildrenCollapsible(False)
        self._tabs.addTab(rank_split, "Ранжирование объектов")

        self._canvas_before = MplCanvas(width=5.0, height=5.0)
        self._canvas_after = MplCanvas(width=5.0, height=5.0)
        sim_split = QSplitter(Qt.Horizontal)
        sim_split.addWidget(self._canvas_before)
        sim_split.addWidget(self._canvas_after)
        sim_split.setSizes([480, 480])
        self._tabs.addTab(sim_split, "Сходство: до / после")

        self._table_missing = DataFrameTable()
        self._tabs.addTab(self._wrap("Кандидаты на добавление", self._table_missing), "Недостающие")

        self._lbl_history = QLabel(
            "Каждая строка — один шаг алгоритма: какой признак удалён и как изменилась оценка."
        )
        self._lbl_history.setStyleSheet("color: #8a93a6; padding: 4px 2px;")
        self._lbl_history.setWordWrap(True)
        self._tab_history = DataFrameTable()
        hist_w = QWidget()
        hist_l = QVBoxLayout(hist_w)
        hist_l.setContentsMargins(0, 0, 0, 0)
        hist_l.addWidget(self._lbl_history)
        hist_l.addWidget(self._tab_history)
        self._tabs.addTab(hist_w, "Журнал шагов")

        self._placeholder = Placeholder(
            "Нет матрицы",
            "Загрузите бинарную матрицу на странице «Матрица объектов».",
        )
        self._root.addWidget(self._placeholder)
        self._tabs.hide()

        self.state.matrix_changed.connect(self._on_matrix)

    def _build_parameters(self) -> None:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 6, 12, 12)
        lay.setSpacing(10)

        lay.addWidget(SectionTitle("Алгоритм"))

        self._cmb_sim = QComboBox()
        self._cmb_sim.addItem("Жаккар", "jaccard")
        self._cmb_sim.addItem("Включение", "inclusion")
        lay.addWidget(_param_row(
            "Мера сходства",
            self._cmb_sim,
            "Базовая метрика для сходства объектов. «Жаккар» — симметричный дефолт. "
            "«Включение» — асимметричный вариант для вложенностей.",
        ))

        lay.addWidget(SectionTitle("Пороги частот"))

        self._sp_min_freq = QDoubleSpinBox()
        self._sp_min_freq.setRange(0.0, 1.0)
        self._sp_min_freq.setSingleStep(0.01)
        self._sp_min_freq.setDecimals(3)
        self._sp_min_freq.setValue(0.05)
        lay.addWidget(_param_row(
            "Мин. частота признака",
            self._sp_min_freq,
            "Признаки, встречающиеся реже этого порога, исключаются как «редкий шум». "
            "0.05 = присутствует менее чем у 5% объектов.",
        ))

        self._sp_max_freq = QDoubleSpinBox()
        self._sp_max_freq.setRange(0.0, 1.0)
        self._sp_max_freq.setSingleStep(0.01)
        self._sp_max_freq.setDecimals(3)
        self._sp_max_freq.setValue(0.98)
        lay.addWidget(_param_row(
            "Макс. частота признака",
            self._sp_max_freq,
            "Признаки, общие для почти всех объектов, исключаются — они не различают объекты.",
        ))

        lay.addWidget(SectionTitle("Информативность"))

        self._sp_info = QDoubleSpinBox()
        self._sp_info.setRange(0.0, 10.0)
        self._sp_info.setDecimals(5)
        self._sp_info.setSingleStep(0.0001)
        self._sp_info.setValue(0.0001)
        lay.addWidget(_param_row(
            "Порог информативности",
            self._sp_info,
            "Минимальный вклад признака, при котором его ещё имеет смысл оставить. "
            "Ниже порога — исключается. Уменьшайте, чтобы сохранить больше признаков.",
        ))

        self._sp_missing = QDoubleSpinBox()
        self._sp_missing.setRange(0.0, 1.0)
        self._sp_missing.setSingleStep(0.05)
        self._sp_missing.setDecimals(2)
        self._sp_missing.setValue(0.60)
        lay.addWidget(_param_row(
            "Порог «недостающих»",
            self._sp_missing,
            "Доля объектов, у которых должно отсутствовать значение, чтобы признак "
            "считался кандидатом на добавление. 0.60 = отсутствует у 60%+ объектов.",
        ))

        self._sp_iter = QSpinBox()
        self._sp_iter.setRange(1, 200)
        self._sp_iter.setValue(25)
        lay.addWidget(_param_row(
            "Макс. итераций",
            self._sp_iter,
            "Жёсткий предел числа шагов. Обычно сходимость наступает раньше.",
        ))

        lay.addSpacing(8)
        self._btn_run = QPushButton("Запустить оптимизацию")
        self._btn_run.setObjectName("Primary")
        self._btn_run.clicked.connect(self._run)
        lay.addWidget(self._btn_run)
        self._run_pulse = GlowPulse(self._btn_run)

        self._btn_apply = QPushButton("Применить состав к матрице")
        self._btn_apply.setToolTip(
            "Заменить рабочую матрицу на оптимизированный состав. "
            "Исходный набор можно вернуть, перезагрузив данные."
        )
        self._btn_apply.clicked.connect(self._apply)
        self._btn_apply.setEnabled(False)
        lay.addWidget(self._btn_apply)

        lay.addStretch(1)
        self._params = panel

    @staticmethod
    def _wrap(title: str, widget: QWidget) -> QWidget:
        box = QGroupBox(title)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(10, 16, 10, 10)
        lay.addWidget(widget)
        return box

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self.state.matrix is not None and self.state.optimization is None:
            self._run_pulse.start()

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        self._run_pulse.stop()

    def _on_matrix(self, matrix: BinaryMatrix | None) -> None:
        if matrix is None:
            self._tabs.hide()
            self._placeholder.show()
            self._params.setEnabled(False)
            self._btn_apply.setEnabled(False)
            self._run_pulse.stop()
            return
        self._placeholder.hide()
        self._tabs.show()
        self._params.setEnabled(True)
        if self.state.optimization is None:
            self._run_pulse.start()
        else:
            self._run_pulse.stop()

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
        self._run_pulse.stop()
        cfg = self._current_config()
        self.state.update_config(cfg)
        result = KhubaevOptimizer(cfg).run(matrix)
        self.state.set_optimization(result)
        self._render(result)
        self._btn_apply.setEnabled(True)
        self.state.status_message.emit(
            f"Оптимизация: оставлено {len(result.kept_features)} из {matrix.n_features}"
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

        kept = len(opt.kept_features)
        removed = len(opt.removed_features)
        total = kept + removed
        share = removed / total if total else 0.0
        miss = 0 if opt.missing.empty else len(opt.missing)
        self._summary.setText(
            f"Готово. Сохранено <b>{kept}</b> из <b>{total}</b> признаков "
            f"(исключено {removed}, {share:.0%}); шагов: <b>{len(opt.history)}</b>; "
            f"кандидатов на добавление: <b>{miss}</b>. "
            "Сравните «Сходство: до / после», чтобы оценить, не пострадала ли различительная способность."
        )
