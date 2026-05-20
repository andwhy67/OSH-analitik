from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
)

from app.modules.core.matrix import BinaryMatrix
from app.modules.data.io import DataLoader, DataSaveOptions, LoadOptions, save_matrix
from app.modules.data.samples import sample_file
from app.ui.widgets import DataFrameTable

from .base import BasePage


class MatrixPage(BasePage):
    title = "Матрица объектов"
    subtitle = (
        "Загрузка и редактирование бинарной матрицы объектов и характеристик. "
        "Поддерживаются CSV и XLSX; ориентация — объекты в строках либо в столбцах."
    )

    def build(self) -> None:
        controls = QGroupBox("Источник данных")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setSpacing(12)

        self._orientation = QComboBox()
        self._orientation.addItem("Объекты в строках", "objects_in_rows")
        self._orientation.addItem("Характеристики в строках (объекты в столбцах)", "objects_in_columns")

        self._btn_load = QPushButton("Загрузить файл…")
        self._btn_load.setObjectName("Primary")
        self._btn_load.clicked.connect(self._on_load)

        self._btn_open_sample = QPushButton("Открыть пример (samples/laptops.csv)")
        self._btn_open_sample.clicked.connect(self._on_open_sample)

        self._btn_sample = QPushButton("Сгенерировать случайный набор")
        self._btn_sample.clicked.connect(self._on_sample)

        self._btn_save = QPushButton("Сохранить…")
        self._btn_save.clicked.connect(self._on_save)
        self._btn_save.setEnabled(False)

        controls_layout.addWidget(QLabel("Ориентация:"))
        controls_layout.addWidget(self._orientation)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self._btn_open_sample)
        controls_layout.addWidget(self._btn_sample)
        controls_layout.addWidget(self._btn_load)
        controls_layout.addWidget(self._btn_save)

        self._root.addWidget(controls)

        self._info_label = QLabel("Данные не загружены.")
        self._info_label.setStyleSheet("color: #8a93a6;")
        self._root.addWidget(self._info_label)

        self._table = DataFrameTable()
        self._root.addWidget(self._table, 1)

        self.state.matrix_changed.connect(self._on_matrix_changed)

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
            QMessageBox.warning(
                self,
                "Пример не найден",
                "Файл samples/laptops.csv не найден ни рядом с приложением, "
                "ни в каталоге проекта.",
            )
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
            self._info_label.setText("Данные не загружены.")
            self._table.set_dataframe(pd.DataFrame())
            self._btn_save.setEnabled(False)
            return
        density = matrix.data.sum() / max(matrix.n_objects * matrix.n_features, 1)
        self._info_label.setText(
            f"Объектов: {matrix.n_objects}  ·  характеристик: {matrix.n_features}  ·  плотность: {density:.1%}"
        )
        self._table.set_dataframe(matrix.to_dataframe())
        self._btn_save.setEnabled(True)
