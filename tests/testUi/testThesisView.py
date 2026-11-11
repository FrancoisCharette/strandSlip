"""A 1992 program tab: answer, run, read the question it asks, export."""

from __future__ import annotations

from pathlib import Path

import pytest

from masterRebuild.models.thesisInput import SinusoidChoice
from masterRebuild.models.thesisProgram import (
    ThesisDeflection,
    radiusPrograms,
    sinusoidPrograms,
)
from masterRebuild.ui.views.thesisView import ThesisView


def makeView(qtbot, sinusoid: bool = False) -> ThesisView:
    if sinusoid:
        view = ThesisView(sinusoidPrograms, ThesisDeflection.sinusoid)
    else:
        view = ThesisView(radiusPrograms, ThesisDeflection.constantRadius)
    qtbot.addWidget(view)
    return view


def runAndWait(qtbot, view: ThesisView) -> None:
    view.run()
    qtbot.waitUntil(lambda: not view.isRunning(), timeout=60000)


def visibleRows(view: ThesisView) -> set[str]:
    form = view.form
    return {key for key, widget in form.rows.items() if form.formLayout.isRowVisible(widget)}


def testTheFormAsksWhatEachProgramAsks(qtbot) -> None:
    view = makeView(qtbot)
    assert visibleRows(view) == {"radius", "profile"}
    view.programCombo.setCurrentIndex(1)  # CONTRHOB
    assert visibleRows(view) == {"radius", "profile", "approximations"}
    view.programCombo.setCurrentIndex(2)  # ZETARHOB
    assert visibleRows(view) == {"radius", "compliance", "profile", "approximations"}
    assert view.runButton.text() == "Run ZETARHOB"

    sinusoid = makeView(qtbot, sinusoid=True)
    assert visibleRows(sinusoid) == {"choice", "wavelength", "amplitude", "turns", "profile"}
    sinusoid.form.choiceCombo.setCurrentIndex(0)  # over the wavelength: no XTOUR, no profile
    assert visibleRows(sinusoid) == {"choice", "wavelength", "amplitude"}


def testARunFillsTablesSummaryScreenAndPlots(qtbot) -> None:
    view = makeView(qtbot)
    runAndWait(qtbot, view)

    assert view.tableModel.rowCount() == 1
    assert view.profileModel.rowCount() == 501
    assert "bounds XB1 = 0.14758362" in view.summaryEdit.toPlainText()
    assert "XB1=0.14758362D+00" in view.consoleEdit.toPlainText()
    assert view.questionLabel.isHidden()
    assert view.exportLegacyButton.isEnabled()
    for index in range(view.plotCombo.count()):
        view.plotCombo.setCurrentIndex(index)  # every plot draws without error
    assert view.plotCombo.count() == 4
    assert view.plotPanel.figure.axes


def testTheQuestionTheProgramAsksIsShownAndAnsweredFromTheForm(qtbot) -> None:
    view = makeView(qtbot)
    view.programCombo.setCurrentIndex(2)  # ZETARHOB
    view.form.radiusEdit.setText("0.7")
    view.form.profileCheck.setChecked(False)
    runAndWait(qtbot, view)
    assert not view.questionLabel.isHidden()
    assert "XB1C" in view.questionLabel.text()
    assert "Entrez la nouvelle approximation de XB1C:" in view.consoleEdit.toPlainText()

    view.form.approximationsEdit.setText("0.10")
    view.form.approximationsEdit.textEdited.emit("0.10")
    assert not view.staleLabel.isHidden()
    runAndWait(qtbot, view)
    assert view.questionLabel.isHidden()
    assert view.output.result.approximationsUsed == (0.10,)


def testTheWholeWavelengthPlotsEnergyByHalfLayLength(qtbot) -> None:
    view = makeView(qtbot, sinusoid=True)
    view.form.choiceCombo.setCurrentIndex(int(SinusoidChoice.wholeWavelength) - 1)
    view.form.amplitudeEdit.setText("1.3")
    runAndWait(qtbot, view)
    result = view.output.result
    assert result.totalEnergy is not None
    assert [h.start for h in result.halfPitches] == [4.0, 4.5, 5.0, 5.5, 6.0, 6.5]
    assert len(result.skipped) == 8  # 0.0 to 3.5: no macro-slip
    assert view.tableModel.rowCount() == 6
    assert view.plotCombo.findData("energy") >= 0
    view.plotCombo.setCurrentIndex(view.plotCombo.findData("energy"))
    assert view.plotPanel.figure.axes


@pytest.mark.parametrize(
    ("sinusoid", "index", "key"),
    [
        (False, 0, "HARDRHOB"),
        (False, 1, "CONTRHOB"),
        (False, 2, "ZETARHOB"),
        (True, 0, "HARDSIN"),
        (True, 1, "CONTSIN"),
        (True, 2, "ZETASIN"),
    ],
)
def testEveryProgramRunsFromItsTabWithTheDefaultAnswers(qtbot, sinusoid, index, key) -> None:
    view = makeView(qtbot, sinusoid=sinusoid)
    view.programCombo.setCurrentIndex(index)
    runAndWait(qtbot, view)
    result = view.output.result
    assert result.program.key == key and result.pendingQuestion is None
    assert view.tableModel.rowCount() == 1 and view.profileModel.rowCount() >= 500
    assert f"PROGRAM {key}" not in view.consoleEdit.toPlainText()  # the screen, not the source
    assert view.consoleEdit.toPlainText().strip()


def testAnswerThatIsNotANumberIsReported(qtbot) -> None:
    view = makeView(qtbot)
    view.form.radiusEdit.setText("abc")
    with qtbot.waitSignal(view.errorMessage) as blocker:
        view.run()
    title, message = blocker.args
    assert title == "HARDRHOB Did Not Run"
    assert "abc" in message


def testExportsWriteTheRunsFiles(qtbot, tmp_path: Path) -> None:
    view = makeView(qtbot)
    runAndWait(qtbot, view)
    folder = tmp_path / "export"
    view.writeLegacyFilesTo(folder)
    qtbot.waitUntil(lambda: not view.isRunning(), timeout=20000)
    written = sorted(path.name for path in folder.iterdir())
    assert written == ["DEP.DAT", "ELG.DAT", "FRC.DAT", "HARDRHOB.OUT"]
    view.detailTabs.setCurrentIndex(1)
    view.writeCsvTo(tmp_path / "profile.csv")
    assert (tmp_path / "profile.csv").read_text(encoding="utf-8").count("\n") == 502
