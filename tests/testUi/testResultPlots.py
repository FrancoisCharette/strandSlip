"""Every plot of every result draws, in both themes, and reads back on hover."""

from __future__ import annotations

from dataclasses import replace

import pytest
from matplotlib.figure import Figure

from strandSlip.models.legacyProgram import RAYON, SINUS
from strandSlip.models.strandPresets import reportStrandCurvature, reportStrandSinusoid
from strandSlip.services.displacementService import runDisplacement
from strandSlip.services.frictionService import runFriction
from strandSlip.services.stiffnessService import runStiffness
from strandSlip.ui.plotting.chartStyle import darkTheme, lightTheme
from strandSlip.ui.plotting.resultPlots import choicesFor, drawResult

example = replace(reportStrandSinusoid.input, xEnd=3.0)
results = {
    "sinus": runStiffness(example, SINUS),
    "rayon": runStiffness(replace(reportStrandCurvature.input, xEnd=0.05), RAYON),
    "friction": runFriction(example),
    "deplace": runDisplacement(example),
}


@pytest.mark.parametrize("name", list(results))
@pytest.mark.parametrize("theme", [lightTheme, darkTheme], ids=["light", "dark"])
def testEveryChoiceDraws(name: str, theme) -> None:
    result = results[name]
    for choice in choicesFor(result):
        figure = Figure()
        hover = drawResult(figure, theme, result, choice.key, wire=3)
        axes = figure.axes[0]
        assert axes.get_title(loc="left"), choice.key
        assert hover is not None
        found = hover.locate(1.0, 4.0)
        assert found is not None and "X = " in found[2]


def testTheStiffnessPlotShowsTheStuckValueAsAReference() -> None:
    figure = Figure()
    drawResult(figure, lightTheme, results["sinus"], "stiffness", wire=0)
    texts = [t.get_text() for t in figure.axes[0].texts]
    assert any(text.startswith("Every wire stuck: 1779.9") for text in texts)


def testTheHoverReadsTheNearestPoint() -> None:
    figure = Figure()
    hover = drawResult(figure, lightTheme, results["sinus"], "stiffness", wire=0)
    x, y, text = hover.locate(2.52, 0.0)
    assert x == pytest.approx(2.5)
    assert "EI = 1671.24" in text


def testAWireOutsideTheRangeIsClamped() -> None:
    figure = Figure()
    drawResult(figure, lightTheme, results["friction"], "frictionDemand", wire=99)
    assert "Wire 22" in [t.get_text() for t in figure.axes[0].get_legend().get_texts()]
