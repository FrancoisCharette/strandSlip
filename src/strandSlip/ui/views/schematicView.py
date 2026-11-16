"""The Input tab's Schematics page: the strand between two posts, and its section.

Drawn from the values on the Numerical Entries page. The amplitude slot is A
for the sinusoid programs and ρ for RAYON, so the page asks which deflection
to draw; loading an example or a file picks the one it was written for.
Redrawing waits until the page is on screen, so typing on the other page
stays quick.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from strandSlip.models.legacyProgram import Deflection
from strandSlip.models.strandInput import StrandInput
from strandSlip.services import strandGeometry
from strandSlip.ui.plotting.strandSchematics import drawSchematics, programsFor
from strandSlip.ui.widgets.plotPanel import PlotPanel

redrawDelayMs = 150  # after the last change, so a burst of edits draws once

deflectionLabels = {
    Deflection.sinusoid: "Sinusoid, Y = A sin(2πX/λ)",
    Deflection.constantCurvature: "Constant Curvature, Radius ρ",
}


class SchematicView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.value: StrandInput | None = None
        self.stale = True
        self.deflectionCombo = QComboBox()
        self.deflectionCombo.setObjectName("deflectionCombo")
        for deflection, label in deflectionLabels.items():
            # Qt hands an enum back as its plain string: store that, convert on the way out.
            self.deflectionCombo.addItem(f"{label} ({programsFor(deflection)})", deflection.value)
        self.deflectionCombo.currentIndexChanged.connect(self.scheduleRedraw)
        self.plotPanel = PlotPanel()
        self.redrawTimer = QTimer(self)
        self.redrawTimer.setSingleShot(True)
        self.redrawTimer.setInterval(redrawDelayMs)
        self.redrawTimer.timeout.connect(self.redraw)

        row = QHBoxLayout()
        row.addWidget(QLabel("Deflection Drawn:"))
        row.addWidget(self.deflectionCombo)
        row.addStretch()
        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.plotPanel, 1)

    def currentDeflection(self) -> Deflection:
        return Deflection(self.deflectionCombo.currentData())

    def setInput(self, value: StrandInput | None) -> None:
        """The values on the other page, or None while some are not numbers."""
        self.value = value
        self.scheduleRedraw()

    def chooseDeflectionFor(self, value: StrandInput) -> None:
        """A whole new set of values, from an example or a file: draw what it was made for."""
        index = self.deflectionCombo.findData(strandGeometry.likelyDeflection(value).value)
        self.deflectionCombo.setCurrentIndex(index)

    def scheduleRedraw(self) -> None:
        self.stale = True
        if self.isVisible():
            self.redrawTimer.start()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self.stale:
            self.redraw()

    def redraw(self) -> None:
        self.redrawTimer.stop()
        self.stale = False
        value, deflection = self.value, self.currentDeflection()
        self.plotPanel.setDrawing(
            lambda figure, theme: drawSchematics(figure, theme, value, deflection)
        )
