"""FRICTION and DEPLACE against a literal transcription."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from legacyReference import literalPrograms
from masterRebuild.models.strandPresets import reportStrandSinusoid
from masterRebuild.services.analysisErrors import InputError
from masterRebuild.services.displacementService import runDisplacement
from masterRebuild.services.frictionService import runFriction

example = reportStrandSinusoid.input
cases = [
    pytest.param(example, id="report"),
    pytest.param(
        replace(example, wireCount=6, helixAngle=0.3, xStart=-0.5, xEnd=1.0, positionCount=1000),
        id="six-wires",
    ),
]


@pytest.mark.parametrize("value", cases)
def testFrictionMatchesTheTranscriptionExactly(value) -> None:
    rows, info = literalPrograms.friction(*value.values())
    result = runFriction(value)
    assert result.frictionDemand.size == len(rows)
    assert np.array_equal(result.frictionDemand.ravel(), np.array([r[1] for r in rows]))
    assert np.array_equal(np.repeat(result.positions, value.wireCount), [r[0] for r in rows])
    assert result.deflection.frictionConstant == info["CST9"]


@pytest.mark.parametrize("value", cases)
def testDisplacementMatchesTheTranscriptionExactly(value) -> None:
    rows, info = literalPrograms.deplace(*value.values())
    result = runDisplacement(value)
    assert np.array_equal(result.displacementScaled.ravel(), [r[1] for r in rows])
    assert np.array_equal(result.termA.ravel(), [r[3] for r in rows])
    assert np.array_equal(result.termB.ravel(), [r[4] for r in rows])
    assert result.deflection.displacementConstant == info["CST19"]


def testTheScanStopsBeforeTheEndPosition() -> None:
    result = runFriction(example)
    assert len(result.positions) == 101
    assert result.positions[-1] < example.xEnd


def testTheReportStrandNeedsMoreFrictionThanItHas() -> None:
    """A/Ac = 1.47, so the demand exceeds the 0.8 limit near maximum curvature."""
    result = runFriction(example)
    assert np.abs(result.frictionDemand).max() > example.frictionLimit
    gentle = runFriction(replace(example, amplitude=0.01))
    assert np.abs(gentle.frictionDemand).max() < example.frictionLimit


def testDisplacementIsWrittenTimesTenThousand() -> None:
    result = runDisplacement(example)
    unscaled = result.deflection.displacementConstant * (result.termA - result.termB)
    assert np.allclose(result.displacementScaled, unscaled * 10000, rtol=1e-15, atol=0)


def testBothNeedASinusoid() -> None:
    with pytest.raises(InputError, match="Wavelength"):
        runFriction(replace(example, wavelength=0.0))
    with pytest.raises(InputError, match="Wavelength"):
        runDisplacement(replace(example, wavelength=-1.0))
