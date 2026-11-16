"""Smoke tests for the main window."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication

from strandSlip import appConfig
from strandSlip.models.legacyProgram import SINUS
from strandSlip.models.strandPresets import reportStrandCurvature
from strandSlip.services import themeService
from strandSlip.ui.mainWindow import MainWindow
from strandSlip.ui.widgets.fullWidthTabWidget import FullWidthTabWidget
from strandSlip.ui.widgets.pageTabWidget import PageTabWidget


def testMainWindowOpens(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    mainWindow.show()

    assert mainWindow.isVisible()
    assert mainWindow.windowTitle() == appConfig.windowTitle
    assert mainWindow.windowTitle().startswith("Strand Slip")
    assert mainWindow.statusBar().currentMessage().startswith("Ready")


def testOneTabForTheInputAndEachKindOfAnalysis(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    labels = [mainWindow.tabs.tabText(i) for i in range(mainWindow.tabs.count())]
    assert labels == [
        "Input · ENTRE",
        "Sinusoid · SINUS BSINUS NSINUS",
        "Constant Curvature · RAYON",
        "Friction · FRICTION",
        "Displacement · DEPLACE",
        "Thesis · Constant Curvature",
        "Thesis · Sinusoid",
    ]
    programs = [p.key for view in mainWindow.analysisViews for p in view.programs]
    assert programs == ["SINUS", "BSINUS", "NSINUS", "RAYON", "FRICTION", "DEPLACE"]
    thesis = [p.key for view in mainWindow.thesisViews for p in view.programs]
    assert thesis == ["HARDRHOB", "CONTRHOB", "ZETARHOB", "HARDSIN", "CONTSIN", "ZETASIN"]
    assert "HARDRHOB, CONTRHOB, ZETARHOB" in mainWindow.tabs.tabToolTip(5)


def testTheTabsInsideEveryPageAreMarkedTheQuieterWay(qtbot) -> None:
    """Table / Summary / Screen Output show their open tab too, under a thinner bar."""
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    assert isinstance(mainWindow.tabs, FullWidthTabWidget)
    for view in (*mainWindow.analysisViews, *mainWindow.thesisViews):
        assert isinstance(view.detailTabs, PageTabWidget)


def testF5RunsAThesisProgram(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    view = mainWindow.thesisRadiusView
    mainWindow.tabs.setCurrentWidget(view)
    assert mainWindow.runAction.isEnabled()

    mainWindow.runAction.trigger()
    qtbot.waitUntil(lambda: not view.isRunning(), timeout=20000)

    assert view.output is not None and view.output.result.program.key == "HARDRHOB"
    assert mainWindow.statusBar().currentMessage().startswith("HARDRHOB: 1 half lay length")


def testMenuBarStructure(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    menuTitles = [action.text() for action in mainWindow.menuBar().actions()]
    assert menuTitles == ["&File", "&Run", "&Help"]

    fileItems = [a.text() for a in mainWindow.fileMenu.actions() if not a.isSeparator()]
    assert fileItems == [
        "&Open ENTRE.DAT...",
        "&Save ENTRE.DAT As...",
        "Load &Example",
        "Export &Legacy Files...",
        "Export &CSV...",
        "E&xit",
    ]
    runItems = [a.text() for a in mainWindow.runMenu.actions()]
    assert runItems == ["&Run Current Program", "&Stop"]
    assert mainWindow.runAction.shortcut() == QKeySequence("F5")

    helpItems = [a.text() for a in mainWindow.helpMenu.actions() if not a.isSeparator()]
    assert helpItems == ["&Theme", "User &Manual...", "Legacy Fortran &Sources...", "&About"]


def testRunAndExportNeedAProgramTab(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    assert mainWindow.tabs.currentWidget() is mainWindow.inputView
    assert not mainWindow.runAction.isEnabled()
    mainWindow.tabs.setCurrentWidget(mainWindow.frictionView)
    assert mainWindow.runAction.isEnabled()
    assert mainWindow.exportLegacyAction.isEnabled()


def testF5RunsTheProgramOfTheCurrentTab(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    mainWindow.tabs.setCurrentWidget(mainWindow.sinusoidView)

    mainWindow.runAction.trigger()
    qtbot.waitUntil(lambda: not mainWindow.sinusoidView.isRunning(), timeout=20000)

    output = mainWindow.sinusoidView.output
    assert output is not None and output.result.program is SINUS
    assert mainWindow.sinusoidView.tableModel.rowCount() == 101
    assert mainWindow.statusBar().currentMessage().startswith("SINUS: 102 positions")


def testLoadingAnExampleFromTheMenuFillsTheInputTab(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    mainWindow.tabs.setCurrentWidget(mainWindow.curvatureView)

    mainWindow.examplesMenu.actions()[1].trigger()

    assert mainWindow.tabs.currentWidget() is mainWindow.inputView
    assert mainWindow.inputView.currentInput() == reportStrandCurvature.input


def testChangingAnInputMarksAShownResultAsStale(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    view = mainWindow.frictionView
    view.run()
    qtbot.waitUntil(lambda: not view.isRunning(), timeout=20000)
    assert view.staleLabel.isHidden()

    edit = mainWindow.inputView.edits["amplitude"]
    edit.setText("0.05")
    edit.textEdited.emit("0.05")

    assert not view.staleLabel.isHidden()


def testThemeMenuOffersSystemLightDark(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    labels = [a.text() for a in mainWindow.themeMenu.actions()]
    assert labels == ["Use &System Theme", "&Light", "&Dark"]
    assert all(a.isCheckable() for a in mainWindow.themeMenu.actions())
    assert mainWindow.themeGroup.isExclusive()
    # Following Windows is the default.
    assert mainWindow.themeActions[themeService.systemTheme].isChecked()


def testChoosingDarkAppliesAndRemembersIt(qtbot, observableColorScheme) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    mainWindow.themeActions[themeService.darkTheme].trigger()

    # The window's own job: remember the choice and say so.
    assert themeService.loadTheme() == themeService.darkTheme
    assert "Dark theme applied" in mainWindow.statusBar().currentMessage()
    # Whether Qt then paints dark is only observable on some platforms.
    if observableColorScheme:
        assert themeService.currentColorScheme() == Qt.ColorScheme.Dark


def testSwitchingThemeReachesTheInputTab(qtbot, observableColorScheme) -> None:
    """The bug: from dark, Help > Theme > Light left the whole Input tab dark.

    Its own style sheet stopped it taking palette changes. The program tabs'
    style is rebuilt on every palette change, which hands the new palette down
    to every page. Only a real scheme change shows it, so this skips on the
    offscreen plugin.
    """
    if not observableColorScheme:
        pytest.skip("this platform plugin does not report a forced colour scheme")
    themeService.applyTheme(themeService.darkTheme)
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    mainWindow.show()
    qtbot.wait(100)
    edit = mainWindow.inputView.edits["amplitude"]

    mainWindow.themeActions[themeService.lightTheme].trigger()

    light = QApplication.palette(edit).base().color()
    assert light.lightnessF() > 0.5
    qtbot.waitUntil(lambda: edit.palette().base().color() == light, timeout=3000)


def testSavedThemeIsRestoredOnNextLaunch(qtbot) -> None:
    first = MainWindow()
    qtbot.addWidget(first)
    first.themeActions[themeService.lightTheme].trigger()

    reopened = MainWindow()
    qtbot.addWidget(reopened)

    assert reopened.themeActions[themeService.lightTheme].isChecked()


def testAboutOpensTheDialogAndReportsADonation(qtbot, monkeypatch) -> None:
    """The About text itself is covered in testAboutDialog."""
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    monkeypatch.setattr("strandSlip.ui.mainWindow.showAbout", lambda parent: True)

    mainWindow.onHelpAbout()

    assert "donation page" in mainWindow.statusBar().currentMessage()


def openedUrls(monkeypatch) -> list[str]:
    """Collect what the app asked the desktop to open, and say it worked."""
    opened: list[str] = []
    monkeypatch.setattr(
        "strandSlip.ui.mainWindow.QDesktopServices.openUrl",
        lambda url: opened.append(url.toString()) or True,
    )
    return opened


def testManualHasTheStandardHelpShortcut(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    assert mainWindow.manualAction.shortcut() == QKeySequence.StandardKey.HelpContents


def testTheStubManualShipsWithTheTemplate() -> None:
    """Without it the menu item would fail the first time anybody clicked it."""
    assert appConfig.manualPath.exists()
    assert appConfig.manualPath.read_text(encoding="utf-8").strip()


def testNothingIsPublishedUntilTheAuthorSaysSo() -> None:
    """A new app has no manual online, so the default must not pretend it has."""
    assert appConfig.manualUrl == ""


def testTheLocalCopyIsOpenedWhenNothingIsPublished(qtbot, monkeypatch) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    opened = openedUrls(monkeypatch)

    mainWindow.openManual(publishedIsReachable=False)

    assert len(opened) == 1
    assert opened[0].startswith("file:")
    assert opened[0].endswith("README.md")
    assert "local copy" in mainWindow.statusBar().currentMessage()


def testThePublishedCopyWinsWhenItAnswers(qtbot, monkeypatch) -> None:
    """Set manualUrl and the behaviour switches, with no other change."""
    monkeypatch.setattr(appConfig, "manualUrl", "https://example.invalid/manual")
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    opened = openedUrls(monkeypatch)

    mainWindow.openManual(publishedIsReachable=True)

    assert opened == ["https://example.invalid/manual"]
    assert "browser" in mainWindow.statusBar().currentMessage()


def testAMissingManualLeavesTheReaderAnAddress(qtbot, monkeypatch, tmp_path) -> None:
    """Nothing opened, so the path has to be readable somewhere."""
    monkeypatch.setattr(appConfig, "manualPath", tmp_path / "gone.md")
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    openedUrls(monkeypatch)
    shown: list[str] = []
    monkeypatch.setattr(
        "strandSlip.ui.mainWindow.QMessageBox.information",
        lambda parent, title, text: shown.append(text),
    )

    mainWindow.openManual(publishedIsReachable=False)

    assert shown and "gone.md" in shown[0]
    assert "nothing published" in shown[0]


def testTheCheckRunsOffTheInterfaceThread(qtbot, monkeypatch) -> None:
    """A network probe can hang until its timeout; the window must not."""
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    openedUrls(monkeypatch)

    with qtbot.waitSignal(mainWindow.manualAction.changed, timeout=5000):
        mainWindow.onHelpManual()
    # Disabled while the probe is in flight, so it cannot be started twice.
    assert not mainWindow.manualAction.isEnabled()

    assert mainWindow.manualWorker is not None
    mainWindow.manualWorker.wait(5000)
    qtbot.waitUntil(lambda: mainWindow.manualWorker is None, timeout=5000)
    assert mainWindow.manualAction.isEnabled()
