"""One tab per imposed deflection for the 1992 thesis programs: answer, run, read, export.

The tab offers the three models of one deflection (Hardy, continuity of
deformation, compliance), asks the keyboard questions as a form, runs the
chosen program off the interface thread and shows a plot, the half lay
lengths solved, the profile, a summary and the screen output. When the
program stops to ask a question the form did not answer, the question is
shown under the form; the run's screen and results so far stay readable.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from strandSlip.models.thesisProgram import ThesisDeflection, ThesisProgramSpec
from strandSlip.services import settingsService
from strandSlip.services.analysisErrors import InputError
from strandSlip.services.analysisWorker import AnalysisWorker
from strandSlip.services.resultTableService import writeCsv
from strandSlip.services.thesisRunner import legacyFiles, validationIssues, writeLegacyFiles
from strandSlip.services.thesisTables import ThesisRunOutput, runAndPresentThesis
from strandSlip.ui.plotting.thesisPlots import drawThesisResult, thesisChoices
from strandSlip.ui.widgets.pageTabWidget import PageTabWidget
from strandSlip.ui.widgets.plotPanel import PlotPanel
from strandSlip.ui.widgets.reportingView import ReportingView
from strandSlip.ui.widgets.resultTableModel import ResultTableModel
from strandSlip.ui.widgets.thesisInputForm import ThesisInputForm

lastExportFolderKey = "files/lastExportFolder"


def _monospaced(name: str) -> QPlainTextEdit:
    edit = QPlainTextEdit()
    edit.setObjectName(name)
    edit.setReadOnly(True)
    edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    edit.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
    return edit


def _table(name: str, model: ResultTableModel) -> QTableView:
    view = QTableView()
    view.setObjectName(name)
    view.setModel(model)
    view.setAlternatingRowColors(True)
    return view


class ThesisView(ReportingView):
    """Runs one of `programs` (one deflection's three models) on the form's answers."""

    def __init__(
        self,
        programs: tuple[ThesisProgramSpec, ...],
        deflection: ThesisDeflection,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.programs = programs
        self.output: ThesisRunOutput | None = None
        self.worker: AnalysisWorker | None = None
        self.busyWith = ""

        self.titleLabel = QLabel()
        self.titleLabel.setObjectName("titleLabel")
        font = self.titleLabel.font()
        font.setPointSizeF(font.pointSizeF() * 1.25)
        font.setBold(True)
        self.titleLabel.setFont(font)
        self.summaryLabel = QLabel()
        self.summaryLabel.setWordWrap(True)
        self.sourceLabel = QLabel()
        self.sourceLabel.setEnabled(False)  # muted
        self.form = ThesisInputForm(deflection)
        self.form.changed.connect(self.markInputsChanged)
        self.questionLabel = QLabel()
        self.questionLabel.setObjectName("questionLabel")
        self.questionLabel.setWordWrap(True)
        self.questionLabel.setStyleSheet("color: #c98500;")
        self.questionLabel.setVisible(False)
        self.staleLabel = QLabel("The answers have changed since this run; run again to update it.")
        self.staleLabel.setObjectName("staleLabel")
        self.staleLabel.setStyleSheet("color: #c98500;")
        self.staleLabel.setVisible(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.summaryLabel)
        layout.addWidget(self.sourceLabel)
        layout.addLayout(self.buildControls())
        layout.addWidget(self.questionLabel)
        layout.addWidget(self.staleLabel)
        layout.addWidget(self.buildBody(), 1)
        self.onProgramChanged()
        self.setResultActionsEnabled(False)

    def buildControls(self) -> QVBoxLayout:
        self.programCombo = QComboBox()
        self.programCombo.setObjectName("programCombo")
        for program in self.programs:
            self.programCombo.addItem(f"{program.key} — {program.title}")
        self.programCombo.currentIndexChanged.connect(self.onProgramChanged)
        self.runButton = QPushButton("Run")
        self.runButton.setObjectName("runButton")
        self.runButton.setDefault(True)
        self.runButton.clicked.connect(self.run)
        self.stopButton = QPushButton("Stop")
        self.stopButton.setEnabled(False)
        self.stopButton.clicked.connect(self.stop)
        self.progressBar = QProgressBar()
        self.progressBar.setMaximumWidth(180)
        self.progressBar.setVisible(False)
        self.progressTimer = QTimer(self)
        self.progressTimer.setInterval(100)
        self.progressTimer.timeout.connect(self.showProgress)
        self.exportLegacyButton = QPushButton("Export Legacy Files...")
        self.exportLegacyButton.clicked.connect(self.exportLegacyFiles)
        self.exportCsvButton = QPushButton("Export CSV...")
        self.exportCsvButton.clicked.connect(self.exportCsv)
        buttons = QHBoxLayout()
        buttons.addWidget(self.programCombo)
        buttons.addWidget(self.runButton)
        buttons.addWidget(self.stopButton)
        buttons.addWidget(self.progressBar)
        buttons.addStretch()
        buttons.addWidget(self.exportLegacyButton)
        buttons.addWidget(self.exportCsvButton)
        formRow = QHBoxLayout()
        formRow.addWidget(self.form)
        formRow.addStretch()
        column = QVBoxLayout()
        column.addLayout(buttons)
        column.addLayout(formRow)
        return column

    def buildBody(self) -> QSplitter:
        self.plotCombo = QComboBox()
        self.plotCombo.setObjectName("plotCombo")
        self.plotCombo.currentIndexChanged.connect(self.redrawPlot)
        plotControls = QHBoxLayout()
        plotControls.addWidget(QLabel("Plot"))
        plotControls.addWidget(self.plotCombo, 1)
        self.plotPanel = PlotPanel()
        plotSide = QWidget()
        plotLayout = QVBoxLayout(plotSide)
        plotLayout.setContentsMargins(0, 0, 0, 0)
        plotLayout.addLayout(plotControls)
        plotLayout.addWidget(self.plotPanel, 1)

        self.tableModel = ResultTableModel(self)
        self.profileModel = ResultTableModel(self)
        self.tableView = _table("halfPitchTable", self.tableModel)
        self.profileView = _table("profileTable", self.profileModel)
        self.summaryEdit = _monospaced("summaryEdit")
        self.consoleEdit = _monospaced("consoleEdit")
        self.detailTabs = PageTabWidget()
        self.detailTabs.addTab(self.tableView, "Half Lay Lengths")
        self.detailTabs.addTab(self.profileView, "Profile")
        self.detailTabs.addTab(self.summaryEdit, "Summary")
        self.detailTabs.addTab(self.consoleEdit, "Screen Output")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(plotSide)
        splitter.addWidget(self.detailTabs)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([780, 520])
        return splitter

    # -- program choice -------------------------------------------------------

    def currentProgram(self) -> ThesisProgramSpec:
        return self.programs[max(0, self.programCombo.currentIndex())]

    def onProgramChanged(self) -> None:
        program = self.currentProgram()
        self.titleLabel.setText(program.title)
        self.summaryLabel.setText(program.summary)
        self.sourceLabel.setText(
            f"1992 program {program.sourceFile}, printed on page {program.page} of the program "
            f"manual; diskette directory {program.directory} (legacy/manuel1992/)."
        )
        self.runButton.setText(f"Run {program.key}")
        self.form.setProgram(program)

    # -- running --------------------------------------------------------------

    def isRunning(self) -> bool:
        return self.worker is not None

    def run(self) -> None:
        if self.isRunning():
            return
        program = self.currentProgram()
        try:
            value = self.form.currentInput()
        except InputError as error:
            self.reportError(f"{program.key} Did Not Run", f"Check the answers.\n{error}")
            return
        issues = validationIssues(value, program)
        if issues:
            self.reportError(
                f"{program.key} Did Not Run",
                f"{program.sourceFile} cannot run on these answers.\n" + "\n".join(issues),
            )
            return
        self.startWorker(
            lambda hook: runAndPresentThesis(program, value, hook),
            f"Running {program.key}",
            self.onRunSucceeded,
        )

    def startWorker(self, job, message: str, onSuccess) -> None:
        worker = AnalysisWorker(job, parent=self)
        worker.succeeded.connect(onSuccess)
        worker.failed.connect(self.onWorkerFailed)
        worker.cancelled.connect(self.onWorkerCancelled)
        worker.finished.connect(self.onWorkerFinished)
        self.worker = worker
        self.busyWith = message
        self.setBusy(True)
        self.reportStatus(f"{message}...")
        worker.start()
        self.progressTimer.start()

    def showProgress(self) -> None:
        if self.worker is not None:
            self.progressBar.setValue(self.worker.percent)

    def setBusy(self, busy: bool) -> None:
        self.runButton.setEnabled(not busy)
        self.programCombo.setEnabled(not busy)
        self.form.setEnabled(not busy)
        self.stopButton.setEnabled(busy)
        self.progressBar.setValue(0)
        self.progressBar.setVisible(busy)
        self.setResultActionsEnabled(not busy and self.output is not None)

    def setResultActionsEnabled(self, enabled: bool) -> None:
        self.exportLegacyButton.setEnabled(enabled)
        self.exportCsvButton.setEnabled(enabled)

    def stop(self) -> None:
        if self.worker is not None:
            self.worker.cancel()

    def shutdown(self) -> None:
        """Stop and wait for a run before the window closes."""
        if self.worker is not None:
            self.worker.cancel()
            self.worker.wait(15000)

    def onWorkerCancelled(self) -> None:
        self.reportStatus(f"{self.busyWith} stopped.")

    def onWorkerFailed(self, message: str) -> None:
        self.reportError(f"{self.busyWith} Failed", message)

    def onWorkerFinished(self) -> None:
        self.progressTimer.stop()
        if self.worker is not None:
            self.worker.wait()  # finished is emitted just before the thread exits
            self.worker.deleteLater()
            self.worker = None
        self.setBusy(False)

    def onRunSucceeded(self, output: ThesisRunOutput) -> None:
        self.showOutput(output)
        result = output.result
        if result.pendingQuestion:
            self.reportStatus(f"{result.program.key} stopped: it asks a question; see the tab.")
            return
        solved = len(result.halfPitches)
        self.reportStatus(
            f"{result.program.key}: {solved} half lay length{'s' if solved != 1 else ''} "
            f"solved in {result.elapsedSeconds:.2f} s."
        )

    def markInputsChanged(self) -> None:
        self.staleLabel.setVisible(self.output is not None)

    # -- showing a result ---------------------------------------------------------

    def showOutput(self, output: ThesisRunOutput) -> None:
        self.output = output
        result = output.result
        self.staleLabel.setVisible(False)
        question = result.pendingQuestion
        self.questionLabel.setText(
            f"{result.program.key} stopped to ask: {question}" if question else ""
        )
        self.questionLabel.setVisible(bool(question))
        self.tableModel.setTable(output.table)
        self.tableView.resizeColumnsToContents()
        self.profileModel.setTable(output.profileTable)
        self.profileView.resizeColumnsToContents()
        self.detailTabs.setTabEnabled(1, output.profileTable is not None)
        self.summaryEdit.setPlainText(output.summaryText)
        self.consoleEdit.setPlainText(output.consoleText)
        if question:  # the screen ends with the question: show it there
            self.detailTabs.setCurrentWidget(self.consoleEdit)
            QTimer.singleShot(0, self.scrollConsoleToEnd)
        previous = self.plotCombo.currentData()
        self.plotCombo.blockSignals(True)
        self.plotCombo.clear()
        for choice in thesisChoices(result):
            self.plotCombo.addItem(choice.label, choice.key)
        self.plotCombo.setCurrentIndex(max(0, self.plotCombo.findData(previous)))
        self.plotCombo.blockSignals(False)
        self.setResultActionsEnabled(True)
        self.redrawPlot()

    def scrollConsoleToEnd(self) -> None:
        bar = self.consoleEdit.verticalScrollBar()
        bar.setValue(bar.maximum())

    def redrawPlot(self) -> None:
        if self.output is None:
            self.plotPanel.setDrawing(None)
            return
        result, key = self.output.result, self.plotCombo.currentData()
        self.plotPanel.setDrawing(
            lambda figure, theme: drawThesisResult(figure, theme, result, key)
        )

    # -- exporting ------------------------------------------------------------

    def exportFolder(self) -> str:
        folder = settingsService.openSettings().value(lastExportFolderKey, "")
        return str(folder) if folder and Path(str(folder)).is_dir() else str(Path.home())

    def exportLegacyFiles(self) -> None:
        if self.output is None or self.isRunning():
            return
        names = list(legacyFiles(self.output.result))
        folder = QFileDialog.getExistingDirectory(
            self, f"Folder for {', '.join(names)}", self.exportFolder()
        )
        if folder:
            self.writeLegacyFilesTo(Path(folder))

    def writeLegacyFilesTo(self, folder: Path) -> None:
        result = self.output.result
        names = list(legacyFiles(result))
        existing = [name for name in names if (folder / name).exists()]
        if existing and not self.confirmOverwrite(folder, existing):
            self.reportStatus("Nothing exported.")
            return
        settingsService.writeValue(lastExportFolderKey, str(folder))
        self.startWorker(
            lambda hook: writeLegacyFiles(result, folder, overwrite=True),
            f"Writing {result.program.key} files",
            self.onLegacyFilesWritten,  # a bound method: a lambda here aborted on thread cleanup
        )

    def onLegacyFilesWritten(self, paths: list[Path]) -> None:
        folder = paths[0].parent if paths else ""
        self.reportStatus(f"Wrote {len(paths)} files to {folder}.")

    def confirmOverwrite(self, folder: Path, existing: list[str]) -> bool:
        answer = QMessageBox.question(
            self,
            "Replace Files?",
            f"{folder} already holds {', '.join(existing)}.\n\nReplace them?",
        )
        return answer == QMessageBox.StandardButton.Yes

    def currentTable(self):
        """The profile when its tab is showing, else the half lay lengths."""
        if self.detailTabs.currentIndex() == 1 and self.output.profileTable is not None:
            return self.output.profileTable, "profile"
        return self.output.table, "halfPitches"

    def exportCsv(self) -> None:
        if self.output is None:
            return
        _table, suffix = self.currentTable()
        program = self.output.result.program
        target = str(Path(self.exportFolder()) / f"{program.key}-{suffix}.csv")
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", target, "CSV Files (*.csv)")
        if path:
            self.writeCsvTo(Path(path))

    def writeCsvTo(self, path: Path) -> None:
        table, _suffix = self.currentTable()
        try:
            writeCsv(table, path)
        except OSError as error:
            self.reportError(
                "Could Not Export the CSV", f"Writing {path} failed: {error.strerror or error}"
            )
            return
        settingsService.writeValue(lastExportFolderKey, str(path.parent))
        self.reportStatus(f"Exported {table.rowCount:,} rows to {path}.")
