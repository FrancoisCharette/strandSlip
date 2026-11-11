"""The seven 1990 Fortran programs and what each one did.

All but ENTRE read ENTRE.DAT; each wrote its results to fixed file names in
the current directory, opened STATUS='NEW' so a second run failed until the
previous files were deleted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Analysis(StrEnum):
    input = "input"
    stiffness = "stiffness"
    friction = "friction"
    displacement = "displacement"


class Deflection(StrEnum):
    sinusoid = "sinusoid"  # Y = A sin(2 pi X / lambda), equation 18
    constantCurvature = "constantCurvature"  # Y = -X^2 / (2 rho), equation 9


class Assembly(StrEnum):
    strand = "strand"  # wires around a core ("toron", RF/EF/RA/EA)
    cable = "cable"  # strands around a core ("cable toronne", RT/ET/RN/EN)


@dataclass(frozen=True)
class ProgramSpec:
    key: str
    sourceFile: str
    sourceDate: str  # file date of the .FOR
    title: str
    summary: str
    analysis: Analysis
    deflection: Deflection | None
    assembly: Assembly
    slipSearchDivisor: int  # DX = PITCH / divisor when hunting for slip bounds; 0 if unused
    resultFile: str | None
    summaryFile: str | None
    listsSlipZones: bool = False  # NSINUS prints every wire's slip bounds

    @property
    def outputFiles(self) -> tuple[str, ...]:
        return tuple(name for name in (self.resultFile, self.summaryFile) if name)


ENTRE = ProgramSpec(
    key="ENTRE",
    sourceFile="ENTRE.FOR",
    sourceDate="1990-07-15",
    title="Input File Preparation",
    summary="Asks for the fifteen strand, deflection and position values and writes "
    "ENTRE.DAT for SINUS.FOR or RAYON.FOR (0 where a question does not apply).",
    analysis=Analysis.input,
    deflection=None,
    assembly=Assembly.strand,
    slipSearchDivisor=0,
    resultFile="ENTRE.DAT",
    summaryFile=None,
)

SINUS = ProgramSpec(
    key="SINUS",
    sourceFile="SINUS.FOR",
    sourceDate="1990-07-18",
    title="Strand Stiffness, Sinusoidal Deflection",
    summary="Stiffness of a strand (wires around a core) along X for a deflection "
    "following a pure sinusoid, from the equations of report #1 (SM-90-03).",
    analysis=Analysis.stiffness,
    deflection=Deflection.sinusoid,
    assembly=Assembly.strand,
    slipSearchDivisor=1000,
    resultFile="RESSIN.DAT",
    summaryFile="DONSIN.DAT",
)

BSINUS = ProgramSpec(
    key="BSINUS",
    sourceFile="BSINUS.FOR",
    sourceDate="1990-06-12",
    title="Stranded Cable Stiffness, Sinusoidal Deflection",
    summary="Stiffness of a stranded cable (strands around a core) along X for a "
    "deflection following a pure sinusoid. Same equations as SINUS, with the wire "
    "fields read as strand properties.",
    analysis=Analysis.stiffness,
    deflection=Deflection.sinusoid,
    assembly=Assembly.cable,
    slipSearchDivisor=1000,
    resultFile="RESFIN.DAT",
    summaryFile="DONNE1.DAT",
)

NSINUS = ProgramSpec(
    key="NSINUS",
    sourceFile="NSINUS.FOR",
    sourceDate="1990-06-21",
    title="Stranded Cable Stiffness, Slip-Zone Listing",
    summary="BSINUS with a ten times finer slip-bound search (p/10000) that lists, for "
    "every strand at every position, where slipping starts and ends and the core "
    "displacement there.",
    analysis=Analysis.stiffness,
    deflection=Deflection.sinusoid,
    assembly=Assembly.cable,
    slipSearchDivisor=10000,
    resultFile="RESFIN.DAT",
    summaryFile="DONNE1.DAT",
    listsSlipZones=True,
)

RAYON = ProgramSpec(
    key="RAYON",
    sourceFile="RAYON.FOR",
    sourceDate="1990-07-19",
    title="Strand Stiffness, Constant Radius of Curvature",
    summary="Stiffness of a strand along X for a deflection with a constant radius of "
    "curvature. Reads the amplitude field as the radius of curvature and ignores the "
    "wavelength.",
    analysis=Analysis.stiffness,
    deflection=Deflection.constantCurvature,
    assembly=Assembly.strand,
    slipSearchDivisor=1000,
    resultFile="RESRAY.DAT",
    summaryFile="DONRAY.DAT",
)

FRICTION = ProgramSpec(
    key="FRICTION",
    sourceFile="FRICTION.FOR",
    sourceDate="1990-06-21",
    title="Required Friction Coefficient",
    summary="Friction coefficient each wire needs to stay stuck to the core, along X, "
    "for the sinusoidal deflection (equation 19 of report #1).",
    analysis=Analysis.friction,
    deflection=Deflection.sinusoid,
    assembly=Assembly.cable,
    slipSearchDivisor=0,
    resultFile="F_RESFIN.DAT",
    summaryFile="F_DONNE1.DAT",
)

DEPLACE = ProgramSpec(
    key="DEPLACE",
    sourceFile="DEPLACE.FOR",
    sourceDate="1990-06-21",
    title="Core Surface Displacement",
    summary="Displacement of the core surface along each contact helix, along X, for the "
    "sinusoidal deflection (equation 23 of report #1), written times 10 000.",
    analysis=Analysis.displacement,
    deflection=Deflection.sinusoid,
    assembly=Assembly.cable,
    slipSearchDivisor=0,
    resultFile="D_RESFIN.DAT",
    summaryFile=None,
)

allPrograms: tuple[ProgramSpec, ...] = (ENTRE, SINUS, BSINUS, NSINUS, RAYON, FRICTION, DEPLACE)
programByKey: dict[str, ProgramSpec] = {program.key: program for program in allPrograms}
