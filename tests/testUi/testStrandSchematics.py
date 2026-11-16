"""The schematics draw for every kind of input, in both themes, without a window."""

from __future__ import annotations

from dataclasses import replace

import pytest
from matplotlib.figure import Figure

from strandSlip.models.legacyProgram import Deflection
from strandSlip.models.strandPresets import reportStrandCurvature, reportStrandSinusoid
from strandSlip.ui.plotting.chartStyle import darkTheme, lightTheme
from strandSlip.ui.plotting.strandSchematics import drawSchematics, programsFor

sinusoidStrand = reportStrandSinusoid.input
curvatureStrand = reportStrandCurvature.input

cases = {
    "reportSinusoid": (sinusoidStrand, Deflection.sinusoid),
    "reportCurvature": (curvatureStrand, Deflection.constantCurvature),
    "fourWaves": (replace(sinusoidStrand, wavelength=2.5), Deflection.sinusoid),
    "longerThanTheSpan": (replace(sinusoidStrand, wavelength=25.0), Deflection.sinusoid),
    "tinyWaves": (replace(sinusoidStrand, wavelength=0.05), Deflection.sinusoid),
    "noWavelength": (curvatureStrand, Deflection.sinusoid),
    "downwards": (replace(sinusoidStrand, amplitude=-0.04), Deflection.sinusoid),
    "bentTheOtherWay": (replace(curvatureStrand, amplitude=-50.0), Deflection.constantCurvature),
    "beyondThePosts": (replace(sinusoidStrand, xStart=-2.0, xEnd=14.0), Deflection.sinusoid),
    "fortyWires": (replace(sinusoidStrand, wireCount=40), Deflection.sinusoid),
    "noCore": (replace(sinusoidStrand, coreRadius=0.0), Deflection.sinusoid),
    "noSpan": (replace(sinusoidStrand, strandLength=0.0), Deflection.sinusoid),
}


@pytest.mark.parametrize("theme", [lightTheme, darkTheme], ids=["light", "dark"])
@pytest.mark.parametrize("case", list(cases))
def testEveryCaseDraws(case, theme) -> None:
    value, deflection = cases[case]
    figure = Figure(layout="constrained")

    drawSchematics(figure, theme, value, deflection)
    figure.canvas.draw()

    sideView, sectionView = figure.axes
    assert sideView.get_title(loc="left").startswith("Side View")
    assert sectionView.get_title(loc="left").startswith("Section")


def testTheSideViewReadsTheTrueDeflectionOnHover() -> None:
    """The drawing is ten times taller than true; the readout is not."""
    figure = Figure(layout="constrained")
    hover = drawSchematics(figure, lightTheme, sinusoidStrand, Deflection.sinusoid)

    x, drawnY, text = hover.locate(2.5, 0.0)

    assert x == pytest.approx(2.5, abs=0.02)
    assert drawnY == pytest.approx(0.4, rel=1e-3)
    assert text.endswith("Y = 0.04 m")


def testTheTitleSaysWhichProgramsUseTheDeflectionAndHowTallItIsDrawn() -> None:
    figure = Figure(layout="constrained")
    drawSchematics(figure, lightTheme, curvatureStrand, Deflection.constantCurvature)

    note = figure.axes[0].get_title(loc="right")
    assert "RAYON" in note and "vertical scale ×2" in note
    assert programsFor(Deflection.sinusoid) == "SINUS, BSINUS, NSINUS, FRICTION and DEPLACE"


def testValuesThatAreNotNumbersAreSaid() -> None:
    figure = Figure(layout="constrained")

    assert drawSchematics(figure, darkTheme, None, Deflection.sinusoid) is None
    assert not figure.axes
    assert "not numbers yet" in figure.texts[0].get_text()
