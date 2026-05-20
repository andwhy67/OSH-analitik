from __future__ import annotations

import networkx as nx
import numpy as np
from matplotlib.figure import Figure

from .palette import PALETTE


def build_similarity_graph(
    sim: np.ndarray,
    labels: list[str],
    threshold: float = 0.4,
) -> nx.Graph:
    g = nx.Graph()
    for name in labels:
        g.add_node(name, degree_weight=0.0)
    n = len(labels)
    for i in range(n):
        for j in range(i + 1, n):
            w = float(sim[i, j])
            if w >= threshold:
                g.add_edge(labels[i], labels[j], weight=w)
    for node in g.nodes:
        g.nodes[node]["degree_weight"] = sum(
            d.get("weight", 0.0) for _, _, d in g.edges(node, data=True)
        )
    return g


def plot_object_graph(
    fig: Figure,
    sim: np.ndarray,
    labels: list[str],
    threshold: float = 0.4,
    title: str = "Граф связей объектов",
) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    g = build_similarity_graph(sim, labels, threshold=threshold)
    if len(g.nodes) == 0:
        ax.set_title(title)
        ax.text(
            0.5, 0.5, "нет связей выше порога",
            ha="center", va="center", color=PALETTE.text_dim, transform=ax.transAxes,
        )
        ax.axis("off")
        return

    pos = nx.spring_layout(g, seed=42, weight="weight", k=1.2 / max(1, len(g.nodes) ** 0.5))
    weights = np.array([d.get("weight", 0.0) for _, _, d in g.edges(data=True)])
    widths = 0.5 + 3.0 * (weights / (weights.max() + 1e-9))
    edge_colors = [PALETTE.accent_strong] * len(weights)
    node_sizes = [
        300 + 1200 * (g.nodes[n]["degree_weight"] / (max(g.nodes[n]["degree_weight"] for n in g.nodes) + 1e-9))
        for n in g.nodes
    ]
    nx.draw_networkx_edges(g, pos, ax=ax, width=widths, edge_color=edge_colors, alpha=0.6)
    nx.draw_networkx_nodes(
        g, pos, ax=ax, node_size=node_sizes,
        node_color=PALETTE.accent, edgecolors=PALETTE.border, linewidths=1.0,
    )
    nx.draw_networkx_labels(g, pos, ax=ax, font_color=PALETTE.text, font_size=9)
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
