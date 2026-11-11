"""The Input tab: ENTRE's questions as one form."""

from __future__ import annotations

from masterRebuild.models.strandPresets import reportStrandCurvature, reportStrandSinusoid
from masterRebuild.services.analysisErrors import InputError
from masterRebuild.services.entreFileService import formatEntreText, readEntreFile
from masterRebuild.ui.views.inputView import InputView


def makeView(qtbot) -> InputView:
    view = InputView()
    qtbot.addWidget(view)
    return view


def testStartsOnTheReportStrand(qtbot) -> None:
    view = makeView(qtbot)
    assert view.currentInput() == reportStrandSinusoid.input
    assert view.edits["strandLength"].text() == "10"
    assert view.edits["wireModulus"].text() == "7e10"
    assert view.previewEdit.toPlainText() == formatEntreText(reportStrandSinusoid.input)


def testDerivedQuantitiesFollowTheForm(qtbot) -> None:
    view = makeView(qtbot)
    quantities = {
        view.derivedTable.item(row, 0).text(): view.derivedTable.item(row, 1).text()
        for row in range(view.derivedTable.rowCount())
    }
    assert quantities["Critical Amplitude Ac"] == "0.0272586 m"
    assert quantities["Lay Length p"] == "0.317266 m"

    edit = view.edits["helixAngle"]
    edit.setText("0.35")
    edit.textEdited.emit("0.35")
    assert view.hints["helixAngle"].text() == "= 20.0535°"
    assert view.derivedTable.item(0, 1).text() != "0.317266 m"


def testFortranSpellingsAndADecimalCommaAreAccepted(qtbot) -> None:
    view = makeView(qtbot)
    view.edits["wireModulus"].setText("0.7D+11")
    view.edits["corePoisson"].setText("0,3")
    view.refresh()
    value = view.currentInput()
    assert value.wireModulus == 7e10
    assert value.corePoisson == 0.3


def testANonNumberIsFlaggedAndBlocksTheRun(qtbot) -> None:
    view = makeView(qtbot)
    edit = view.edits["wireTension"]
    edit.setText("lots")
    edit.textEdited.emit("lots")

    assert edit.property("invalid") is True
    assert "Tension in One Wire (TI)" in view.issuesLabel.text()
    try:
        view.currentInput()
    except InputError as error:
        assert "'lots' is not a number" in str(error)
    else:
        raise AssertionError("an unreadable field must stop the run")


def testOutOfRangeValuesAreExplained(qtbot) -> None:
    view = makeView(qtbot)
    edit = view.edits["helixAngle"]
    edit.setText("15")
    edit.textEdited.emit("15")
    assert "looks like degrees" in view.issuesLabel.text()
    assert view.derivedTable.rowCount() == 0


def testExamplesLoad(qtbot) -> None:
    view = makeView(qtbot)
    view.presetCombo.setCurrentIndex(1)
    view.loadPresetButton.click()
    assert view.currentInput() == reportStrandCurvature.input


def testSaveAndOpenRoundTrip(qtbot, tmp_path) -> None:
    view = makeView(qtbot)
    path = tmp_path / "ENTRE.DAT"
    view.saveTo(view.currentInput(), path)
    assert readEntreFile(path).input == reportStrandSinusoid.input

    other = makeView(qtbot)
    other.presetCombo.setCurrentIndex(1)
    other.loadPresetButton.click()
    with qtbot.waitSignal(other.statusMessage):
        other.loadFile(path)
    assert other.currentInput() == reportStrandSinusoid.input
    assert str(path) in other.fileLabel.text()


def testAnUnreadableFileGoesToADialog(qtbot, tmp_path) -> None:
    view = makeView(qtbot)
    path = tmp_path / "ENTRE.DAT"
    path.write_text(" 0.1D+02\n 22\n")
    with qtbot.waitSignal(view.errorMessage) as blocker:
        view.loadFile(path)
    title, message = blocker.args
    assert title == "Could Not Read the Input File"
    assert "needs 15 lines" in message


def testWarningsFromAHandEditedFileAreShown(qtbot, tmp_path) -> None:
    view = makeView(qtbot)
    lines = formatEntreText(reportStrandSinusoid.input).splitlines()
    lines[0] = " 10"
    path = tmp_path / "ENTRE.DAT"
    path.write_text("\n".join(lines))
    view.loadFile(path)
    assert "no decimal point" in view.issuesLabel.text()
