"""What a run of one of the 1990 programs produces.

Arrays are indexed [position] or [position, wire]. Names follow the
interface; the Fortran variable each one holds is noted beside it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from strandSlip.models.legacyProgram import Deflection, ProgramSpec
from strandSlip.models.strandInput import StrandInput

stuck = 0
slipAbove = 1  # friction demand above +CFL: the X3..X4 branch (equations 33, 35)
slipBelow = -1  # friction demand below -CFL: the X1..X2 branch (equations 32, 34)


@dataclass(frozen=True, eq=False)
class StrandConstants:
    """Values every program derives from ENTRE.DAT before its loop."""

    thetas: np.ndarray  # THETA(I), accumulated as THETA(I-1) + 2 PI / NFIL
    positionStep: float  # DXPAS = CL / NPAS
    poissonFactor: float  # F, equation 3
    pitch: float  # PITCH, lay length, equation 13
    wireArea: float  # AF (AT)
    bearingPressure: float  # Q, contact force per length, equation 12
    gamma: float  # GAM, rounded to REAL*4 like the original (G is not in IMPLICIT D.P.)


@dataclass(frozen=True)
class DeflectionConstants:
    """The constants that depend on the imposed deflection."""

    deflection: Deflection
    critical: float  # AMPC (equation 21) or RHOC (equation 14)
    ratio: float  # AMPR = AMP / AMPC, or RHOR = RHO / RHOC
    frictionConstant: float  # CST9, factor of equation 19 or 10
    displacementConstant: float  # CST19, factor of equation 23 or 17


@dataclass(frozen=True, eq=False)
class WireStates:
    """The state of every wire at every position."""

    frictionDemand: np.ndarray  # CFX
    zone: np.ndarray  # stuck, slipAbove or slipBelow
    lowerBound: np.ndarray  # X3 or X1, NaN where stuck
    upperBound: np.ndarray  # X4 or X2, NaN where stuck
    lowerDisplacement: np.ndarray  # DX3 or DX1, NaN where stuck
    upperDisplacement: np.ndarray  # DX4 or DX2, NaN where stuck
    elongation: np.ndarray  # EX
    searchStepAssigned: bool  # whether DX was ever set (DONSIN prints it regardless)


@dataclass(frozen=True, eq=False)
class StiffnessResult:
    """SINUS, BSINUS, NSINUS or RAYON."""

    program: ProgramSpec
    input: StrandInput
    constants: StrandConstants
    deflection: DeflectionConstants
    positions: np.ndarray  # every X the loop visited
    wires: WireStates
    torsion: np.ndarray  # TMXT, moment about X
    momentY: np.ndarray  # FMXYT
    momentZ: np.ndarray  # FMXZT, the bending moment the stiffness comes from
    forceX: np.ndarray  # FXT
    forceY: np.ndarray  # FYT
    forceZ: np.ndarray  # FZT
    stiffness: np.ndarray  # RIG, NaN where nothing was written
    written: np.ndarray  # rows the program wrote: it skipped X equal to zero
    searchStep: float  # DX as DONSIN.DAT printed it, 0 if it was never assigned
    fullStickStiffness: float | None  # (n/2) E a Ra^2 f cos(alpha); None below 3 wires
    elapsedSeconds: float


@dataclass(frozen=True, eq=False)
class FrictionResult:
    """FRICTION."""

    program: ProgramSpec
    input: StrandInput
    constants: StrandConstants
    deflection: DeflectionConstants
    positions: np.ndarray
    frictionDemand: np.ndarray  # CFX
    elapsedSeconds: float


@dataclass(frozen=True, eq=False)
class DisplacementResult:
    """DEPLACE."""

    program: ProgramSpec
    input: StrandInput
    constants: StrandConstants
    deflection: DeflectionConstants
    positions: np.ndarray
    termA: np.ndarray  # CA19
    termB: np.ndarray  # CB19
    displacementScaled: np.ndarray  # DX = CST19 (CA19 - CB19) * 10000
    elapsedSeconds: float


AnalysisResult = StiffnessResult | FrictionResult | DisplacementResult


@dataclass(frozen=True, eq=False)
class ResultColumn:
    header: str
    legacyName: str
    values: np.ndarray
    integer: bool = False


@dataclass(frozen=True, eq=False)
class ResultTable:
    """Rows as the program wrote them to its result file, at full precision."""

    columns: tuple[ResultColumn, ...]

    @property
    def rowCount(self) -> int:
        return len(self.columns[0].values) if self.columns else 0
