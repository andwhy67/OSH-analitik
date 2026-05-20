from __future__ import annotations

from dataclasses import dataclass

import matplotlib as mpl


@dataclass(frozen=True)
class DarkPalette:
    bg: str = "#0f1218"
    surface: str = "#161a23"
    surface_alt: str = "#1d2230"
    border: str = "#2a2f3d"
    text: str = "#e6e8ee"
    text_dim: str = "#8a93a6"
    accent: str = "#5aa9ff"
    accent_strong: str = "#3f86ff"
    success: str = "#4cd790"
    warning: str = "#f7b955"
    danger: str = "#ef5b5b"
    cmap_seq: str = "viridis"
    cmap_div: str = "coolwarm"


PALETTE = DarkPalette()


def apply_dark_style() -> None:
    """Глобальные настройки matplotlib под тёмную тему приложения."""
    mpl.rcParams.update(
        {
            "figure.facecolor": PALETTE.bg,
            "axes.facecolor": PALETTE.surface,
            "axes.edgecolor": PALETTE.border,
            "axes.labelcolor": PALETTE.text,
            "axes.titlecolor": PALETTE.text,
            "axes.titleweight": "600",
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "xtick.color": PALETTE.text_dim,
            "ytick.color": PALETTE.text_dim,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "grid.color": PALETTE.border,
            "grid.linestyle": "--",
            "grid.alpha": 0.35,
            "text.color": PALETTE.text,
            "savefig.facecolor": PALETTE.bg,
            "savefig.edgecolor": PALETTE.bg,
            "legend.facecolor": PALETTE.surface_alt,
            "legend.edgecolor": PALETTE.border,
            "legend.labelcolor": PALETTE.text,
            "font.family": ["Segoe UI", "Inter", "DejaVu Sans"],
            "font.size": 9,
        }
    )
