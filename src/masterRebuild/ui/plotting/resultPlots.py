"""The plots each kind of result offers, drawn onto a matplotlib figure.

One quantity per plot, on one axis. Wire-by-wire curves use emphasis: every
wire in a muted context colour, the chosen one in the series colour, so 22
wires never turn into 22 hues.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from masterRebuild.models.analysisResults import (
    AnalysisResult,
    DisplacementResult,
    FrictionResult,
    StiffnessResult,
    slipAbove,
    slipBelow,
)
from masterRebuild.services.wireStateSolver import classifyDemand
from masterRebuild.ui.plotting.chartStyle import (
    ChartTheme,
    contextLineWidth,
    lineWidth,
    setTitle,
    styleAxes,
    styleLegend,
)


@dataclass(frozen=True)
class PlotChoice:
    key: str
    label: str
    usesWire: bool = False


@dataclass
class Hover:
    """Snaps the pointer to the nearest datum and says what it is."""

    axes: Axes
    locate: Callable[[float, float], tuple[float, float, str] | None]
    markerColor: str | None = None


stiffnessChoices = (
    PlotChoice("stiffness", "Stiffness EI"),
    PlotChoice("momentZ", "Bending Moment Mz"),
    PlotChoice("momentY", "Bending Moment My"),
    PlotChoice("torsion", "Torsion Mx"),
    PlotChoice("forceX", "Axial Force Fx"),
    PlotChoice("forceY", "Shear Force Fy"),
    PlotChoice("forceZ", "Shear Force Fz"),
    PlotChoice("slipMap", "Slip Map"),
    PlotChoice("elongation", "Wire Elongation", usesWire=True),
    PlotChoice("frictionDemand", "Required Friction", usesWire=True),
)
frictionChoices = (
    PlotChoice("frictionDemand", "Required Friction", usesWire=True),
    PlotChoice("slipMap", "Slip Map"),
)
displacementChoices = (
    PlotChoice("displacement", "Core Displacement", usesWire=True),
    PlotChoice("brackets", "Equation 23 Brackets", usesWire=True),
)

# key: (symbol, unit, legacy name)
_totals = {
    "stiffness": ("EI", "N·m²", "RIG"),
    "momentZ": ("Mz", "N·m", "FMXZT"),
    "momentY": ("My", "N·m", "FMXYT"),
    "torsion": ("Mx", "N·m", "TMXT"),
    "forceX": ("Fx", "N", "FXT"),
    "forceY": ("Fy", "N", "FYT"),
    "forceZ": ("Fz", "N", "FZT"),
}


def choicesFor(result: AnalysisResult) -> tuple[PlotChoice, ...]:
    if isinstance(result, StiffnessResult):
        return stiffnessChoices
    if isinstance(result, FrictionResult):
        return frictionChoices
    return displacementChoices


def lineHover(axes: Axes, x: np.ndarray, y: np.ndarray, describe, color: str) -> Hover:
    order = np.argsort(x)
    sortedX = x[order]

    def locate(pointerX: float, _pointerY: float) -> tuple[float, float, str] | None:
        if sortedX.size == 0:
            return None
        index = int(np.searchsorted(sortedX, pointerX))
        candidates = [i for i in (index - 1, index) if 0 <= i < sortedX.size]
        nearest = min(candidates, key=lambda i: abs(sortedX[i] - pointerX))
        row = order[nearest]
        if not np.isfinite(y[row]):
            return None
        return float(x[row]), float(y[row]), describe(float(x[row]), float(y[row]))

    return Hover(axes, locate, color)


def _robustLimits(axes: Axes, values: np.ndarray, keep: float | None, theme: ChartTheme) -> None:
    """Keep the y range readable when a few points blow up near sin(2 pi X/lambda) = 0."""
    finite = values[np.isfinite(values)]
    if finite.size < 10:
        return
    low, high = np.percentile(finite, [1, 99])
    span = high - low
    if span <= 0 or finite.max() - finite.min() <= 20 * span:
        return
    if keep is not None:
        low, high = min(low, keep), max(high, keep)
        span = high - low
    axes.set_ylim(low - 0.25 * span, high + 0.25 * span)
    axes.text(
        0.0,
        -0.16,
        "A few spikes are outside the y range; zoom out with the toolbar.",
        transform=axes.transAxes,
        fontsize=8,
        color=theme.mutedInk,
    )


def _drawTotal(axes: Axes, theme: ChartTheme, result: StiffnessResult, key: str) -> Hover:
    symbol, unit, legacy = _totals[key]
    x = result.positions[result.written]
    y = getattr(result, key)[result.written]
    axes.plot(
        x,
        y,
        color=theme.series,
        linewidth=lineWidth,
        solid_joinstyle="round",
        solid_capstyle="round",
    )
    axes.set_xlabel("X (m)")
    axes.set_ylabel(f"{symbol} ({unit})")
    label = next(choice.label for choice in stiffnessChoices if choice.key == key)
    setTitle(axes, theme, f"{label} Along X  ·  {result.program.key}  ·  {legacy}")
    reference = None
    if key == "stiffness" and result.fullStickStiffness is not None:
        reference = result.fullStickStiffness
        axes.axhline(reference, color=theme.mutedInk, linewidth=0.8, linestyle=(0, (4, 3)))
        axes.annotate(
            f"Every wire stuck: {reference:.6g}",
            xy=(1.0, reference),
            xycoords=("axes fraction", "data"),
            xytext=(-4, 4),
            textcoords="offset points",
            ha="right",
            va="bottom",
            fontsize=8,
            color=theme.secondaryInk,
        )
    if key == "stiffness":
        _robustLimits(axes, y, reference, theme)
    return lineHover(
        axes, x, y, lambda xv, yv: f"X = {xv:.4f} m\n{symbol} = {yv:.6g} {unit}", theme.series
    )


def _drawSlipMap(
    axes: Axes, theme: ChartTheme, positions: np.ndarray, zone: np.ndarray, title: str, step: float
) -> Hover:
    count = zone.shape[1]
    half = (positions[1] - positions[0]) / 2 if len(positions) > 1 else step / 2
    cmap = ListedColormap([theme.slipBelow, theme.stuck, theme.slipAbove])
    norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5], cmap.N)
    axes.imshow(
        zone.T,
        origin="lower",
        aspect="auto",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        extent=(positions[0] - half, positions[-1] + half, 0.5, count + 0.5),
    )
    axes.grid(False)
    axes.set_xlabel("X (m)")
    axes.set_ylabel("Wire")
    setTitle(axes, theme, title)
    handles = [
        Patch(facecolor=theme.slipBelow, label="Slipping: demand below −μL"),
        Patch(facecolor=theme.stuck, edgecolor=theme.axis, label="Stuck"),
        Patch(facecolor=theme.slipAbove, label="Slipping: demand above +μL"),
    ]
    legend = axes.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=3,
        frameon=False,
        fontsize=8,
    )
    for text in legend.get_texts():
        text.set_color(theme.secondaryInk)
    names = {slipAbove: "slipping above +μL", slipBelow: "slipping below −μL"}

    def locate(pointerX: float, pointerY: float) -> tuple[float, float, str] | None:
        row = int(np.argmin(np.abs(positions - pointerX)))
        wire = int(round(pointerY)) - 1
        if not 0 <= wire < count:
            return None
        state = names.get(int(zone[row, wire]), "stuck")
        text = f"X = {positions[row]:.4f} m\nWire {wire + 1}: {state}"
        return float(positions[row]), wire + 1.0, text

    return Hover(axes, locate, None)


def _drawWires(
    axes: Axes,
    theme: ChartTheme,
    positions: np.ndarray,
    values: np.ndarray,
    wire: int,
    ylabel: str,
    title: str,
    describe,
) -> Hover:
    others = [
        np.column_stack([positions, values[:, k]]) for k in range(values.shape[1]) if k != wire
    ]
    if others:
        axes.add_collection(
            LineCollection(others, colors=theme.context, linewidths=contextLineWidth)
        )
    axes.plot(
        positions,
        values[:, wire],
        color=theme.series,
        linewidth=lineWidth,
        solid_joinstyle="round",
        solid_capstyle="round",
    )
    axes.autoscale_view()
    axes.set_xlabel("X (m)")
    axes.set_ylabel(ylabel)
    setTitle(axes, theme, title)
    handles = [Line2D([], [], color=theme.series, linewidth=lineWidth, label=f"Wire {wire + 1}")]
    if others:
        handles.append(Line2D([], [], color=theme.context, linewidth=1.2, label="Other wires"))
    axes.legend(handles=handles, loc="upper right", frameon=False, fontsize=8)
    for text in axes.get_legend().get_texts():
        text.set_color(theme.secondaryInk)
    return lineHover(axes, positions, values[:, wire], describe, theme.series)


def _drawLimits(axes: Axes, theme: ChartTheme, limit: float) -> None:
    for level, name in ((limit, "+μL"), (-limit, "−μL")):
        axes.axhline(level, color=theme.secondaryInk, linewidth=0.8, linestyle=(0, (4, 3)))
        axes.annotate(
            f"{name} = {level:g}",
            xy=(0.0, level),
            xycoords=("axes fraction", "data"),
            xytext=(4, 3 if level > 0 else -11),
            textcoords="offset points",
            fontsize=8,
            color=theme.secondaryInk,
        )


def _drawFriction(axes, theme, positions, demand, limit, wire, programKey) -> Hover:
    hover = _drawWires(
        axes,
        theme,
        positions,
        demand,
        wire,
        "Required μ (–)",
        f"Friction Needed to Stay Stuck  ·  {programKey}  ·  CFX, eq. 19",
        lambda xv, yv: f"X = {xv:.4f} m\nWire {wire + 1}: μ = {yv:.5g}",
    )
    _drawLimits(axes, theme, limit)
    return hover


def _drawBrackets(axes: Axes, theme: ChartTheme, result: DisplacementResult, wire: int) -> Hover:
    x = result.positions
    axes.plot(
        x,
        result.termA[:, wire],
        color=theme.series,
        linewidth=lineWidth,
        label="CA19: sin(2πX(1/p − 1/λ) + θ) − sin θ, over λ − p",
    )
    axes.plot(
        x,
        result.termB[:, wire],
        color=theme.secondSeries,
        linewidth=lineWidth,
        label="CB19: sin(2πX(1/p + 1/λ) + θ) − sin θ, over λ + p",
    )
    axes.set_xlabel("X (m)")
    axes.set_ylabel("Bracket (1/m)")
    setTitle(axes, theme, f"The Two Brackets of Equation 23, Wire {wire + 1}  ·  DEPLACE")
    styleLegend(axes, theme, loc="upper right")
    return lineHover(
        axes,
        x,
        result.termA[:, wire],
        lambda xv, yv: f"X = {xv:.4f} m\nCA19 = {yv:.5g}",
        theme.series,
    )


def drawResult(
    figure: Figure, theme: ChartTheme, result: AnalysisResult, key: str, wire: int
) -> Hover | None:
    figure.set_facecolor(theme.surface)
    axes = figure.add_subplot(1, 1, 1)
    styleAxes(axes, theme)
    wire = int(np.clip(wire, 0, result.input.wireCount - 1))
    program = result.program.key
    if isinstance(result, StiffnessResult):
        if key in _totals:
            return _drawTotal(axes, theme, result, key)
        if key == "slipMap":
            return _drawSlipMap(
                axes,
                theme,
                result.positions,
                result.wires.zone,
                f"Where Each Wire Slips  ·  {program}",
                result.constants.positionStep,
            )
        if key == "elongation":
            return _drawWires(
                axes,
                theme,
                result.positions,
                result.wires.elongation,
                wire,
                "Elongation εF (–)",
                f"Wire Elongation  ·  {program}  ·  EX, eq. 22 / 35",
                lambda xv, yv: f"X = {xv:.4f} m\nWire {wire + 1}: ε = {yv:.4g}",
            )
        return _drawFriction(
            axes,
            theme,
            result.positions,
            result.wires.frictionDemand,
            result.input.frictionLimit,
            wire,
            program,
        )
    if isinstance(result, FrictionResult):
        if key == "slipMap":
            zone = classifyDemand(result.frictionDemand, result.input.frictionLimit)
            return _drawSlipMap(
                axes,
                theme,
                result.positions,
                zone,
                f"Where Each Wire Would Slip  ·  {program}",
                result.constants.positionStep,
            )
        return _drawFriction(
            axes,
            theme,
            result.positions,
            result.frictionDemand,
            result.input.frictionLimit,
            wire,
            program,
        )
    if key == "brackets":
        return _drawBrackets(axes, theme, result, wire)
    return _drawWires(
        axes,
        theme,
        result.positions,
        result.displacementScaled,
        wire,
        "Da × 10⁴ (m)",
        f"Core Surface Displacement  ·  {program}  ·  DX, eq. 23",
        lambda xv, yv: f"X = {xv:.4f} m\nWire {wire + 1}: Da × 10⁴ = {yv:.5g} m",
    )
