"""Tables and the summary text the 1992 program tabs show."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from strandSlip.models.analysisResults import ResultColumn, ResultTable
from strandSlip.models.thesisInput import SinusoidChoice
from strandSlip.models.thesisProgram import ThesisDeflection, ThesisModel, ThesisProgramSpec
from strandSlip.models.thesisResults import ThesisResult
from strandSlip.services.analysisErrors import ProgressHook
from strandSlip.services.thesisRunner import runThesisProgram, thesisScreenText

unknownNames = {
    ThesisModel.hardy: ("XIH", "PSIH"),
    ThesisModel.continuity: ("XIC", "PSIC"),
    ThesisModel.compliance: ("BTM", "ETM"),
}
choiceTitles = {
    SinusoidChoice.wholeWavelength: "energy over the wavelength (θi = 90°)",
    SinusoidChoice.displacementRatio: "relative displacement difference at λ/4 (θi = 0°)",
    SinusoidChoice.oneHalfPitch: "one half lay length (θi = 90°)",
}


def _column(header: str, legacy: str, values, integer: bool = False) -> ResultColumn:
    return ResultColumn(header, legacy, np.array(values, dtype=float), integer)


def halfPitchTable(result: ThesisResult) -> ResultTable:
    """One row per half lay length solved."""
    rows = result.halfPitches
    slope, offset = unknownNames[result.program.model]
    columns = [
        _column("Start ξ", "XINF", [h.start for h in rows]),
        _column("End ξ", "XSUP", [h.end for h in rows]),
        _column("Side", "ICOTE", [h.side for h in rows], integer=True),
        _column("First Bound ξ", "XB1", [h.lowerBound for h in rows]),
        _column("Second Bound ξ", "XB2", [h.upperBound for h in rows]),
        _column("Slope", slope, [h.slope for h in rows]),
        _column("Offset", offset, [h.offset for h in rows]),
        _column("Energy Dissipated", "DSP", [h.energy for h in rows]),
    ]
    if any(h.displacementRatio is not None for h in rows):
        ratios = [np.nan if h.displacementRatio is None else h.displacementRatio for h in rows]
        columns.append(_column("Displacement Ratio", "RDEP", ratios))
    if result.program.model is ThesisModel.compliance:
        columns += [
            _column("Regions", "NPORTION", [h.regions for h in rows], integer=True),
            _column("2δ at the Centre", "DFDEP", [h.centerDifference for h in rows]),
            _column("Macro-Slip Energy", "DMAC", [_orNan(h.macroEnergy) for h in rows]),
            _column("Micro-Slip in Macro", "DMICMAC", [_orNan(h.microInMacroEnergy) for h in rows]),
        ]
    return ResultTable(tuple(columns))


def _orNan(value: float | None) -> float:
    return np.nan if value is None else value


def profileTable(result: ThesisResult) -> ResultTable | None:
    """DEP.DAT, ELG.DAT and FRC.DAT (or ZETA*.DAT) side by side."""
    profile = result.profile
    if profile is None:
        return None
    return ResultTable(
        (
            ResultColumn("Position ξ", "X", profile.x),
            ResultColumn("Core Displacement", "DAME", profile.coreDisplacement),
            ResultColumn("Wire Displacement", "DFIL", profile.wireDisplacement),
            ResultColumn("Core Strain", "EAME", profile.coreStrain),
            ResultColumn("Wire Strain", "EFIL", profile.wireStrain),
            ResultColumn("Friction Ratio, Stuck", "FAME", profile.coreFriction),
            ResultColumn("Friction Ratio, Wire", "FFIL", profile.wireFriction),
        )
    )


def _inputLines(result: ThesisResult) -> list[str]:
    program, value = result.program, result.input
    lines = [f"{program.key} — {program.title}", f"Listing {program.sourceFile}, manual page "
             f"{program.page}; diskette directory {program.directory}.", ""]  # fmt: skip
    if program.deflection is ThesisDeflection.constantRadius:
        lines.append(f"Radius of curvature ρ/ρc = {value.radius:g}")
    else:
        lines.append(f"Calculation {int(value.choice)}: {choiceTitles[value.choice]}")
        lines.append(f"Lay lengths per wavelength λ/p = {value.wavelength:g}")
        lines.append(f"Amplitude A/Ac = {value.amplitude:g}")
        if value.choice == SinusoidChoice.oneHalfPitch:
            lines.append(f"Half lay length starting at XTOUR = {value.turns:g} turns")
    if program.model is ThesisModel.compliance:
        lines.append(f"Compliance factor γ1 = {value.compliance:g}")
    if result.approximationsUsed:
        typed = ", ".join(f"{a:g}" for a in result.approximationsUsed)
        lines.append(f"Approximations typed in: {typed}")
    unused = len(value.approximations) - len(result.approximationsUsed)
    if unused > 0:
        lines.append(f"({unused} approximation(s) given were not asked for.)")
    return lines


def summaryText(result: ThesisResult) -> str:
    lines = _inputLines(result)
    lines.append("")
    if result.pendingQuestion:
        lines += ["The program stopped to ask:", result.pendingQuestion, ""]
    for skipped in result.skipped:
        lines.append(f"Half lay length {skipped[0]:g} to {skipped[1]:g}: no macro-slip.")
    slope, offset = unknownNames[result.program.model]
    for h in result.halfPitches:
        lines.append(f"Half lay length {h.start:g} to {h.end:g}:")
        lines.append(f"  bounds XB1 = {h.lowerBound:.8g}, XB2 = {h.upperBound:.8g}")
        lines.append(f"  {slope} = {h.slope:.8g}, {offset} = {h.offset:.8g}")
        lines.append(f"  energy dissipated DSP = {h.energy:.8g}")
        if h.displacementRatio is not None:
            lines.append(f"  relative displacement difference RDEP = {h.displacementRatio:.8g}")
        if h.regions is not None:
            lines.append(f"  {h.regions} regions; 2δ at the centre = {h.centerDifference:.6g}")
        if h.macroEnergy is not None:
            lines.append(
                f"  of which macro-slip {h.macroEnergy:.8g}, "
                f"micro-slip in the macro-slip region {h.microInMacroEnergy:.8g}"
            )
    if result.totalEnergy is not None:
        lines += ["", f"Energy over the whole wavelength (4 × the sum) = {result.totalEnergy:.8g}"]
    if result.files:
        lines += ["", f"Files written: {', '.join(result.files)}."]
    return "\n".join(lines) + "\n"


@dataclass(frozen=True, eq=False)
class ThesisRunOutput:
    """A result with its tables and texts, prepared off the interface thread."""

    result: ThesisResult
    table: ResultTable
    profileTable: ResultTable | None
    summaryText: str
    consoleText: str


def runAndPresentThesis(
    program: ThesisProgramSpec, value, hook: ProgressHook | None = None
) -> ThesisRunOutput:
    result = runThesisProgram(program, value, hook)
    return ThesisRunOutput(
        result, halfPitchTable(result), profileTable(result), summaryText(result),
        thesisScreenText(result),
    )  # fmt: skip
