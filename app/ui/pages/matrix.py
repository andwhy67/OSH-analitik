from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.modules.core.matrix import BinaryMatrix
from app.modules.data.io import DataLoader, DataSaveOptions, LoadOptions, save_matrix
from app.modules.data.samples import sample_file
from app.ui.widgets import DataFrameTable, HintBadge, ResultSummary, SectionTitle

from .base import BasePage


class MatrixPage(BasePage):
    title = "Матрица объектов"
    subtitle = "Бинарная матрица «объект × характеристика» — вход для всех расчётов."
    info_title = "Что такое бинарная матрица"
    info_body = (
        "Каждая <b>строка</b> — это объект (либо признак при обратной ориентации), "
        "каждая <b>колонка</b> — характеристика. Значения только <b>0</b> и <b>1</b>: "
        "признак присутствует или нет. Поддерживаются CSV и XLSX. Если в вашей таблице "
        "строки и столбцы перепутаны — переключите «Ориентацию» в панели справа."
    )

    def build(self) -> None:
        self._build_parameters()

        self._summary = ResultSummary(
            "Данные не загружены. Откройте файл, демонстрационный пример или сгенерируйте набор справа."
        )
        self._root.addWidget(self._summary)

        self._table = DataFrameTable()
        self._root.addWidget(self._table, 1)

        self.state.matrix_changed.connect(self._on_matrix_changed)

    def _build_parameters(self) -> None:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 6, 12, 12)
        lay.setSpacing(10)

        lay.addWidget(SectionTitle("Источник данных"))

        orient_row = QHBoxLayout()
        orient_row.setSpacing(6)
        orient_row.addWidget(QLabel("Ориентация:"))
        orient_row.addWidget(HintBadge(
            "Объекты в строках — стандартный вариант. "
            "Если в файле наоборот (строка = признак), выберите второй пункт — "
            "данные транспонируются при загрузке."
        ))
        lay.addLayout(orient_row)

        self._orientation = QComboBox()
        self._orientation.addItem("Объекты в строках", "objects_in_rows")
        self._orientation.addItem("Характеристики в строках", "objects_in_columns")
        lay.addWidget(self._orientation)

        lay.addSpacing(6)
        lay.addWidget(SectionTitle("Действия"))

        self._btn_load = QPushButton("Загрузить файл…")
        self._btn_load.setObjectName("Primary")
        self._btn_load.clicked.connect(self._on_load)
        lay.addWidget(self._btn_load)

        self._btn_open_sample = QPushButton("Открыть пример (laptops.csv)")
        self._btn_open_sample.clicked.connect(self._on_open_sample)
        lay.addWidget(self._btn_open_sample)

        self._btn_sample = QPushButton("Случайный демо-набор")
        self._btn_sample.clicked.connect(self._on_sample)
        lay.addWidget(self._btn_sample)

        lay.addSpacing(6)
        self._btn_save = QPushButton("Сохранить матрицу…")
        self._btn_save.clicked.connect(self._on_save)
        self._btn_save.setEnabled(False)
        lay.addWidget(self._btn_save)

        lay.addStretch(1)
        self._params = panel

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузка матрицы",
            "",
            "Таблицы (*.csv *.tsv *.xlsx *.xlsm);;CSV (*.csv *.tsv *.txt);;Excel (*.xlsx *.xlsm);;Все файлы (*)",
        )
        if not path:
            return
        orientation = self._orientation.currentData()
        try:
            loader = DataLoader(LoadOptions(orientation=orientation))
            matrix = loader.load(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", str(e))
            return
        self.state.set_matrix(matrix, source=path)
        self.state.status_message.emit(f"Загружено: {Path(path).name}")

    def _on_open_sample(self) -> None:
        path = sample_file("laptops.csv")
        if path is None:
            QMessageBox.warning(self, "Пример не найден", "Файл samples/laptops.csv не найден.")
            return
        try:
            matrix = DataLoader(LoadOptions(orientation="objects_in_rows")).load(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки примера", str(e))
            return
        self.state.set_matrix(matrix, source=str(path))
        self.state.status_message.emit(f"Загружен пример: {path.name}")

    def _on_sample(self) -> None:
        import numpy as np
        rng = np.random.default_rng(7)
        objects = [f"Объект {i+1}" for i in range(8)]
        features = [
            "ЦПУ ≥ 6 ядер", "ОЗУ ≥ 16 ГБ", "SSD NVMe", "Дискр. ГП",
            "Экран 4K", "Сенсорный экран", "Подсветка клавиатуры",
            "Сканер отпечатка", "Wi-Fi 6E", "Thunderbolt 4", "Вес < 1.6 кг",
        ]
        probs = np.linspace(0.85, 0.25, len(features))
        data = (rng.random((len(objects), len(features))) < probs).astype(np.int8)
        bm = BinaryMatrix(data, objects=objects, features=features)
        self.state.set_matrix(bm, source="<sample>")
        self.state.status_message.emit("Сгенерирован демонстрационный набор")

    def _on_save(self) -> None:
        bm = self.state.matrix
        if bm is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранение матрицы", "matrix.xlsx",
            "Excel (*.xlsx);;CSV (*.csv)",
        )
        if not path:
            return
        try:
            save_matrix(bm, path, DataSaveOptions())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))
            return
        self.state.status_message.emit(f"Сохранено: {Path(path).name}")

    def _on_matrix_changed(self, matrix: BinaryMatrix | None) -> None:
        if matrix is None:
            self._summary.setText(
                "Данные не загружены. Откройте файл, демонстрационный пример или сгенерируйте набор справа."
            )
            self._table.set_dataframe(pd.DataFrame())
            self._btn_save.setEnabled(False)
            return
        density = matrix.data.sum() / max(matrix.n_objects * matrix.n_features, 1)
        self._summary.setText(
            f"Загружено: <b>{matrix.n_objects}</b> объектов · "
            f"<b>{matrix.n_features}</b> характеристик · плотность <b>{density:.1%}</b>. "
            "Дальше — «Анализ» или «Оптимизация»."
        )
        self._table.set_dataframe(matrix.to_dataframe())
        self._btn_save.setEnabled(True)
