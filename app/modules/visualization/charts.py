from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from app.modules.core.matrix import BinaryMatrix

from .palette import PALETTE


def plot_feature_importance(
    fig: Figure,
    importance: pd.DataFrame,
    title: str = "Информативность характеристик",
) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    df = importance.sort_values("informativeness", ascending=True, kind="mergesort")
    colors = [PALETTE.accent if k else PALETTE.text_dim for k in df["kept"].tolist()]
    ax.barh(df["feature"], df["informativeness"], color=colors, edgecolor=PALETTE.border)
    ax.set_title(title)
    ax.set_xlabel("вклад в дифференциацию объектов")
    ax.grid(axis="x", linestyle="--", alpha=0.3)
def plot_object_ranking(
    fig: Figure,
    ranking: pd.DataFrame,
    value: str = "dominance",
    title: str = "Ранжирование объектов",
) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    df = ranking.sort_values(value, ascending=True, kind="mergesort")
    ax.barh(df["object"], df[value], color=PALETTE.accent_strong, edgecolor=PALETTE.border)
    ax.set_title(title)
    ax.set_xlabel(value)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
def plot_richness(
    fig: Figure,
    bm: BinaryMatrix,
    title: str = "Число характеристик у объекта",
) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    rich = bm.object_richness()
    order = np.argsort(rich)[::-1]
    ax.bar(
        [bm.objects[i] for i in order],
        rich[order],
        color=PALETTE.success,
        edgecolor=PALETTE.border,
    )
    ax.set_title(title)
    ax.set_ylabel("|A_i|")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
