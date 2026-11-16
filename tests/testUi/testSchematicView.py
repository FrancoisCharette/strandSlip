"""The Strand tab's two pages: the numerical entries, and the schematics drawn from them."""

from __future__ import annotations

from strandSlip.models.legacyProgram import Deflection
from strandSlip.ui.views.inputView import InputView
from strandSlip.ui.widgets.pageTabWidget import PageTabWidget


def makeView(qtbot) -> InputView:
    view = InputView()
    qtbot.addWidget(view)
    view.resize(1200, 800)
    return view


def showSchematics(qtbot, view: InputView) -> None:
    view.show()
    view.pages.setCurrentWidget(view.schematicView)
    qtbot.waitUntil(lambda: not view.schematicView.stale, timeout=3000)


def edit(view: InputView, name: str, text: str) -> None:
    view.edits[name].setText(text)
    view.edits[name].textEdited.emit(text)


def sideTitle(view: InputView, loc: str = "left") -> str:
    return view.schematicView.plotPanel.figure.axes[0].get_title(loc=loc)


def testTheEntriesComeFirstThenTheSchematics(qtbot) -> None:
    view = makeView(qtbot)

    assert isinstance(view.pages, PageTabWidget)
    pages = [view.pages.tabText(i) for i in range(view.pages.count())]
    assert pages == ["Numerical Entries", "Schematics"]
    assert view.pages.currentIndex() == 0
    assert view.edits["strandLength"].isVisibleTo(view.pages.widget(0))


def testTheSchematicsAreDrawnFromTheEntries(qtbot) -> None:
    view = makeView(qtbot)
    showSchematics(qtbot, view)
    assert sideTitle(view).startswith("Side View")
    assert "vertical scale ×10" in sideTitle(view, "right")

    edit(view, "amplitude", "0.2")

    qtbot.waitUntil(lambda: "vertical scale ×2.5" in sideTitle(view, "right"), timeout=3000)
    _x, _y, text = view.schematicView.plotPanel.hover.locate(2.5, 0.0)
    assert text.endswith("Y = 0.2 m")


def testRedrawingWaitsUntilTheSchematicsAreShown(qtbot, monkeypatch) -> None:
    """Typing on the entries page does not redraw a page nobody is looking at."""
    view = makeView(qtbot)
    view.show()
    drawn: list[object] = []
    monkeypatch.setattr(view.schematicView.plotPanel, "setDrawing", drawn.append)

    edit(view, "wavelength", "2.5")
    qtbot.wait(300)
    assert drawn == [] and view.schematicView.stale

    view.pages.setCurrentWidget(view.schematicView)
    assert len(drawn) == 1


def testAnExampleDrawsTheDeflectionItWasWrittenFor(qtbot) -> None:
    view = makeView(qtbot)
    assert view.schematicView.currentDeflection() is Deflection.sinusoid

    view.presetCombo.setCurrentIndex(1)
    view.loadPresetButton.click()
    showSchematics(qtbot, view)

    assert view.schematicView.currentDeflection() is Deflection.constantCurvature
    assert "RAYON" in sideTitle(view, "right")


def testTheDeflectionCanBeChosen(qtbot) -> None:
    view = makeView(qtbot)
    showSchematics(qtbot, view)
    combo = view.schematicView.deflectionCombo

    combo.setCurrentIndex(1)

    assert view.schematicView.currentDeflection() is Deflection.constantCurvature
    qtbot.waitUntil(lambda: "RAYON" in sideTitle(view, "right"), timeout=3000)


def testValuesThatAreNotNumbersAreSaidOnTheSchematics(qtbot) -> None:
    view = makeView(qtbot)
    showSchematics(qtbot, view)

    edit(view, "coreRadius", "abc")

    figure = view.schematicView.plotPanel.figure
    qtbot.waitUntil(lambda: not figure.axes, timeout=3000)
    assert "not numbers yet" in figure.texts[0].get_text()
