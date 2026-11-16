"""The Strand tab's schematics: the span between two posts, and the strand's section.

Drawings rather than charts: no grid or axes. The side view is true to scale
along X, with the vertical exaggerated by the round factor the geometry chose,
which its title states; the section is true to scale. Labels carry the values
typed on the Numerical Entries tab. The geometry is in services/strandGeometry.
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Ellipse, Rectangle

from strandSlip.models.legacyProgram import Deflection, allPrograms
from strandSlip.models.strandInput import StrandInput
from strandSlip.services import strandGeometry
from strandSlip.services.strandGeometry import SchematicError, Section, SideView
from strandSlip.ui.plotting.chartStyle import ChartTheme, contextLineWidth
from strandSlip.ui.plotting.resultPlots import Hover, lineHover

labelSize = 8
numberSize = 6.5
maxNumberedWires = 40
# Heights in the side view, as fractions of the span, in drawn (exaggerated) units.
cableRoom = strandGeometry.drawnExtent
groundLevel = -(cableRoom + 0.035)
rulerLevel = groundLevel - 0.018
spanLevel = groundLevel - 0.06
dimensionLevel = cableRoom + 0.022


def programsFor(deflection: Deflection) -> str:
    keys = [program.key for program in allPrograms if program.deflection is deflection]
    return keys[0] if len(keys) == 1 else ", ".join(keys[:-1]) + " and " + keys[-1]


def length(value: float, unit: str = "m") -> str:
    return f"{value:.4g} {unit}"


def drawSchematics(
    figure: Figure, theme: ChartTheme, value: StrandInput | None, deflection: Deflection
) -> Hover | None:
    if value is None:
        figure.text(
            0.5,
            0.5,
            "Some values on the Numerical Entries tab are not numbers yet.",
            ha="center",
            va="center",
            color=theme.mutedInk,
            fontsize=10,
        )
        return None
    grid = figure.add_gridspec(2, 1, height_ratios=(1.0, 1.15))
    hover = drawSideView(figure.add_subplot(grid[0]), theme, value, deflection)
    drawSection(figure.add_subplot(grid[1]), theme, value)
    return hover


def _blank(axes: Axes, theme: ChartTheme, title: str, message: str) -> None:
    axes.set_axis_off()
    axes.set_title(title, loc="left", color=theme.ink, pad=8)
    axes.text(0.5, 0.5, message, ha="center", va="center", color=theme.mutedInk, fontsize=9)


def _text(axes: Axes, theme: ChartTheme, x: float, y: float, text: str, **options) -> None:
    options.setdefault("fontsize", labelSize)
    options.setdefault("color", theme.secondaryInk)
    axes.text(x, y, text, **options)


def _dimension(
    axes: Axes, theme: ChartTheme, start: tuple[float, float], end: tuple[float, float]
) -> None:
    axes.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": "<|-|>",
            "color": theme.secondaryInk,
            "linewidth": 0.8,
            "shrinkA": 0,
            "shrinkB": 0,
            "mutation_scale": 7,
        },
    )


# -- side view ------------------------------------------------------------------------


def drawSideView(
    axes: Axes, theme: ChartTheme, value: StrandInput, deflection: Deflection
) -> Hover | None:
    title = "Side View, the Full Strand Length Between Two Posts"
    try:
        view = strandGeometry.sideView(value, deflection)
    except SchematicError as error:
        _blank(axes, theme, title, str(error))
        return None
    span, scale = view.span, view.exaggeration
    axes.set_axis_off()
    _sideTitles(axes, theme, title, view, deflection)
    left = min(0.0, view.xStart) - 0.1 * span
    right = max(span, view.xEnd) + 0.1 * span
    _drawGroundAndPosts(axes, theme, span, left, right)
    drawnY = view.y * scale
    axes.plot([0, span], [0, 0], color=theme.context, linewidth=contextLineWidth, linestyle="--")
    axes.plot(view.x, drawnY, color=theme.series, linewidth=2.4, solid_capstyle="round")
    axes.plot([0, span], [0, 0], linestyle="none", marker="o", markersize=4.5, color=theme.ink)
    _drawTension(axes, theme, view)
    if view.problem:
        _text(axes, theme, span / 2, 0.02 * span, view.problem, ha="center", va="bottom")
    elif deflection is Deflection.sinusoid:
        _drawSinusoidDimensions(axes, theme, view)
    else:
        _drawCurvatureDimensions(axes, theme, view)
    _drawPositions(axes, theme, view)
    _drawSpan(axes, theme, span)
    axes.set_xlim(left, right)
    axes.set_ylim((spanLevel - 0.02) * span, (dimensionLevel + 0.03) * span)
    axes.set_aspect("equal")
    return lineHover(
        axes,
        view.x,
        drawnY,
        lambda x, y: f"X = {x:.4g} m\nY = {y / scale:.4g} m",
        theme.series,
    )


def _sideTitles(
    axes: Axes, theme: ChartTheme, title: str, view: SideView, deflection: Deflection
) -> None:
    """The view on the left; on the right, the equation drawn and how tall it is drawn."""
    axes.set_title(title, loc="left", color=theme.ink, pad=8)
    scale = view.exaggeration
    scaleNote = f"vertical scale ×{scale:g}" if scale != 1 else "true scale"
    if view.problem:
        equation = ""
    elif deflection is Deflection.sinusoid:
        equation = f"Y = A sin(2πX/λ), as in {programsFor(deflection)}  ·  "
    else:
        equation = f"the curvature 1/ρ of Y = −X²/2ρ, as in {programsFor(deflection)}  ·  "
    axes.set_title(
        equation + scaleNote, loc="right", color=theme.secondaryInk, fontsize=labelSize, pad=8
    )


def _drawSpan(axes: Axes, theme: ChartTheme, span: float) -> None:
    _dimension(axes, theme, (0, spanLevel * span), (span, spanLevel * span))
    _text(
        axes,
        theme,
        span / 2,
        spanLevel * span,
        f"L = CL = {length(span)}",
        ha="center",
        va="center",
        bbox={"facecolor": theme.surface, "edgecolor": "none", "pad": 1.5},
    )


def _drawGroundAndPosts(
    axes: Axes, theme: ChartTheme, span: float, left: float, right: float
) -> None:
    ground = groundLevel * span
    axes.plot([left, right], [ground, ground], color=theme.axis, linewidth=1.0)
    step = 0.015 * span
    hatch = [
        ((x, ground), (x - 0.008 * span, ground - 0.008 * span))
        for x in np.arange(left + step, right, step)
    ]
    axes.add_collection(LineCollection(hatch, colors=theme.axis, linewidths=0.6))
    width = 0.008 * span
    for x in (0.0, span):
        axes.add_patch(
            Rectangle(
                (x - width / 2, ground),
                width,
                -ground,
                facecolor=theme.secondaryInk,
                edgecolor="none",
            )
        )


def _drawTension(axes: Axes, theme: ChartTheme, view: SideView) -> None:
    reach = 0.06 * view.span
    for start, end in ((0.0, -reach), (view.span, view.span + reach)):
        axes.annotate(
            "",
            xy=(end, 0),
            xytext=(start, 0),
            arrowprops={
                "arrowstyle": "-|>",
                "color": theme.secondaryInk,
                "linewidth": 1.0,
                "shrinkA": 4,
                "shrinkB": 0,
                "mutation_scale": 9,
            },
        )
    _text(
        axes,
        theme,
        -0.012 * view.span,
        0.012 * view.span,
        f"T_i = {view.wireTension:.4g} N\nin each of {view.wireCount} wires",
        ha="right",
        va="bottom",
    )


def _drawSinusoidDimensions(axes: Axes, theme: ChartTheme, view: SideView) -> None:
    span, wavelength, scale = view.span, view.wavelength, view.exaggeration
    level = dimensionLevel * span
    waves = span / wavelength
    if wavelength <= span * (1 + 1e-9) and wavelength >= 0.06 * span:
        for x in (0.0, wavelength):
            axes.plot([x, x], [0.01 * span, level + 0.008 * span], color=theme.axis, linewidth=0.6)
        _dimension(axes, theme, (0, level), (wavelength, level))
        label = f"λ = {length(wavelength)}"
        _text(axes, theme, wavelength / 2, level + 0.004 * span, label, ha="center", va="bottom")
    else:
        about = f"{waves:.3g} of a wave" if waves < 1 else f"{waves:.4g} waves"
        label = f"λ = {length(wavelength)}: {about} between the posts"
        _text(axes, theme, span / 2, level, label, ha="center", va="bottom")
    crest = wavelength / 4 if wavelength / 4 <= span else float(view.x[np.argmax(np.abs(view.y))])
    height = view.amplitude * math.sin(2 * math.pi * crest / wavelength) * scale
    if abs(height) > 0.004 * span:
        _dimension(axes, theme, (crest, 0), (crest, height))
    # Beyond the crest, where a short wave leaves no room beside the arrow.
    _text(
        axes,
        theme,
        crest + 0.006 * span,
        height + (0.004 if height >= 0 else -0.004) * span,
        f"A = {length(view.amplitude)}",
        ha="left",
        va="bottom" if height >= 0 else "top",
    )


def _drawCurvatureDimensions(axes: Axes, theme: ChartTheme, view: SideView) -> None:
    span, scale = view.span, view.exaggeration
    rise = view.midSpanRise * scale
    middle = span / 2
    if abs(rise) > 0.004 * span:
        _dimension(axes, theme, (middle, 0), (middle, rise))
    _text(
        axes,
        theme,
        middle + 0.01 * span,
        rise / 2,
        f"L²/8ρ = {length(view.midSpanRise)}",
        ha="left",
        va="center",
    )
    above = rise >= 0
    _text(
        axes,
        theme,
        middle,
        rise + (0.008 if above else -0.008) * span,
        f"constant radius ρ = {length(view.amplitude)}",
        ha="center",
        va="bottom" if above else "top",
    )


def _drawPositions(axes: Axes, theme: ChartTheme, view: SideView) -> None:
    span = view.span
    level = rulerLevel * span
    half = 0.005 * span
    if view.positions is not None:
        ticks = [((x, level - half), (x, level + half)) for x in view.positions]
        axes.add_collection(LineCollection(ticks, colors=theme.series, linewidths=0.8))
        axes.plot(
            [view.positions[0], view.positions[-1]],
            [level, level],
            color=theme.series,
            linewidth=0.6,
        )
    else:
        axes.add_patch(
            Rectangle(
                (view.xStart, level - half / 2),
                max(view.xEnd - view.xStart, 0.002 * span),
                half,
                facecolor=theme.series,
                edgecolor="none",
            )
        )
    label = (
        f"N = {view.positionCount:,} positions, ΔX = CL/N = {length(view.positionStep)}, "
        f"from X₀ = {length(view.xStart)} to X_f = {length(view.xEnd)}"
    )
    _text(axes, theme, max(view.xStart, 0.0), level - 1.6 * half, label, ha="left", va="top")


# -- section ---------------------------------------------------------------------------


def drawSection(axes: Axes, theme: ChartTheme, value: StrandInput) -> None:
    title = "Section at X = 0, Seen Along X"
    try:
        section = strandGeometry.section(value)
    except SchematicError as error:
        _blank(axes, theme, title, str(error))
        return
    mm = 1000.0
    outer = section.outerRadius * mm
    axes.set_axis_off()
    axes.set_title(title, loc="left", color=theme.ink, pad=8)
    axes.set_title("true scale", loc="right", color=theme.secondaryInk, fontsize=labelSize, pad=8)
    _drawStrand(axes, theme, section)
    _drawSectionLabels(axes, theme, section)
    _drawFacts(axes, theme, section, 1.35 * outer)
    _drawAxisArrows(axes, theme, -1.45 * outer, -1.45 * outer, 0.35 * outer)
    axes.set_xlim(-1.55 * outer, 5.6 * outer)
    axes.set_ylim(-1.55 * outer, 1.2 * outer)
    axes.set_aspect("equal")


def _drawStrand(axes: Axes, theme: ChartTheme, section: Section) -> None:
    mm = 1000.0
    axes.add_patch(
        Circle(
            (0, 0),
            section.coreRadius * mm,
            facecolor=theme.context,
            edgecolor=theme.secondaryInk,
            linewidth=0.8,
            alpha=0.85,
        )
    )
    radius = section.axisRadius * mm
    numbered = section.wireCount <= maxNumberedWires
    for index, angle in enumerate(section.angles):
        centre = (radius * math.cos(angle), radius * math.sin(angle))
        axes.add_patch(
            Ellipse(
                centre,
                2 * section.wireRadius * mm,
                2 * section.alongCircle * mm,
                angle=math.degrees(angle),
                facecolor=theme.surface,
                edgecolor=theme.series,
                linewidth=0.9,
            )
        )
        if numbered:
            _text(
                axes,
                theme,
                *centre,
                str(index + 1),
                ha="center",
                va="center",
                fontsize=numberSize,
                color=theme.ink,
            )
    axes.plot([0], [0], marker="+", markersize=6, color=theme.secondaryInk)


def _drawSectionLabels(axes: Axes, theme: ChartTheme, section: Section) -> None:
    mm = 1000.0
    core, outer = section.coreRadius * mm, section.outerRadius * mm
    toward = math.radians(135)
    axes.annotate(
        "",
        xy=(core * math.cos(toward), core * math.sin(toward)),
        xytext=(0, 0),
        arrowprops={
            "arrowstyle": "-|>",
            "color": theme.ink,
            "linewidth": 0.8,
            "shrinkA": 0,
            "shrinkB": 0,
            "mutation_scale": 7,
        },
    )
    _text(axes, theme, 0.08 * core, -0.08 * core, "R_a", ha="left", va="top", color=theme.ink)
    wire = int(np.argmin(np.abs(np.angle(np.exp(1j * (section.angles + math.pi / 4))))))
    angle = section.angles[wire]
    radius = section.axisRadius * mm
    axes.annotate(
        "R_F",
        xy=(radius * math.cos(angle), radius * math.sin(angle)),
        xytext=(1.12 * outer, -1.12 * outer),
        fontsize=labelSize,
        color=theme.ink,
        ha="left",
        va="top",
        arrowprops={"arrowstyle": "-", "color": theme.secondaryInk, "linewidth": 0.6},
    )
    level = -1.25 * outer
    for x in (-outer, outer):
        axes.plot([x, x], [0, level - 0.06 * outer], color=theme.axis, linewidth=0.6)
    _dimension(axes, theme, (-outer, level), (outer, level))
    _text(
        axes,
        theme,
        0,
        level,
        "D",
        ha="center",
        va="center",
        color=theme.ink,
        bbox={"facecolor": theme.surface, "edgecolor": "none", "pad": 1.5},
    )


def _drawFacts(axes: Axes, theme: ChartTheme, section: Section, left: float) -> None:
    mm = 1000.0
    lines = [
        f"{section.wireCount} wires of radius R_F = {length(section.wireRadius * mm, 'mm')}",
        f"on a core of radius R_a = {length(section.coreRadius * mm, 'mm')}",
        f"D = 2(R_a + 2R_F) = {length(2 * section.outerRadius * mm, 'mm')}",
        f"helix angle α = {math.degrees(section.helixAngle):.2f}° at the core,",
        f"{math.degrees(section.axisHelixAngle):.2f}° at the wire axes",
        f"lay length p = 2πR_a / tan α = {length(section.layLength)}",
        "wire 1 at θ = 0, numbered towards Y as THETA(I)",
    ]
    top = section.outerRadius * mm
    _text(axes, theme, left, top, "\n".join(lines), ha="left", va="top", linespacing=1.6)
    if section.fill > 1.02:
        _text(
            axes,
            theme,
            left,
            -0.95 * top,
            f"These wires overlap: side by side they need {section.fill:.0%}\n"
            "of the circle through their axes.",
            ha="left",
            va="top",
            color=theme.slipAbove,
        )


def _drawAxisArrows(axes: Axes, theme: ChartTheme, x: float, y: float, size: float) -> None:
    """Y up, as the deflection in the side view; Z across, the axis the strand bends about."""
    for dx, dy, name in ((0.0, size, " Y"), (size, 0.0, " Z")):
        axes.annotate(
            "",
            xy=(x + dx, y + dy),
            xytext=(x, y),
            arrowprops={
                "arrowstyle": "-|>",
                "color": theme.secondaryInk,
                "linewidth": 0.8,
                "shrinkA": 0,
                "shrinkB": 0,
                "mutation_scale": 7,
            },
        )
        _text(axes, theme, x + dx, y + dy, name, ha="left", va="center")
