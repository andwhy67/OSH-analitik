from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from .palette import PALETTE


class MplCanvas(FigureCanvasQTAgg):
    """Qt-канвас Matplotlib. Палитра уже настроена глобально в run()."""

    def __init__(self, parent=None, width: float = 5.0, height: float = 4.0, dpi: int = 110):
        self.figure = Figure(figsize=(width, height), dpi=dpi, facecolor=PALETTE.bg)
        super().__init__(self.figure)
        self.setParent(parent)
        self.figure.patch.set_facecolor(PALETTE.bg)

    def clear(self) -> None:
        self.figure.clear()
        self.draw_idle()
