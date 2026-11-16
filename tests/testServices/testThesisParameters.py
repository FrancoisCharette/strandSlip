"""Chapter 5's dimensionless parameters, from the strand the thesis itself uses."""

from __future__ import annotations

from dataclasses import replace

import pytest

from strandSlip.models.strandPresets import reportStrandCurvature, reportStrandSinusoid
from strandSlip.services.analysisErrors import InputError
from strandSlip.services.thesisParameters import thesisParameters


def testTheThesisExampleStrand() -> None:
    """Section 5.2: the 1991 strand has γ1 = 0.05621."""
    parameters = thesisParameters(reportStrandSinusoid.input)

    assert round(parameters.compliance, 5) == 0.05621
    assert parameters.criticalRadius == pytest.approx(92.9259, rel=1e-6)  # RHOC
    assert parameters.criticalAmplitude == pytest.approx(0.0272586, rel=1e-6)  # AMPC
    assert parameters.amplitudeRatio == pytest.approx(1.46743, rel=1e-5)
    assert parameters.waveRatio == pytest.approx(10.0 / 0.317266, rel=1e-5)


def testTheRadiusIsTheAmplitudeSlotReadAsRayonReadsIt() -> None:
    parameters = thesisParameters(reportStrandCurvature.input)

    assert parameters.radiusRatio == pytest.approx(50.0 / 92.9259, rel=1e-6)
    assert parameters.criticalAmplitude is None and parameters.waveRatio is None


def testAStrandThatCannotGiveThemSaysWhy() -> None:
    with pytest.raises(InputError):
        thesisParameters(replace(reportStrandSinusoid.input, helixAngle=0.0))


def testTheStrandTabShowsTheThesisParameters() -> None:
    from strandSlip.services.constantsReport import describeInput

    rows = {line.quantity: line.value for line in describeInput(reportStrandSinusoid.input)}
    assert rows["Compliance Factor γ1"] == "0.0562111"
    assert rows["Lay Lengths per Wavelength λ/p"] == "31.5192"
