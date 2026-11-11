"""The compliance model's nonlinear system: COMP, VECB, JACOB, NEWTON and UNRES.

With compliance, the friction force grows with the relative displacement δ
along a curve f(δ) cut into ten linear portions (COMP). A half-pitch with n
regions has n - 1 micro-slip regions on each side of a central one, joined at
2(n - 2) transition points XK and the bounds XB1, XB2; the central region is
a micro-slip region of portion n, or macro-slip when n = 11. Each micro-slip
region carries two constants (BETA, ETA) of e^{±x sqrt(GAMEXP/ZETA)}.

The unknowns, in the listing's column order: BETAG(1..n-1), ETAG, BETAD, ETAD,
XK(1..2(n-2)), XB1, XB2, BTM, ETM - 6n - 4 of them. The residuals (VECB) and
the Jacobian (JACOB) are the listing's, entry for entry.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from masterRebuild.services.thesisDeflections import (
    Compliance,
    Deflection,
    HalfPitch,
    decayMinus,
    decayMinusSlope,
    decayPlus,
    decayPlusSlope,
    macroDisplacement,
    macroStrain,
    pi,
)

curvePortions = 10  # NMAX: COMP is always called with 10
macroPortions = 11  # NPORTION = 11: the central region slips


@dataclass(frozen=True)
class ComplianceCurve:
    """COMP: the ten linear portions of the f(δ) curve; index 0 is portion 1."""

    xComp: tuple[float, ...]  # XCOMP(1..11)
    yComp: tuple[float, ...]  # YCOMP(1..11)
    zeta: tuple[float, ...]  # ZETA(1..10): the inverse slope of each portion


def complianceCurve(en: float, portions: int = curvePortions) -> ComplianceCurve:
    xComp = [0.0] * (portions + 1)
    yComp = [0.0] * (portions + 1)
    zeta = [0.0] * portions
    step = 1.0 / portions
    for i in range(1, portions + 1):
        yComp[i] = yComp[i - 1] + step
        if i == portions:
            yComp[i] = 1.0
    for i in range(1, portions + 1):
        yComp[i] = (yComp[i] + (1.5 * i - 1.0)) / (1.5 * i)
        xComp[i] = (3.0 / 2.0) * (1.0 - (1.0 - yComp[i]) ** en)
        zeta[i - 1] = (xComp[i] - xComp[i - 1]) / (yComp[i] - yComp[i - 1])
    return ComplianceCurve(tuple(xComp), tuple(yComp), tuple(zeta))


@dataclass
class ComplianceUnknowns:
    """One half-pitch's unknowns for `regions` (NPORTION) regions."""

    regions: int
    betaLeft: list[float] = field(default_factory=list)  # BETAG
    etaLeft: list[float] = field(default_factory=list)  # ETAG
    betaRight: list[float] = field(default_factory=list)  # BETAD
    etaRight: list[float] = field(default_factory=list)  # ETAD
    points: list[float] = field(default_factory=list)  # XK
    lowerBound: float = 0.0  # XB1
    upperBound: float = 0.0  # XB2
    centerBeta: float = 0.0  # BTM
    centerEta: float = 0.0  # ETM

    def __post_init__(self) -> None:
        sides = max(0, self.regions - 1)
        for name in ("betaLeft", "etaLeft", "betaRight", "etaRight"):
            if not getattr(self, name):
                setattr(self, name, [0.0] * sides)
        if not self.points:
            self.points = [0.0] * max(0, 2 * (self.regions - 2))

    @property
    def size(self) -> int:  # JDIM
        return 6 * self.regions - 4


@dataclass(frozen=True)
class Problem:
    """What VECB and JACOB read from COMMON: the deflection, its constants, the half-pitch."""

    deflection: Deflection
    compliance: Compliance
    curve: ComplianceCurve
    half: HalfPitch

    def wire(self, portion: int, beta: float, eta: float, x: float) -> float:  # DEPFIL
        c, curve = self.compliance, self.curve
        return self.deflection.wireDisplacement(
            c, self.half.side, curve.xComp[portion - 1], curve.yComp[portion - 1],
            curve.zeta[portion - 1], beta, eta, x,
        )  # fmt: skip

    def strain(self, portion: int, beta: float, eta: float, x: float) -> float:  # ELGFIL
        zeta = self.curve.zeta[portion - 1]
        return self.deflection.wireStrain(self.compliance, zeta, beta, eta, x)

    def curvature(self, portion: int, beta: float, eta: float, x: float) -> float:  # FRCFIL
        zeta = self.curve.zeta[portion - 1]
        return self.deflection.wireCurvature(self.compliance, zeta, beta, eta, x)

    def offsetTerm(self, portion: int) -> float:  # 2 ICOTE (GAM1/4 PI) XCOMP(portion)
        return (
            2.0
            * self.half.side
            * (self.compliance.gamma / (4.0 * pi))
            * self.curve.xComp[portion - 1]
        )


def residuals(p: Problem, u: ComplianceUnknowns) -> list[float]:
    """VECB: minus the boundary conditions 3.36-3.52, in the Jacobian's row order."""
    n, half, core = u.regions, p.half, p.deflection.coreDisplacement
    b = [0.0] * u.size
    b[0] = -(core(half.start) - p.wire(1, u.betaLeft[0], u.etaLeft[0], half.start))  # 3.51
    b[1] = -(core(half.end) - p.wire(1, u.betaRight[0], u.etaRight[0], half.end))  # 3.52
    row = 2
    for beta, eta, right in ((u.betaLeft, u.etaLeft, False), (u.betaRight, u.etaRight, True)):
        for i in range(1, n - 1):
            x = u.points[len(u.points) - i] if right else u.points[i - 1]
            b[row] = -(p.wire(i, beta[i - 1], eta[i - 1], x) - p.wire(i + 1, beta[i], eta[i], x))
            b[row + 1] = -(
                p.strain(i, beta[i - 1], eta[i - 1], x) - p.strain(i + 1, beta[i], eta[i], x)
            )
            b[row + 2] = -(core(x) - p.wire(i, beta[i - 1], eta[i - 1], x) + p.offsetTerm(i + 1))
            row += 3
    m, x1, x2 = n - 1, u.lowerBound, u.upperBound
    left = (u.betaLeft[m - 1], u.etaLeft[m - 1])
    rightSide = (u.betaRight[m - 1], u.etaRight[m - 1])
    if n != macroPortions:  # 3.39-3.44: the central region is micro-slip, portion n
        center = (u.centerBeta, u.centerEta)
        b[row] = -(p.wire(m, *left, x1) - p.wire(n, *center, x1))
        b[row + 1] = -(p.strain(m, *left, x1) - p.strain(n, *center, x1))
        b[row + 3] = -(p.wire(m, *rightSide, x2) - p.wire(n, *center, x2))
        b[row + 4] = -(p.strain(m, *rightSide, x2) - p.strain(n, *center, x2))
    else:  # 3.45-3.50: macro-slip, the wire follows DEPH from XB1
        side = half.side
        b[row] = -(
            p.wire(m, *left, x1) - macroDisplacement(x1, x1, u.centerBeta, u.centerEta, side)
        )
        b[row + 1] = -(p.strain(m, *left, x1) - macroStrain(x1, x1, u.centerBeta, side))
        b[row + 3] = -(
            p.wire(m, *rightSide, x2) - macroDisplacement(x2, x1, u.centerBeta, u.centerEta, side)
        )
        b[row + 4] = -(p.strain(m, *rightSide, x2) - macroStrain(x2, x1, u.centerBeta, side))
    b[row + 2] = -(core(x1) - p.wire(m, *left, x1) + p.offsetTerm(n))
    b[row + 5] = -(core(x2) - p.wire(m, *rightSide, x2) + p.offsetTerm(n))
    return b


def jacobian(p: Problem, u: ComplianceUnknowns) -> list[list[float]]:
    """JACOB: the derivatives of the residuals, entry for entry; rows as in `residuals`."""
    n, size, half, c = u.regions, u.size, p.half, p.compliance
    m = n - 1
    a = [[0.0] * size for _ in range(size)]
    zeta = p.curve.zeta
    xb1Column, xb2Column, betaColumn, etaColumn = size - 4, size - 3, size - 2, size - 1
    a[0][0] = -decayPlus(c, half.start, zeta[0])  # 3.51
    a[0][m] = -decayMinus(c, half.start, zeta[0])
    a[1][2 * m] = -decayPlus(c, half.end, zeta[0])  # 3.52
    a[1][3 * m] = -decayMinus(c, half.end, zeta[0])
    row = 2
    for first, beta, eta, right in (
        (0, u.betaLeft, u.etaLeft, False),
        (2 * m, u.betaRight, u.etaRight, True),
    ):
        for k in range(1, n - 1):
            point = len(u.points) + 1 - k if right else k  # XK(JPOINT) or XK(IPOINT)
            x = u.points[point - 1]
            pointColumn = 4 * m + point - 1
            for offset, plus, minus, derived in (
                (0, decayPlus, decayMinus, p.strain),  # 3.36: displacements meet
                (1, decayPlusSlope, decayMinusSlope, p.curvature),  # 3.37: strains meet
            ):
                for q, sign in ((k, 1), (k + 1, -1)):
                    a[row + offset][first + q - 1] = sign * plus(c, x, zeta[q - 1])
                    a[row + offset][first + q - 1 + m] = sign * minus(c, x, zeta[q - 1])
                a[row + offset][pointColumn] = derived(k, beta[k - 1], eta[k - 1], x) - derived(
                    k + 1, beta[k], eta[k], x
                )
            a[row + 2][first + k - 1] = -decayPlus(c, x, zeta[k - 1])  # 3.38
            a[row + 2][first + k - 1 + m] = -decayMinus(c, x, zeta[k - 1])
            a[row + 2][pointColumn] = p.deflection.coreStrain(x) - p.strain(
                k, beta[k - 1], eta[k - 1], x
            )
            row += 3
    zl, zn = zeta[m - 1], zeta[n - 1] if n <= len(zeta) else 0.0
    for offset, x, beta, eta, boundColumn, first in (
        (0, u.lowerBound, u.betaLeft[m - 1], u.etaLeft[m - 1], xb1Column, m - 1),
        (3, u.upperBound, u.betaRight[m - 1], u.etaRight[m - 1], xb2Column, 3 * m - 1),
    ):
        r = row + offset
        a[r][first] = decayPlus(c, x, zl)
        a[r][first + m] = decayMinus(c, x, zl)
        a[r + 1][first] = decayPlusSlope(c, x, zl)
        a[r + 1][first + m] = decayMinusSlope(c, x, zl)
        a[r + 2][first] = -decayPlus(c, x, zl)
        a[r + 2][first + m] = -decayMinus(c, x, zl)
        a[r + 2][boundColumn] = p.deflection.coreStrain(x) - p.strain(m, beta, eta, x)
        if n != macroPortions:  # 3.39-3.44
            center = (u.centerBeta, u.centerEta)
            a[r][boundColumn] = p.strain(m, beta, eta, x) - p.strain(n, *center, x)
            a[r][betaColumn] = -decayPlus(c, x, zn)
            a[r][etaColumn] = -decayMinus(c, x, zn)
            a[r + 1][boundColumn] = p.curvature(m, beta, eta, x) - p.curvature(n, *center, x)
            a[r + 1][betaColumn] = -decayPlusSlope(c, x, zn)
            a[r + 1][etaColumn] = -decayMinusSlope(c, x, zn)
    if n == macroPortions:  # 3.45-3.50
        x1, x2, side = u.lowerBound, u.upperBound, half.side
        betaL, etaL = u.betaLeft[m - 1], u.etaLeft[m - 1]
        betaR, etaR = u.betaRight[m - 1], u.etaRight[m - 1]
        a[row][xb1Column] = p.strain(m, betaL, etaL, x1)
        a[row][etaColumn] = -1.0
        a[row + 1][xb1Column] = p.curvature(m, betaL, etaL, x1)
        a[row + 1][betaColumn] = -1.0
        a[row + 3][xb1Column] = side * (2.0 * pi) * (x2 - x1) + u.centerBeta
        a[row + 3][xb2Column] = p.strain(m, betaR, etaR, x2) - macroStrain(
            x2, x1, u.centerBeta, side
        )
        a[row + 3][betaColumn] = -(x2 - x1)
        a[row + 3][etaColumn] = -1.0
        a[row + 4][xb1Column] = side * 2.0 * pi
        a[row + 4][xb2Column] = p.curvature(m, betaR, etaR, x2) - side * 2.0 * pi
        a[row + 4][betaColumn] = -1.0
    return a
