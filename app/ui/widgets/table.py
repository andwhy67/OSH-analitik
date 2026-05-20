from __future__ import annotations

import numpy as np
import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QHeaderView, QTableView


class _DataFrameModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame | None = None):
        super().__init__()
        self._df = df if df is not None else pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df.copy()
        self.endResetModel()

    def dataframe(self) -> pd.DataFrame:
        return self._df

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        val = self._df.iat[index.row(), index.column()]
        if role == Qt.DisplayRole:
            if pd.isna(val):
                return ""
            if isinstance(val, (float, np.floating)):
                return f"{val:.4f}".rstrip("0").rstrip(".") or "0"
            return str(val)
        if role == Qt.TextAlignmentRole:
            if isinstance(val, (int, float, np.integer, np.floating)):
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if section < len(self._df.columns):
                return str(self._df.columns[section])
        else:
            if section < len(self._df.index):
                return str(self._df.index[section])
        return None


class DataFrameTable(QTableView):
    """QTableView, удобный для отображения pandas DataFrame."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = _DataFrameModel()
        self.setModel(self._model)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setFrameShape(QTableView.NoFrame)
        self.verticalHeader().setDefaultSectionSize(26)
        self.verticalHeader().setVisible(True)
        self.verticalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSortingEnabled(False)
        self.setCornerButtonEnabled(False)

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self._model.set_dataframe(df)
        self.resizeColumnsToContents()

    def dataframe(self) -> pd.DataFrame:
        return self._model.dataframe()
