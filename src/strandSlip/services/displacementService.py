"""DEPLACE: displacement of the core surface along each contact helix (equation 23).

DEPLACE wrote the displacement multiplied by 10 000, next to the two
brackets of equation 23 (CA19, CB19) it was computed from.
"""

from __future__ import annotations

import logging
import time

import numpy as np

from strandSlip.models.analysisResults import DisplacementResult
from strandSlip.models.legacyProgram import DEPLACE
from strandSlip.models.strandInput import StrandInput
from strandSlip.services import inputValidation
from strandSlip.services.analysisErrors import ProgressHook, advance
from strandSlip.services.strandModel import (
    SinusoidalDeflection,
    computeStrandConstants,
    scanPositions,
)

logger = logging.getLogger(__name__)

positionsPerChunk = 20_000
legacyScale = 10000  # DX=CST19*(CA19-CB19)*10000


def runDisplacement(value: StrandInput, hook: ProgressHook | None = None) -> DisplacementResult:
    inputValidation.requireValid(value, DEPLACE)
    started = time.perf_counter()
    constants = computeStrandConstants(value)
    model = SinusoidalDeflection(value, constants)
    positions = scanPositions(value, constants.positionStep, inputValidation.maxPositions)
    shape = (len(positions), value.wireCount)
    termA, termB, scaled = np.empty(shape), np.empty(shape), np.empty(shape)
    advance(hook, 0, len(positions))
    for start in range(0, len(positions), positionsPerChunk):
        stop = min(start + positionsPerChunk, len(positions))
        x = positions[start:stop, None]
        a, b = model.coreDisplacementTerms(x, constants.thetas[None, :])
        termA[start:stop], termB[start:stop] = a, b
        scaled[start:stop] = model.constants.displacementConstant * (a - b) * legacyScale
        advance(hook, stop, len(positions))
    elapsed = time.perf_counter() - started
    logger.info("DEPLACE: %d positions x %d wires", len(positions), value.wireCount)
    return DisplacementResult(
        program=DEPLACE,
        input=value,
        constants=constants,
        deflection=model.constants,
        positions=positions,
        termA=termA,
        termB=termB,
        displacementScaled=scaled,
        elapsedSeconds=elapsed,
    )
