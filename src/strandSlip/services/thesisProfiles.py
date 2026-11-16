"""Displacement, strain and friction ratio along the half-pitch: SORTIE and SORTZETA.

Both step X from XINF by 0.001 (accumulated, as X=X+DX) and print the wire's
values with and without slip; SORTIE's loop end allows 1E-9 past XSUP, so it
prints X = XSUP, while SORTZETA's (X.LE.XSUP) usually stops one step short.
SORTZETA keeps the previous row's values where X falls in no region, prints
the region each X falls in, writes the transition points to ZETA*X.DAT, and
sets the friction ratio of a macro-slip region to -1 whatever the side.
"""

from __future__ import annotations

import numpy as np

from strandSlip.models.thesisResults import SlipProfile
from strandSlip.services import thesisScreens as screens
from strandSlip.services.complianceSystem import ComplianceUnknowns, Problem, macroPortions
from strandSlip.services.macroSlipModels import MacroSlipSolution
from strandSlip.services.thesisDeflections import (
    Deflection,
    HalfPitch,
    macroDisplacement,
    macroStrain,
    pi,
)
from strandSlip.services.thesisSession import ThesisSession

profileStep = 0.001  # DX


def _profile(rows: list[tuple[float, ...]], transitions: list[tuple[float, ...]]) -> SlipProfile:
    table = np.array(rows, dtype=float).reshape(-1, 7)
    return SlipProfile(
        *(table[:, k] for k in range(7)),
        transitions=np.array(transitions, dtype=float).reshape(-1, 4),
    )


def macroSlipProfile(
    deflection: Deflection, solution: MacroSlipSolution, half: HalfPitch, session: ThesisSession
) -> SlipProfile:
    """SORTIE: stuck outside XB1..XB2 (strictly between: the wire follows DEPH)."""
    session.write(screens.profileHeading)
    rows: list[tuple[float, ...]] = []
    x = half.start
    while True:
        dame = deflection.coreDisplacement(x)
        eame = deflection.coreStrain(x)
        fame = deflection.coreCurvature(x) / (2.0 * pi)
        if x > solution.lowerBound and x < solution.upperBound:
            dfil = solution.wireDisplacement(x, half.side)
            efil = solution.wireStrain(x, half.side)
            ffil = half.side * 1.0
        else:
            dfil, efil, ffil = dame, eame, fame
        session.write(screens.profileRow, x, dfil, efil, ffil)
        rows.append((x, dame, dfil, eame, efil, fame, ffil))
        x = x + profileStep
        if not x <= half.end + 0.1e-8:
            break
    for name, core, wire in (("DEP.DAT", 1, 2), ("ELG.DAT", 3, 4), ("FRC.DAT", 5, 6)):
        session.openFile(name)
        for row in rows:
            session.writeFile(name, screens.profileFileRow, row[0], row[core], row[wire])
    return _profile(rows, [])


def _regionOf(p: Problem, u: ComplianceUnknowns, x: float, session: ThesisSession):
    """Which region X falls in, in the order SORTZETA tests them (they may overlap).

    Returns the matches as (portion, side, transition) with side "left", "right",
    "center" or "macro", and writes SORTZETA's region lines as it goes.
    """
    n, half, x1, x2 = u.regions, p.half, u.lowerBound, u.upperBound
    if n == 1:
        return [(1, "center", False)]
    if n == 2:
        found = []
        if x < x1:
            found.append((1, "left", x > x1 - profileStep and x < x1))
        if x >= x1 and x <= x2:
            found.append((2, "center", False))
        if x > x2:
            found.append((1, "right", x > x2 and x < x2 + profileStep))
        return found
    found = []
    points = u.points
    count, middle = len(points), len(points) // 2
    if x >= half.start and x < points[0]:
        found.append((1, "left", x > points[0] - profileStep and x < points[0]))
        session.write(screens.portionOne)
    for i in range(1, middle):
        if x >= points[i - 1] and x < points[i]:
            found.append((i + 1, "left", x > points[i] - profileStep and x < points[i]))
            session.write(screens.portionNumber, i + 1)
    if x >= points[middle - 1] and x < x1:
        found.append((middle + 1, "left", x > x1 - profileStep and x < x1))
        session.write(screens.portionNumber, middle + 1)
    if x >= x1 and x < x2:
        if n < macroPortions:
            found.append((n, "center", False))
        else:
            found.append((n, "macro", False))
            session.write(screens.macroRegion)
    if x >= x2 and x < points[middle]:
        session.write(screens.portionNumber, middle + 1)
        found.append((middle + 1, "right", x > x2 and x < x2 + profileStep))
    for i in range(middle + 1, count):
        portion = count - (i - 1)
        if x >= points[i - 1] and x < points[i]:
            found.append((portion, "right", x > points[i - 1] and x < points[i - 1] + profileStep))
            session.write(screens.portionNumber, portion)
    if x >= points[count - 1] and x <= half.end:
        found.append((1, "right", x > points[count - 1] and x < points[count - 1] + profileStep))
        session.write(screens.portionOne)
    return found


def _wireAt(p: Problem, u: ComplianceUnknowns, portion: int, side: str, x: float):
    """DFIL, EFIL and FFIL in one region (FFIL = -1 in a macro-slip region, as printed)."""
    if side == "macro":
        sign = p.half.side
        return (
            macroDisplacement(x, u.lowerBound, u.centerBeta, u.centerEta, sign),
            macroStrain(x, u.lowerBound, u.centerBeta, sign),
            -1.0,
        )
    if side == "center":
        beta, eta = u.centerBeta, u.centerEta
    elif side == "left":
        beta, eta = u.betaLeft[portion - 1], u.etaLeft[portion - 1]
    else:
        beta, eta = u.betaRight[portion - 1], u.etaRight[portion - 1]
    return (
        p.wire(portion, beta, eta, x),
        p.strain(portion, beta, eta, x),
        p.curvature(portion, beta, eta, x) / (2.0 * pi),
    )


def complianceProfile(p: Problem, u: ComplianceUnknowns, session: ThesisSession) -> SlipProfile:
    """SORTZETA: the profile region by region, with the transition points."""
    session.write(screens.profileHeading)
    deflection, half = p.deflection, p.half
    rows: list[tuple[float, ...]] = []
    transitions: list[tuple[float, ...]] = []
    wire = (0.0, 0.0, 0.0)  # DFIL, EFIL, FFIL: kept from the last row where X fits no region
    x = half.start
    while True:
        dame = deflection.coreDisplacement(x)
        eame = deflection.coreStrain(x)
        fame = deflection.coreCurvature(x) / (2.0 * pi)
        for portion, side, isTransition in _regionOf(p, u, x, session):
            wire = _wireAt(p, u, portion, side, x)
            if isTransition:
                transitions.append((x, *wire))
        session.write(screens.profileRow, x, *wire)
        rows.append((x, dame, wire[0], eame, wire[1], fame, wire[2]))
        x = x + profileStep
        if not x <= half.end:
            break
    for name, core, wireColumn in (
        ("ZETADEP.DAT", 1, 2),
        ("ZETAELG.DAT", 3, 4),
        ("ZETAFRC.DAT", 5, 6),
    ):
        session.openFile(name)
        for row in rows:
            session.writeFile(
                name, screens.profileRow, row[0], row[core], row[wireColumn],
                row[core] - row[wireColumn],
            )  # fmt: skip
    for name, column in (("ZETADEPX.DAT", 1), ("ZETAELGX.DAT", 2), ("ZETAFRCX.DAT", 3)):
        session.openFile(name)
        for point in transitions:
            session.writeFile(name, screens.transitionRow, point[0], point[column])
    return _profile(rows, transitions)
