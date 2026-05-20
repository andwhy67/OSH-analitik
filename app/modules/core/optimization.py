"""Универсальный метод Хубаева оптимизации состава характеристик объектов.

Кратко (по Хубаев Г. Н., 2019):
  1. Строится бинарная матрица M объектов x характеристик.
  2. Вычисляются попарные коэффициенты сходства (Жаккара) и включения.
  3. Оценивается информационный вклад каждой характеристики — как изменится
     структура матрицы сходства, если её исключить.
  4. Итеративно исключаются характеристики с низкой частотностью,
     убиквитарные (присутствующие почти у всех) и с нулевым вкладом в
     дифференциацию объектов.
  5. На оставшемся составе выдаётся ранжирование объектов по доминированию
     и список "недостающих" характеристик — кандидатов на добавление.

Метод универсален и не привязан к конкретной предметной области.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from .matrix import BinaryMatrix
from .ranking import missing_characteristics, rank_objects_by_dominance
from .similarity import inclusion_matrix, jaccard_matrix

SimilarityKind = Literal["jaccard", "inclusion"]


@dataclass
class OptimizationConfig:
    similarity: SimilarityKind = "jaccard"
    min_feature_frequency: float = 0.05
    max_feature_frequency: float = 0.98
    informativeness_threshold: float = 1e-4
    missing_coverage_threshold: float = 0.6
    max_iterations: int = 25


@dataclass
class OptimizationResult:
    optimized_matrix: BinaryMatrix
    feature_importance: pd.DataFrame
    object_ranking: pd.DataFrame
    missing: pd.DataFrame
    similarity_before: np.ndarray
    similarity_after: np.ndarray
    history: list[dict] = field(default_factory=list)

    @property
    def removed_features(self) -> list[str]:
        df = self.feature_importance
        return df.loc[~df["kept"], "feature"].tolist()

    @property
    def kept_features(self) -> list[str]:
        df = self.feature_importance
        return df.loc[df["kept"], "feature"].tolist()


def _similarity(bm: BinaryMatrix, kind: SimilarityKind) -> np.ndarray:
    if kind == "jaccard":
        return jaccard_matrix(bm)
    if kind == "inclusion":
        return inclusion_matrix(bm)
    raise ValueError(f"неизвестный тип сходства: {kind}")


def _feature_informativeness(
    bm: BinaryMatrix, kind: SimilarityKind
) -> np.ndarray:
    """Вклад каждой характеристики — норма Фробениуса разности матриц
    сходства "с признаком" и "без признака". Чем больше — тем информативнее.
    """
    base = _similarity(bm, kind)
    n_feat = bm.n_features
    out = np.zeros(n_feat)
    for j in range(n_feat):
        reduced = bm.drop_features([j])
        if reduced.n_features == 0:
            out[j] = float("inf")
            continue
        sim = _similarity(reduced, kind)
        out[j] = float(np.linalg.norm(base - sim))
    return out


class KhubaevOptimizer:
    """Сервис: итеративная оптимизация состава характеристик по Хубаеву."""

    def __init__(self, config: OptimizationConfig | None = None):
        self.config = config or OptimizationConfig()

    def run(self, bm: BinaryMatrix) -> OptimizationResult:
        cfg = self.config
        original = bm
        similarity_before = _similarity(bm, cfg.similarity)

        current = bm
        history: list[dict] = []

        for it in range(cfg.max_iterations):
            if current.n_features <= 2:
                break
            freq_share = current.feature_share()
            informativeness = _feature_informativeness(current, cfg.similarity)

            to_drop: list[int] = []
            for j in range(current.n_features):
                share = float(freq_share[j])
                info = float(informativeness[j])
                if share < cfg.min_feature_frequency:
                    to_drop.append(j)
                elif share > cfg.max_feature_frequency:
                    to_drop.append(j)
                elif info < cfg.informativeness_threshold:
                    to_drop.append(j)

            if not to_drop:
                break

            # не позволяем оптимизации стереть состав до пустого —
            # сохраняем минимум два самых информативных признака
            min_keep = 2
            if current.n_features - len(to_drop) < min_keep:
                ranked = np.argsort(informativeness)  # от наименее к наиболее информативным
                allowed = set(int(j) for j in ranked[: max(0, current.n_features - min_keep)])
                to_drop = [j for j in to_drop if j in allowed]
                if not to_drop:
                    break

            dropped_names = [current.features[j] for j in to_drop]
            history.append(
                {
                    "iteration": it,
                    "dropped": dropped_names,
                    "remaining": current.n_features - len(to_drop),
                }
            )
            current = current.drop_features(to_drop)

        similarity_after = _similarity(current, cfg.similarity)

        # важности считаются на исходной матрице — чтобы было видно,
        # какие признаки и почему оказались исключены
        original_info = _feature_informativeness(original, cfg.similarity)
        original_share = original.feature_share()
        kept_set = set(current.features)
        importance_df = (
            pd.DataFrame(
                {
                    "feature": original.features,
                    "informativeness": original_info,
                    "frequency": original_share,
                    "kept": [f in kept_set for f in original.features],
                }
            )
            .sort_values(
                ["kept", "informativeness"],
                ascending=[False, False],
                kind="mergesort",
            )
            .reset_index(drop=True)
        )

        object_ranking = rank_objects_by_dominance(current)
        missing = missing_characteristics(
            current, min_coverage=cfg.missing_coverage_threshold
        )

        return OptimizationResult(
            optimized_matrix=current,
            feature_importance=importance_df,
            object_ranking=object_ranking,
            missing=missing,
            similarity_before=similarity_before,
            similarity_after=similarity_after,
            history=history,
        )
