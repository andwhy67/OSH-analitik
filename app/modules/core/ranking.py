from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .matrix import BinaryMatrix
from .similarity import inclusion_matrix


def rank_objects_by_richness(bm: BinaryMatrix) -> pd.DataFrame:
    """Ранжирование объектов по числу характеристик (по убыванию)."""
    rich = bm.object_richness()
    df = pd.DataFrame(
        {
            "object": bm.objects,
            "characteristics": rich,
            "share": rich / max(bm.n_features, 1),
        }
    )
    df = df.sort_values("characteristics", ascending=False, kind="mergesort")
    df["rank"] = np.arange(1, len(df) + 1)
    return df.reset_index(drop=True)


def rank_objects_by_dominance(bm: BinaryMatrix) -> pd.DataFrame:
    """Ранжирование по доминированию: средний коэффициент включения других
    объектов в данный. Чем выше показатель, тем больше объектов "укладывается"
    в характеристики данного.
    """
    inc = inclusion_matrix(bm)
    n = inc.shape[0]
    if n <= 1:
        score = np.zeros(n)
    else:
        mask = ~np.eye(n, dtype=bool)
        score = np.where(mask, inc, 0.0).sum(axis=0) / (n - 1)
    df = pd.DataFrame(
        {
            "object": bm.objects,
            "dominance": score,
            "characteristics": bm.object_richness(),
        }
    )
    df = df.sort_values(
        ["dominance", "characteristics"], ascending=[False, False], kind="mergesort"
    )
    df["rank"] = np.arange(1, len(df) + 1)
    return df.reset_index(drop=True)


@dataclass
class MissingFeature:
    object: str
    feature: str
    coverage: float
    among_richer: float


def missing_characteristics(
    bm: BinaryMatrix,
    *,
    min_coverage: float = 0.5,
) -> pd.DataFrame:
    """Поиск "недостающих" характеристик: для каждого объекта — те, которых
    у него нет, но которые часто встречаются у остальных (по Хубаеву —
    кандидаты на добавление в состав).
    """
    rows: list[MissingFeature] = []
    rich = bm.object_richness()
    freq = bm.feature_frequency().astype(float)
    n_obj = bm.n_objects
    for i, obj in enumerate(bm.objects):
        missing_idx = np.where(bm.data[i] == 0)[0]
        for j in missing_idx:
            cov = freq[j] / max(n_obj, 1)
            if cov < min_coverage:
                continue
            richer_mask = rich > rich[i]
            denom = int(richer_mask.sum())
            richer_cov = (
                float(bm.data[richer_mask, j].sum()) / denom if denom > 0 else 0.0
            )
            rows.append(
                MissingFeature(obj, bm.features[j], float(cov), richer_cov)
            )
    df = pd.DataFrame([r.__dict__ for r in rows])
    if df.empty:
        return df
    return df.sort_values(
        ["object", "coverage"], ascending=[True, False], kind="mergesort"
    ).reset_index(drop=True)
