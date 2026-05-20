from __future__ import annotations

import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure

from app.modules.core.matrix import BinaryMatrix

from .palette import PALETTE


def _binary_cmap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        "sysan_binary", [PALETTE.surface, PALETTE.accent]
    )


def plot_binary_matrix(
    fig: Figure,
    bm: BinaryMatrix,
    title: str = "Бинарная матрица объект x характеристика",
) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    ax.imshow(bm.data, aspect="auto", cmap=_binary_cmap(), interpolation="nearest")
    ax.set_xticks(range(bm.n_features))
    ax.set_xticklabels(bm.features, rotation=45, ha="right")
    ax.set_yticks(range(bm.n_objects))
    ax.set_yticklabels(bm.objects)
    ax.set_title(title)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_color(PALETTE.border)
def plot_similarity_matrix(
    fig: Figure,
    sim: np.ndarray,
    labels: list[str],
    title: str = "Матрица сходства",
    cmap: str | None = None,
    annotate: bool = True,
) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    im = ax.imshow(sim, cmap=cmap or PALETTE.cmap_seq, vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.outline.set_edgecolor(PALETTE.border)
    cbar.ax.yaxis.set_tick_params(color=PALETTE.text_dim)
    if annotate and len(labels) <= 14:
        for i in range(sim.shape[0]):
            for j in range(sim.shape[1]):
                ax.text(
                    j,
                    i,
                    f"{sim[i, j]:.2f}",
                    ha="center",
                    va="center",
                    color=PALETTE.text,
                    fontsize=7,
                )
    ax.grid(False)
