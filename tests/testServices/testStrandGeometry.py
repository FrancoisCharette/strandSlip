"""What the Strand tab's schematics draw, checked against the programs' own equations."""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from strandSlip.models.legacyProgram import Deflection
from strandSlip.models.strandPresets import reportStrandCurvature, reportStrandSinusoid
from strandSlip.services import strandGeometry
from strandSlip.services.strandGeometry import SchematicError, niceScale, section, sideView
from strandSlip.services.strandModel import computeStrandConstants

sinusoidStrand = reportStrandSinusoid.input
curvatureStrand = reportStrandCurvature.input


def testTheSinusoidIsTheProgramsOwn() -> None:
    """Y = A sin(2πX/λ), equation 18, over the whole strand between the posts."""
    view = sideView(sinusoidStrand, Deflection.sinusoid)

    assert view.x[0] == 0 and view.x[-1] == sinusoidStrand.strandLength
    expected = 0.04 * np.sin(2 * math.pi * view.x / 10.0)
    assert np.allclose(view.y, expected)
    assert view.extent == pytest.approx(0.04, rel=1e-4)
    assert view.problem == ""
    # 0.04 m on a 10 m span is drawn ten times taller, a round factor.
    assert view.exaggeration == 10


def testTheConstantCurvatureArcHasRayonsCurvature() -> None:
    """Only the curvature of Y = −X²/2ρ enters RAYON, so the arc through both posts has it."""
    view = sideView(curvatureStrand, Deflection.constantCurvature)

    curvature = np.gradient(np.gradient(view.y, view.x), view.x)
    assert np.allclose(curvature[2:-2], -1 / 50.0, rtol=1e-6)
    assert view.y[0] == 0 and view.y[-1] == pytest.approx(0, abs=1e-12)
    assert view.midSpanRise == pytest.approx(10.0**2 / (8 * 50.0))
    assert view.extent == pytest.approx(view.midSpanRise, rel=1e-4)
    assert view.exaggeration == 2


@pytest.mark.parametrize(
    ("raw", "nice"),
    [(12.5, 10), (2.0, 2), (4.9, 2.5), (9.99, 5), (0.003, 0.0025), (1.0, 1), (0, 1), (math.inf, 1)],
)
def testExaggerationIsARoundFactorNotAboveTheOneThatFits(raw, nice) -> None:
    assert niceScale(raw) == pytest.approx(nice)


def testTheDeflectionAFileWasWrittenFor() -> None:
    """ENTRE wrote 0 for the wavelength RAYON ignores."""
    assert strandGeometry.likelyDeflection(sinusoidStrand) is Deflection.sinusoid
    assert strandGeometry.likelyDeflection(curvatureStrand) is Deflection.constantCurvature


def testADeflectionThatCannotBeDrawnLeavesTheStrandStraightAndSaysWhy() -> None:
    noWave = sideView(replace(sinusoidStrand, wavelength=0.0), Deflection.sinusoid)
    assert "λ must be positive" in noWave.problem
    assert not noWave.y.any() and noWave.exaggeration == 1

    noRadius = sideView(replace(curvatureStrand, amplitude=0.0), Deflection.constantCurvature)
    assert "ρ cannot be zero" in noRadius.problem


@pytest.mark.parametrize("changes", [{"strandLength": 0.0}, {"positionCount": 0}])
def testASpanThatCannotBeDrawnIsAnError(changes) -> None:
    with pytest.raises(SchematicError):
        sideView(replace(sinusoidStrand, **changes), Deflection.sinusoid)


def testPositionsAreMarkedWhereTheStiffnessProgramsCompute() -> None:
    view = sideView(sinusoidStrand, Deflection.sinusoid)
    assert view.positions is not None
    assert view.positions[0] == 0 and view.positions[-1] >= 10.0
    assert np.allclose(np.diff(view.positions), view.positionStep)
    # Ten thousand positions over one lay length: a band, not ten thousand ticks.
    assert sideView(curvatureStrand, Deflection.constantCurvature).positions is None


def testTheSectionOfTheReportStrand() -> None:
    cut = section(sinusoidStrand)

    assert cut.axisRadius == pytest.approx(0.01353 + 0.002135)
    assert cut.outerRadius == pytest.approx(0.01353 + 2 * 0.002135)
    assert len(cut.angles) == 22 and cut.angles[0] == 0
    assert np.allclose(np.diff(cut.angles), 2 * math.pi / 22)
    # Equation 13, as the programs compute it.
    assert cut.layLength == pytest.approx(computeStrandConstants(sinusoidStrand).pitch)
    # The same lay length on the circle through the wire axes: a steeper helix there.
    assert math.tan(cut.axisHelixAngle) == pytest.approx(
        math.tan(0.2618) * cut.axisRadius / 0.01353
    )
    assert cut.alongCircle == pytest.approx(0.002135 / math.cos(cut.axisHelixAngle))
    # The report's 22 wires lie side by side around the core.
    assert 0.98 < cut.fill < 1.02


def testTooManyWiresForTheCoreOverlap() -> None:
    assert section(replace(sinusoidStrand, wireCount=40)).fill > 1.5


@pytest.mark.parametrize(
    "changes",
    [{"coreRadius": 0.0}, {"wireRadius": -1.0}, {"helixAngle": 0.0}, {"wireCount": 0}],
)
def testASectionNeedsPositiveSizes(changes) -> None:
    with pytest.raises(SchematicError):
        section(replace(sinusoidStrand, **changes))
