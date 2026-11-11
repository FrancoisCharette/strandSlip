"""Inputs the 1990 programs could not run on, caught before the run.

The originals had no checks: a zero ended in a division error, a negative
step looped forever, more than 50 wires overran the arrays. Each message
here names the field and says why the program needs it.
"""

from __future__ import annotations

import math

from masterRebuild.models.legacyProgram import Analysis, Deflection, ProgramSpec
from masterRebuild.models.strandInput import (
    StrandInput,
    fieldByName,
    maxLegacyInteger,
    maxWireCount,
)
from masterRebuild.services.analysisErrors import InputError

# Positions and position-by-wire cells one run may hold in memory.
maxPositions = 200_000
maxCells = 2_000_000


def _label(name: str) -> str:
    field = fieldByName[name]
    return f"{field.label} ({field.strandName})"


def _basicIssues(value: StrandInput) -> list[str]:
    issues: list[str] = []
    for name in fieldByName:
        number = getattr(value, name)
        if isinstance(number, float) and not math.isfinite(number):
            issues.append(f"{_label(name)} must be a finite number.")
    if issues:
        return issues
    if value.strandLength <= 0:
        issues.append(
            f"{_label('strandLength')} must be positive: the step along X is CL/NPAS, and "
            "with a zero or negative step the loop never reaches the end position."
        )
    if not 1 <= value.wireCount <= maxWireCount:
        issues.append(
            f"{_label('wireCount')} must be between 1 and {maxWireCount}: the programs "
            f"dimension their wire arrays at {maxWireCount}."
        )
    if not 0 < value.helixAngle < math.pi / 2:
        hint = ""
        if 1 <= value.helixAngle < 90:
            hint = (
                f" It looks like degrees: {value.helixAngle:g}° is "
                f"{math.radians(value.helixAngle):.4f} rad."
            )
        issues.append(
            f"{_label('helixAngle')} must be in radians, between 0 and π/2: the lay length "
            f"divides by tan(α).{hint}"
        )
    for name, why in (
        ("wireRadius", "the wire area divides the stiffness terms"),
        ("wireModulus", "the elongation divides by E·a"),
        ("wireTension", "the contact force q comes from it and divides the friction terms"),
        ("coreRadius", "q divides by it"),
        ("frictionLimit", "the critical amplitude and radius are proportional to it"),
    ):
        if getattr(value, name) <= 0:
            issues.append(f"{_label(name)} must be positive: {why}.")
    if not 1 <= value.positionCount <= maxLegacyInteger:
        issues.append(
            f"{_label('positionCount')} must be between 1 and {maxLegacyInteger}: it divides "
            "the strand length, and the programs held it in a two-byte integer."
        )
    return issues


def poissonFactor(value: StrandInput) -> float:
    tangent = math.tan(value.helixAngle)
    cosine = math.cos(value.helixAngle)
    return (1 - value.corePoisson * (tangent * tangent)) * (cosine * cosine)


def _deflectionIssues(value: StrandInput, program: ProgramSpec) -> list[str]:
    issues: list[str] = []
    if program.deflection is None:
        return issues
    if poissonFactor(value) <= 0:
        issues.append(
            f"{_label('corePoisson')} is too large for this helix angle: the factor "
            "f = (1 − ν tan²α) cos²α (equation 3) must stay positive."
        )
    if program.deflection is Deflection.sinusoid:
        if value.wavelength <= 0:
            issues.append(f"{_label('wavelength')} must be positive for {program.sourceFile}.")
        if value.amplitude == 0:
            issues.append(
                f"{_label('amplitude')} is the sinusoid amplitude here and cannot be zero: "
                "the stiffness divides by it."
            )
        pitch = 2 * math.pi * value.coreRadius / math.tan(value.helixAngle)
        if value.wavelength == pitch:
            issues.append(
                f"{_label('wavelength')} equals the lay length {pitch:.6g} m: equation 23 "
                "divides by λ − p."
            )
    elif value.amplitude == 0:
        issues.append(
            f"{_label('amplitude')} is the radius of curvature ρ for {program.sourceFile} "
            "and cannot be zero."
        )
    return issues


def countPositions(value: StrandInput, program: ProgramSpec) -> int:
    """How many X positions the program's loop visits (estimate, before running)."""
    step = value.strandLength / value.positionCount
    span = max(0.0, value.xEnd - value.xStart)
    count = math.floor(span / step) + 1
    if program.analysis is Analysis.stiffness:
        count += 1  # the stiffness loop also runs the first X at or past the end
    return max(1, count)


def validationIssues(value: StrandInput, program: ProgramSpec) -> list[str]:
    issues = _basicIssues(value)
    if issues:
        return issues
    issues.extend(_deflectionIssues(value, program))
    if program.analysis is Analysis.input:
        return issues
    positions = countPositions(value, program)
    step = value.strandLength / value.positionCount
    if positions > maxPositions:
        issues.append(
            f"That is about {positions:,} positions along X, more than {maxPositions:,}. "
            f"The step is CL/NPAS = {step:.6g} m, set by the strand length and the number of "
            "positions, not by the start and end points."
        )
    elif positions * value.wireCount > maxCells:
        issues.append(
            f"{positions:,} positions × {value.wireCount} wires is more than {maxCells:,} "
            "wire states. Use fewer positions or a shorter span."
        )
    return issues


def requireValid(value: StrandInput, program: ProgramSpec) -> None:
    issues = validationIssues(value, program)
    if issues:
        raise InputError(issues)
