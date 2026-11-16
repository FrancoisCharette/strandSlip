"""The thesis's dimensionless parameters, from the strand on the Strand tab.

The 1992 programs asked for ρ/ρc, λ/p, A/Ac and γ1 directly. Chapter 5 of
the thesis defines them from the physical strand, the same values ENTRE.DAT
holds; its worked example (section 5.2) is the 1991 strand, for which it
gives γ1 = 0.05621.

    ρ/ρc = ρ Ti sinα μ / (π Ra (1 − ν tan²α) cos²α E RF²)             (5.7)
    λ/p, with p = 2π Ra / tan α                                       (5.8)
    A/Ac = A π Ra (1 − ν tan²α) cos²α E RF² (2π/λ)² / (Ti sinα μ)     (5.10)
    γ1   = 4 (RF/Ra)² (1 + ν) sin²α [0.059125 + ln √(E Ra (RF + Ra)
                                     / (Ti sin²α (1 − ν²)))]           (5.11)

ρc and Ac are equations 2.10 and 2.23, the critical radius and amplitude the
1990 programs call RHOC and AMPC. The thesis takes the core and the wires of
one material; ENTRE.DAT has a modulus for each, so E here is the wires'
(EF), as in RHOC and AMPC, and ν is the core's (CPN), as in the factor f.
The amplitude slot of ENTRE.DAT is read as ρ for the radius and as A for
the sinusoid, the way RAYON and SINUS read it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from strandSlip.models.legacyProgram import ENTRE
from strandSlip.models.strandInput import StrandInput
from strandSlip.services import inputValidation
from strandSlip.services.analysisErrors import InputError


@dataclass(frozen=True)
class ThesisParameters:
    layLength: float  # p
    criticalRadius: float  # ρc, equation 2.10
    criticalAmplitude: float | None  # Ac, equation 2.23; None without a wavelength
    radiusRatio: float | None  # ρ/ρc, the amplitude slot read as ρ; None when it is 0
    waveRatio: float | None  # λ/p; None without a wavelength
    amplitudeRatio: float | None  # A/Ac, the amplitude slot read as A
    compliance: float  # γ1


def thesisParameters(value: StrandInput) -> ThesisParameters:
    """InputError, listing why, when the strand cannot give them."""
    issues = inputValidation.validationIssues(value, ENTRE)
    if not issues and inputValidation.poissonFactor(value) <= 0:
        issues.append("The factor f = (1 − ν tan²α) cos²α must stay positive.")
    if not -1 < value.corePoisson < 1:
        issues.append("γ1 needs a Poisson's ratio ν between −1 and 1: it takes ln(1 − ν²).")
    if issues:
        raise InputError(issues)
    alpha = value.helixAngle
    sine = math.sin(alpha)
    poissonFactor = inputValidation.poissonFactor(value)  # f, equation 1.6
    core, wire, modulus, tension = (
        value.coreRadius,
        value.wireRadius,
        value.wireModulus,
        value.wireTension,
    )
    stiffness = math.pi * core * poissonFactor * modulus * wire * wire  # Ra f E a
    load = tension * sine * value.frictionLimit  # Ti sinα μ
    criticalRadius = stiffness / load
    layLength = 2 * math.pi * core / math.tan(alpha)
    wavelength = value.wavelength
    criticalAmplitude = None
    if wavelength > 0:
        half = wavelength / (2 * math.pi)
        criticalAmplitude = half * half * load / stiffness
    nu = value.corePoisson
    logArgument = modulus * core * (wire + core) / (tension * sine * sine * (1 - nu * nu))
    compliance = (
        4
        * (wire / core) ** 2
        * (1 + nu)
        * sine
        * sine
        * (0.059125 + math.log(math.sqrt(logArgument)))
    )
    amplitude = value.amplitude
    return ThesisParameters(
        layLength=layLength,
        criticalRadius=criticalRadius,
        criticalAmplitude=criticalAmplitude,
        radiusRatio=amplitude / criticalRadius if amplitude != 0 else None,
        waveRatio=wavelength / layLength if wavelength > 0 else None,
        amplitudeRatio=amplitude / criticalAmplitude if criticalAmplitude else None,
        compliance=compliance,
    )
