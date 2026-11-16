"""The files and screen output of the 1990 programs.

Every FORMAT below is copied from the .FOR source, with its statement label,
so a record can be checked against the listing. Result and summary files are
written the way the programs wrote them; the screen output, which DOS users
captured with `SINUS > SINUS.OUT`, is rebuilt as <PROGRAM>.OUT.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from strandSlip.models.analysisResults import (
    AnalysisResult,
    DisplacementResult,
    FrictionResult,
    StiffnessResult,
    slipAbove,
    slipBelow,
)
from strandSlip.models.legacyProgram import Deflection, ProgramSpec
from strandSlip.services import entreFileService
from strandSlip.services.fortranFormat import formatRecord

logger = logging.getLogger(__name__)

thetaFormat = "3X,I2,6X,F9.4"  # 4, every program
stiffnessRowFormat = "1X,F8.4,1X,F10.4,2X,F6.4,1X,F6.4,1X,F8.3,2X,F6.4,1X,F6.3,1X,F8.3"  # 21
frictionRowFormat = "3X,F9.4,3X,F12.7,3X,I3"  # FRICTION 10
displacementRowFormat = "1X,F7.4,3X,E12.5,3X,I3,3X,E11.5,3X,E11.5"  # DEPLACE 10
stickAboveFormat = "1X,F9.5,2X,I3,2X,E9.3"  # NSINUS 331
stickBelowFormat = "1X,E11.5,2X,I3,2X,E9.3"  # NSINUS 332
slipAboveFormat = "1X,F9.5,2X,I3,2X,F9.7,2X,F9.7,2X,E9.3,2X,E9.3,2X,E9.3"  # NSINUS 333
slipBelowFormat = "1X,E11.5,2X,I3,2X,F9.7,2X,F9.7,2X,E9.3,2X,E9.3,2X,E9.3"  # NSINUS 334

amplitudeFormat = (  # 40
    "2X,'AMPLITUDE=',E9.4,/,2X,'R. DU NOYEAU=',F5.3,/,2X,'COEFFICIENT DE POISSON=',F5.3"
)
radiusFormat = (  # RAYON 40
    "2X,'RAYON DE COUR.=',F9.3,/,2X,'R. DU NOYEAU=',F5.3,/,2X,'COEFFICIENT DE POISSON=',F5.3"
)
angleFormat = (  # 41
    "2X,'ANGLE D ENROULEMENT=',F7.5,/,2X,'R. DU TORON=',E9.4,/,2X,'MODULE DE YOUNG DU TORON=',E9.4"
)
pressureFormat = (  # 42
    "2X,'PRESSION D APPUI=',E9.4e2,/,2X,'LONGUEUR D ONDE=',F5.2,/,2X,'LONGUEUR DU CABLE=',F9.3"
)
pressureRadiusFormat = "2X,'PRESSION D APPUI=',E9.4e2,/,2X,'LONGUEUR DU CABLE=',F9.3"  # RAYON 42
waveFrictionFormat = "2X,'LONGUEUR D ONDE=',F5.2,/,2X,'LONGUEUR DU CABLE=',F9.3"  # FRICTION 42
criticalAmplitudeFormat = (  # 43
    "2X,'AMPL. CRITIQUE=',E9.4,/,2X,'COEFF. F=',F7.4,/,2X,'PITCH=',F7.4"
)
criticalRadiusFormat = (  # RAYON 43
    "2X,'RAYON CRITIQUE=',E9.4,/,2X,'COEFF. F=',F7.4,/,2X,'PITCH=',F7.4"
)
frictionPitchFormat = "2X,'COEFF. F=',F7.4,/,2X,'PITCH=',F7.4"  # FRICTION 43
areaFormat = (  # 44
    "2X,'AIRE DU TORON=',E9.4,/,2X,'INCREMENT EN X=',F9.5,"
    "/,2X,'INCREMENT EN XPAS=',F9.5,/,2X,'CONSTANTE EQ9=',E12.7"
)
areaFrictionFormat = (  # FRICTION 44
    "2X,'AIRE DU TORON=',E9.4,/,2X,'INCREMENT EN X=',F9.5,/,2X,'CONSTANTE EQ9=',E12.7"
)
wiresFormat = (  # 45
    "2X,'NOMBRE DE FIL:',I2,/,2X,'MOD. DE YOUG DU NOYEAU=',E9.4,/,2X,'F SELON EQUATION 2b=',E9.4"
)
tensionAmplitudeFormat = (  # 46
    "2X,'TENSION DANS LE FIL=',E9.4,/,2X,'RAPPORT D AMP.=',E9.4,"
    "/,2X,'GAMMA SELON EQUATION 17=',E9.4"
)
tensionRadiusFormat = (  # RAYON 46
    "2X,'TENSION DANS LE FIL=',E9.4,/,2X,'RAPPORT DE RAYON=',E9.4,"
    "/,2X,'GAMMA SELON EQUATION 17=',E9.4"
)
tensionFrictionFormat = "2X,'TENSION DANS LE FIL=',E9.4"  # FRICTION 46

consoleLineLimit = 50_000  # what the Console view shows; .OUT files are complete


def stiffnessRow(result: StiffnessResult, index: int) -> str:
    """WRITE(1,21) X,RIG,TMXT,FMXYT,FMXZT,FXT,FYT,FZT for one position."""
    columns = (
        result.positions,
        result.stiffness,
        result.torsion,
        result.momentY,
        result.momentZ,
        result.forceX,
        result.forceY,
        result.forceZ,
    )
    return formatRecord(stiffnessRowFormat, [float(column[index]) for column in columns])


def stiffnessRows(result: StiffnessResult) -> list[str]:
    """RESSIN.DAT / RESFIN.DAT / RESRAY.DAT: one record per position, X = 0 skipped."""
    return [stiffnessRow(result, int(index)) for index in np.flatnonzero(result.written)]


def iterFrictionRows(result: FrictionResult) -> Iterator[str]:
    """F_RESFIN.DAT: X, CFX and the wire number, wire by wire."""
    for row, x in enumerate(result.positions):
        for wire in range(result.input.wireCount):
            yield formatRecord(
                frictionRowFormat, [float(x), float(result.frictionDemand[row, wire]), wire + 1]
            )


def frictionRows(result: FrictionResult) -> list[str]:
    return list(iterFrictionRows(result))


def iterDisplacementRows(result: DisplacementResult) -> Iterator[str]:
    """D_RESFIN.DAT: X, DX times 10 000, the wire, and the two brackets."""
    for row, x in enumerate(result.positions):
        for wire in range(result.input.wireCount):
            yield formatRecord(
                displacementRowFormat,
                [
                    float(x),
                    float(result.displacementScaled[row, wire]),
                    wire + 1,
                    float(result.termA[row, wire]),
                    float(result.termB[row, wire]),
                ],
            )


def displacementRows(result: DisplacementResult) -> list[str]:
    return list(iterDisplacementRows(result))


def stiffnessSummary(result: StiffnessResult) -> list[str]:
    """DONSIN.DAT / DONNE1.DAT / DONRAY.DAT: seven WRITEs of formats 40 to 46."""
    value, constants, deflection = result.input, result.constants, result.deflection
    if deflection.deflection is Deflection.constantCurvature:
        return [
            formatRecord(radiusFormat, [value.amplitude, value.coreRadius, value.corePoisson]),
            formatRecord(angleFormat, [value.helixAngle, value.wireRadius, value.wireModulus]),
            formatRecord(pressureRadiusFormat, [constants.bearingPressure, value.strandLength]),
            formatRecord(
                criticalRadiusFormat, [deflection.critical, value.frictionLimit, constants.pitch]
            ),
            formatRecord(
                areaFormat,
                [
                    constants.wireArea,
                    constants.positionStep,
                    result.searchStep,
                    deflection.frictionConstant,
                ],
            ),
            formatRecord(
                wiresFormat, [value.wireCount, value.coreModulus, constants.poissonFactor]
            ),
            formatRecord(
                tensionRadiusFormat, [value.wireTension, deflection.ratio, constants.gamma]
            ),
        ]
    return [
        formatRecord(amplitudeFormat, [value.amplitude, value.coreRadius, value.corePoisson]),
        formatRecord(angleFormat, [value.helixAngle, value.wireRadius, value.wireModulus]),
        formatRecord(
            pressureFormat, [constants.bearingPressure, value.wavelength, value.strandLength]
        ),
        formatRecord(
            criticalAmplitudeFormat, [deflection.critical, value.frictionLimit, constants.pitch]
        ),
        formatRecord(
            areaFormat,
            [
                constants.wireArea,
                constants.positionStep,
                result.searchStep,
                deflection.frictionConstant,
            ],
        ),
        formatRecord(wiresFormat, [value.wireCount, value.coreModulus, constants.poissonFactor]),
        formatRecord(
            tensionAmplitudeFormat, [value.wireTension, deflection.ratio, constants.gamma]
        ),
    ]


def frictionSummary(result: FrictionResult) -> list[str]:
    """F_DONNE1.DAT"""
    value, constants = result.input, result.constants
    return [
        formatRecord(amplitudeFormat, [value.amplitude, value.coreRadius, value.corePoisson]),
        formatRecord(angleFormat, [value.helixAngle, value.wireRadius, value.wireModulus]),
        formatRecord(waveFrictionFormat, [value.wavelength, value.strandLength]),
        formatRecord(frictionPitchFormat, [value.frictionLimit, constants.pitch]),
        formatRecord(
            areaFrictionFormat,
            [constants.wireArea, constants.positionStep, result.deflection.frictionConstant],
        ),
        formatRecord(wiresFormat, [value.wireCount, value.coreModulus, constants.poissonFactor]),
        formatRecord(tensionFrictionFormat, [value.wireTension]),
    ]


def _thetaLines(result: AnalysisResult) -> Iterator[str]:
    thetas = result.constants.thetas
    for index in range(1, len(thetas)):
        yield formatRecord(thetaFormat, [index + 1, float(thetas[index])])


def _slipZoneLines(result: StiffnessResult, row: int) -> Iterator[str]:
    """NSINUS's line per wire at one position (formats 331 to 334)."""
    wires, x = result.wires, float(result.positions[row])
    for wire in range(result.input.wireCount):
        zone = int(wires.zone[row, wire])
        ex = float(wires.elongation[row, wire])
        if zone == slipAbove or zone == slipBelow:
            spec = slipAboveFormat if zone == slipAbove else slipBelowFormat
            yield formatRecord(
                spec,
                [
                    x,
                    wire + 1,
                    float(wires.lowerBound[row, wire]),
                    float(wires.upperBound[row, wire]),
                    float(wires.lowerDisplacement[row, wire]),
                    float(wires.upperDisplacement[row, wire]),
                    ex,
                ],
            )
        else:
            belowZero = wires.frictionDemand[row, wire] < 0
            yield formatRecord(
                stickBelowFormat if belowZero else stickAboveFormat, [x, wire + 1, ex]
            )


def consoleRecords(result: AnalysisResult) -> Iterator[str]:
    """Every record the program wrote to the screen, in order."""
    yield from _thetaLines(result)
    if isinstance(result, StiffnessResult):
        for row in range(len(result.positions)):
            if result.program.listsSlipZones:
                yield from _slipZoneLines(result, row)
            if result.written[row]:
                yield stiffnessRow(result, row)
    elif isinstance(result, FrictionResult):
        yield from iterFrictionRows(result)
    else:
        yield from iterDisplacementRows(result)


def screenText(records: Iterator[str], limit: int | None = None) -> str:
    """Records as the screen showed them.

    The screen used Fortran carriage control: the first character of a
    record (the 1X or 2X every FORMAT starts with) was not printed.
    """
    lines: list[str] = []
    for count, record in enumerate(records):
        if limit is not None and count >= limit:
            lines.append(
                f"... (stopped after {limit:,} lines; Export Legacy Files writes them all)"
            )
            break
        lines.extend(line[1:] if line.startswith(" ") else line for line in record.split("\n"))
    return "\n".join(lines) + "\n"


def summaryRecords(result: AnalysisResult) -> list[str]:
    """The summary file's WRITEs (DONSIN.DAT...); DEPLACE wrote none."""
    if isinstance(result, StiffnessResult):
        return stiffnessSummary(result)
    if isinstance(result, FrictionResult):
        return frictionSummary(result)
    return []


def legacyFileNames(program: ProgramSpec) -> list[str]:
    return [*program.outputFiles, "ENTRE.DAT", f"{program.key}.OUT"]


def legacyFiles(result: AnalysisResult) -> dict[str, str]:
    """File name to contents (records joined with \\n) for this run."""
    program = result.program
    if isinstance(result, StiffnessResult):
        rows = stiffnessRows(result)
    elif isinstance(result, FrictionResult):
        rows = frictionRows(result)
    else:
        rows = displacementRows(result)
    files: dict[str, str] = {}
    files[program.resultFile or f"{program.key}.DAT"] = "\n".join(rows) + ("\n" if rows else "")
    if program.summaryFile:
        files[program.summaryFile] = "\n".join(summaryRecords(result)) + "\n"
    files["ENTRE.DAT"] = entreFileService.formatEntreText(result.input)
    files[f"{program.key}.OUT"] = screenText(consoleRecords(result))
    return files


def writeLegacyFiles(result: AnalysisResult, folder: Path, overwrite: bool = False) -> list[Path]:
    """Write the run's files with DOS line endings.

    The programs opened their outputs STATUS='NEW' and stopped if a file was
    already there; here an existing file is an error unless `overwrite`.
    """
    files = legacyFiles(result)
    targets = {name: folder / name for name in files}
    existing = [name for name, path in targets.items() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(", ".join(existing))
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        dosText = text.replace("\n", entreFileService.recordSeparator)
        targets[name].write_bytes(dosText.encode("cp437"))
    logger.info("Wrote %s to %s", ", ".join(files), folder)
    return list(targets.values())
