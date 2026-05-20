from __future__ import annotations

from dataclasses import dataclass

import matplotlib as mpl


@dataclass(frozen=True)
class DarkPalette:
    bg: str = "#0e1117"
    surface: str = "#141823"
    surface_alt: str = "#1a1f2b"
    border: str = "#262b39"
    text: str = "#dce0ea"
    text_dim: str = "#8a93a6"
    accent: str = "#98a8c8"
    accent_strong: str = "#7c8ab0"
    success: str = "#7fb59a"
    warning: str = "#d6a85f"
    danger: str = "#c97676"
    cmap_seq: str = "cividis"
    cmap_div: str = "RdBu_r"


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
            "font.family": ["IBM Plex Sans", "Inter", "Segoe UI", "DejaVu Sans"],
            "font.size": 9,
            "figure.constrained_layout.use": True,
            "figure.constrained_layout.h_pad": 0.06,
            "figure.constrained_layout.w_pad": 0.06,
            "figure.constrained_layout.hspace": 0.04,
            "figure.constrained_layout.wspace": 0.04,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
        }
    )
