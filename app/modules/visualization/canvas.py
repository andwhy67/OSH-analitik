from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from app.ui.widgets.animations import WipeOverlay

from .palette import PALETTE


class MplCanvas(FigureCanvasQTAgg):
    """Qt-канвас Matplotlib с лёгкой «шторкой» при обновлении."""

    def __init__(self, parent=None, width: float = 5.0, height: float = 4.0, dpi: int = 110):
        self.figure = Figure(figsize=(width, height), dpi=dpi, facecolor=PALETTE.bg)
        super().__init__(self.figure)
        self.setParent(parent)
        self.figure.patch.set_facecolor(PALETTE.bg)
        self._wipe = WipeOverlay(self)

    def draw_idle(self) -> None:  # type: ignore[override]
        super().draw_idle()
        # короткая шторка (140 мс) проявляет свежий контент
        if self.isVisible() and self.width() > 8 and self.height() > 8:
            self._wipe.play()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "_wipe"):
            self._wipe.setGeometry(self.rect())

    def clear(self) -> None:
        self.figure.clear()
        self.draw_idle()
