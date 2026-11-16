"""Main application window: the input tab and one tab per kind of analysis."""

from __future__ import annotations

from functools import partial

from PySide6.QtCore import QUrl
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QCloseEvent,
    QDesktopServices,
    QKeySequence,
)
from PySide6.QtWidgets import QMainWindow, QMessageBox

from strandSlip import appConfig
from strandSlip.models.legacyProgram import BSINUS, DEPLACE, FRICTION, NSINUS, RAYON, SINUS
from strandSlip.models.strandPresets import allPresets
from strandSlip.models.thesisProgram import (
    ThesisDeflection,
    radiusPrograms,
    sinusoidPrograms,
)
from strandSlip.services import themeService
from strandSlip.services.manualWorker import ManualWorker
from strandSlip.ui.dialogs.aboutDialog import showAbout
from strandSlip.ui.dialogs.errorDialog import showError
from strandSlip.ui.views.analysisView import AnalysisView
from strandSlip.ui.views.inputView import InputView
from strandSlip.ui.views.thesisView import ThesisView
from strandSlip.ui.widgets.fullWidthTabWidget import FullWidthTabWidget
from strandSlip.ui.widgets.reportingView import ReportingView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(appConfig.windowTitle)
        self.resize(appConfig.defaultWindowWidth, appConfig.defaultWindowHeight)
        self.manualWorker: ManualWorker | None = None
        self.sourcesWorker: ManualWorker | None = None

        self.inputView = InputView()
        provider = self.inputView.currentInput
        self.sinusoidView = AnalysisView((SINUS, BSINUS, NSINUS), provider)
        self.curvatureView = AnalysisView((RAYON,), provider)
        self.frictionView = AnalysisView((FRICTION,), provider)
        self.displacementView = AnalysisView((DEPLACE,), provider)
        self.analysisViews = (
            self.sinusoidView,
            self.curvatureView,
            self.frictionView,
            self.displacementView,
        )
        self.thesisRadiusView = ThesisView(radiusPrograms, ThesisDeflection.constantRadius)
        self.thesisSinusoidView = ThesisView(sinusoidPrograms, ThesisDeflection.sinusoid)
        self.thesisViews = (self.thesisRadiusView, self.thesisSinusoidView)

        self.tabs = FullWidthTabWidget()
        self.tabs.setObjectName("programTabs")
        self.tabs.addTab(self.inputView, "Input · ENTRE")
        self.tabs.addTab(self.sinusoidView, "Sinusoid · SINUS BSINUS NSINUS")
        self.tabs.addTab(self.curvatureView, "Constant Curvature · RAYON")
        self.tabs.addTab(self.frictionView, "Friction · FRICTION")
        self.tabs.addTab(self.displacementView, "Displacement · DEPLACE")
        for view, label in (
            (self.thesisRadiusView, "Thesis · Constant Curvature"),
            (self.thesisSinusoidView, "Thesis · Sinusoid"),
        ):
            index = self.tabs.addTab(view, label)
            keys = ", ".join(program.key for program in view.programs)
            self.tabs.setTabToolTip(index, f"The 1992 thesis programs {keys}")
        self.tabs.currentChanged.connect(self.onTabChanged)
        self.setCentralWidget(self.tabs)

        for view in (self.inputView, *self.analysisViews, *self.thesisViews):
            self.connectView(view)
        for view in self.analysisViews:
            self.inputView.inputChanged.connect(view.markInputsChanged)

        self.buildMenuBar()
        self.onTabChanged()
        self.showStatus("Ready. The 1991 example strand is loaded; press F5 on a program tab.")

    def buildMenuBar(self) -> None:
        # Menus are kept as attributes: features can extend them later, and it
        # prevents the Python wrappers from being garbage-collected.
        fileMenu = self.fileMenu = self.menuBar().addMenu("&File")
        self.openAction = self.makeAction(
            fileMenu, "&Open ENTRE.DAT...", self.inputView.openFile, QKeySequence.StandardKey.Open
        )
        self.saveAction = self.makeAction(
            fileMenu,
            "&Save ENTRE.DAT As...",
            self.inputView.saveFile,
            QKeySequence.StandardKey.Save,
        )
        self.examplesMenu = fileMenu.addMenu("Load &Example")
        for preset in allPresets:
            self.makeAction(self.examplesMenu, preset.name, partial(self.loadPreset, preset))
        fileMenu.addSeparator()
        self.exportLegacyAction = self.makeAction(
            fileMenu, "Export &Legacy Files...", self.exportLegacyFiles, QKeySequence("Ctrl+E")
        )
        self.exportCsvAction = self.makeAction(fileMenu, "Export &CSV...", self.exportCsv)
        fileMenu.addSeparator()
        self.exitAction = self.makeAction(fileMenu, "E&xit", self.close, QKeySequence("Ctrl+Q"))

        runMenu = self.runMenu = self.menuBar().addMenu("&Run")
        self.runAction = self.makeAction(
            runMenu, "&Run Current Program", self.runCurrent, QKeySequence("F5")
        )
        self.stopAction = self.makeAction(
            runMenu, "&Stop", self.stopCurrent, QKeySequence("Shift+F5")
        )

        helpMenu = self.helpMenu = self.menuBar().addMenu("&Help")
        self.themeMenu = helpMenu.addMenu("&Theme")
        self.themeGroup = QActionGroup(self)
        self.themeGroup.setExclusive(True)
        self.themeActions: dict[str, QAction] = {}
        activeTheme = themeService.loadTheme()
        for theme in themeService.themeChoices:
            action = QAction(themeService.themeLabels[theme], self)
            action.setCheckable(True)
            action.setChecked(theme == activeTheme)
            action.triggered.connect(partial(self.onThemeChosen, theme))
            self.themeGroup.addAction(action)
            self.themeMenu.addAction(action)
            self.themeActions[theme] = action
        helpMenu.addSeparator()
        self.manualAction = self.makeAction(
            helpMenu, "User &Manual...", self.onHelpManual, QKeySequence.StandardKey.HelpContents
        )  # F1
        self.sourcesAction = self.makeAction(
            helpMenu, "Legacy Fortran &Sources...", self.onOpenLegacySources
        )
        self.aboutAction = self.makeAction(helpMenu, "&About", self.onHelpAbout)

    def makeAction(self, menu, text: str, slot, shortcut=None) -> QAction:
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def connectView(self, view: ReportingView) -> None:
        """Wire a view's status and failures into this window.

        Status goes to the bar, failures go to a dialog, and the view is spared
        knowing which is which.
        """
        view.statusMessage.connect(self.showStatus)
        view.errorMessage.connect(self.showError)

    def showStatus(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def showError(self, title: str, message: str) -> None:
        """Kept a method so tests can watch for it without a dialog opening."""
        showError(self, title, message)

    # -- tabs and runs ------------------------------------------------------------

    def currentAnalysis(self) -> AnalysisView | ThesisView | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, AnalysisView | ThesisView) else None

    def onTabChanged(self, _index: int = 0) -> None:
        onAnalysis = self.currentAnalysis() is not None
        for action in (
            self.runAction,
            self.stopAction,
            self.exportLegacyAction,
            self.exportCsvAction,
        ):
            action.setEnabled(onAnalysis)

    def runCurrent(self) -> None:
        view = self.currentAnalysis()
        if view is None:
            self.showStatus("Choose a program tab, then run it.")
            return
        view.run()

    def stopCurrent(self) -> None:
        view = self.currentAnalysis()
        if view is not None:
            view.stop()

    def exportLegacyFiles(self) -> None:
        view = self.currentAnalysis()
        if view is not None and view.output is not None:
            view.exportLegacyFiles()
        else:
            self.showStatus("Run the program first; then its files can be exported.")

    def exportCsv(self) -> None:
        view = self.currentAnalysis()
        if view is not None and view.output is not None:
            view.exportCsv()
        else:
            self.showStatus("Run the program first; then its results can be exported.")

    def loadPreset(self, preset) -> None:
        self.inputView.presetCombo.setCurrentIndex(allPresets.index(preset))
        self.inputView.onLoadPreset()
        self.tabs.setCurrentWidget(self.inputView)

    # -- help -----------------------------------------------------------------

    def onThemeChosen(self, theme: str) -> None:
        themeService.saveTheme(theme)
        themeService.applyTheme(theme)
        if theme == themeService.systemTheme:
            self.showStatus("Theme follows the Windows setting.")
        else:
            self.showStatus(f"{theme.capitalize()} theme applied.")

    def onOpenLegacySources(self) -> None:
        """The sources on GitHub when it answers, else the folder in this checkout.

        Asked off this thread, as for the manual: the probe can hang until its
        timeout.
        """
        if self.sourcesWorker is not None:
            return
        self.sourcesAction.setEnabled(False)
        self.showStatus("Looking for the legacy sources...")
        worker = ManualWorker(parent=self, url=appConfig.legacySourcesUrl)
        worker.resolved.connect(self.openLegacySources)
        worker.finished.connect(self.onSourcesCheckFinished)
        self.sourcesWorker = worker
        worker.start()

    def openLegacySources(self, publishedIsReachable: bool) -> None:
        url = appConfig.legacySourcesUrl
        if publishedIsReachable and QDesktopServices.openUrl(QUrl(url)):
            self.showStatus("The legacy sources are opening in your browser.")
            return
        folder = appConfig.legacySourcesDir
        if folder.is_dir() and QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))):
            self.showStatus(f"Opening the local copy, {folder}")
            return
        QMessageBox.information(
            self,
            "Legacy Fortran Sources",
            "The 1990 originals (.FOR and .EXE) and the 1992 listings are at:\n\n"
            f"{url}\n\n{folder}",
        )

    def onSourcesCheckFinished(self) -> None:
        if self.sourcesWorker is not None:
            self.sourcesWorker.deleteLater()
            self.sourcesWorker = None
        self.sourcesAction.setEnabled(True)

    def onHelpManual(self) -> None:
        """Open the manual, preferring the published copy when there is one.

        Whether it is reachable has to be asked separately: openUrl reports
        that a browser launched, not that the page loaded. The ask can hang
        until its timeout, so it happens off this thread. With manualUrl empty
        the service answers no immediately and the local copy is used without
        touching the network.
        """
        if self.manualWorker is not None:
            return
        self.manualAction.setEnabled(False)
        self.showStatus("Looking for the manual...")
        worker = ManualWorker(parent=self)
        worker.resolved.connect(self.openManual)
        worker.finished.connect(self.onManualCheckFinished)
        self.manualWorker = worker
        worker.start()

    def openManual(self, publishedIsReachable: bool) -> None:
        if publishedIsReachable and QDesktopServices.openUrl(QUrl(appConfig.manualUrl)):
            self.showStatus("The manual is opening in your browser.")
            return
        local = appConfig.manualPath
        if local.exists() and QDesktopServices.openUrl(QUrl.fromLocalFile(str(local))):
            self.showStatus(f"Opening the local copy, {local}")
            return
        # Leaving the reader with nothing is worse than making them copy a path.
        QMessageBox.information(
            self,
            "User Manual",
            "Could not open the manual. It is at:\n\n"
            f"{appConfig.manualUrl or '(nothing published)'}\n\n{local}",
        )

    def onManualCheckFinished(self) -> None:
        if self.manualWorker is not None:
            self.manualWorker.deleteLater()
            self.manualWorker = None
        self.manualAction.setEnabled(True)

    def closeEvent(self, event: QCloseEvent) -> None:
        # A thread running into interpreter shutdown turns a clean exit into a crash.
        for view in (*self.analysisViews, *self.thesisViews):
            view.shutdown()
        for worker in (self.manualWorker, self.sourcesWorker):
            if worker is not None:
                worker.wait(int(appConfig.manualTimeoutSeconds * 1000) + 1000)
        super().closeEvent(event)

    def onHelpAbout(self) -> None:
        if showAbout(self):
            self.showStatus("Thank you - the donation page is opening in your browser.")
