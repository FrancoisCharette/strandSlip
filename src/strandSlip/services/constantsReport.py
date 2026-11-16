"""Derived quantities and run summaries, named for people rather than for Fortran."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from strandSlip.models.analysisResults import (
    AnalysisResult,
    DisplacementResult,
    FrictionResult,
    StiffnessResult,
    slipAbove,
    slipBelow,
    stuck,
)
from strandSlip.models.legacyProgram import ENTRE, FRICTION, SINUS, Deflection
from strandSlip.models.strandInput import StrandInput
from strandSlip.services import inputValidation
from strandSlip.services.strandModel import (
    ConstantCurvatureDeflection,
    SinusoidalDeflection,
    computeStrandConstants,
    fullStickStiffness,
)


@dataclass(frozen=True)
class ReportLine:
    quantity: str
    value: str
    legacy: str = ""  # Fortran variable and equation of report SM-90-03
    note: str = ""


def number(value: float, unit: str = "", digits: int = 6) -> str:
    return f"{value:.{digits}g} {unit}".strip()


def describeInput(value: StrandInput) -> list[ReportLine]:
    """What the programs derive from these inputs before their loops."""
    if inputValidation.validationIssues(value, ENTRE):
        return []
    constants = computeStrandConstants(value)
    lines = [
        ReportLine("Lay Length p", number(constants.pitch, "m"), "PITCH, eq. 13"),
        ReportLine("Wire Area a", number(constants.wireArea * 1e6, "mm²"), "AF / AT"),
        ReportLine("Contact Force q", number(constants.bearingPressure, "N/m"), "Q, eq. 12"),
        ReportLine("Poisson Factor f", number(constants.poissonFactor), "F, eq. 3"),
        ReportLine("Gamma Γ", number(constants.gamma), "GAM, eq. 17", "single precision"),
    ]
    stuckEi = fullStickStiffness(value, constants)
    if stuckEi is not None:
        lines.append(ReportLine("Full-Stick EI", number(stuckEi, "N·m²"), "(n/2)·E·a·Ra²·f·cos α"))
    if not inputValidation.validationIssues(value, SINUS):
        sinusoid = SinusoidalDeflection(value, constants).constants
        lines += [
            ReportLine("Critical Amplitude Ac", number(sinusoid.critical, "m"), "AMPC, eq. 21"),
            ReportLine(
                "Amplitude Ratio A/Ac",
                number(sinusoid.ratio),
                "AMPR",
                "wires slip" if abs(sinusoid.ratio) > 1 else "no slip expected",
            ),
            ReportLine("Friction Factor, eq. 19", number(sinusoid.frictionConstant), "CST9"),
        ]
    if value.amplitude != 0:
        curvature = ConstantCurvatureDeflection(value, constants).constants
        lines += [
            ReportLine("Critical Radius ρc", number(curvature.critical, "m"), "RHOC, eq. 14"),
            ReportLine(
                "Radius Ratio ρ/ρc",
                number(curvature.ratio),
                "RHOR",
                "wires slip" if 0 < curvature.ratio < 1 else "no slip expected",
            ),
        ]
    lines += [
        ReportLine("Step Along X", number(constants.positionStep, "m"), "DXPAS = CL/NPAS"),
        ReportLine(
            "Stiffness Positions",
            f"{inputValidation.countPositions(value, SINUS):,}",
            "SINUS, RAYON",
        ),
        ReportLine(
            "Scan Positions",
            f"{inputValidation.countPositions(value, FRICTION):,}",
            "FRICTION, DEPLACE",
        ),
    ]
    return lines


def _positionsLine(result: AnalysisResult) -> ReportLine:
    positions = result.positions
    return ReportLine(
        "Positions",
        f"{len(positions):,}, X from {positions[0]:.6g} to {positions[-1]:.6g} m",
        f"step DXPAS = {result.constants.positionStep:.6g} m",
    )


def _stiffnessLines(result: StiffnessResult) -> list[ReportLine]:
    zone = result.wires.zone
    written = result.stiffness[result.written]
    lines = [
        ReportLine(
            "Rows Written",
            f"{int(result.written.sum()):,}",
            "X = 0 is skipped" if not result.written.all() else "",
        ),
        ReportLine(
            "Wire States",
            f"stuck {int((zone == stuck).sum()):,} · slipping above +μL "
            f"{int((zone == slipAbove).sum()):,} · below −μL {int((zone == slipBelow).sum()):,}",
        ),
    ]
    if written.size and np.isfinite(written).any():
        lines.append(
            ReportLine(
                "Stiffness EI",
                f"{np.nanmin(written):.6g} to {np.nanmax(written):.6g} N·m²",
                "RIG",
            )
        )
    if result.fullStickStiffness is not None:
        lines.append(ReportLine("Full-Stick EI", number(result.fullStickStiffness, "N·m²")))
    deflection = result.deflection
    if deflection.deflection is Deflection.sinusoid:
        lines.append(
            ReportLine(
                "Critical Amplitude Ac",
                number(deflection.critical, "m"),
                "AMPC, eq. 21",
                f"A/Ac = {deflection.ratio:.4g}",
            )
        )
    else:
        lines.append(
            ReportLine(
                "Critical Radius ρc",
                number(deflection.critical, "m"),
                "RHOC, eq. 14",
                f"ρ/ρc = {deflection.ratio:.4g}",
            )
        )
    divisor = result.program.slipSearchDivisor
    lines.append(
        ReportLine(
            "Slip Search Step",
            f"p/{divisor:,} = {result.constants.pitch / divisor:.4g} m",
            "DX",
        )
    )
    return lines


def describeResult(result: AnalysisResult) -> list[ReportLine]:
    program = result.program
    lines = [
        ReportLine("Program", f"{program.sourceFile} ({program.sourceDate})", program.title),
        _positionsLine(result),
    ]
    if isinstance(result, StiffnessResult):
        lines += _stiffnessLines(result)
    elif isinstance(result, FrictionResult):
        demand = result.frictionDemand
        above = int((np.abs(demand) > result.input.frictionLimit).sum())
        lines += [
            ReportLine("Largest |μ| Needed", number(float(np.abs(demand).max())), "CFX, eq. 19"),
            ReportLine(
                "Wire Positions Beyond μL",
                f"{above:,} of {demand.size:,}",
                f"μL = {result.input.frictionLimit:g}",
            ),
        ]
    elif isinstance(result, DisplacementResult):
        largest = float(np.abs(result.displacementScaled).max())
        lines.append(
            ReportLine(
                "Largest |Da| × 10⁴", number(largest, "m"), "DX, eq. 23", f"{largest / 10:.4g} mm"
            )
        )
    lines.append(ReportLine("Run Time", f"{result.elapsedSeconds:.2f} s"))
    return lines


def formatLines(lines: list[ReportLine]) -> str:
    """Aligned plain text, for the Summary view."""
    if not lines:
        return ""
    width = max(len(line.quantity) for line in lines)
    out = []
    for line in lines:
        extras = " · ".join(part for part in (line.legacy, line.note) if part)
        out.append(f"{line.quantity:<{width}}  {line.value}" + (f"   [{extras}]" if extras else ""))
    return "\n".join(out)


def degrees(radians: float) -> str:
    return f"{math.degrees(radians):.4f}°"
