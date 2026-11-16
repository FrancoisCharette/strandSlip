"""Chart colours and chrome, one set for each theme.

Values come from the validated reference palette: slot 1 blue for the
series being read, muted gray for context lines, and a blue/red pair with a
gray midpoint for the slip map (validated for colour-vision deficiency in
both themes). Text never wears a series colour.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib
from matplotlib import font_manager
from matplotlib.axes import Axes


@dataclass(frozen=True)
class ChartTheme:
    dark: bool
    surface: str
    ink: str
    secondaryInk: str
    mutedInk: str
    grid: str
    axis: str
    series: str  # slot 1
    secondSeries: str  # slot 2
    context: str  # the lines that are not the one being read
    slipBelow: str  # blue pole
    stuck: str  # neutral midpoint
    slipAbove: str  # red pole


lightTheme = ChartTheme(
    dark=False,
    surface="#fcfcfb",
    ink="#0b0b0b",
    secondaryInk="#52514e",
    mutedInk="#898781",
    grid="#e1e0d9",
    axis="#c3c2b7",
    series="#2a78d6",
    secondSeries="#eb6834",
    context="#c3c2b7",
    slipBelow="#2a78d6",
    stuck="#f0efec",
    slipAbove="#e34948",
)

darkTheme = ChartTheme(
    dark=True,
    surface="#1a1a19",
    ink="#f0efec",
    secondaryInk="#c3c2b7",
    mutedInk="#898781",
    grid="#2c2c2a",
    axis="#383835",
    series="#3987e5",
    secondSeries="#d95926",
    context="#52514e",
    slipBelow="#3987e5",
    stuck="#383835",
    slipAbove="#e66767",
)

lineWidth = 1.5  # points: 2 px at 96 dpi
contextLineWidth = 0.75


def _pickSansFont() -> tuple[str, str]:
    """The system sans, and the title weight it actually has."""
    entries = font_manager.fontManager.ttflist
    for name in ("Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"):
        weights = {entry.weight for entry in entries if entry.name == name}
        if weights:
            return name, "semibold" if 600 in weights else "bold"
    return "sans-serif", "bold"


_family, _titleWeight = _pickSansFont()
# One family only: matplotlib warns about every listed family missing a weight.
matplotlib.rcParams["font.family"] = [_family]
matplotlib.rcParams["font.size"] = 9
matplotlib.rcParams["axes.titlesize"] = 10
matplotlib.rcParams["axes.titleweight"] = _titleWeight


def styleAxes(axes: Axes, theme: ChartTheme) -> None:
    """Recessive chrome: hairline solid grid, two spines, muted ticks."""
    axes.set_facecolor(theme.surface)
    axes.grid(True, color=theme.grid, linewidth=0.6, linestyle="-")
    axes.set_axisbelow(True)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axes.spines[side].set_color(theme.axis)
        axes.spines[side].set_linewidth(0.8)
    axes.tick_params(colors=theme.mutedInk, labelcolor=theme.secondaryInk, length=3)
    axes.xaxis.label.set_color(theme.secondaryInk)
    axes.yaxis.label.set_color(theme.secondaryInk)


def setTitle(axes: Axes, theme: ChartTheme, text: str) -> None:
    """Left-aligned over the plot, in primary ink: the title names the series."""
    axes.set_title(text, loc="left", color=theme.ink, pad=8)


def styleLegend(axes: Axes, theme: ChartTheme, **options) -> None:
    legend = axes.legend(frameon=False, fontsize=8, **options)
    for text in legend.get_texts():
        text.set_color(theme.secondaryInk)
