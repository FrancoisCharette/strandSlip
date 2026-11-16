"""The plots a 1992 program's result offers.

The profiles follow the thesis's figures 6.1 to 6.3 and 6.8: the wire with
slip as a solid line, without slip (the core's surface) dashed, and for the
compliance model the transition points between linear portions as dots.
"""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from strandSlip.models.thesisProgram import ThesisModel
from strandSlip.models.thesisResults import ThesisResult
from strandSlip.ui.plotting.chartStyle import (
    ChartTheme,
    lineWidth,
    setTitle,
    styleAxes,
    styleLegend,
)
from strandSlip.ui.plotting.resultPlots import Hover, PlotChoice, lineHover

profileChoices = (
    PlotChoice("displacement", "Wire Displacement"),
    PlotChoice("strain", "Wire Strain"),
    PlotChoice("friction", "Friction Ratio Rμ"),
)
# key: (profile attributes, y label, legacy names, transition column)
_profiles = {
    "displacement": ("wireDisplacement", "coreDisplacement", "Displacement (–)", "DFIL", 1),
    "strain": ("wireStrain", "coreStrain", "Strain (–)", "EFIL", 2),
    "friction": ("wireFriction", "coreFriction", "Rμ (–)", "FFIL", 3),
}


def thesisChoices(result: ThesisResult) -> tuple[PlotChoice, ...]:
    choices: list[PlotChoice] = []
    if result.profile is not None:
        choices.extend(profileChoices)
    if len(result.halfPitches) > 1:
        choices.append(PlotChoice("energy", "Energy per Half Lay Length"))
    if result.halfPitches:
        choices.append(PlotChoice("regions", "Slip Regions"))
    if any(h.regionEnergies for h in result.halfPitches):
        choices.append(PlotChoice("regionEnergy", "Energy by Region"))
    return tuple(choices)


def _drawProfile(axes: Axes, theme: ChartTheme, result: ThesisResult, key: str) -> Hover:
    wireName, coreName, ylabel, legacy, column = _profiles[key]
    profile = result.profile
    x, wire, core = profile.x, getattr(profile, wireName), getattr(profile, coreName)
    axes.plot(x, core, color=theme.secondaryInk, linewidth=1.0, linestyle=(0, (5, 3)),
              label="Without slip (core surface)")  # fmt: skip
    axes.plot(x, wire, color=theme.series, linewidth=lineWidth, label="With slip (wire)")
    if profile.transitions.size:
        axes.plot(
            profile.transitions[:, 0], profile.transitions[:, column], linestyle="none",
            marker="o", markersize=4, color=theme.secondSeries, label="Transition points",
        )  # fmt: skip
    half = result.halfPitches[-1]
    if result.program.model is not ThesisModel.compliance or half.regions == 11:
        axes.axvspan(half.lowerBound, half.upperBound, color=theme.context, alpha=0.25, lw=0)
    axes.set_xlabel("Position along the wire ξ = X/p (lay lengths)")
    axes.set_ylabel(ylabel)
    label = next(choice.label for choice in profileChoices if choice.key == key)
    setTitle(axes, theme, f"{label}  ·  {result.program.key}  ·  {legacy}")
    styleLegend(axes, theme, loc="best")
    return lineHover(
        axes, x, wire, lambda xv, yv: f"ξ = {xv:.4f}\n{legacy} = {yv:.6g}", theme.series
    )


def _drawEnergy(axes: Axes, theme: ChartTheme, result: ThesisResult) -> Hover:
    starts = np.array([h.start for h in result.halfPitches])
    energy = np.array([h.energy for h in result.halfPitches])
    axes.bar(starts + 0.25, energy, width=0.4, color=theme.series)
    for skipped in result.skipped:
        axes.axvspan(skipped[0], skipped[1], color=theme.context, alpha=0.2, lw=0)
    axes.set_xlabel("Half lay length (ξ from the origin)")
    axes.set_ylabel("Energy dissipated DSP (–)")
    total = "" if result.totalEnergy is None else f"  ·  4 × sum = {result.totalEnergy:.6g}"
    setTitle(axes, theme, f"Energy per Half Lay Length  ·  {result.program.key}{total}")
    return lineHover(
        axes, starts + 0.25, energy,
        lambda xv, yv: f"Half lay length from {xv - 0.25:g}\nDSP = {yv:.6g}", theme.series,
    )  # fmt: skip


def _drawRegions(axes: Axes, theme: ChartTheme, result: ThesisResult) -> Hover:
    """Each half lay length solved, with its macro-slip region shaded."""
    compliance = result.program.model is ThesisModel.compliance
    for row, h in enumerate(result.halfPitches):
        axes.barh(row, h.end - h.start, left=h.start, height=0.6, color=theme.stuck,
                  edgecolor=theme.axis, linewidth=0.6)  # fmt: skip
        if not compliance or h.regions == 11:
            axes.barh(row, h.upperBound - h.lowerBound, left=h.lowerBound, height=0.6,
                      color=theme.slipAbove if h.side > 0 else theme.slipBelow)  # fmt: skip
    axes.set_yticks(range(len(result.halfPitches)), [f"{h.start:g}" for h in result.halfPitches])
    axes.set_xlabel("ξ = X/p (lay lengths)")
    axes.set_ylabel("Half lay length starting at")
    axes.grid(False, axis="y")
    stuck = "Micro-slip (compliance)" if compliance else "Stuck"
    handles = [
        Patch(facecolor=theme.stuck, edgecolor=theme.axis, label=stuck),
        Patch(facecolor=theme.slipAbove, label="Macro-slip, friction at +μc"),
        Patch(facecolor=theme.slipBelow, label="Macro-slip, friction at −μc"),
    ]
    legend = axes.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.14),
                         ncol=3, frameon=False, fontsize=8)  # fmt: skip
    for text in legend.get_texts():
        text.set_color(theme.secondaryInk)
    setTitle(axes, theme, f"Where the Wire Slips  ·  {result.program.key}  ·  XB1..XB2")
    halves = result.halfPitches

    def locate(pointerX: float, pointerY: float):
        row = int(round(pointerY))
        if not 0 <= row < len(halves):
            return None
        h = halves[row]
        text = f"{h.start:g} to {h.end:g}\nXB1 = {h.lowerBound:.6g}\nXB2 = {h.upperBound:.6g}"
        return min(max(pointerX, h.start), h.end), float(row), text

    return Hover(axes, locate, None)


def _drawRegionEnergy(axes: Axes, theme: ChartTheme, result: ThesisResult) -> Hover:
    half = next(h for h in reversed(result.halfPitches) if h.regionEnergies)
    numbers = np.array([n for n, _ in half.regionEnergies], dtype=float)
    energy = np.array([e for _, e in half.regionEnergies])
    order = np.arange(len(numbers))
    axes.bar(order, energy, color=theme.series)
    axes.set_xticks(order, [f"{int(n)}" for n in numbers])
    axes.set_xlabel("Region (ENERGY.DAT numbering, from XINF)")
    axes.set_ylabel("Energy dissipated (–)")
    setTitle(axes, theme, f"Energy by Region, {half.start:g} to {half.end:g}  ·  ENERGY.DAT")
    return lineHover(
        axes, order.astype(float), energy,
        lambda xv, yv: f"Region {int(numbers[int(round(xv))])}\nEnergy = {yv:.6g}", theme.series,
    )  # fmt: skip


def drawThesisResult(figure: Figure, theme: ChartTheme, result: ThesisResult, key: str):
    figure.set_facecolor(theme.surface)
    axes = figure.add_subplot(1, 1, 1)
    styleAxes(axes, theme)
    if key in _profiles and result.profile is not None:
        return _drawProfile(axes, theme, result, key)
    if key == "energy":
        return _drawEnergy(axes, theme, result)
    if key == "regionEnergy":
        return _drawRegionEnergy(axes, theme, result)
    if result.halfPitches:
        return _drawRegions(axes, theme, result)
    axes.set_axis_off()
    axes.text(0.5, 0.5, "Nothing solved yet: see the question below the inputs.",
              ha="center", va="center", color=theme.mutedInk, transform=axes.transAxes)  # fmt: skip
    return None
