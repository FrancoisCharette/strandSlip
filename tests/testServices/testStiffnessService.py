"""SINUS, BSINUS, NSINUS and RAYON against the 1991 report and a literal transcription."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from legacyReference import literalPrograms
from masterRebuild.models.analysisResults import slipAbove, slipBelow, stuck
from masterRebuild.models.legacyProgram import BSINUS, NSINUS, RAYON, SINUS
from masterRebuild.models.strandPresets import reportStrandCurvature, reportStrandSinusoid
from masterRebuild.services.analysisErrors import AnalysisCancelled, InputError, ProgressHook
from masterRebuild.services.stiffnessService import runStiffness

example = reportStrandSinusoid.input


def engineRows(result) -> np.ndarray:
    rows = result.written
    return np.column_stack(
        [
            result.positions[rows],
            result.stiffness[rows],
            result.torsion[rows],
            result.momentY[rows],
            result.momentZ[rows],
            result.forceX[rows],
            result.forceY[rows],
            result.forceZ[rows],
        ]
    )


def testTheRowPrintedInProgressReportTwo() -> None:
    """Rapport d'etape no. 2 (Feb. 1991), table at X = 2.500 for SINUS.FOR.

    The report gives MX 0, MY 0.1696, MZ 26.391, FX 0, FY 3.358 and a
    stiffness of 1671.24. It also prints FZ 522.24, which cannot be right:
    FZ/MZ is tan(alpha)/Ra for every wire, so MZ 26.391 means FZ 522.65.
    """
    result = runStiffness(example, SINUS)
    row = int(np.argmin(np.abs(result.positions - 2.5)))
    assert f"{result.stiffness[row]:.2f}" == "1671.24"
    assert f"{result.torsion[row]:.4f}" in ("0.0000", "-0.0000")
    assert f"{result.momentY[row]:.4f}" == "0.1696"
    assert f"{result.momentZ[row]:.3f}" == "26.391"
    assert f"{result.forceX[row]:.4f}" in ("0.0000", "-0.0000")
    assert f"{result.forceY[row]:.3f}" == "3.358"
    assert result.forceZ[row] / result.momentZ[row] == pytest.approx(0.26795 / 0.01353, rel=1e-4)


literalCases = [
    pytest.param(SINUS, example, {}, id="sinus-report"),
    pytest.param(
        SINUS, replace(example, amplitude=0.12, positionCount=300), {}, id="sinus-deep-slip"
    ),
    pytest.param(
        SINUS,
        replace(
            example,
            wireCount=7,
            helixAngle=0.35,
            amplitude=0.08,
            positionCount=250,
            xStart=-1.0,
            xEnd=4.0,
        ),
        {},
        id="sinus-7-wires-negative-start",
    ),
    pytest.param(NSINUS, replace(example, xStart=2.0, xEnd=3.0), {"divisor": 10000}, id="nsinus"),
]


@pytest.mark.parametrize(("program", "value", "options"), literalCases)
def testSinusoidMatchesTheLiteralTranscriptionExactly(program, value, options) -> None:
    rows, info = literalPrograms.sinus(*value.values(), **options)
    result = runStiffness(value, program)
    assert np.array_equal(engineRows(result), np.array(rows))
    assert result.searchStep == info["DX"]
    assert result.deflection.critical == info["AMPC"]
    assert result.deflection.frictionConstant == info["CST9"]
    assert result.constants.gamma == info["GAM"]


@pytest.mark.parametrize(
    "value",
    [
        replace(reportStrandCurvature.input, positionCount=2000),
        replace(reportStrandCurvature.input, amplitude=12.0, wireCount=9),
        replace(reportStrandCurvature.input, amplitude=200.0),
    ],
    ids=["rayon-report", "rayon-tight", "rayon-no-slip"],
)
def testRayonMatchesTheLiteralTranscriptionExactly(value) -> None:
    rows, info = literalPrograms.rayon(*value.values())
    result = runStiffness(value, RAYON)
    assert np.array_equal(engineRows(result), np.array(rows))
    assert result.searchStep == info["DX"]
    assert result.deflection.critical == info["RHOC"]


def testNsinusSlipZoneListingMatchesTheTranscription() -> None:
    value = replace(example, xStart=2.5, xEnd=2.5)
    trace: list[tuple] = []
    literalPrograms.sinus(*value.values(), divisor=10000, trace=trace)
    result = runStiffness(value, NSINUS)
    zones = {"slipAbove": slipAbove, "slipBelow": slipBelow}
    for entry in trace:
        kind, x, wire = entry[0], entry[1], entry[2] - 1
        assert result.positions[0] == x
        if kind in zones:
            assert result.wires.zone[0, wire] == zones[kind]
            assert result.wires.lowerBound[0, wire] == entry[3]
            assert result.wires.upperBound[0, wire] == entry[4]
            assert result.wires.lowerDisplacement[0, wire] == entry[5]
            assert result.wires.upperDisplacement[0, wire] == entry[6]
        else:
            assert result.wires.zone[0, wire] == stuck
        assert result.wires.elongation[0, wire] == entry[-1]


def testBsinusIsSinusUnderAnotherName() -> None:
    sinus = runStiffness(example, SINUS)
    cable = runStiffness(example, BSINUS)
    assert np.array_equal(engineRows(sinus), engineRows(cable))


def testTheFinerSearchOfNsinusMovesTheResultSlightly() -> None:
    value = replace(example, xStart=2.0, xEnd=3.0)
    coarse = runStiffness(value, BSINUS).stiffness[1:]
    fine = runStiffness(value, NSINUS).stiffness[1:]
    assert not np.array_equal(coarse, fine)
    assert np.allclose(coarse, fine, rtol=2e-3)


def testPositionZeroIsNotWritten() -> None:
    result = runStiffness(example, SINUS)
    assert result.positions[0] == 0.0
    assert not result.written[0]
    assert np.isnan(result.stiffness[0])
    assert result.written[1:].all()


@pytest.mark.parametrize(
    ("program", "value"),
    [
        (SINUS, replace(example, amplitude=0.01)),  # A/Ac = 0.37
        (RAYON, replace(reportStrandCurvature.input, amplitude=150.0, positionCount=1000)),
    ],
    ids=["sinusoid", "constant-curvature"],
)
def testBelowTheCriticalValueNothingSlipsAndEiIsTheStuckValue(program, value) -> None:
    result = runStiffness(value, program)
    assert (result.wires.zone == stuck).all()
    written = result.stiffness[result.written]
    assert np.allclose(written, result.fullStickStiffness, rtol=1e-6)


def testSlipLowersTheStiffness() -> None:
    result = runStiffness(example, SINUS)
    assert (result.wires.zone != stuck).any()
    assert np.nanmin(result.stiffness) < 0.95 * result.fullStickStiffness


def testTheSearchStepIsZeroWhenTheProgramNeverAssignedIt() -> None:
    """One wire, stuck, demand positive: DX was never set and printed as 0."""
    value = replace(reportStrandCurvature.input, wireCount=1, amplitude=500.0, xStart=0.0, xEnd=0.0)
    result = runStiffness(value, RAYON)
    assert result.searchStep == 0.0
    assert result.wires.frictionDemand[0, 0] > 0


def testProgressReachesOneHundredAndCancelStops() -> None:
    seen: list[int] = []
    runStiffness(example, SINUS, ProgressHook(seen.append))
    assert seen[0] == 0 and seen[-1] == 100

    hook = ProgressHook()
    hook.cancel()
    with pytest.raises(AnalysisCancelled):
        runStiffness(example, SINUS, hook)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"wireCount": 51}, "dimension their wire arrays at 50"),
        ({"helixAngle": 15.0}, "looks like degrees"),
        ({"amplitude": 0.0}, "cannot be zero"),
        ({"positionCount": 0}, "between 1 and 32767"),
        ({"xEnd": 1e6}, "positions"),
        ({"frictionLimit": 0.0}, "must be positive"),
    ],
)
def testInputsTheProgramsCouldNotRunOnAreRefused(change, message) -> None:
    with pytest.raises(InputError, match=message):
        runStiffness(replace(example, **change), SINUS)
