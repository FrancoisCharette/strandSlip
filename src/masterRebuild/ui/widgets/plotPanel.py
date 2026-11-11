"""A matplotlib figure that follows the app theme and reads values on hover."""

from __future__ import annotations

import os
from collections.abc import Callable

os.environ.setdefault("QT_API", "pyside6")

from matplotlib.backend_bases import MouseEvent  # noqa: E402
from matplotlib.backends.backend_qtagg import (  # noqa: E402
    FigureCanvasQTAgg,
    NavigationToolbar2QT,
)
from matplotlib.figure import Figure  # noqa: E402
from PySide6.QtCore import QEvent  # noqa: E402
from PySide6.QtGui import QPalette  # noqa: E402
from PySide6.QtWidgets import QVBoxLayout, QWidget  # noqa: E402

from masterRebuild.ui.plotting.chartStyle import ChartTheme, darkTheme, lightTheme  # noqa: E402
from masterRebuild.ui.plotting.resultPlots import Hover  # noqa: E402

Drawing = Callable[[Figure, ChartTheme], Hover | None]


class PlotPanel(QWidget):
    """Redraws through a callback, so a theme change can repaint everything."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(layout="constrained")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setObjectName("plotCanvas")
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.drawing: Drawing | None = None
        self.hover: Hover | None = None
        self.hoverArtists: list = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)
        self.canvas.mpl_connect("motion_notify_event", self.onPointerMoved)
        self.canvas.mpl_connect("axes_leave_event", lambda _event: self.clearHover())
        self.redraw()

    def theme(self) -> ChartTheme:
        window = self.palette().color(QPalette.ColorRole.Window)
        return darkTheme if window.lightness() < 128 else lightTheme

    def setDrawing(self, drawing: Drawing | None) -> None:
        self.drawing = drawing
        self.redraw()

    def redraw(self) -> None:
        theme = self.theme()
        self.figure.clear()
        self.hoverArtists = []
        self.figure.set_facecolor(theme.surface)
        self.hover = self.drawing(self.figure, theme) if self.drawing else None
        if self.drawing is None:
            self.figure.text(
                0.5,
                0.5,
                "Run the program to see its results here.",
                ha="center",
                va="center",
                color=theme.mutedInk,
                fontsize=10,
            )
        self.canvas.draw_idle()

    def changeEvent(self, event: QEvent) -> None:
        # Qt delivers the new palette after the theme is applied, so the
        # colours are only right when rebuilt here.
        if event.type() == QEvent.Type.PaletteChange:
            self.redraw()
        super().changeEvent(event)

    def clearHover(self) -> None:
        if self.hoverArtists:
            for artist in self.hoverArtists:
                artist.remove()
            self.hoverArtists = []
            self.canvas.draw_idle()

    def onPointerMoved(self, event: MouseEvent) -> None:
        hover = self.hover
        if hover is None or event.inaxes is not hover.axes or event.xdata is None:
            self.clearHover()
            return
        found = hover.locate(event.xdata, event.ydata)
        self.clearHover()
        if found is None:
            return
        x, y, text = found
        theme = self.theme()
        axes = hover.axes
        self.hoverArtists.append(axes.axvline(x, color=theme.mutedInk, linewidth=0.6))
        if hover.markerColor is not None:
            (marker,) = axes.plot(
                [x],
                [y],
                marker="o",
                markersize=7,
                color=hover.markerColor,
                markeredgecolor=theme.surface,
                markeredgewidth=1.5,
            )
            self.hoverArtists.append(marker)
        # Keep the readout inside the plot: flip it left past 60 % of the width.
        right = axes.transAxes.inverted().transform((event.x, event.y))[0] > 0.6
        label = axes.annotate(
            text,
            xy=(x, y),
            xytext=(-10 if right else 10, 10),
            textcoords="offset points",
            ha="right" if right else "left",
            va="bottom",
            fontsize=8,
            color=theme.ink,
            bbox={
                "boxstyle": "round,pad=0.4",
                "facecolor": theme.surface,
                "edgecolor": theme.axis,
                "linewidth": 0.6,
            },
        )
        self.hoverArtists.append(label)
        self.canvas.draw_idle()
