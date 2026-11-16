"""A program tab: run, plot, read, export."""

from __future__ import annotations

from dataclasses import replace

import pytest

from strandSlip.models.legacyProgram import BSINUS, DEPLACE, FRICTION, NSINUS, RAYON, SINUS
from strandSlip.models.strandPresets import reportStrandCurvature, reportStrandSinusoid
from strandSlip.services.analysisErrors import InputError
from strandSlip.ui.views.analysisView import AnalysisView

example = reportStrandSinusoid.input


def makeView(qtbot, programs, value=example) -> AnalysisView:
    view = AnalysisView(programs, lambda: value)
    qtbot.addWidget(view)
    return view


def runAndWait(qtbot, view: AnalysisView) -> None:
    view.run()
    qtbot.waitUntil(lambda: not view.isRunning(), timeout=30000)


def testNothingToExportBeforeARun(qtbot) -> None:
    view = makeView(qtbot, (SINUS, BSINUS, NSINUS))
    assert view.runButton.text() == "Run SINUS"
    assert not view.exportLegacyButton.isEnabled()
    assert view.programCombo.count() == 3


def testChoosingAnotherProgramChangesTheButtonAndFiles(qtbot) -> None:
    view = makeView(qtbot, (SINUS, BSINUS, NSINUS))
    view.programCombo.setCurrentIndex(2)
    assert view.runButton.text() == "Run NSINUS"
    assert "RESFIN.DAT and DONNE1.DAT" in view.sourceLabel.text()


def testARunFillsTableSummaryScreenAndPlots(qtbot) -> None:
    view = makeView(qtbot, (SINUS,))
    runAndWait(qtbot, view)

    assert view.tableModel.rowCount() == 101
    assert "DONSIN.DAT, as SINUS.FOR wrote it:" in view.summaryEdit.toPlainText()
    assert "  RAPPORT D AMP.=.1467E+01" in view.summaryEdit.toPlainText()
    screen = view.consoleEdit.toPlainText().splitlines()
    assert screen[0] == "   2         0.2856"
    assert view.exportLegacyButton.isEnabled()
    for index in range(view.plotCombo.count()):
        view.plotCombo.setCurrentIndex(index)  # every plot draws without error
    assert view.plotPanel.figure.axes


def testTheWirePickerShowsOnlyForWirePlots(qtbot) -> None:
    view = makeView(qtbot, (FRICTION,))
    runAndWait(qtbot, view)
    view.plotCombo.setCurrentIndex(view.plotCombo.findData("frictionDemand"))
    assert not view.wireSpin.isHidden()
    assert view.wireSpin.maximum() == 22
    view.plotCombo.setCurrentIndex(view.plotCombo.findData("slipMap"))
    assert view.wireSpin.isHidden()


@pytest.mark.parametrize(
    ("programs", "value", "rows"),
    [
        ((RAYON,), replace(reportStrandCurvature.input, xEnd=0.05), 50),  # X = 0 skipped
        ((FRICTION,), example, 2222),
        ((DEPLACE,), example, 2222),
    ],
    ids=["rayon", "friction", "deplace"],
)
def testEveryProgramRuns(qtbot, programs, value, rows) -> None:
    view = makeView(qtbot, programs, value)
    runAndWait(qtbot, view)
    assert view.tableModel.rowCount() == rows


def testInputsTheProgramCannotUseGoToADialog(qtbot) -> None:
    view = makeView(qtbot, (SINUS,), replace(example, wavelength=0.0))
    with qtbot.waitSignal(view.errorMessage) as blocker:
        view.run()
    title, message = blocker.args
    assert title == "SINUS Did Not Run"
    assert "Wavelength (WL) must be positive" in message
    assert not view.isRunning()


def testAnUnreadableInputTabGoesToADialog(qtbot) -> None:
    def broken():
        raise InputError(["Tension in One Wire (TI) 'lots' is not a number."])

    view = AnalysisView((SINUS,), broken)
    qtbot.addWidget(view)
    with qtbot.waitSignal(view.errorMessage) as blocker:
        view.run()
    assert "Fix the Strand tab first" in blocker.args[1]


def testAnAmplitudeGivenToRayonIsPointedOut(qtbot) -> None:
    view = makeView(qtbot, (RAYON,), replace(example, xEnd=0.05))
    with qtbot.waitSignal(
        view.statusMessage, timeout=30000, check_params_cb=lambda m: m.startswith("RAYON:")
    ) as blocker:
        view.run()
    qtbot.waitUntil(lambda: not view.isRunning(), timeout=30000)
    assert "is that an amplitude rather than a radius?" in blocker.args[0]


def testExportWritesTheLegacyFilesAndAsksBeforeReplacing(qtbot, tmp_path, monkeypatch) -> None:
    view = makeView(qtbot, (SINUS,), replace(example, xEnd=1.0))
    runAndWait(qtbot, view)
    folder = tmp_path / "run"  # tmp_path also holds the test's settings.ini
    folder.mkdir()

    view.writeLegacyFilesTo(folder)
    qtbot.waitUntil(lambda: not view.isRunning(), timeout=30000)
    assert sorted(p.name for p in folder.iterdir()) == [
        "DONSIN.DAT",
        "ENTRE.DAT",
        "RESSIN.DAT",
        "SINUS.OUT",
    ]

    asked: list[list[str]] = []
    monkeypatch.setattr(view, "confirmOverwrite", lambda folder, names: asked.append(names))
    view.writeLegacyFilesTo(folder)
    assert asked == [["RESSIN.DAT", "DONSIN.DAT", "ENTRE.DAT", "SINUS.OUT"]]
    assert not view.isRunning()  # declined: nothing started


def testCsvExport(qtbot, tmp_path) -> None:
    view = makeView(qtbot, (DEPLACE,), replace(example, xEnd=0.25))
    runAndWait(qtbot, view)
    path = tmp_path / "deplace.csv"
    view.writeCsvTo(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("X (m) [X],Displacement")
    assert len(lines) == 1 + 3 * 22
