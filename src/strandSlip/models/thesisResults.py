"""What a run of one of the 1992 programs produces."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from strandSlip.models.thesisInput import ThesisInput
from strandSlip.models.thesisProgram import ThesisProgramSpec


@dataclass(frozen=True, eq=False)
class SlipProfile:
    """SORTIE / SORTZETA: the core and the wire along the half lay length, by X."""

    x: np.ndarray
    coreDisplacement: np.ndarray  # DAME (without slip)
    wireDisplacement: np.ndarray  # DFIL (with slip)
    coreStrain: np.ndarray  # EAME
    wireStrain: np.ndarray  # EFIL
    coreFriction: np.ndarray  # FAME: friction ratio without slip
    wireFriction: np.ndarray  # FFIL
    transitions: np.ndarray  # rows (X, DFIL, EFIL, FFIL) of ZETA*X.DAT; empty otherwise


@dataclass(frozen=True)
class HalfPitchResult:
    """One half lay length solved: its bounds, constants and energy."""

    start: float  # XINF
    end: float  # XSUP
    side: int  # ICOTE
    lowerBound: float  # XB1
    upperBound: float  # XB2
    slope: float  # XIH, XIC or BTM
    offset: float  # PSIH, PSIC or ETM
    energy: float  # DSP
    displacementRatio: float | None  # RDEP, where the program computes it
    regions: int | None = None  # NPORTION (compliance)
    centerDifference: float | None = None  # |DFDEP| = 2δ at the centre (compliance)
    regionEnergies: tuple[tuple[int, float], ...] = ()  # ENERGY.DAT, (region, energy)
    macroRegionEnergy: float | None = None  # DSPMAC
    microInMacroEnergy: float | None = None  # DMICMAC

    @property
    def macroEnergy(self) -> float | None:  # DMAC: macro-slip only
        if self.macroRegionEnergy is None or self.microInMacroEnergy is None:
            return None
        return self.macroRegionEnergy - self.microInMacroEnergy


@dataclass(frozen=True, eq=False)
class ThesisResult:
    program: ThesisProgramSpec
    input: ThesisInput
    halfPitches: tuple[HalfPitchResult, ...]
    skipped: tuple[tuple[float, float], ...]  # half lay lengths without macro-slip
    totalEnergy: float | None  # DSPTOTAL: four times the sum up to λ/4 (choice 1)
    profile: SlipProfile | None
    console: tuple[str, ...]  # the screen, record by record
    files: dict[str, tuple[str, ...]] = field(default_factory=dict)  # .DAT files, by name
    pendingQuestion: str | None = None  # the run stopped where the program asks this
    approximationsUsed: tuple[float, ...] = ()
    elapsedSeconds: float = 0.0
