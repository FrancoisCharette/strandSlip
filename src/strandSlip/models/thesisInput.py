"""What the 1992 programs ask at the keyboard, given in advance.

All values are dimensionless (annex A of the thesis): ρ̄ = ρ/ρc for the radius
of curvature, Ā = A/Ac for the amplitude, Λ = λ/p lay lengths per wavelength,
γ1 for the compliance, and positions in lay lengths.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class SinusoidChoice(IntEnum):
    """ICHOIX, the sinusoid programs' menu."""

    wholeWavelength = 1  # energy over the wavelength, THETAi = 90 deg
    displacementRatio = 2  # relative displacement difference at λ/4, THETAi = 0
    oneHalfPitch = 3  # one half lay length, chosen by XTOUR, THETAi = 90 deg


@dataclass(frozen=True)
class ThesisInput:
    radius: float = 0.8  # RHOB (constant radius)
    compliance: float = 0.06  # GAM1, γ1 (compliance model)
    choice: SinusoidChoice = SinusoidChoice.oneHalfPitch  # ICHOIX (sinusoid)
    wavelength: float = 28.0  # WLBAR, Λ: an even number of lay lengths
    amplitude: float = 1.4  # ABAR, Ā
    turns: float = 6.5  # XTOUR: where the half lay length starts (choice 3)
    profile: bool = True  # ISORTIE: 0 => compute the profiles along the half lay length
    # Typed in when an automatic approximation fails, in the order the program asks:
    # XB1 (CONTRHOB), XB1 then XB2 (CONTSIN), XB1C (ZETARHOB, ZETASIN).
    approximations: tuple[float, ...] = ()
