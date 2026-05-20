from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import AgglomerativeClustering

from .matrix import BinaryMatrix
from .similarity import jaccard_matrix


@dataclass
class ClusterResult:
    labels: np.ndarray
    items: list[str]
    linkage_matrix: np.ndarray | None
    distance_matrix: np.ndarray

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame({"item": self.items, "cluster": self.labels})


def _distance_from_similarity(sim: np.ndarray) -> np.ndarray:
    """Перевод матрицы сходства в матрицу расстояний (1 - sim, симметричная)."""
    sim = np.clip(sim, 0.0, 1.0)
    sym = 0.5 * (sim + sim.T)
    dist = 1.0 - sym
    np.fill_diagonal(dist, 0.0)
    return dist


def _condensed(dist: np.ndarray) -> np.ndarray:
    n = dist.shape[0]
    iu = np.triu_indices(n, k=1)
    return dist[iu]


def cluster_objects(
    bm: BinaryMatrix,
    n_clusters: int = 3,
    method: str = "average",
) -> ClusterResult:
    """Иерархическая кластеризация объектов на расстоянии 1 - Jaccard."""
    sim = jaccard_matrix(bm)
    dist = _distance_from_similarity(sim)
    if bm.n_objects < 2:
        return ClusterResult(
            labels=np.zeros(bm.n_objects, dtype=int),
            items=list(bm.objects),
            linkage_matrix=None,
            distance_matrix=dist,
        )
    Z = linkage(_condensed(dist), method=method)
    k = max(1, min(n_clusters, bm.n_objects))
    labels = fcluster(Z, t=k, criterion="maxclust")
    return ClusterResult(
        labels=labels,
        items=list(bm.objects),
        linkage_matrix=Z,
        distance_matrix=dist,
    )


def cluster_experts(
    rankings: pd.DataFrame,
    n_clusters: int = 2,
) -> ClusterResult:
    """Кластеризация экспертов по матрице их ранжирований.

    На входе DataFrame: индекс — эксперты, столбцы — объекты, значения — ранги.
    """
    arr = rankings.to_numpy(dtype=float)
    if arr.shape[0] < 2:
        labels = np.zeros(arr.shape[0], dtype=int)
        return ClusterResult(
            labels=labels,
            items=[str(x) for x in rankings.index.tolist()],
            linkage_matrix=None,
            distance_matrix=np.zeros((arr.shape[0], arr.shape[0])),
        )
    n = arr.shape[0]
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = float(np.sum(np.abs(arr[i] - arr[j])))
            dist[i, j] = dist[j, i] = d
    Z = linkage(_condensed(dist), method="average")
    k = max(1, min(n_clusters, n))
    labels = fcluster(Z, t=k, criterion="maxclust")
    return ClusterResult(
        labels=labels,
        items=[str(x) for x in rankings.index.tolist()],
        linkage_matrix=Z,
        distance_matrix=dist,
    )


def cluster_by_precomputed(
    distance: np.ndarray,
    items: list[str],
    n_clusters: int = 3,
) -> ClusterResult:
    if distance.shape[0] < 2:
        return ClusterResult(
            labels=np.zeros(distance.shape[0], dtype=int),
            items=list(items),
            linkage_matrix=None,
            distance_matrix=distance,
        )
    model = AgglomerativeClustering(
        n_clusters=max(1, min(n_clusters, distance.shape[0])),
        metric="precomputed",
        linkage="average",
    )
    labels = model.fit_predict(distance) + 1
    return ClusterResult(
        labels=labels, items=list(items), linkage_matrix=None, distance_matrix=distance
    )
