from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from app.modules.core.matrix import BinaryMatrix


Orientation = Literal["objects_in_rows", "objects_in_columns"]


@dataclass
class LoadOptions:
    orientation: Orientation = "objects_in_rows"
    sheet: str | int | None = 0
    encoding: str = "utf-8"
    separator: str | None = None  # None — автоопределение для csv
    binarize_threshold: float | None = None
    true_values: list[str] = field(
        default_factory=lambda: ["1", "true", "True", "TRUE", "y", "Y", "+", "да", "Да", "ДА", "yes", "Yes", "YES"]
    )
    false_values: list[str] = field(
        default_factory=lambda: ["0", "false", "False", "FALSE", "n", "N", "-", "нет", "Нет", "НЕТ", "no", "No", "NO", ""]
    )


@dataclass
class DataSaveOptions:
    sheet: str = "matrix"
    encoding: str = "utf-8"


def _read_raw(path: Path, opts: LoadOptions) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls", ".xlsm"):
        return pd.read_excel(path, sheet_name=opts.sheet, index_col=0)
    if suffix in (".csv", ".tsv", ".txt"):
        sep = opts.separator
        if sep is None:
            sep = "\t" if suffix == ".tsv" else None
        return pd.read_csv(
            path,
            sep=sep,
            engine="python",
            encoding=opts.encoding,
            index_col=0,
        )
    raise ValueError(f"неподдерживаемый формат файла: {suffix}")


def _coerce_binary(df: pd.DataFrame, opts: LoadOptions) -> pd.DataFrame:
    df = df.copy()

    def to_bin(v):
        if pd.isna(v):
            return 0
        if isinstance(v, (int, float, np.integer, np.floating)):
            if opts.binarize_threshold is not None:
                return 1 if float(v) >= opts.binarize_threshold else 0
            return 1 if float(v) != 0.0 else 0
        s = str(v).strip()
        if s in opts.true_values:
            return 1
        if s in opts.false_values:
            return 0
        try:
            return 1 if float(s.replace(",", ".")) != 0.0 else 0
        except ValueError:
            return 0

    return df.map(to_bin).astype(np.int8)


@dataclass
class DataLoader:
    options: LoadOptions = field(default_factory=LoadOptions)

    def load(self, path: str | Path) -> BinaryMatrix:
        p = Path(path)
        raw = _read_raw(p, self.options)
        if self.options.orientation == "objects_in_columns":
            raw = raw.T
        raw.index = raw.index.astype(str)
        raw.columns = raw.columns.astype(str)
        bin_df = _coerce_binary(raw, self.options)
        return BinaryMatrix.from_dataframe(bin_df)


def load_matrix(path: str | Path, options: LoadOptions | None = None) -> BinaryMatrix:
    return DataLoader(options or LoadOptions()).load(path)


def save_matrix(
    bm: BinaryMatrix,
    path: str | Path,
    options: DataSaveOptions | None = None,
) -> None:
    save_dataframe(bm.to_dataframe(), path, options)


def save_dataframe(
    df: pd.DataFrame,
    path: str | Path,
    options: DataSaveOptions | None = None,
) -> None:
    opts = options or DataSaveOptions()
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        with pd.ExcelWriter(p, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=opts.sheet)
        return
    if suffix in (".csv", ".tsv", ".txt"):
        sep = "\t" if suffix == ".tsv" else ","
        df.to_csv(p, sep=sep, encoding=opts.encoding)
        return
    raise ValueError(f"неподдерживаемый формат для сохранения: {suffix}")
