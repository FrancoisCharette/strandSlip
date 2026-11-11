"""Solving one half-pitch with the compliance model (ZETARHOB and ZETASIN).

The number of regions grows from one until the relative displacement at the
centre of the half-pitch fits the last portion used (the check after label
990); each step solves the system of `complianceSystem` by Newton (NEWTON)
from the approximations of APPROX or APPSIN, then DISPENRG integrates the
energy of every region.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from masterRebuild.services import thesisScreens as screens
from masterRebuild.services.analysisErrors import AnalysisError
from masterRebuild.services.complianceSystem import (
    ComplianceUnknowns,
    Problem,
    jacobian,
    macroPortions,
    residuals,
)
from masterRebuild.services.thesisDeflections import (
    ConstantRadius,
    decayMinus,
    decayPlus,
    macroDisplacement,
    pi,
)
from masterRebuild.services.thesisNumerics import luDecompose, luSolve, romberg
from masterRebuild.services.thesisSession import ThesisSession


def nearestWhole(value: float) -> float:
    """DNINT: halves away from zero."""
    return float(math.floor(value + 0.5)) if value >= 0 else float(math.ceil(value - 0.5))


def _stillMoving(delta: list[float], u: ComplianceUnknowns, iterations: int) -> bool:
    """NEWTON's tolerance block: True where it says GOTO 980."""
    tolerance = 1.0e-10
    if iterations == 0:
        return True
    m = u.regions - 1
    for i in range(m):
        if abs(delta[i] / u.betaLeft[i]) >= tolerance:
            return True
        if abs(delta[i + m] / u.etaLeft[i]) >= tolerance:
            return True
        if abs(delta[i + 2 * m] / u.betaRight[i]) >= tolerance:
            return True
        if abs(delta[i + 3 * m] / u.etaRight[i]) >= tolerance:
            return True
    for i, point in enumerate(u.points):
        if abs(delta[i + 4 * m] / point) >= tolerance:
            return True
    size = u.size
    return (
        abs(delta[size - 4] / u.lowerBound) >= tolerance
        or abs(delta[size - 3] / u.upperBound) >= tolerance
        or abs(delta[size - 2] / u.centerBeta) >= tolerance
        or abs(delta[size - 1] / u.centerEta) >= tolerance
    )


def _logIteration(p: Problem, u: ComplianceUnknowns, iterations: int, session) -> None:
    half, points = p.half, u.points
    pairs = [(i, len(points) - 1 - i) for i in range(len(points) // 2)]
    session.write(screens.iteration, iterations)
    session.write(screens.newtonBounds, u.lowerBound, u.upperBound)
    for i, j in pairs:
        session.write(screens.newtonPoints, i + 1, points[i], j + 1, points[j])
    session.write(screens.newtonOffsets, u.lowerBound - half.start, half.end - u.upperBound)
    for i, j in pairs:
        session.write(
            screens.newtonPointOffsets, i + 1, points[i] - half.start, j + 1, half.end - points[j]
        )


def newton(p: Problem, u: ComplianceUnknowns, session: ThesisSession) -> bool:
    """NEWTON: True if it converged, False after printing the convergence problem."""
    half, m, size = p.half, u.regions - 1, u.size
    delta = [0.0] * size
    iterations = 0
    while True:
        for i in range(m):
            u.betaLeft[i] = u.betaLeft[i] + delta[i]
            u.etaLeft[i] = u.etaLeft[i] + delta[i + m]
            u.betaRight[i] = u.betaRight[i] + delta[i + 2 * m]
            u.etaRight[i] = u.etaRight[i] + delta[i + 3 * m]
        negative = False
        for i in range(len(u.points)):
            u.points[i] = u.points[i] + delta[i + 4 * m]
            if u.points[i] < 0.0:
                negative = True  # IERROR=1, GOTO 750
                break
        if not negative:
            u.lowerBound = u.lowerBound + delta[size - 4]
            u.upperBound = u.upperBound + delta[size - 3]
            u.centerBeta = u.centerBeta + delta[size - 2]
            u.centerEta = u.centerEta + delta[size - 1]
            delta = residuals(p, u)
            a = jacobian(p, u)
            luSolve(a, size, luDecompose(a, size, session.pause), delta)
            if (
                u.lowerBound - half.start < 0
                or half.end - u.upperBound < 0
                or half.end - u.lowerBound < 0
                or u.upperBound - half.start < 0
                or u.lowerBound > u.upperBound
                or iterations == 14
            ):
                session.write(screens.convergenceProblem)
                return False
        points = u.points
        for i in range(len(points) // 2):  # 750
            j = len(points) - 1 - i
            if (
                points[i] - half.start < 0
                or half.end - points[j] < 0
                or points[j] - half.start < 0
                or points[i] > points[j]
                or negative
            ):
                session.write(screens.convergenceProblem)
                return False
        _logIteration(p, u, iterations, session)
        if not _stillMoving(delta, u, iterations):
            return True
        iterations = iterations + 1
        if iterations > 15:
            return True


def singleRegion(p: Problem, session: ThesisSession) -> tuple[float, float]:
    """UNRES: BTM and ETM when the whole half-pitch is one micro-slip region (ZETASIN)."""
    c, curve, half = p.compliance, p.curve, p.half
    zeta = curve.zeta[0]
    a = [
        [decayPlus(c, half.start, zeta), decayMinus(c, half.start, zeta)],
        [decayPlus(c, half.end, zeta), decayMinus(c, half.end, zeta)],
    ]
    core = p.deflection.coreDisplacement
    b = [
        core(half.start) - p.wire(1, curve.xComp[0], curve.yComp[0], half.start),
        core(half.end) - p.wire(1, curve.xComp[0], curve.yComp[0], half.end),
    ]
    luSolve(a, 2, luDecompose(a, 2, session.pause), b)
    return b[0], b[1]


def firstBoundGuess(p: Problem, regions: int, session: ThesisSession, retry: bool):
    """APPROX or APPSIN: XB1C (XB1 - XINF), and the ratio XB2 is placed with.

    After Newton failed (`retry`), the program shows its guess and reads another.
    """
    lastFull = regions if regions != macroPortions else regions - 1  # NPORTEMP
    curve, c, half = p.curve, p.compliance, p.half
    zetaPrime = curve.xComp[lastFull - 1] / curve.yComp[lastFull - 1]
    if isinstance(p.deflection, ConstantRadius):
        factor = (c.gamma * zetaPrime + 1.0) / c.strainFactor
        ratio, tried = 1.0, screens.triedRadius
    else:
        sinusoid = p.deflection
        frequency = (2.0 * pi) / sinusoid.wavelength
        radius = 1.0 / abs(-(sinusoid.amplitude * math.sin(frequency * half.end)))
        if half.start < 1:  # IF(XINF.LT.0001): 0001 is the integer 1
            startRadius = 1.0
        else:
            startRadius = 1.0 / abs(-(sinusoid.amplitude * math.sin(frequency * half.start)))
        factor = radius * (c.gamma * zetaPrime + 1.0)
        ratio, tried = radius / startRadius, screens.triedSinusoid
    cosine = factor * -curve.yComp[lastFull - 1]
    if not -1.0 <= cosine <= 1.0:
        raise AnalysisError(
            f"The automatic approximation of XB1 needs the arc cosine of {cosine:.6g}, "
            "outside -1..1: the 1992 program stopped here on a math DOMAIN error. "
            "The deflection is too small or too large for this model."
        )
    guess = (math.acos(cosine) - pi / 2.0) / (2.0 * pi)
    if retry:
        session.write(tried, guess)
        guess = session.askApproximation(
            screens.approximationPrompt,
            f"Newton did not converge from the approximation XB1C = {guess:.8g} "
            f"(half lay length {half.start:g} to {half.end:g}, {regions} regions). The program "
            "asks for another approximation of XB1C, the distance from XINF to the first "
            "bound; it is usually smaller.",
        )
    return guess, ratio


def startingPoint(p: Problem, regions: int, session: ThesisSession, retry: bool):
    """Label 500 and the approximation routine: everything zero, then the guesses."""
    u = ComplianceUnknowns(regions)
    guess, ratio = firstBoundGuess(p, regions, session, retry)
    half, curve = p.half, p.curve
    u.lowerBound = guess + half.start
    if ratio == 1.0 and isinstance(p.deflection, ConstantRadius):
        u.upperBound = half.end - guess
    else:
        u.upperBound = half.end - (guess * ratio)
    lastFull = regions if regions != macroPortions else regions - 1
    count = len(u.points)
    for i in range(1, count // 2 + 1):
        offset = (curve.xComp[i] / curve.xComp[lastFull]) * guess
        u.points[i - 1] = offset + half.start
        u.points[count - i] = half.end - offset
    return u


@dataclass(frozen=True)
class HalfPitchCompliance:
    """The solution the portion loop stopped at."""

    unknowns: ComplianceUnknowns
    centerDifference: float  # DFDEP: 4 pi (core - wire) / GAM1 at XM
    ratio: float  # RDEP
    printedPoints: int  # NPOINT as INCONNUS.DAT prints it


def centerDifference(p: Problem, u: ComplianceUnknowns) -> tuple[float, float]:
    """DFDEP (signed) and RDEP at the middle of the half-pitch."""
    core, half, c = p.deflection.coreDisplacement, p.half, p.compliance
    if u.regions < macroPortions:
        wire = p.wire(u.regions, u.centerBeta, u.centerEta, half.middle)
    else:
        wire = macroDisplacement(half.middle, u.lowerBound, u.centerBeta, u.centerEta, half.side)
    difference = ((core(half.middle) - wire) / c.gamma) * 4.0 * pi
    return difference, (core(half.middle) - wire) / core(half.middle)


def _solveRegions(p: Problem, regions: int, session: ThesisSession, retry: bool = False):
    """Label 500 to 990 for two regions or more: guesses, Newton, and again on failure."""
    while True:
        u = startingPoint(p, regions, session, retry)
        if newton(p, u, session):
            return u
        retry = True


def solveHalfPitch(
    p: Problem, session: ThesisSession, sinusoid: bool, startRegions: int = 0
) -> HalfPitchCompliance:
    """Labels 1000 to the portion check: add regions until the centre's 2δ fits.

    ZETARHOB starts from one region with BTM = ETM = 0 (never assigned: DOS left
    them zero); ZETASIN solves that case with UNRES and carries the count from
    one half-pitch to the next (`startRegions`).
    """
    regions = startRegions
    while True:
        regions = regions + 1
        if regions == 1:
            u = ComplianceUnknowns(1)
            if sinusoid:
                u.centerBeta, u.centerEta = singleRegion(p, session)
        else:
            u = _solveRegions(p, regions, session)
        difference, ratio = centerDifference(p, u)
        lastFull = regions if regions < macroPortions else regions - 1
        limit = p.curve.xComp[lastFull]  # XCOMP(NPORTEMP+1): the δ the last portion allows
        session.write(
            screens.portionsSinusoid if sinusoid else screens.portionsRadius,
            regions,
            abs(difference),
            limit * (2.0),
        )
        if not ((abs(difference) - 2.0 * limit) > 0.0 and regions < macroPortions):
            break
    printedPoints = 2 * (regions - 2) if (sinusoid or regions != 1) else 0
    return HalfPitchCompliance(u, abs(difference), ratio, printedPoints)


def microIntegrand(p: Problem, portion: int, beta: float, eta: float, session: ThesisSession):
    """DMICRO (A.51) for one micro-slip region: the energy density of partial slip."""
    c, core = p.compliance, p.deflection.coreDisplacement
    exponent, inverse = (c.en + 1.0) / c.en, 1.0 / c.en

    def integrand(x: float) -> float:
        share = (4.0 * pi * abs(core(x) - p.wire(portion, beta, eta, x))) / (3.0 * c.gamma)
        scale = (6.0 * c.gamma) / ((c.en + 1.0) * pi)
        if share > 1.0:
            share = nearestWhole(share)
        if share > 1.0:
            session.write(screens.dmicroWarning, share, 1.0)
            session.pause(screens.pressEnter)
            share = 1.0
        tmp1 = 1.0 - (1.0 - share) ** exponent
        tmp2 = ((c.en + 1.0) - (((c.en + 1.0) / 2.0) * share)) * (1.0 - (1.0 - share) ** inverse)
        return scale * (tmp1 - tmp2)

    return integrand


@dataclass(frozen=True)
class RegionEnergies:
    """DISPENRG: what ENERGY.DAT holds for one half-pitch."""

    regions: tuple[tuple[int, float], ...]  # (number as written, energy)
    total: float  # DSP
    macroRegion: float | None = None  # DSPMAC: all the energy of the macro-slip region
    microInMacro: float | None = None  # DMICMAC: its micro-slip share

    @property
    def macroOnly(self) -> float | None:  # DMAC
        if self.macroRegion is None or self.microInMacro is None:
            return None
        return self.macroRegion - self.microInMacro

    @property
    def microOnly(self) -> float:  # DMIC (all micro-slip energy), or DSP without macro-slip
        if self.macroRegion is None or self.microInMacro is None:
            return self.total
        return self.total - self.macroRegion + self.microInMacro


def dissipation(p: Problem, u: ComplianceUnknowns, session: ThesisSession) -> RegionEnergies:
    """DISPENRG: integrate every region from INF to SUP, in the listing's order."""
    n, half, c = u.regions, p.half, p.compliance

    def micro(portion: int, beta: float, eta: float, a: float, b: float) -> float:
        return romberg(microIntegrand(p, portion, beta, eta, session), a, b, session.pause)

    if n == 1:
        total = micro(1, u.centerBeta, u.centerEta, half.start, half.end)
        return RegionEnergies(((1, total),), total)
    x1, x2 = u.lowerBound, u.upperBound
    if n == 2:
        energies = [
            micro(1, u.betaLeft[0], u.etaLeft[0], half.start, x1),
            micro(2, u.centerBeta, u.centerEta, x1, x2),
            micro(1, u.betaRight[0], u.etaRight[0], x2, half.end),
        ]
        total = 0.0
        for energy in energies:
            total = total + energy
        return RegionEnergies(tuple(zip((1, 2, 3), energies, strict=True)), total)
    points, half2 = u.points, len(u.points) // 2
    written: list[tuple[int, float]] = []
    total = 0.0
    number = 1
    edges = [half.start, *points[:half2], x1]
    for k in range(1, half2 + 2):  # left side: portion k from edges[k-1] to edges[k]
        energy = micro(k, u.betaLeft[k - 1], u.etaLeft[k - 1], edges[k - 1], edges[k])
        total = total + energy
        written.append((number, energy))
        number = number + 1
    macroRegion = microInMacro = None
    if n < macroPortions:
        energy = micro(n, u.centerBeta, u.centerEta, x1, x2)
        total = total + energy
        written.append((n, energy))
    else:
        side = half.side

        def macroIntegrand(x: float) -> float:
            core = p.deflection.coreDisplacement(x)
            return 4.0 * abs(core - macroDisplacement(x, x1, u.centerBeta, u.centerEta, side))

        integral = romberg(macroIntegrand, x1, x2, session.pause)
        macroRegion = integral + ((6.0 * c.gamma) / pi) * (1.0 / (c.en + 1.0) - 1) * (x2 - x1)
        microInMacro = ((6.0 * c.gamma) / pi) * (1.0 / (c.en + 1.0) - 0.5) * (x2 - x1)
        total = total + macroRegion
        written.append((n, macroRegion))
    number = number + 1  # IREGION=IREGION+2 after the centre
    edges = [x2, *points[half2:], half.end]
    for k in range(half2 + 1, 0, -1):  # right side: portion k, from the centre outwards
        start, end = edges[half2 + 1 - k], edges[half2 + 2 - k]
        energy = micro(k, u.betaRight[k - 1], u.etaRight[k - 1], start, end)
        total = total + energy
        written.append((number, energy))
        number = number + 1
    return RegionEnergies(tuple(written), total, macroRegion, microInMacro)
