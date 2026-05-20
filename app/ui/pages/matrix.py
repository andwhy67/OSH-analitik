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
from app.ui.widgets import DataFrameTable, HintBadge, InfoNote, ResultSummary

from .base import BasePage


class MatrixPage(BasePage):
    title = "Матрица объектов"
    subtitle = (
        "Бинарная матрица «объект × характеристика»: 1 — признак у объекта присутствует, "
        "0 — отсутствует. Это вход для всех остальных расчётов."
    )

    def build(self) -> None:
        intro = InfoNote(
            "Поддерживаются <b>CSV и XLSX</b>. В файле первая колонка — имена объектов "
            "(либо имена характеристик, если выбрана соответствующая ориентация), "
            "далее — столбцы со значениями <b>0/1</b>. Для пробы есть готовый пример и кнопка "
            "случайной генерации."
        )
        self._root.addWidget(intro)

        controls = QGroupBox("Источник данных")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setSpacing(10)

        self._orientation = QComboBox()
        self._orientation.addItem("Объекты в строках", "objects_in_rows")
        self._orientation.addItem("Характеристики в строках (объекты в столбцах)", "objects_in_columns")
        self._orientation.setMinimumWidth(280)
        orient_hint = HintBadge(
            "Если в вашей таблице каждая строка — это объект, а столбцы — признаки, "
            "оставьте первый вариант. Если наоборот (строка = признак, столбец = объект), "
            "выберите второй — данные будут транспонированы при загрузке."
        )

        self._btn_load = QPushButton("Загрузить файл…")
        self._btn_load.setObjectName("Primary")
        self._btn_load.clicked.connect(self._on_load)

        self._btn_open_sample = QPushButton("Открыть пример")
        self._btn_open_sample.setToolTip("samples/laptops.csv — небольшая демонстрационная матрица")
        self._btn_open_sample.clicked.connect(self._on_open_sample)

        self._btn_sample = QPushButton("Сгенерировать случайный набор")
        self._btn_sample.setToolTip("Создаёт детерминированный пример из 8 объектов и 11 признаков")
        self._btn_sample.clicked.connect(self._on_sample)

        self._btn_save = QPushButton("Сохранить…")
        self._btn_save.clicked.connect(self._on_save)
        self._btn_save.setEnabled(False)

        controls_layout.addWidget(QLabel("Ориентация:"))
        controls_layout.addWidget(orient_hint)
        controls_layout.addWidget(self._orientation)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self._btn_open_sample)
        controls_layout.addWidget(self._btn_sample)
        controls_layout.addWidget(self._btn_load)
        controls_layout.addWidget(self._btn_save)

        self._root.addWidget(controls)

        self._summary = ResultSummary(
            "Данные не загружены. Откройте файл, демонстрационный пример или сгенерируйте набор."
        )
        self._root.addWidget(self._summary)

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
            self._summary.setText(
                "Данные не загружены. Откройте файл, демонстрационный пример или сгенерируйте набор."
            )
            self._table.set_dataframe(pd.DataFrame())
            self._btn_save.setEnabled(False)
            return
        density = matrix.data.sum() / max(matrix.n_objects * matrix.n_features, 1)
        self._summary.setText(
            f"Загружено: <b>{matrix.n_objects}</b> объектов · "
            f"<b>{matrix.n_features}</b> характеристик · плотность <b>{density:.1%}</b>. "
            "Дальше — переход в «Анализ» или «Оптимизацию»."
        )
        self._table.set_dataframe(matrix.to_dataframe())
        self._btn_save.setEnabled(True)
