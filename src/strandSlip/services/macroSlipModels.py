"""The two models without compliance: Hardy's and continuity of deformation.

In both, a wire sticks to the core except in one macro-slip region XB1..XB2
of the half-pitch, where its displacement follows DEPH (a parabola of slope
XI and offset PSI at XB1). Hardy's model puts the bounds where the friction
needed to stick reaches the Coulomb limit (FRICTION = 0) and accepts a jump
in strain there; the continuity model also imposes continuous strain, which
makes the bounds and constants the root of four equations (NEWT, VCB, JACO).
"""

from __future__ import annotations

from dataclasses import dataclass

from strandSlip.services import thesisScreens as screens
from strandSlip.services.thesisDeflections import (
    Deflection,
    HalfPitch,
    macroDisplacement,
    macroStrain,
    pi,
)
from strandSlip.services.thesisNumerics import (
    falsePositionRoot,
    goldenMinimum,
    luDecompose,
    luSolve,
    real4,
    romberg,
    secantRoot,
)
from strandSlip.services.thesisSession import ThesisSession

boundBracket = real4(0.03)  # XM-.03 and XM+0.03: REAL*4 constants


@dataclass(frozen=True)
class MacroSlipSolution:
    """The four unknowns of a half-pitch: XB1, XB2, XIH/XIC and PSIH/PSIC."""

    lowerBound: float
    upperBound: float
    slope: float
    offset: float

    def wireDisplacement(self, x: float, side: int) -> float:  # DEPH
        return macroDisplacement(x, self.lowerBound, self.slope, self.offset, side)

    def wireStrain(self, x: float, side: int) -> float:  # DR2H
        return macroStrain(x, self.lowerBound, self.slope, side)


def displacementRatio(
    deflection: Deflection, solution: MacroSlipSolution, x: float, side: int
) -> float:
    """RDEP: (core - wire) / core displacement at x."""
    return (
        deflection.coreDisplacement(x) - solution.wireDisplacement(x, side)
    ) / deflection.coreDisplacement(x)


def macroDissipation(
    deflection: Deflection, solution: MacroSlipSolution, side: int, session: ThesisSession
) -> float:
    """QROMB of DMACRO (A.45) over the macro-slip region."""

    def integrand(x: float) -> float:
        difference = abs(deflection.coreDisplacement(x) - solution.wireDisplacement(x, side))
        return 4.0 * difference

    return romberg(integrand, solution.lowerBound, solution.upperBound, session.pause)


def hardyRadius(deflection: Deflection, half: HalfPitch, session: ThesisSession):
    """HARDRHOB: bounds by the secant method, then equations 2.16 and 2.17."""
    accuracy = 1e-10  # XACC=1D-10

    def margin(x: float) -> float:
        return deflection.frictionMargin(x, half.side)

    lower = secantRoot(margin, half.start, half.middle, accuracy, session.pause)
    upper = secantRoot(margin, half.middle, half.end, accuracy, session.pause)
    offset = deflection.coreDisplacement(lower)
    slope = -(half.side * pi * (upper - lower))
    return MacroSlipSolution(lower, upper, slope, offset)


def peakDemand(deflection, half: HalfPitch) -> tuple[float, float]:
    """GOLDEN on VMIN: the largest friction demand in the half-pitch and where it is."""
    return goldenMinimum(
        lambda x: deflection.frictionPeak(x, half.side), half.start, half.middle, half.end, 1.0e-6
    )


def hardySinusoid(deflection, half: HalfPitch, peakAt: float, session: ThesisSession):
    """HARDSIN: bounds by false position either side of the peak, then 2.27 and 2.28.

    Returns None where false position had no bracket: HARDSIN carried on with
    the undefined value RTFLSP returned.
    """
    accuracy = 1.0e-9  # XACC=1.0D-9

    def margin(x: float) -> float:
        return deflection.frictionMargin(x, half.side)

    lower = falsePositionRoot(margin, half.start, peakAt, accuracy, session.pause)
    upper = falsePositionRoot(margin, peakAt, half.end, accuracy, session.pause)
    if lower is None or upper is None:
        return None
    offset = deflection.coreDisplacement(lower)
    slope = (deflection.coreDisplacement(upper) - deflection.coreDisplacement(lower)) / (
        upper - lower
    ) - half.side * pi * (upper - lower)
    return MacroSlipSolution(lower, upper, slope, offset)


def continuityGuess(deflection, half: HalfPitch, session: ThesisSession, accuracy: float):
    """APPBRN and RTFLSP: where the stuck strain meets the slipping one, either side of XM.

    Returns (XB1, XB2), or None where a bracket failed (ICONVERG=1).
    """

    def equation(x: float) -> float:
        return deflection.boundEquation(x, half)

    lower = falsePositionRoot(
        equation, half.start, half.middle - boundBracket, accuracy, session.pause
    )
    if lower is None:
        return None
    upper = falsePositionRoot(
        equation, half.middle + boundBracket, half.end, accuracy, session.pause
    )
    if upper is None:
        return None
    return lower, upper


def continuityNewton(
    deflection, half: HalfPitch, lower: float, upper: float, session: ThesisSession
) -> MacroSlipSolution | None:
    """NEWT: Newton on VCB with the Jacobian JACO, from XIC = PSIC = 0. None if it fails.

    Returns the iterate before the last correction, as the listing does.
    """
    delta = [0.0, 0.0, 0.0, 0.0]
    slope = offset = 0.0
    side = half.side
    iterations = 0
    while True:
        lower = lower + delta[0]
        upper = upper + delta[1]
        slope = slope + delta[2]
        offset = offset + delta[3]
        solution = MacroSlipSolution(lower, upper, slope, offset)
        delta = [  # VCB
            -(deflection.coreDisplacement(lower) - offset),
            -(deflection.coreStrain(lower) - slope),
            -(deflection.coreDisplacement(upper) - solution.wireDisplacement(upper, side)),
            -(deflection.coreStrain(upper) - solution.wireStrain(upper, side)),
        ]
        jacobian = [  # JACO
            [deflection.coreStrain(lower), 0.0, 0.0, -1.0],
            [deflection.coreCurvature(lower), 0.0, -1.0, 0.0],
            [
                -(side * 2.0 * pi * (lower - upper)) + slope,
                deflection.coreStrain(upper) - solution.wireStrain(upper, side),
                lower - upper,
                -1.0,
            ],
            [side * 2.0 * pi, deflection.coreCurvature(upper) - side * 2.0 * pi, -1.0, 0.0],
        ]
        pivots = luDecompose(jacobian, 4, session.pause)
        luSolve(jacobian, 4, pivots, delta)
        if lower - half.start < 0 or half.end - upper < 0 or lower > upper or iterations >= 15:
            session.write(screens.convergenceProblem)
            return None
        session.write(screens.iteration, iterations)
        session.write(screens.newtBounds, lower, upper)
        session.write(screens.newtConstants, slope, offset)
        tolerance = 1.0e-8
        if not (
            iterations == 0
            or abs(delta[0] / lower) >= tolerance
            or abs(delta[1] / upper) >= tolerance
            or abs(delta[2] / slope) >= tolerance
            or abs(delta[3] / offset) >= tolerance
        ):
            return solution
        iterations = iterations + 1
