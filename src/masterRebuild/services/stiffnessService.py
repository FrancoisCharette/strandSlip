"""SINUS, BSINUS, NSINUS and RAYON: transverse stiffness of a strand along X.

At each position the wire elongations give forces and moments (equations
36-38), summed over the wires in order, and the bending moment Mz gives the
stiffness (equation 41 for the sinusoid, 40 for constant curvature). The
programs skipped the position X = 0 - the test is written `IF(X.EQ.O)`, the
letter O, an uninitialised REAL that the DOS runtime left at zero.
"""

from __future__ import annotations

import logging
import math
import time

import numpy as np

from masterRebuild.models.analysisResults import StiffnessResult, StrandConstants, WireStates
from masterRebuild.models.legacyProgram import Analysis, ProgramSpec
from masterRebuild.models.strandInput import StrandInput
from masterRebuild.services import inputValidation
from masterRebuild.services.analysisErrors import ProgressHook, advance
from masterRebuild.services.strandModel import (
    computeStrandConstants,
    fullStickStiffness,
    makeDeflectionModel,
    pi,
    stiffnessPositions,
)
from masterRebuild.services.wireStateSolver import concatenateStates, solveWireStates

logger = logging.getLogger(__name__)

# Wire states solved per chunk: bounds memory and paces progress reports.
cellsPerChunk = 50_000


def _sequentialSum(values: np.ndarray) -> np.ndarray:
    """FXT=FXT+FX(I) over I: a running sum, not numpy's pairwise one."""
    return np.cumsum(values, axis=1)[:, -1]


def _totals(
    value: StrandInput, constants: StrandConstants, states: WireStates, positions: np.ndarray
) -> dict[str, np.ndarray]:
    """Forces and moments of each wire (label 310), summed per position (label 120)."""
    sine = math.sin(value.helixAngle)
    cosine = math.cos(value.helixAngle)
    phase = (2 * pi * positions[:, None]) / constants.pitch + constants.thetas[None, :]
    stiffnessTerm = states.elongation * value.wireModulus  # EX*EF
    radial = stiffnessTerm * constants.wireArea * sine  # FYZ
    axial = stiffnessTerm * constants.wireArea * cosine  # FX(I)
    sinPhase, cosPhase = np.sin(phase), np.cos(phase)
    return {
        "forceX": _sequentialSum(axial),
        "forceY": _sequentialSum(radial * cosPhase),
        "forceZ": _sequentialSum(radial * sinPhase),
        "momentZ": _sequentialSum(axial * value.coreRadius * sinPhase),
        "momentY": _sequentialSum(axial * value.coreRadius * cosPhase),
        "torsion": _sequentialSum(radial * value.coreRadius),
    }


def runStiffness(
    value: StrandInput, program: ProgramSpec, hook: ProgressHook | None = None
) -> StiffnessResult:
    if program.analysis is not Analysis.stiffness or program.deflection is None:
        raise ValueError(f"{program.key} is not a stiffness program")
    inputValidation.requireValid(value, program)
    started = time.perf_counter()
    constants = computeStrandConstants(value)
    model = makeDeflectionModel(program.deflection, value, constants)
    positions = stiffnessPositions(value, constants.positionStep, inputValidation.maxPositions)

    chunk = max(1, cellsPerChunk // value.wireCount)
    divisor = program.slipSearchDivisor
    parts: list[WireStates] = []
    advance(hook, 0, len(positions))
    for start in range(0, len(positions), chunk):
        stop = min(start + chunk, len(positions))
        parts.append(solveWireStates(model, value, constants, positions[start:stop], divisor))
        advance(hook, stop, len(positions))
    states = concatenateStates(parts)

    totals = _totals(value, constants, states, positions)
    written = positions != 0.0
    stiffness = np.full(len(positions), np.nan)
    stiffness[written] = model.stiffness(totals["momentZ"][written], positions[written])
    elapsed = time.perf_counter() - started
    logger.info(
        "%s: %d positions x %d wires in %.2f s",
        program.key,
        len(positions),
        value.wireCount,
        elapsed,
    )
    return StiffnessResult(
        program=program,
        input=value,
        constants=constants,
        deflection=model.constants,
        positions=positions,
        wires=states,
        torsion=totals["torsion"],
        momentY=totals["momentY"],
        momentZ=totals["momentZ"],
        forceX=totals["forceX"],
        forceY=totals["forceY"],
        forceZ=totals["forceZ"],
        stiffness=stiffness,
        written=written,
        searchStep=constants.pitch / divisor if states.searchStepAssigned else 0.0,
        fullStickStiffness=fullStickStiffness(value, constants),
        elapsedSeconds=elapsed,
    )
