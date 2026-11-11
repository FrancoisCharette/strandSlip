"""Derived constants and the X loops, against the 1991 reports and the source."""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from masterRebuild.models.strandPresets import reportStrandSinusoid
from masterRebuild.services.strandModel import (
    ConstantCurvatureDeflection,
    SinusoidalDeflection,
    computeStrandConstants,
    fullStickStiffness,
    scanPositions,
    stiffnessPositions,
)

example = reportStrandSinusoid.input


def testConstantsOfTheReportStrand() -> None:
    constants = computeStrandConstants(example)
    # Progress report no. 2: "Aire d'un fil : 14,32 mm2"
    assert constants.wireArea * 1e6 == pytest.approx(14.32, abs=0.005)
    assert constants.pitch == pytest.approx(2 * math.pi * 0.01353 / math.tan(0.2618))
    assert constants.bearingPressure == pytest.approx(3186.00, abs=0.01)  # .3186E+04
    assert constants.positionStep == pytest.approx(0.1)


def testCriticalAmplitudeIsTheReportedOne() -> None:
    """GS.DOC (1991): "l'amplitude critique est de l'ordre de 0.027 metre"."""
    constants = computeStrandConstants(example)
    sinusoid = SinusoidalDeflection(example, constants)
    assert sinusoid.constants.critical == pytest.approx(0.027, abs=0.0005)
    assert sinusoid.constants.ratio == pytest.approx(0.04 / sinusoid.constants.critical)


def testGammaIsSinglePrecisionLikeTheOriginal() -> None:
    constants = computeStrandConstants(example)
    double = (643.5 * math.sin(0.2618) * 0.8) / (70e9 * constants.wireArea)
    assert constants.gamma == float(np.float32(double))
    assert constants.gamma != double


def testThetasAreAccumulatedNotMultiplied() -> None:
    constants = computeStrandConstants(example)
    accumulated = [0.0]
    for _ in range(21):
        accumulated.append(accumulated[-1] + (2 * math.pi) / 22)
    assert constants.thetas.tolist() == accumulated


def testCriticalRadiusOfTheConstantCurvatureModel() -> None:
    constants = computeStrandConstants(example)
    curvature = ConstantCurvatureDeflection(replace(example, amplitude=50.0), constants)
    assert curvature.constants.critical == pytest.approx(92.93, abs=0.01)
    assert curvature.constants.ratio == pytest.approx(50.0 / curvature.constants.critical)
    # Slip starts when the friction factor reaches the limit: rho = rho_c.
    atCritical = ConstantCurvatureDeflection(
        replace(example, amplitude=curvature.constants.critical), constants
    )
    assert atCritical.constants.frictionConstant == pytest.approx(0.8)


def testFullStickStiffness() -> None:
    constants = computeStrandConstants(example)
    assert fullStickStiffness(example, constants) == pytest.approx(1779.94, abs=0.01)
    assert fullStickStiffness(replace(example, wireCount=2), constants) is None


def testStiffnessLoopRunsTheFirstPositionPastTheEnd() -> None:
    positions = stiffnessPositions(example, 0.1, 1000)
    assert len(positions) == 102
    assert positions[-2] < 10.0 <= positions[-1]
    single = stiffnessPositions(replace(example, xStart=3.0, xEnd=2.0), 0.1, 1000)
    assert single.tolist() == [3.0]


def testScanLoopStopsBeforeTheEnd() -> None:
    positions = scanPositions(example, 0.1, 1000)
    assert len(positions) == 101
    assert positions[-1] < 10.0
    single = scanPositions(replace(example, xStart=3.0, xEnd=2.0), 0.1, 1000)
    assert single.tolist() == [3.0]


def testPositionsAccumulateTheStep() -> None:
    positions = stiffnessPositions(example, 0.1, 1000)
    x = 0.0
    for expected in positions[1:]:
        x = x + 0.1
        assert expected == x
