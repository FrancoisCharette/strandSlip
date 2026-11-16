"""What the Strand tab's schematics draw: the span between two posts, and the section.

Pure geometry from the ENTRE.DAT values, in metres; ui/plotting/strandSchematics
draws it.

The side view runs the whole strand length CL between two posts, X = 0 at the
left one, Y up. The sinusoid is the programs' own, Y = A sin(2πX/λ) (equation
18). RAYON bends the strand to a constant radius, Y = −X²/2ρ (equation 9); only
the curvature −1/ρ enters its equations, so the drawing puts that curvature on
the arc through both posts, Y = X(L − X)/2ρ. Deflections are centimetres on a
span of metres, so the vertical is drawn exaggerated by a round factor, stated
on the drawing.

The section is the plane X = 0 seen along X: the core of radius R_a, and the n
wires whose axes lie on the circle of radius R_a + R_F, wire i at
θ_i = 2π(i − 1)/n from the Z axis towards Y, as THETA(I) in the programs. A wire
crosses that plane at its helix angle, so its section is an ellipse, R_F across
radially and R_F / cos α_c along the circle. α_c is the helix angle at the
wire's axis: the lay length p = 2πR_a / tan α (equation 13) is the same at every
radius, so tan α_c = 2π(R_a + R_F) / p.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from strandSlip.models.legacyProgram import SINUS, Deflection
from strandSlip.models.strandInput import StrandInput
from strandSlip.services import inputValidation
from strandSlip.services.analysisErrors import InputError
from strandSlip.services.strandModel import stiffnessPositions

drawnExtent = 0.05  # of the span: how tall the largest deflection is drawn
maxPositionMarks = 150  # more positions than this are drawn as a band, not ticks
maxDrawnWires = 200
pointsPerWave = 48
minCurvePoints = 400
maxCurvePoints = 20_000


class SchematicError(Exception):
    """These values cannot be drawn; the message says which one and why."""


@dataclass(frozen=True)
class SideView:
    span: float  # CL: from the left post to the right one
    deflection: Deflection
    x: np.ndarray
    y: np.ndarray  # the deflection, true size, m
    extent: float  # the largest |Y| along the span, m
    exaggeration: float  # how much taller than true the vertical is drawn
    wavelength: float  # λ, for the sinusoid
    amplitude: float  # A for the sinusoid, ρ for the constant curvature
    problem: str  # why the deflection is not drawn ("" when it is)
    xStart: float
    xEnd: float
    positionCount: int  # NPAS
    positionStep: float  # CL / NPAS
    positions: np.ndarray | None  # where SINUS and RAYON compute, when few enough to mark
    wireCount: int
    wireTension: float

    @property
    def midSpanRise(self) -> float:
        """L²/8ρ: how far the constant-curvature arc stands off the chord at mid-span."""
        if self.deflection is not Deflection.constantCurvature or self.amplitude == 0:
            return 0.0
        return self.span * self.span / (8 * self.amplitude)


@dataclass(frozen=True)
class Section:
    coreRadius: float  # R_a
    wireRadius: float  # R_F
    wireCount: int
    helixAngle: float  # α, at the core surface where the wires touch it
    axisHelixAngle: float  # α_c, at the wires' axes
    axisRadius: float  # R_a + R_F: the circle the wire axes lie on
    angles: np.ndarray  # θ_i from the Z axis towards Y, radians
    alongCircle: float  # half the ellipse's length along that circle: R_F / cos α_c
    layLength: float  # p
    outerRadius: float  # R_a + 2 R_F

    @property
    def fill(self) -> float:
        """How much of the circle through the wire axes the wires take: over 1, they overlap."""
        return self.wireCount * 2 * self.alongCircle / (2 * math.pi * self.axisRadius)


def niceScale(raw: float) -> float:
    """The largest of 1, 2, 2.5, 5 times a power of ten that is not above `raw`."""
    if not math.isfinite(raw) or raw <= 0:
        return 1.0
    power = 10.0 ** math.floor(math.log10(raw))
    for step in (5.0, 2.5, 2.0, 1.0):
        if step * power <= raw * (1 + 1e-9):
            return step * power
    return power


def likelyDeflection(value: StrandInput) -> Deflection:
    """The deflection a file was written for: ENTRE wrote λ = 0 for RAYON, which ignores it."""
    if value.wavelength <= 0 and value.amplitude != 0:
        return Deflection.constantCurvature
    return Deflection.sinusoid


def _deflectionCurve(
    value: StrandInput, deflection: Deflection
) -> tuple[np.ndarray, np.ndarray, str]:
    span = value.strandLength
    if deflection is Deflection.sinusoid:
        if value.wavelength <= 0:
            return _straight(span, "λ must be positive to draw the sinusoid.")
        waves = span / value.wavelength
        count = int(min(maxCurvePoints, max(minCurvePoints, waves * pointsPerWave)))
        x = np.linspace(0.0, span, count)
        return x, value.amplitude * np.sin(2 * math.pi * x / value.wavelength), ""
    if value.amplitude == 0:
        return _straight(span, "ρ cannot be zero: RAYON reads the amplitude as the radius.")
    x = np.linspace(0.0, span, minCurvePoints)
    return x, x * (span - x) / (2 * value.amplitude), ""


def _straight(span: float, problem: str) -> tuple[np.ndarray, np.ndarray, str]:
    x = np.array([0.0, span])
    return x, np.zeros(2), problem


def _positionMarks(value: StrandInput) -> np.ndarray | None:
    if inputValidation.countPositions(value, SINUS) > maxPositionMarks:
        return None
    try:
        step = value.strandLength / value.positionCount
        return stiffnessPositions(value, step, maxPositionMarks)
    except InputError:
        return None


def sideView(value: StrandInput, deflection: Deflection) -> SideView:
    span = value.strandLength
    if not math.isfinite(span) or span <= 0:
        raise SchematicError("The strand length L must be positive to draw the span.")
    if value.positionCount < 1:
        raise SchematicError("The number of positions N must be at least 1.")
    x, y, problem = _deflectionCurve(value, deflection)
    extent = float(np.max(np.abs(y)))
    return SideView(
        span=span,
        deflection=deflection,
        x=x,
        y=y,
        extent=extent,
        exaggeration=niceScale(drawnExtent * span / extent) if extent > 0 else 1.0,
        wavelength=value.wavelength,
        amplitude=value.amplitude,
        problem=problem,
        xStart=value.xStart,
        xEnd=value.xEnd,
        positionCount=value.positionCount,
        positionStep=span / value.positionCount,
        positions=_positionMarks(value),
        wireCount=value.wireCount,
        wireTension=value.wireTension,
    )


def section(value: StrandInput) -> Section:
    core, wire, count, alpha = (
        value.coreRadius,
        value.wireRadius,
        value.wireCount,
        value.helixAngle,
    )
    if not 1 <= count <= maxDrawnWires:
        raise SchematicError(f"The number of wires n must be between 1 and {maxDrawnWires}.")
    if core <= 0 or wire <= 0:
        raise SchematicError("The core radius R_a and the wire radius R_F must be positive.")
    if not 0 < alpha < math.pi / 2:
        raise SchematicError("The helix angle α must be between 0 and π/2 radians.")
    layLength = 2 * math.pi * core / math.tan(alpha)
    axisRadius = core + wire
    axisHelixAngle = math.atan(2 * math.pi * axisRadius / layLength)
    return Section(
        coreRadius=core,
        wireRadius=wire,
        wireCount=count,
        helixAngle=alpha,
        axisHelixAngle=axisHelixAngle,
        axisRadius=axisRadius,
        angles=np.arange(count) * (2 * math.pi / count),
        alongCircle=wire / math.cos(axisHelixAngle),
        layLength=layLength,
        outerRadius=core + 2 * wire,
    )
