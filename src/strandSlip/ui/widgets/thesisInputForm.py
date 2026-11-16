"""The keyboard answers of a 1992 program, as a form.

Each field is a question the program asked; it shows only for the programs
and calculations that ask it, and its tooltip quotes the prompt. The typed
approximations answer, in order, the questions the program asks only when an
automatic approximation fails.
"""

from __future__ import annotations

import re

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QWidget,
)

from strandSlip.models.thesisInput import SinusoidChoice, ThesisInput
from strandSlip.models.thesisProgram import ThesisDeflection, ThesisModel, ThesisProgramSpec
from strandSlip.services.analysisErrors import InputError
from strandSlip.services.thesisParameters import ThesisParameters

choiceLabels = {
    SinusoidChoice.wholeWavelength: "1. Energy over the whole wavelength (θi = 90°)",
    SinusoidChoice.displacementRatio: "2. Displacement difference at λ/4 (θi = 0°)",
    SinusoidChoice.oneHalfPitch: "3. One half lay length (θi = 90°)",
}
approximationHints = {
    "CONTRHOB": "XB1, one per question (the second bound is set to 0.5 − XB1)",
    "CONTSIN": "XB1 then XB2, a pair per question",
    "ZETARHOB": "XB1C = XB1 − XINF, one per question; usually below the value tried",
    "ZETASIN": "XB1C = XB1 − XINF, one per question; usually below the value tried",
}
defaults = ThesisInput()


def _numberEdit(name: str, value: float, prompt: str) -> QLineEdit:
    edit = QLineEdit(f"{value:g}")
    edit.setObjectName(name)
    edit.setMaximumWidth(160)
    edit.setToolTip(f"The program asked: «{prompt}»")
    return edit


class ThesisInputForm(QGroupBox):
    """The answers for one deflection's three programs."""

    changed = Signal()

    def __init__(self, deflection: ThesisDeflection, parent: QWidget | None = None) -> None:
        super().__init__("Keyboard Answers", parent)
        self.deflection = deflection
        self.program: ThesisProgramSpec | None = None
        layout = self.formLayout = QFormLayout(self)
        self.choiceCombo = QComboBox()
        self.choiceCombo.setObjectName("choiceCombo")
        for choice, label in choiceLabels.items():
            self.choiceCombo.addItem(label, int(choice))
        self.choiceCombo.setCurrentIndex(2)
        self.choiceCombo.setToolTip("The program asked: «Entrez votre choix:»")
        self.radiusEdit = _numberEdit(
            "radiusEdit", defaults.radius, "Entrez le rayon de courbure adim.:"
        )
        self.wavelengthEdit = _numberEdit(
            "wavelengthEdit", defaults.wavelength,
            "Entrez un nombre pair de pas par longueur d onde:",
        )  # fmt: skip
        self.amplitudeEdit = _numberEdit(
            "amplitudeEdit", defaults.amplitude, "Entrez l amplitude adimensionnelle:"
        )
        self.complianceEdit = _numberEdit(
            "complianceEdit", defaults.compliance, "Entrez le facteur de complaisance GAMMA1:"
        )
        self.turnsEdit = _numberEdit(
            "turnsEdit", defaults.turns, "Nombre de tour de l origine (XTOUR) :"
        )
        self.profileCheck = QCheckBox("Displacement, strain and friction along it")
        self.profileCheck.setObjectName("profileCheck")
        self.profileCheck.setChecked(defaults.profile)
        self.profileCheck.setToolTip(
            "The program asked: «Désirez-vous faire calculer le déplacement, la déformation "
            "et le rapport de friction le long du demi-pas (0=>OUI, 1=>NON):»"
        )
        self.approximationsEdit = QLineEdit()
        self.approximationsEdit.setObjectName("approximationsEdit")
        self.approximationsEdit.setPlaceholderText("e.g. 0.1  0.08 (none: stop where it asks)")
        self.approximationsHint = QLabel()
        self.approximationsHint.setEnabled(False)  # muted
        self.approximationsHint.setWordWrap(True)
        self.setMaximumWidth(720)
        self.rows: dict[str, QWidget] = {}
        for key, label, widget in (
            ("choice", "Calculation", self.choiceCombo),
            ("radius", "Radius of curvature ρ/ρc", self.radiusEdit),
            ("wavelength", "Lay lengths per wavelength λ/p", self.wavelengthEdit),
            ("amplitude", "Amplitude A/Ac", self.amplitudeEdit),
            ("compliance", "Compliance factor γ1", self.complianceEdit),
            ("turns", "Half lay length starting at XTOUR", self.turnsEdit),
            ("profile", "Profiles along the half lay length", self.profileCheck),
            ("approximations", "Typed approximations", self.approximationsEdit),
        ):
            layout.addRow(label, widget)
            self.rows[key] = widget
        layout.addRow("", self.approximationsHint)
        for edit in (self.radiusEdit, self.wavelengthEdit, self.amplitudeEdit,
                     self.complianceEdit, self.turnsEdit, self.approximationsEdit):  # fmt: skip
            edit.textEdited.connect(self.changed)
        self.profileCheck.toggled.connect(self.changed)
        self.choiceCombo.currentIndexChanged.connect(self.onChoiceChanged)

    def fillFromStrand(self, parameters: ThesisParameters) -> list[str]:
        """This deflection's ratios and γ1 from the Strand tab; what was filled, as text.

        InputError when the strand lacks what this deflection needs.
        """
        if self.deflection is ThesisDeflection.constantRadius:
            if parameters.radiusRatio is None:
                raise InputError(["The amplitude field, read as the radius ρ, is 0."])
            filled = [("ρ/ρc", self.radiusEdit, parameters.radiusRatio)]
        else:
            if parameters.waveRatio is None or parameters.amplitudeRatio is None:
                raise InputError(["The wavelength λ is 0, so λ/p and A/Ac cannot be computed."])
            filled = [
                ("λ/p", self.wavelengthEdit, parameters.waveRatio),
                ("A/Ac", self.amplitudeEdit, parameters.amplitudeRatio),
            ]
        filled.append(("γ1", self.complianceEdit, parameters.compliance))
        for _name, edit, number in filled:
            edit.setText(f"{number:.6g}")
        self.changed.emit()
        return [f"{name} = {number:.6g}" for name, _edit, number in filled]

    def _showRow(self, key: str, visible: bool) -> None:
        self.formLayout.setRowVisible(self.rows[key], visible)

    def setProgram(self, program: ThesisProgramSpec) -> None:
        self.program = program
        self.updateRows()

    def onChoiceChanged(self) -> None:
        self.updateRows()
        self.changed.emit()

    def currentChoice(self) -> SinusoidChoice:
        return SinusoidChoice(int(self.choiceCombo.currentData()))

    def updateRows(self) -> None:
        program = self.program
        sinusoid = self.deflection is ThesisDeflection.sinusoid
        oneHalf = not sinusoid or self.currentChoice() == SinusoidChoice.oneHalfPitch
        for key in ("choice", "wavelength", "amplitude"):
            self._showRow(key, sinusoid)
        self._showRow("radius", not sinusoid)
        self._showRow("turns", sinusoid and oneHalf)
        self._showRow("profile", oneHalf)
        compliance = program is not None and program.model is ThesisModel.compliance
        self._showRow("compliance", compliance)
        hint = approximationHints.get(program.key, "") if program else ""
        self._showRow("approximations", bool(hint))
        self.approximationsHint.setText(hint)
        self.approximationsHint.setVisible(bool(hint))

    def _number(self, edit: QLineEdit, label: str, issues: list[str]) -> float:
        try:
            return float(edit.text().replace(",", ".").strip())
        except ValueError:
            issues.append(f"{label}: «{edit.text()}» is not a number.")
            return 0.0

    def currentInput(self) -> ThesisInput:
        """The answers as typed; raises InputError for anything that is not a number."""
        issues: list[str] = []
        values = {
            "radius": self._number(self.radiusEdit, "Radius of curvature", issues),
            "wavelength": self._number(self.wavelengthEdit, "Lay lengths per wavelength", issues),
            "amplitude": self._number(self.amplitudeEdit, "Amplitude", issues),
            "compliance": self._number(self.complianceEdit, "Compliance factor", issues),
            "turns": self._number(self.turnsEdit, "XTOUR", issues),
        }
        approximations: list[float] = []
        for text in re.split(r"[,;\s]+", self.approximationsEdit.text().strip()):
            if not text:
                continue
            try:
                approximations.append(float(text))
            except ValueError:
                issues.append(f"Typed approximations: «{text}» is not a number.")
        if issues:
            raise InputError(issues)
        return ThesisInput(
            choice=self.currentChoice(),
            profile=self.profileCheck.isChecked(),
            approximations=tuple(approximations),
            **values,
        )
