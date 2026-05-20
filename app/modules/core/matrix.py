from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


@dataclass
class BinaryMatrix:
    """Бинарная матрица объектов x характеристик.

    Форма (n_objects, n_features). data[i, j] = 1, если объект i обладает
    характеристикой j. Это центральная структура данных метода Хубаева.
    """

    data: np.ndarray
    objects: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.data = np.asarray(self.data, dtype=np.int8)
        if self.data.ndim != 2:
            raise ValueError("BinaryMatrix.data должна быть двумерной")
        n, m = self.data.shape
        if not self.objects:
            self.objects = [f"O{i + 1}" for i in range(n)]
        if not self.features:
            self.features = [f"F{j + 1}" for j in range(m)]
        if len(self.objects) != n or len(self.features) != m:
            raise ValueError(
                f"несоответствие меток: data={self.data.shape}, "
                f"objects={len(self.objects)}, features={len(self.features)}"
            )
        unique = set(np.unique(self.data).tolist())
        if not unique.issubset({0, 1}):
            raise ValueError(f"допустимы только значения 0/1, получено: {unique}")

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "BinaryMatrix":
        df = df.copy().fillna(0)
        objects = [str(x) for x in df.index.tolist()]
        features = [str(c) for c in df.columns.tolist()]
        arr = (df.to_numpy() != 0).astype(np.int8)
        return cls(arr, objects=objects, features=features)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.data, index=self.objects, columns=self.features)

    @property
    def n_objects(self) -> int:
        return int(self.data.shape[0])

    @property
    def n_features(self) -> int:
        return int(self.data.shape[1])

    @property
    def shape(self) -> tuple[int, int]:
        return self.data.shape  # type: ignore[return-value]

    def object_richness(self) -> np.ndarray:
        """Мощность множества характеристик объекта |A_i|."""
        return self.data.sum(axis=1).astype(int)

    def feature_frequency(self) -> np.ndarray:
        """Количество объектов, обладающих характеристикой."""
        return self.data.sum(axis=0).astype(int)

    def feature_share(self) -> np.ndarray:
        return self.feature_frequency() / max(self.n_objects, 1)

    def subset_features(self, indices: Sequence[int]) -> "BinaryMatrix":
        idx = list(indices)
        return BinaryMatrix(
            self.data[:, idx],
            objects=list(self.objects),
            features=[self.features[i] for i in idx],
        )

    def drop_features(self, indices: Iterable[int]) -> "BinaryMatrix":
        idx = sorted({int(i) for i in indices})
        keep = [j for j in range(self.n_features) if j not in idx]
        return self.subset_features(keep)

    def with_added_feature(self, name: str, column: np.ndarray) -> "BinaryMatrix":
        col = (np.asarray(column) != 0).astype(np.int8).reshape(-1, 1)
        if col.shape[0] != self.n_objects:
            raise ValueError("длина столбца не совпадает с числом объектов")
        return BinaryMatrix(
            np.hstack([self.data, col]),
            objects=list(self.objects),
            features=list(self.features) + [name],
        )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"BinaryMatrix(shape={self.shape}, "
            f"objects={self.objects[:3]}..., features={self.features[:3]}...)"
        )
