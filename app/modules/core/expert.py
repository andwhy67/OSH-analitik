"""Экспертные оценки: агрегация ранжирований и бинарных оценок.

Поддерживаются два режима работы с экспертами:

* "ranking" — каждый эксперт ранжирует объекты (1 — лучший). Считается
  расстояние Кемени между ранжированиями, медианное ранжирование (поиск
  перестановки, минимизирующей сумму расстояний — точный для небольших
  размеров, жадный для больших), коэффициент конкордации Кендалла W.
* "binary" — каждый эксперт даёт свою бинарную матрицу объект x признак.
  Агрегация — мажоритарным голосованием с настраиваемым порогом.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

import numpy as np
import pandas as pd

from .matrix import BinaryMatrix


# ---------- ранжирования ---------------------------------------------------


def _ranks_to_pref(ranks: np.ndarray) -> np.ndarray:
    """Преобразовать вектор рангов в матрицу превосходства: P[i,j]=1, если
    объект i стоит выше j (т. е. имеет меньший ранг)."""
    n = len(ranks)
    r = ranks.reshape(-1, 1)
    return (r < r.T).astype(np.int8)


def kemeny_distance(rank_a: np.ndarray, rank_b: np.ndarray) -> int:
    """Расстояние Кемени между двумя ранжированиями = число пар,
    в которых эксперты расходятся (Kendall tau distance, без учёта связок)."""
    pa = _ranks_to_pref(np.asarray(rank_a))
    pb = _ranks_to_pref(np.asarray(rank_b))
    diff = np.triu(np.abs(pa - pb), k=1)
    return int(diff.sum())


def consensus_matrix(rankings: pd.DataFrame) -> np.ndarray:
    """Матрица консенсуса: для каждой пары (i, j) — доля экспертов,
    поставивших i выше j."""
    arr = rankings.to_numpy()
    n_exp, n_obj = arr.shape
    out = np.zeros((n_obj, n_obj), dtype=float)
    for k in range(n_exp):
        out += _ranks_to_pref(arr[k])
    return out / max(n_exp, 1)


def kendall_w(rankings: pd.DataFrame) -> float:
    """Коэффициент конкордации Кендалла W для согласованности экспертов."""
    arr = rankings.to_numpy(dtype=float)
    m, n = arr.shape
    if m < 2 or n < 2:
        return float("nan")
    rj = arr.sum(axis=0)
    mean_r = rj.mean()
    s = float(((rj - mean_r) ** 2).sum())
    return 12.0 * s / (m * m * (n**3 - n))


def median_ranking(
    rankings: pd.DataFrame,
    *,
    exact_limit: int = 8,
) -> pd.Series:
    """Медиана Кемени — ранжирование, минимизирующее сумму расстояний.

    Для n <= exact_limit делается точный перебор перестановок, иначе —
    жадная оптимизация: старт от среднего ранга, локальные перестановки
    соседних пар, пока есть улучшение.
    """
    objects = list(rankings.columns)
    arr = rankings.to_numpy()
    n = len(objects)

    if n == 0:
        return pd.Series([], dtype=int, name="median_rank")

    expert_prefs = np.stack([_ranks_to_pref(r) for r in arr]) if len(arr) else None

    def total_distance(order: np.ndarray) -> int:
        if expert_prefs is None:
            return 0
        po = _ranks_to_pref(order)
        diff = np.abs(expert_prefs - po[None, :, :])
        upper = np.triu(diff, k=1)
        return int(upper.sum())

    if n <= exact_limit:
        best_order = None
        best_d = None
        for perm in permutations(range(1, n + 1)):
            order = np.array(perm, dtype=int)
            d = total_distance(order)
            if best_d is None or d < best_d:
                best_d = d
                best_order = order
        result = best_order
    else:
        mean_rank = arr.mean(axis=0)
        order_idx = np.argsort(mean_rank)
        current = np.empty(n, dtype=int)
        current[order_idx] = np.arange(1, n + 1)
        improved = True
        while improved:
            improved = False
            for i in range(n - 1):
                a_idx = int(np.where(current == i + 1)[0][0])
                b_idx = int(np.where(current == i + 2)[0][0])
                trial = current.copy()
                trial[a_idx], trial[b_idx] = trial[b_idx], trial[a_idx]
                if total_distance(trial) < total_distance(current):
                    current = trial
                    improved = True
                    break
        result = current

    return pd.Series(result, index=objects, name="median_rank")


# ---------- бинарные экспертные оценки -------------------------------------


@dataclass
class BinaryAggregation:
    matrix: BinaryMatrix
    agreement: np.ndarray  # для каждой ячейки — доля "за"
    threshold: float


def aggregate_binary_experts(
    matrices: list[BinaryMatrix],
    *,
    threshold: float = 0.5,
) -> BinaryAggregation:
    """Мажоритарная агрегация бинарных оценок нескольких экспертов.

    Все матрицы должны иметь одинаковую форму, объекты и признаки.
    """
    if not matrices:
        raise ValueError("список экспертных матриц пуст")
    base = matrices[0]
    shape = base.data.shape
    for m in matrices[1:]:
        if m.data.shape != shape:
            raise ValueError("матрицы экспертов разной формы")
        if m.objects != base.objects or m.features != base.features:
            raise ValueError("метки объектов/признаков не совпадают")

    stack = np.stack([m.data.astype(np.int8) for m in matrices], axis=0)
    agreement = stack.mean(axis=0)
    result = (agreement >= threshold).astype(np.int8)
    aggregated = BinaryMatrix(result, objects=list(base.objects), features=list(base.features))
    return BinaryAggregation(matrix=aggregated, agreement=agreement, threshold=threshold)
