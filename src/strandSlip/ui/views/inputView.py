"""ENTRE: the fifteen values every program reads, and what they imply.

The questions ENTRE.EXE asked one at a time become one form, on the Numerical
Entries page. What the programs derive from the answers (lay length, critical
amplitude...) updates as you type, and the file the values make is shown
exactly as it is written. The Schematics page draws the strand they describe:
its full length between two posts, and its section.
"""

from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from strandSlip.models.legacyProgram import ENTRE
from strandSlip.models.strandInput import StrandInput, inputFields, inputGroups
from strandSlip.models.strandPresets import allPresets, defaultPreset
from strandSlip.services import (
    constantsReport,
    entreFileService,
    inputValidation,
    settingsService,
)
from strandSlip.services.analysisErrors import InputError
from strandSlip.services.fieldText import FieldTextError, formatFieldValue, parseFieldText
from strandSlip.ui.views.schematicView import SchematicView
from strandSlip.ui.widgets.pageTabWidget import PageTabWidget
from strandSlip.ui.widgets.reportingView import ReportingView

lastFolderKey = "files/lastFolder"
rightAligned = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
invalidStyle = 'QLineEdit[invalid="true"] { border: 1px solid #d03b3b; }'


def _hint(name: str, value: float | int, strandLength: float | None) -> str:
    """A friendlier reading of a value in SI units."""
    if name == "helixAngle":
        return f"= {math.degrees(value):.4f}°"
    if name in ("wireRadius", "coreRadius"):
        return f"= {value * 1000:.6g} mm"
    if name in ("wireModulus", "coreModulus"):
        return f"= {value / 1e9:.6g} GPa"
    if name == "positionCount" and strandLength and value:
        return f"step ΔX = CL/NPAS = {strandLength / value:.6g} m"
    if name == "amplitude":
        return "A for SINUS, ρ for RAYON"
    if name == "wavelength":
        return "ignored by RAYON"
    return ""


class InputView(ReportingView):
    """The Input tab."""

    inputChanged = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.edits: dict[str, QLineEdit] = {}
        self.hints: dict[str, QLabel] = {}
        self.fieldErrors: dict[str, str] = {}
        self.setStyleSheet(invalidStyle)

        self.presetCombo = QComboBox()
        for preset in allPresets:
            self.presetCombo.addItem(preset.name)
            self.presetCombo.setItemData(
                self.presetCombo.count() - 1, preset.description, Qt.ItemDataRole.ToolTipRole
            )
        self.loadPresetButton = QPushButton("Load Example")
        self.loadPresetButton.clicked.connect(self.onLoadPreset)
        self.openButton = QPushButton("Open ENTRE.DAT...")
        self.openButton.clicked.connect(self.openFile)
        self.saveButton = QPushButton("Save ENTRE.DAT As...")
        self.saveButton.clicked.connect(self.saveFile)
        self.fileLabel = QLabel("Values of the 1991 example, not saved to a file")
        self.fileLabel.setObjectName("fileLabel")
        self.fileLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Example:"))
        toolbar.addWidget(self.presetCombo)
        toolbar.addWidget(self.loadPresetButton)
        toolbar.addSpacing(16)
        toolbar.addWidget(self.openButton)
        toolbar.addWidget(self.saveButton)
        toolbar.addStretch()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.buildForm())
        splitter.addWidget(self.buildDerivedPanel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([640, 640])
        self.schematicView = SchematicView()
        self.pages = PageTabWidget()
        self.pages.setObjectName("inputPages")
        self.pages.addTab(splitter, "Numerical Entries")
        self.pages.addTab(self.schematicView, "Schematics")

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self.fileLabel)
        layout.addWidget(self.pages, 1)

        self.setInput(defaultPreset.input)

    def buildForm(self) -> QWidget:
        container = QWidget()
        column = QVBoxLayout(container)
        labels = {field.name: QLabel(f"{field.label}  {field.symbol}") for field in inputFields}
        # Each group is its own grid; one label width lines the fields up across them.
        labelWidth = max(label.sizeHint().width() for label in labels.values())
        unitWidth = max(QLabel(field.unit).sizeHint().width() for field in inputFields)
        for group in inputGroups:
            box = QGroupBox(group)
            grid = QGridLayout(box)
            grid.setColumnStretch(4, 1)
            grid.setColumnMinimumWidth(0, labelWidth)
            grid.setColumnMinimumWidth(2, unitWidth)
            grid.setColumnMinimumWidth(3, 90)
            row = 0
            for field in (f for f in inputFields if f.group == group):
                label = labels[field.name]
                edit = QLineEdit()
                edit.setObjectName(f"{field.name}Edit")
                edit.setMaximumWidth(220)
                edit.setToolTip(f"ENTRE.EXE asked: «{field.entrePrompt}»")
                edit.textEdited.connect(self.onFieldEdited)
                names = (
                    field.strandName
                    if field.strandName == field.cableName
                    else (f"{field.strandName} / {field.cableName}")
                )
                legacy = QLabel(names)
                legacy.setToolTip("Fortran variable: strand programs / cable programs")
                legacy.setEnabled(False)  # muted
                hint = QLabel("")
                hint.setEnabled(False)
                grid.addWidget(label, row, 0)
                grid.addWidget(edit, row, 1)
                grid.addWidget(QLabel(field.unit), row, 2)
                grid.addWidget(legacy, row, 3)
                grid.addWidget(hint, row, 4)
                self.edits[field.name] = edit
                self.hints[field.name] = hint
                row += 1
            column.addWidget(box)
        self.issuesLabel = QLabel("")
        self.issuesLabel.setObjectName("issuesLabel")
        self.issuesLabel.setWordWrap(True)
        self.issuesLabel.setStyleSheet("color: #d03b3b;")
        column.addWidget(self.issuesLabel)
        column.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        return scroll

    def buildDerivedPanel(self) -> QWidget:
        self.derivedTable = QTableWidget(0, 3)
        self.derivedTable.setObjectName("derivedTable")
        self.derivedTable.setHorizontalHeaderLabels(["Quantity", "Value", "Fortran · Note"])
        self.derivedTable.verticalHeader().setVisible(False)
        self.derivedTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.derivedTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        self.previewEdit = QPlainTextEdit()
        self.previewEdit.setObjectName("previewEdit")
        self.previewEdit.setReadOnly(True)
        self.previewEdit.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.previewEdit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("What the Programs Derive"))
        layout.addWidget(self.derivedTable, 3)
        layout.addWidget(QLabel("ENTRE.DAT as It Will Be Written"))
        layout.addWidget(self.previewEdit, 2)
        return panel

    # -- values -------------------------------------------------------------

    def setInput(self, value: StrandInput) -> None:
        for field, number in zip(inputFields, value.values(), strict=True):
            self.edits[field.name].setText(formatFieldValue(number))
        self.schematicView.chooseDeflectionFor(value)
        self.refresh()

    def parsedValues(self) -> dict[str, float | int]:
        values: dict[str, float | int] = {}
        self.fieldErrors = {}
        for field in inputFields:
            try:
                values[field.name] = parseFieldText(self.edits[field.name].text(), field.kind)
            except FieldTextError as error:
                self.fieldErrors[field.name] = f"{field.label} ({field.strandName}) {error}."
        return values

    def currentInput(self) -> StrandInput:
        """The form as a StrandInput; InputError lists every field that is not a number."""
        values = self.parsedValues()
        if self.fieldErrors:
            raise InputError(list(self.fieldErrors.values()))
        return StrandInput(**values)

    def refresh(self) -> None:
        values = self.parsedValues()
        for field in inputFields:
            edit = self.edits[field.name]
            invalid = field.name in self.fieldErrors
            if edit.property("invalid") != invalid:
                edit.setProperty("invalid", invalid)
                edit.style().unpolish(edit)
                edit.style().polish(edit)
            edit.setToolTip(
                self.fieldErrors.get(field.name) or f"ENTRE.EXE asked: «{field.entrePrompt}»"
            )
            number = values.get(field.name)
            self.hints[field.name].setText(
                "" if number is None else _hint(field.name, number, values.get("strandLength"))
            )
        if self.fieldErrors:
            self.showIssues(list(self.fieldErrors.values()))
            self.derivedTable.setRowCount(0)
            self.previewEdit.setPlainText("")
            self.schematicView.setInput(None)
            return
        value = StrandInput(**values)
        self.schematicView.setInput(value)
        self.previewEdit.setPlainText(entreFileService.formatEntreText(value))
        lines = constantsReport.describeInput(value)
        self.showIssues([] if lines else inputValidation.validationIssues(value, ENTRE))
        self.fillDerived(lines)

    def fillDerived(self, lines: list[constantsReport.ReportLine]) -> None:
        self.derivedTable.setRowCount(len(lines))
        for row, line in enumerate(lines):
            extras = " · ".join(part for part in (line.legacy, line.note) if part)
            for column, text in enumerate((line.quantity, line.value, extras)):
                item = QTableWidgetItem(text)
                if column == 1:
                    item.setTextAlignment(rightAligned)
                self.derivedTable.setItem(row, column, item)

    def showIssues(self, issues: list[str]) -> None:
        self.issuesLabel.setText("\n".join(issues))
        self.issuesLabel.setVisible(bool(issues))

    def onFieldEdited(self, _text: str) -> None:
        self.refresh()
        self.inputChanged.emit()

    # -- files and examples --------------------------------------------------

    def onLoadPreset(self) -> None:
        preset = allPresets[self.presetCombo.currentIndex()]
        self.setInput(preset.input)
        self.fileLabel.setText(f"Values of the example “{preset.name}”, not saved to a file")
        self.inputChanged.emit()
        self.reportStatus(f"Loaded the example: {preset.name}.")

    def startFolder(self) -> str:
        folder = settingsService.openSettings().value(lastFolderKey, "")
        return str(folder) if folder and Path(str(folder)).is_dir() else str(Path.home())

    def openFile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open ENTRE.DAT", self.startFolder(), "Input Files (*.DAT *.dat);;All Files (*)"
        )
        if path:
            self.loadFile(Path(path))

    def loadFile(self, path: Path) -> None:
        try:
            result = entreFileService.readEntreFile(path)
        except entreFileService.EntreFileError as error:
            self.reportError("Could Not Read the Input File", str(error))
            return
        self.setInput(result.input)
        settingsService.writeValue(lastFolderKey, str(path.parent))
        self.fileLabel.setText(f"Read from {path}")
        self.inputChanged.emit()
        if result.warnings:
            self.showIssues(["Read like the 1990 programs would, but note:", *result.warnings])
            self.reportStatus(f"Opened {path.name} with {len(result.warnings)} warning(s).")
        else:
            self.reportStatus(f"Opened {path}.")

    def saveFile(self) -> None:
        try:
            value = self.currentInput()
        except InputError as error:
            self.reportError("Nothing Saved", f"Some values are not numbers yet.\n{error}")
            return
        target = str(Path(self.startFolder()) / "ENTRE.DAT")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save ENTRE.DAT", target, "Input Files (*.DAT *.dat);;All Files (*)"
        )
        if path:
            self.saveTo(value, Path(path))

    def saveTo(self, value: StrandInput, path: Path) -> None:
        try:
            entreFileService.writeEntreFile(value, path)
        except OSError as error:
            self.reportError(
                "Could Not Save the Input File", f"Writing {path} failed: {error.strerror or error}"
            )
            return
        settingsService.writeValue(lastFolderKey, str(path.parent))
        self.fileLabel.setText(f"Saved to {path}")
        self.reportStatus(f"Saved {path}.")
