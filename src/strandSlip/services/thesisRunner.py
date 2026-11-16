"""Run one of the six 1992 programs and prepare what the views and exports need."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

from strandSlip.models.thesisInput import SinusoidChoice, ThesisInput
from strandSlip.models.thesisProgram import ThesisDeflection, ThesisModel, ThesisProgramSpec
from strandSlip.models.thesisResults import ThesisResult
from strandSlip.services.analysisErrors import AnalysisError, InputError, ProgressHook
from strandSlip.services.legacyOutputService import screenText
from strandSlip.services.thesisPrograms import ProgramRun, runContRhob, runHardRhob, runZetaRhob
from strandSlip.services.thesisSession import ProgramWaits, ThesisSession
from strandSlip.services.thesisSinusoidPrograms import runContSin, runHardSin, runZetaSin

logger = logging.getLogger(__name__)

Runner = Callable[[ThesisInput, ThesisSession, ProgramRun], None]
runners: dict[str, Runner] = {
    "HARDRHOB": runHardRhob,
    "CONTRHOB": runContRhob,
    "ZETARHOB": runZetaRhob,
    "HARDSIN": runHardSin,
    "CONTSIN": runContSin,
    "ZETASIN": runZetaSin,
}
maxWavelength = 200.0  # lay lengths: choice 1 solves up to Λ/2 half lay lengths
maxApproximations = 200


def validationIssues(value: ThesisInput, program: ThesisProgramSpec) -> list[str]:
    """What the originals would divide by zero or overflow on, each with what to change."""
    issues: list[str] = []
    if program.deflection is ThesisDeflection.constantRadius:
        if not value.radius > 0.0:
            issues.append("The radius of curvature ρ/ρc must be greater than 0.")
    else:
        if int(value.choice) not in (1, 2, 3):
            issues.append("The calculation must be 1, 2 or 3.")
        if not 1.0 < value.wavelength <= maxWavelength:
            issues.append(
                f"The number of lay lengths per wavelength λ/p must lie between 1 and "
                f"{maxWavelength:g} (the thesis uses 28, an even number)."
            )
        if not value.amplitude > 0.0:
            issues.append("The amplitude A/Ac must be greater than 0.")
        if value.choice == SinusoidChoice.oneHalfPitch and not value.turns >= 0.0:
            issues.append("XTOUR, the start of the half lay length in turns, cannot be negative.")
    if program.model is ThesisModel.compliance and not value.compliance > 0.0:
        issues.append("The compliance factor γ1 must be greater than 0 (the thesis uses 0.06).")
    if len(value.approximations) > maxApproximations:
        issues.append(f"At most {maxApproximations} typed approximations.")
    return issues


def runThesisProgram(
    program: ThesisProgramSpec, value: ThesisInput, hook: ProgressHook | None = None
) -> ThesisResult:
    issues = validationIssues(value, program)
    if issues:
        raise InputError(issues)
    session = ThesisSession(value.approximations, hook)
    run = ProgramRun()
    started = time.perf_counter()
    pending = None
    try:
        runners[program.key](value, session, run)
    except ProgramWaits as waiting:
        pending = waiting.question
    except ZeroDivisionError as error:
        raise AnalysisError(
            f"{program.key} divided by zero ({error}); the 1992 program stopped here on a "
            "floating-point error. Try other values or another approximation."
        ) from error
    except OverflowError as error:
        raise AnalysisError(
            f"{program.key} overflowed ({error}): the exponentials of the compliance model "
            "grow with the position along the wavelength. Use fewer lay lengths per wavelength."
        ) from error
    session.closeLine()
    session.progress(1, 1)
    elapsed = time.perf_counter() - started
    logger.info("%s ran in %.2f s%s", program.key, elapsed, " (waits for input)" if pending else "")
    return ThesisResult(
        program=program,
        input=value,
        halfPitches=tuple(run.halfPitches),
        skipped=tuple(run.skipped),
        totalEnergy=run.totalEnergy,
        profile=run.profile,
        console=tuple(session.records),
        files={name: tuple(records) for name, records in session.files.items()},
        pendingQuestion=pending,
        approximationsUsed=tuple(session.approximationsUsed),
        elapsedSeconds=elapsed,
    )


def thesisScreenText(result: ThesisResult) -> str:
    """The screen as it looked: carriage-control column dropped."""
    return screenText(iter(result.console))


def legacyFiles(result: ThesisResult) -> dict[str, str]:
    """The .DAT files the run wrote, plus the screen as <PROGRAM>.OUT."""
    files = {name: "\n".join(records) + "\n" for name, records in result.files.items()}
    files[f"{result.program.key}.OUT"] = thesisScreenText(result)
    return files


def writeLegacyFiles(result: ThesisResult, folder: Path, overwrite: bool = False) -> list[Path]:
    """DOS line endings and code page 437, like the 1990 exports."""
    files = legacyFiles(result)
    targets = {name: folder / name for name in files}
    existing = [name for name, path in targets.items() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(", ".join(existing))
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        targets[name].write_bytes(text.replace("\n", "\r\n").encode("cp437"))
    logger.info("Wrote %s to %s", ", ".join(files), folder)
    return list(targets.values())
