"""One tab per kind of analysis: run a 1990 program, plot it, read it, export it.

The tab offers one or more legacy programs (SINUS, BSINUS and NSINUS share a
tab), runs the chosen one off the interface thread, and shows the result as
a plot, a table, the summary file and the screen output.
"""

from __future__ import annotations

from collections.abc import Callable
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
    QSpinBox,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from strandSlip.models.legacyProgram import Deflection, ProgramSpec
from strandSlip.models.strandInput import StrandInput
from strandSlip.services import inputValidation, legacyOutputService, settingsService
from strandSlip.services.analysisErrors import InputError
from strandSlip.services.analysisRunner import RunOutput, runAndPresent
from strandSlip.services.analysisWorker import AnalysisWorker
from strandSlip.services.resultTableService import writeCsv
from strandSlip.ui.plotting.resultPlots import choicesFor, drawResult
from strandSlip.ui.widgets.pageTabWidget import PageTabWidget
from strandSlip.ui.widgets.plotPanel import PlotPanel
from strandSlip.ui.widgets.reportingView import ReportingView
from strandSlip.ui.widgets.resultTableModel import ResultTableModel

lastExportFolderKey = "files/lastExportFolder"


def _monospaced(name: str) -> QPlainTextEdit:
    edit = QPlainTextEdit()
    edit.setObjectName(name)
    edit.setReadOnly(True)
    edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    edit.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
    return edit


class AnalysisView(ReportingView):
    """Runs one of `programs` on the values `inputProvider` returns."""

    def __init__(
        self,
        programs: tuple[ProgramSpec, ...],
        inputProvider: Callable[[], StrandInput],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.programs = programs
        self.inputProvider = inputProvider
        self.output: RunOutput | None = None
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
        self.staleLabel = QLabel("The inputs have changed since this run; run again to update it.")
        self.staleLabel.setObjectName("staleLabel")
        self.staleLabel.setStyleSheet("color: #c98500;")
        self.staleLabel.setVisible(False)

        self.programCombo = QComboBox()
        self.programCombo.setObjectName("programCombo")
        for program in programs:
            self.programCombo.addItem(f"{program.key} — {program.title}")
        self.programCombo.setVisible(len(programs) > 1)
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

        controls = QHBoxLayout()
        controls.addWidget(self.programCombo)
        controls.addWidget(self.runButton)
        controls.addWidget(self.stopButton)
        controls.addWidget(self.progressBar)
        controls.addStretch()
        controls.addWidget(self.exportLegacyButton)
        controls.addWidget(self.exportCsvButton)

        layout = QVBoxLayout(self)
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.summaryLabel)
        layout.addWidget(self.sourceLabel)
        layout.addLayout(controls)
        layout.addWidget(self.staleLabel)
        layout.addWidget(self.buildBody(), 1)
        self.onProgramChanged()
        self.setResultActionsEnabled(False)

    def buildBody(self) -> QSplitter:
        self.plotCombo = QComboBox()
        self.plotCombo.setObjectName("plotCombo")
        self.plotCombo.currentIndexChanged.connect(self.onPlotChoiceChanged)
        self.wireLabel = QLabel("Wire")
        self.wireSpin = QSpinBox()
        self.wireSpin.setObjectName("wireSpin")
        self.wireSpin.setMinimum(1)
        self.wireSpin.valueChanged.connect(self.redrawPlot)
        plotControls = QHBoxLayout()
        plotControls.addWidget(QLabel("Plot"))
        plotControls.addWidget(self.plotCombo, 1)
        plotControls.addWidget(self.wireLabel)
        plotControls.addWidget(self.wireSpin)
        self.plotPanel = PlotPanel()
        plotSide = QWidget()
        plotLayout = QVBoxLayout(plotSide)
        plotLayout.setContentsMargins(0, 0, 0, 0)
        plotLayout.addLayout(plotControls)
        plotLayout.addWidget(self.plotPanel, 1)

        self.tableModel = ResultTableModel(self)
        self.tableView = QTableView()
        self.tableView.setObjectName("resultTable")
        self.tableView.setModel(self.tableModel)
        self.tableView.setAlternatingRowColors(True)
        self.summaryEdit = _monospaced("summaryEdit")
        self.consoleEdit = _monospaced("consoleEdit")
        self.detailTabs = PageTabWidget()
        self.detailTabs.addTab(self.tableView, "Table")
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

    def currentProgram(self) -> ProgramSpec:
        return self.programs[max(0, self.programCombo.currentIndex())]

    def onProgramChanged(self) -> None:
        program = self.currentProgram()
        self.titleLabel.setText(program.title)
        self.summaryLabel.setText(program.summary)
        files = " and ".join(program.outputFiles)
        self.sourceLabel.setText(
            f"Legacy program {program.sourceFile}, dated {program.sourceDate}; reads ENTRE.DAT, "
            f"writes {files}."
        )
        self.runButton.setText(f"Run {program.key}")

    # -- running --------------------------------------------------------------

    def isRunning(self) -> bool:
        return self.worker is not None

    def run(self) -> None:
        if self.isRunning():
            return
        program = self.currentProgram()
        try:
            value = self.inputProvider()
        except InputError as error:
            self.reportError(f"{program.key} Did Not Run", f"Fix the Strand tab first.\n{error}")
            return
        issues = inputValidation.validationIssues(value, program)
        if issues:
            self.reportError(
                f"{program.key} Did Not Run",
                f"{program.sourceFile} cannot run on these inputs.\n" + "\n".join(issues),
            )
            return
        self.startWorker(
            lambda hook: runAndPresent(program, value, hook),
            f"Running {program.key}",
            self.onRunSucceeded,
        )

    def startWorker(self, job, message: str, onSuccess: Callable[[object], None]) -> None:
        worker = AnalysisWorker(job, parent=self)
        # Connected before start: a quick job could otherwise finish unheard.
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

    def onWorkerCancelled(self) -> None:
        self.reportStatus(f"{self.busyWith} stopped.")

    def setBusy(self, busy: bool) -> None:
        self.runButton.setEnabled(not busy)
        self.programCombo.setEnabled(not busy)
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

    def onWorkerFailed(self, message: str) -> None:
        self.reportError(f"{self.busyWith} Failed", message)

    def onWorkerFinished(self) -> None:
        self.progressTimer.stop()
        if self.worker is not None:
            # `finished` is emitted just before the thread exits; deleting a
            # QThread that has not quite exited aborts the process.
            self.worker.wait()
            self.worker.deleteLater()
            self.worker = None
        self.setBusy(False)

    def onRunSucceeded(self, output: RunOutput) -> None:
        self.showOutput(output)
        result = output.result
        message = (
            f"{result.program.key}: {len(result.positions):,} positions × "
            f"{result.input.wireCount} wires in {result.elapsedSeconds:.2f} s."
        )
        deflection = result.deflection
        if deflection.deflection is Deflection.constantCurvature and 0 < deflection.ratio < 0.01:
            message += (
                f" ρ = {result.input.amplitude:g} m is far below ρc = {deflection.critical:.4g} m,"
                " so nearly every wire slips: is that an amplitude rather than a radius?"
            )
        self.reportStatus(message)

    def markInputsChanged(self) -> None:
        """The shown result no longer matches the Strand tab."""
        self.staleLabel.setVisible(self.output is not None)

    # -- showing a result ---------------------------------------------------------

    def showOutput(self, output: RunOutput) -> None:
        self.output = output
        self.staleLabel.setVisible(False)
        self.tableModel.setTable(output.table)
        self.tableView.resizeColumnsToContents()
        self.summaryEdit.setPlainText(output.summaryText)
        self.consoleEdit.setPlainText(output.consoleText)
        previous = self.plotCombo.currentData()
        self.plotCombo.blockSignals(True)
        self.plotCombo.clear()
        for choice in choicesFor(output.result):
            self.plotCombo.addItem(choice.label, choice.key)
        index = self.plotCombo.findData(previous)
        self.plotCombo.setCurrentIndex(max(0, index))
        self.plotCombo.blockSignals(False)
        self.wireSpin.blockSignals(True)
        self.wireSpin.setMaximum(output.result.input.wireCount)
        self.wireSpin.blockSignals(False)
        self.setResultActionsEnabled(True)
        self.onPlotChoiceChanged()

    def onPlotChoiceChanged(self) -> None:
        usesWire = False
        if self.output is not None:
            key = self.plotCombo.currentData()
            usesWire = any(c.key == key and c.usesWire for c in choicesFor(self.output.result))
        self.wireLabel.setVisible(usesWire)
        self.wireSpin.setVisible(usesWire)
        self.redrawPlot()

    def redrawPlot(self) -> None:
        if self.output is None:
            self.plotPanel.setDrawing(None)
            return
        result, key, wire = self.output.result, self.plotCombo.currentData(), self.wireSpin.value()
        self.plotPanel.setDrawing(
            lambda figure, theme: drawResult(figure, theme, result, key, wire - 1)
        )

    # -- exporting ------------------------------------------------------------

    def exportFolder(self) -> str:
        folder = settingsService.openSettings().value(lastExportFolderKey, "")
        return str(folder) if folder and Path(str(folder)).is_dir() else str(Path.home())

    def exportLegacyFiles(self) -> None:
        if self.output is None or self.isRunning():
            return
        result = self.output.result
        names = legacyOutputService.legacyFileNames(result.program)
        folder = QFileDialog.getExistingDirectory(
            self, f"Folder for {', '.join(names)}", self.exportFolder()
        )
        if folder:
            self.writeLegacyFilesTo(Path(folder))

    def writeLegacyFilesTo(self, folder: Path) -> None:
        result = self.output.result
        names = legacyOutputService.legacyFileNames(result.program)
        existing = [name for name in names if (folder / name).exists()]
        if existing and not self.confirmOverwrite(folder, existing):
            self.reportStatus("Nothing exported.")
            return
        settingsService.writeValue(lastExportFolderKey, str(folder))
        self.startWorker(
            lambda hook: legacyOutputService.writeLegacyFiles(result, folder, overwrite=True),
            f"Writing {result.program.key} files",
            lambda paths: self.reportStatus(f"Wrote {len(paths)} files to {folder}."),
        )

    def confirmOverwrite(self, folder: Path, existing: list[str]) -> bool:
        """The programs refused to overwrite (STATUS='NEW'); ask instead."""
        answer = QMessageBox.question(
            self,
            "Replace Files?",
            f"{folder} already holds {', '.join(existing)}.\n\nReplace them?",
        )
        return answer == QMessageBox.StandardButton.Yes

    def exportCsv(self) -> None:
        if self.output is None:
            return
        program = self.output.result.program
        target = str(Path(self.exportFolder()) / f"{program.key}.csv")
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", target, "CSV Files (*.csv)")
        if path:
            self.writeCsvTo(Path(path))

    def writeCsvTo(self, path: Path) -> None:
        try:
            writeCsv(self.output.table, path)
        except OSError as error:
            self.reportError(
                "Could Not Export the CSV", f"Writing {path} failed: {error.strerror or error}"
            )
            return
        settingsService.writeValue(lastExportFolderKey, str(path.parent))
        self.reportStatus(f"Exported {self.output.table.rowCount:,} rows to {path}.")
