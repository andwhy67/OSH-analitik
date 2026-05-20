from __future__ import annotations

from matplotlib.figure import Figure
from scipy.cluster.hierarchy import dendrogram
from sklearn.manifold import MDS

from app.modules.core.clustering import ClusterResult
from .palette import PALETTE

_CLUSTER_COLORS = [
    "#5aa9ff",
    "#4cd790",
    "#f7b955",
    "#ef5b5b",
    "#b48cff",
    "#37d4d4",
    "#ff8fb0",
    "#a4d65e",
]


def _color_for(label: int) -> str:
    return _CLUSTER_COLORS[(int(label) - 1) % len(_CLUSTER_COLORS)]


def plot_dendrogram(
    fig: Figure,
    cluster: ClusterResult,
    title: str = "Дендрограмма кластеризации",
) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    if cluster.linkage_matrix is None:
        ax.text(
            0.5, 0.5, "недостаточно данных для дендрограммы",
            ha="center", va="center", color=PALETTE.text_dim, transform=ax.transAxes,
        )
        ax.axis("off")
        return
    dendrogram(
        cluster.linkage_matrix,
        labels=cluster.items,
        ax=ax,
        color_threshold=0.7 * max(cluster.linkage_matrix[:, 2]),
        above_threshold_color=PALETTE.text_dim,
    )
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel("расстояние")
    fig.tight_layout()


def plot_cluster_scatter(
    fig: Figure,
    cluster: ClusterResult,
    title: str = "Кластеры объектов (MDS-проекция)",
) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    n = cluster.distance_matrix.shape[0]
    if n < 2:
        ax.text(
            0.5, 0.5, "недостаточно объектов для проекции",
            ha="center", va="center", color=PALETTE.text_dim, transform=ax.transAxes,
        )
        ax.axis("off")
        return
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=42, n_init=4)
    coords = mds.fit_transform(cluster.distance_matrix)
    colors = [_color_for(c) for c in cluster.labels]
    ax.scatter(
        coords[:, 0], coords[:, 1], c=colors, s=140,
        edgecolor=PALETTE.border, linewidth=1.0,
    )
    for (x, y), name in zip(coords, cluster.items, strict=False):
        ax.annotate(
            name, (x, y), xytext=(6, 4), textcoords="offset points",
            color=PALETTE.text, fontsize=8,
        )
    ax.set_title(title)
    ax.grid(linestyle="--", alpha=0.3)
    fig.tight_layout()
