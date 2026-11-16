"""Stick or slip, and the elongation, of every wire at every position.

This is the inner loop shared by SINUS, BSINUS, NSINUS and RAYON (labels 370
to 310). For each wire the friction coefficient needed to stay stuck, CFX,
decides the branch:

* -CFL <= CFX <= CFL: the wire sticks and follows the core (equation 22 or 15);
* CFX > CFL: it slips; the slip zone X3..X4 is found by stepping DX = p/1000
  from X until CFX drops back to CFL, and the elongation follows equations 33
  and 35;
* CFX < -CFL: the mirror case, zone X1..X2, equations 32 and 34.

The originals stepped one wire at a time. Here all slipping wires step
together, each by the same repeated X = X + DX, and each stops where its own
scalar loop would have, so the bounds are the same numbers.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np

from strandSlip.models.analysisResults import (
    StrandConstants,
    WireStates,
    slipAbove,
    slipBelow,
    stuck,
)
from strandSlip.models.strandInput import StrandInput
from strandSlip.services.analysisErrors import AnalysisError
from strandSlip.services.strandModel import DeflectionModel, pi


def marchToBound(
    model: DeflectionModel,
    start: np.ndarray,
    theta: np.ndarray,
    step: float,
    stillSlipping: Callable[[np.ndarray], np.ndarray],
    maxSteps: int,
) -> np.ndarray:
    """Step each start point until its friction demand leaves the slip range.

    Mirrors `320 X4=X4+DX ... IF(CFX4.GT.CFL) GOTO 320`: step, evaluate,
    repeat while still slipping. The point returned is the first one that is
    not, as in the original.
    """
    bound = start.copy()
    index = np.arange(start.size)
    position = start.copy()
    angle = theta.copy()
    for _ in range(maxSteps):
        if index.size == 0:
            return bound
        position = position + step
        slipping = stillSlipping(model.frictionDemand(position, angle))
        if not slipping.all():
            finished = ~slipping
            bound[index[finished]] = position[finished]
            index, position, angle = index[slipping], position[slipping], angle[slipping]
    if index.size == 0:
        return bound
    raise AnalysisError(
        f"The search for a slip-zone bound took more than {maxSteps:,} steps of {abs(step):.3g} m "
        "without the friction demand returning to the limit. Check the inputs."
    )


def _slipElongation(
    model: DeflectionModel,
    value: StrandInput,
    constants: StrandConstants,
    x: np.ndarray,
    theta: np.ndarray,
    searchStep: float,
    above: bool,
) -> tuple[np.ndarray, ...]:
    """Bounds, their core displacements and the elongation for one slip branch."""
    limit = value.frictionLimit if above else 0 - value.frictionLimit  # CFL or CFLN
    if above:

        def slipping(demand: np.ndarray) -> np.ndarray:
            return demand > limit
    else:

        def slipping(demand: np.ndarray) -> np.ndarray:
            return demand < limit

    maxSteps = 4 * round(constants.pitch / searchStep) + 16
    upper = marchToBound(model, x, theta, searchStep, slipping, maxSteps)  # X4 / X2
    lower = marchToBound(model, x, theta, -searchStep, slipping, maxSteps)  # X3 / X1
    lowerDisplacement = model.coreDisplacement(lower, theta)
    upperDisplacement = model.coreDisplacement(upper, theta)
    cosine = math.cos(value.helixAngle)
    width = upper - lower
    drift = (constants.gamma * pi * width) / constants.pitch
    meanStrain = (cosine * (upperDisplacement - lowerDisplacement)) / width
    # Equation 33 (EOD) above the limit, 32 (EOG) below it
    offset = meanStrain - drift if above else meanStrain + drift
    # Equations 35 and 34
    elongation = (constants.bearingPressure * limit * (x - lower)) / (
        cosine * value.wireModulus * constants.wireArea
    ) + offset
    return lower, upper, lowerDisplacement, upperDisplacement, elongation


def classifyDemand(demand: np.ndarray, limit: float) -> np.ndarray:
    """The branch each wire takes: stuck, slipAbove or slipBelow.

    Written as the Fortran tests are, `IF(CFX.LT.0)` then `IF(CFX.GE.CFLN)`
    or `IF(CFX.LE.CFL)`, so even a NaN would take the same path.
    """
    negative = demand < 0
    below = negative & ~(demand >= 0 - limit)
    above = ~negative & ~(demand <= limit)
    zone = np.full(demand.shape, stuck, dtype=np.int8)
    zone[above] = slipAbove
    zone[below] = slipBelow
    return zone


def solveWireStates(
    model: DeflectionModel,
    value: StrandInput,
    constants: StrandConstants,
    positions: np.ndarray,
    searchDivisor: int,
) -> WireStates:
    """States for `positions` x every wire (one chunk of the X loop)."""
    x = np.repeat(positions[:, None], value.wireCount, axis=1)
    theta = np.broadcast_to(constants.thetas[None, :], x.shape).copy()
    demand = model.frictionDemand(x, theta)
    zone = classifyDemand(demand, value.frictionLimit)
    above = zone == slipAbove
    below = zone == slipBelow
    negative = demand < 0

    elongation = model.stickElongation(x, theta)
    bounds = np.full((4, *x.shape), np.nan)  # lower, upper, lowerDisp, upperDisp
    searchStep = constants.pitch / searchDivisor
    for mask, isAbove in ((above, True), (below, False)):
        if not mask.any():
            continue
        lower, upper, lowerDisp, upperDisp, slipEx = _slipElongation(
            model, value, constants, x[mask], theta[mask], searchStep, isAbove
        )
        bounds[0][mask], bounds[1][mask] = lower, upper
        bounds[2][mask], bounds[3][mask] = lowerDisp, upperDisp
        elongation[mask] = slipEx
    return WireStates(
        frictionDemand=demand,
        zone=zone,
        lowerBound=bounds[0],
        upperBound=bounds[1],
        lowerDisplacement=bounds[2],
        upperDisplacement=bounds[3],
        elongation=elongation,
        # DX is assigned at label 300 (any CFX < 0) and in the slip branch above.
        searchStepAssigned=bool(negative.any() or above.any()),
    )


def concatenateStates(parts: list[WireStates]) -> WireStates:
    if len(parts) == 1:
        return parts[0]
    return WireStates(
        frictionDemand=np.concatenate([p.frictionDemand for p in parts]),
        zone=np.concatenate([p.zone for p in parts]),
        lowerBound=np.concatenate([p.lowerBound for p in parts]),
        upperBound=np.concatenate([p.upperBound for p in parts]),
        lowerDisplacement=np.concatenate([p.lowerDisplacement for p in parts]),
        upperDisplacement=np.concatenate([p.upperDisplacement for p in parts]),
        elongation=np.concatenate([p.elongation for p in parts]),
        searchStepAssigned=any(p.searchStepAssigned for p in parts),
    )
