"""Run any of the six analysis programs by its spec, and prepare what the views show."""

from __future__ import annotations

from dataclasses import dataclass

from strandSlip.models.analysisResults import AnalysisResult, ResultTable
from strandSlip.models.legacyProgram import Analysis, ProgramSpec
from strandSlip.models.strandInput import StrandInput
from strandSlip.services import constantsReport, legacyOutputService
from strandSlip.services.analysisErrors import ProgressHook
from strandSlip.services.displacementService import runDisplacement
from strandSlip.services.frictionService import runFriction
from strandSlip.services.resultTableService import resultTable
from strandSlip.services.stiffnessService import runStiffness


@dataclass(frozen=True, eq=False)
class RunOutput:
    """A result with its table and texts, prepared off the interface thread."""

    result: AnalysisResult
    table: ResultTable
    summaryText: str
    consoleText: str


def runProgram(
    program: ProgramSpec, value: StrandInput, hook: ProgressHook | None = None
) -> AnalysisResult:
    if program.analysis is Analysis.stiffness:
        return runStiffness(value, program, hook)
    if program.analysis is Analysis.friction:
        return runFriction(value, hook)
    if program.analysis is Analysis.displacement:
        return runDisplacement(value, hook)
    raise ValueError(f"{program.key} has nothing to run: it only prepares ENTRE.DAT")


def summaryText(result: AnalysisResult) -> str:
    text = constantsReport.formatLines(constantsReport.describeResult(result))
    records = legacyOutputService.summaryRecords(result)
    if records:
        program = result.program
        text += f"\n\n{program.summaryFile}, as {program.sourceFile} wrote it:\n\n"
        text += "\n".join(records)
    return text + "\n"


def runAndPresent(
    program: ProgramSpec, value: StrandInput, hook: ProgressHook | None = None
) -> RunOutput:
    result = runProgram(program, value, hook)
    console = legacyOutputService.screenText(
        legacyOutputService.consoleRecords(result), limit=legacyOutputService.consoleLineLimit
    )
    return RunOutput(result, resultTable(result), summaryText(result), console)
