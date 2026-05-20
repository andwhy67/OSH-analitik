from __future__ import annotations

import numpy as np

from .matrix import BinaryMatrix


def _intersect_union(m: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = m.astype(np.int32)
    inter = x @ x.T
    card = x.sum(axis=1)
    a = np.broadcast_to(card[:, None], inter.shape)
    b = np.broadcast_to(card[None, :], inter.shape)
    return inter, a, b


def jaccard_matrix(bm: BinaryMatrix) -> np.ndarray:
    """Коэффициент Жаккара K_J(A_i, A_j) = |A_i ∩ A_j| / |A_i ∪ A_j|."""
    inter, a, b = _intersect_union(bm.data)
    union = a + b - inter
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(union > 0, inter / union, 0.0)
    np.fill_diagonal(out, 1.0)
    return out


def sorensen_dice_matrix(bm: BinaryMatrix) -> np.ndarray:
    """Коэффициент Сёренсена-Дайса 2|A∩B| / (|A|+|B|)."""
    inter, a, b = _intersect_union(bm.data)
    denom = a + b
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(denom > 0, 2.0 * inter / denom, 0.0)
    np.fill_diagonal(out, 1.0)
    return out


def cosine_similarity_binary(bm: BinaryMatrix) -> np.ndarray:
    """Косинусная мера для бинарных векторов."""
    inter, a, b = _intersect_union(bm.data)
    denom = np.sqrt(a.astype(float) * b.astype(float))
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(denom > 0, inter / denom, 0.0)
    np.fill_diagonal(out, 1.0)
    return out


def inclusion_matrix(bm: BinaryMatrix) -> np.ndarray:
    """Коэффициент включения K_⊂(A_i, A_j) = |A_i ∩ A_j| / |A_i|.

    Матрица несимметрична: строка i показывает, насколько объект i
    "содержится" в каждом другом объекте.
    """
    inter, a, _b = _intersect_union(bm.data)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(a > 0, inter / a, 0.0)
    np.fill_diagonal(out, 1.0)
    return out
