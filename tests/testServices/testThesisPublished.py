"""The 1992 programs against the numbers the thesis and the program manual print.

Chapter 6 of the thesis tabulates bounds and dissipated energies (tables 6.1
and 6.2, θi = 90°, γ1 = 0.06, Λ = 28); the manual quotes the approximations
APPROX and APPSIN try. Where the thesis disagrees with the programs, the test
says why the thesis is the one that slipped.
"""

from __future__ import annotations

import math

import pytest

from masterRebuild.models.thesisInput import SinusoidChoice, ThesisInput
from masterRebuild.models.thesisProgram import (
    CONTRHOB,
    CONTSIN,
    HARDRHOB,
    HARDSIN,
    ZETARHOB,
    ZETASIN,
)
from masterRebuild.services.thesisRunner import runThesisProgram

whole, ratio, one = (
    SinusoidChoice.wholeWavelength,
    SinusoidChoice.displacementRatio,
    SinusoidChoice.oneHalfPitch,
)


def rounded(value: float, decimals: int) -> float:
    return round(value, decimals)


def runOne(program, **values):
    result = runThesisProgram(program, ThesisInput(profile=False, **values))
    assert result.pendingQuestion is None, result.pendingQuestion
    return result


# -- table 6.1: constant radius of curvature, half-pitch 0.0 to 0.5 ------------------------


def testTable61HardyModel() -> None:
    at08 = runOne(HARDRHOB, radius=0.8).halfPitches[0]
    assert (rounded(at08.lowerBound, 5), rounded(at08.upperBound, 5)) == (0.14758, 0.35242)
    assert rounded(at08.energy, 6) == 0.003582
    at06 = runOne(HARDRHOB, radius=0.6).halfPitches[0]
    assert rounded(at06.lowerBound, 5) == 0.10242
    assert rounded(at06.energy, 6) == 0.028421
    # Table 6.1(c) prints B2 = 0.39754; the bounds are symmetric (B1 + B2 = 0.5, as at 0.8).
    assert rounded(at06.upperBound, 5) == 0.39758
    assert at06.lowerBound + at06.upperBound == pytest.approx(0.5, abs=1e-12)


def testHardyBoundsAreWhereTheFrictionDemandReachesTheLimit() -> None:
    """cos(2πX + π/2) = -ρ̄ on the first half-pitch: X = asin(ρ̄) / 2π."""
    for radius in (0.3, 0.6, 0.8, 0.95):
        half = runOne(HARDRHOB, radius=radius).halfPitches[0]
        assert half.lowerBound == pytest.approx(math.asin(radius) / (2 * math.pi), abs=1e-10)


def complianceBreakdown(half) -> tuple[float, float, float, float]:
    """The table's four energies: micro-slip regions, micro in macro, macro, total."""
    if half.macroRegionEnergy is None:
        return half.energy, 0.0, 0.0, half.energy
    micro = half.energy - half.macroRegionEnergy
    return micro, half.microInMacroEnergy, half.macroEnergy, half.energy


def testTable61ComplianceModel() -> None:
    at10 = runOne(ZETARHOB, radius=1.0, compliance=0.06).halfPitches[0]
    assert at10.macroRegionEnergy is None and rounded(at10.energy, 6) == 0.000916
    at08 = runOne(ZETARHOB, radius=0.8, compliance=0.06).halfPitches[0]
    assert (rounded(at08.lowerBound, 5), rounded(at08.upperBound, 5)) == (0.15124, 0.34876)
    assert [rounded(e, 6) for e in complianceBreakdown(at08)[:3]] == [0.000681, 0.002264, 0.003269]
    # The table's total, 0.006214, is the sum of its three rounded parts; the energy is 0.0062132.
    assert rounded(at08.energy, 7) == 0.0062132
    # At 0.6 APPROX's guess does not converge; any guess from 0.03 to 0.08 reaches the same root.
    at06 = runThesisProgram(
        ZETARHOB, ThesisInput(radius=0.6, compliance=0.06, approximations=(0.05,), profile=False)
    ).halfPitches[0]
    assert (rounded(at06.lowerBound, 5), rounded(at06.upperBound, 5)) == (0.05238, 0.44762)
    breakdown = [rounded(e, 6) for e in complianceBreakdown(at06)]
    assert breakdown == [0.000227, 0.004529, 0.05476, 0.059516]


def testTheManualsApproxExample() -> None:
    """Manual section 1.3: γ1 = 0.06, ρ̄ = 0.7: APPROX tries 0.136284, which fails; 0.10 works."""
    stopped = runThesisProgram(ZETARHOB, ThesisInput(radius=0.7, compliance=0.06))
    assert stopped.pendingQuestion
    tried = [line for line in stopped.console if "essayee" in line]
    assert tried and "0.13628377D+00" in tried[0]
    solved = runThesisProgram(
        ZETARHOB, ThesisInput(radius=0.7, compliance=0.06, approximations=(0.10,))
    )
    assert solved.pendingQuestion is None and solved.approximationsUsed == (0.10,)


# -- table 6.2: sinusoid, Λ = 28 ----------------------------------------------------------


def testTable62HardyModel() -> None:
    assert rounded(runOne(HARDSIN, choice=whole, amplitude=1.3).totalEnergy, 6) == 0.066745
    near = runOne(HARDSIN, choice=one, amplitude=1.3, turns=6.5).halfPitches[0]
    assert (rounded(near.lowerBound, 5), rounded(near.upperBound, 5)) == (6.64076, 6.8604)
    assert rounded(runOne(HARDSIN, choice=whole, amplitude=2.0).totalEnergy, 5) == 1.20146
    near = runOne(HARDSIN, choice=one, amplitude=2.0, turns=6.5).halfPitches[0]
    assert rounded(near.upperBound, 5) == 6.91676
    # Table 6.2(c) prints B1 = 6.58430; the root of the friction equation is 6.584266
    # (false position and bisection agree to 1E-10).
    assert near.lowerBound == pytest.approx(6.5842662360, abs=1e-9)


def testTable62ComplianceModel() -> None:
    assert rounded(runOne(ZETASIN, choice=whole, amplitude=1.0).totalEnergy, 6) == 0.019013
    near = runOne(ZETASIN, choice=one, amplitude=1.3, turns=6.5).halfPitches[0]
    # The table's B1 = 6.63290 is 6.6328945 rounded twice (to 6.632895, then 6.63290).
    assert rounded(near.lowerBound, 7) == 6.6328945
    assert rounded(near.upperBound, 5) == 6.86815
    # Section 6.1.2: Ā = 1.4, half-pitch 6.5 to 7.0: B1 - INF = 0.10224, SUP - B2 = 0.10129.
    near = runOne(ZETASIN, choice=one, amplitude=1.4, turns=6.5).halfPitches[0]
    assert rounded(near.lowerBound - 6.5, 5) == 0.10224
    assert rounded(7.0 - near.upperBound, 5) == 0.10129


def testTable62bNeedsTheRootTheAuthorTyped() -> None:
    """At Ā = 1.3, half-pitch 4.5 needs two typed approximations; the second picks the root.

    From 0.205 Newton finds a macro-slip region 0.0156 wide and the total is the
    table's 0.130465; from 0.2 it finds one of zero width and 0.130459.
    """
    result = runOne(ZETASIN, choice=whole, amplitude=1.3, approximations=(0.149174136, 0.205))
    assert rounded(result.totalEnergy, 6) == 0.130465
    parts = [complianceBreakdown(h) for h in result.halfPitches]
    sums = [4 * sum(p[k] for p in parts) for k in range(3)]
    assert [rounded(s, 6) for s in sums] == [0.030183, 0.037458, 0.062824]


def testTheManualsAppsinExamples() -> None:
    """Manual section 2.3: γ1 = 0.06, Λ = 28, Ā = 2.0 - APPSIN's tries and what converged."""
    for turns, tried, typed in ((2.5, "0.16647710D+00", 0.19), (3.5, "0.12122923D+00", 0.10)):
        values = dict(choice=one, amplitude=2.0, turns=turns, profile=False)
        stopped = runThesisProgram(ZETASIN, ThesisInput(**values))
        assert any(tried in line for line in stopped.console if "essayée" in line)
        solved = runThesisProgram(ZETASIN, ThesisInput(approximations=(typed,), **values))
        assert solved.pendingQuestion is None


def testTable62cBoundsMacroAndMicro() -> None:
    """Ā = 2.0 over the wavelength, with the approximations the manual's advice leads to.

    Bounds, macro-slip and micro-slip energies match; the micro-in-macro sum is
    0.148457 where the table has 0.148658 and its total (2.455337) carries the
    same 0.0002, with no borderline decision in the run to explain it.
    """
    typed = (0.19, 0.097, 0.066, 0.061, 0.048, 0.047, 0.037, 0.036)
    result = runOne(ZETASIN, choice=whole, amplitude=2.0, approximations=typed)
    near = result.halfPitches[-1]
    assert (rounded(near.lowerBound, 5), rounded(near.upperBound, 5)) == (6.52766, 6.97265)
    parts = [complianceBreakdown(h) for h in result.halfPitches]
    micro, microInMacro, macro = (4 * sum(p[k] for p in parts) for k in range(3))
    assert rounded(macro, 6) == 2.289676
    assert rounded(micro, 5) == 0.01700
    assert rounded(microInMacro, 6) == 0.148457


# -- physics ------------------------------------------------------------------------------


def testContinuityWidensTheMacroSlipRegionAndKeepsStrainContinuous() -> None:
    """Section 6.1.1.4: no concentrated reactions, so a larger region than Hardy's."""
    hardy = runOne(HARDRHOB, radius=0.8).halfPitches[0]
    result = runThesisProgram(CONTRHOB, ThesisInput(radius=0.8))
    continuity = result.halfPitches[0]
    assert continuity.lowerBound < hardy.lowerBound and continuity.upperBound > hardy.upperBound
    profile = result.profile
    inside = (profile.x > continuity.lowerBound) & (profile.x < continuity.upperBound)
    jumps = abs(profile.wireStrain[1:] - profile.wireStrain[:-1])
    assert jumps.max() < 0.02  # Hardy's model jumps at its bounds; this one does not
    assert inside.any()


def testComplianceTendsToContinuityAsGammaVanishes() -> None:
    """Section 6.1.1.4 b): as γ1 tends to zero the compliance model tends to continuity."""
    continuity = runOne(CONTRHOB, radius=0.8).halfPitches[0]
    previous = None
    for gamma in (0.06, 0.03, 0.01, 0.005):
        values = dict(radius=0.8, compliance=gamma, approximations=(0.1,))
        half = runOne(ZETARHOB, **values).halfPitches[0]
        gap = (half.lowerBound - continuity.lowerBound, continuity.energy - half.energy)
        assert gap[0] > 0 and gap[1] > 0
        if previous is not None:
            assert gap[0] < previous[0] and gap[1] < previous[1]
        previous = gap


def testSinusoidRatioChoiceCentresOnTheAntinode() -> None:
    for program in (HARDSIN, CONTSIN):
        half = runOne(program, choice=ratio, amplitude=1.4).halfPitches[0]
        assert (half.start, half.end) == (6.75, 7.25)
        assert 0.0 < half.displacementRatio < 1.0
