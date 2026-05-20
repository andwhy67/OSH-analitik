from .canvas import MplCanvas
from .charts import plot_feature_importance, plot_object_ranking, plot_richness
from .clusters import plot_cluster_scatter, plot_dendrogram
from .graphs import plot_object_graph
from .heatmaps import plot_binary_matrix, plot_similarity_matrix
from .palette import DarkPalette, apply_dark_style

__all__ = [
    "DarkPalette",
    "apply_dark_style",
    "MplCanvas",
    "plot_binary_matrix",
    "plot_similarity_matrix",
    "plot_feature_importance",
    "plot_object_ranking",
    "plot_richness",
    "plot_object_graph",
    "plot_dendrogram",
    "plot_cluster_scatter",
]
