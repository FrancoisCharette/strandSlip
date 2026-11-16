"""FRICTION: the friction coefficient each wire needs to stay stuck (equation 19).

Unlike the stiffness programs, FRICTION steps X before testing it, so it stops
at the last X below XFINAL.
"""

from __future__ import annotations

import logging
import time

import numpy as np

from strandSlip.models.analysisResults import FrictionResult
from strandSlip.models.legacyProgram import FRICTION
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


def runFriction(value: StrandInput, hook: ProgressHook | None = None) -> FrictionResult:
    inputValidation.requireValid(value, FRICTION)
    started = time.perf_counter()
    constants = computeStrandConstants(value)
    model = SinusoidalDeflection(value, constants)
    positions = scanPositions(value, constants.positionStep, inputValidation.maxPositions)
    demand = np.empty((len(positions), value.wireCount))
    advance(hook, 0, len(positions))
    for start in range(0, len(positions), positionsPerChunk):
        stop = min(start + positionsPerChunk, len(positions))
        x = positions[start:stop, None]
        demand[start:stop] = model.frictionDemand(x, constants.thetas[None, :])
        advance(hook, stop, len(positions))
    elapsed = time.perf_counter() - started
    logger.info("FRICTION: %d positions x %d wires", len(positions), value.wireCount)
    return FrictionResult(
        program=FRICTION,
        input=value,
        constants=constants,
        deflection=model.constants,
        positions=positions,
        frictionDemand=demand,
        elapsedSeconds=elapsed,
    )
