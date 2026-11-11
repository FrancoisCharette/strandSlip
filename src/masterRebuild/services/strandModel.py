"""The equations of report SM-90-03 (July 1990), as the Fortran evaluated them.

Every expression keeps the operand order of the .FOR source, so the
floating-point result is the same IEEE double computation the source
describes. Fortran integer powers are written as repeated products (X**2 is
X*X, X**3 is X*X*X), as the compiler emitted them.

Two quirks of the originals are kept on purpose:

* GAM is REAL*4. The programs declare IMPLICIT DOUBLE PRECISION (A-F) and
  (P-X); G falls outside both ranges, so Gamma was rounded to single
  precision when stored.
* THETA(I) is accumulated as THETA(I-1) + 2*PI/NFIL, and X as X + DXPAS,
  rather than computed from the index.

The 8087 of 1990 kept intermediate results in 80-bit registers; nothing here
tries to reproduce that, so the last bit can differ. It does not show at the
precision the programs printed.
"""

from __future__ import annotations

import math

import numpy as np

from masterRebuild.models.analysisResults import DeflectionConstants, StrandConstants
from masterRebuild.models.legacyProgram import Deflection
from masterRebuild.models.strandInput import StrandInput
from masterRebuild.services.analysisErrors import InputError

pi = math.acos(-1.0)  # PI=DACOS(-UN)


def computeStrandConstants(value: StrandInput) -> StrandConstants:
    count = value.wireCount
    thetas = np.zeros(count)
    for index in range(1, count):
        thetas[index] = thetas[index - 1] + (2 * pi) / count
    alpha = value.helixAngle
    tangent = math.tan(alpha)
    cosine = math.cos(alpha)
    sine = math.sin(alpha)
    # Equation 3
    poissonFactor = (1 - value.corePoisson * (tangent * tangent)) * (cosine * cosine)
    # Equation 13
    pitch = (2 * pi * value.coreRadius) / tangent
    wireArea = pi * (value.wireRadius * value.wireRadius)
    # Equation 12
    bearingPressure = (value.wireTension * (sine * sine)) / value.coreRadius
    gamma = (value.wireTension * sine * value.frictionLimit) / (value.wireModulus * wireArea)
    return StrandConstants(
        thetas=thetas,
        positionStep=value.strandLength / value.positionCount,
        poissonFactor=poissonFactor,
        pitch=pitch,
        wireArea=wireArea,
        bearingPressure=bearingPressure,
        gamma=float(np.float32(gamma)),
    )


def fullStickStiffness(value: StrandInput, constants: StrandConstants) -> float | None:
    """EI while every wire sticks: (n/2) E a Ra² f cos α.

    Summing sin² of n evenly spaced angles gives n/2 only from three wires up;
    below that the stuck stiffness still varies along X.
    """
    if value.wireCount < 3:
        return None
    return (
        value.wireCount
        / 2
        * value.wireModulus
        * constants.wireArea
        * value.coreRadius
        * value.coreRadius
        * constants.poissonFactor
        * math.cos(value.helixAngle)
    )


class SinusoidalDeflection:
    """Y = A sin(2 pi X / lambda): equations 18 to 23 and 41."""

    deflection = Deflection.sinusoid

    def __init__(self, value: StrandInput, constants: StrandConstants) -> None:
        self.wavelength = wl = value.wavelength
        self.amplitude = amp = value.amplitude
        self.pitch = pitch = constants.pitch
        alpha = value.helixAngle
        sine = math.sin(alpha)
        cosine = math.cos(alpha)
        ra, ef, af = value.coreRadius, value.wireModulus, constants.wireArea
        f, ti, cfl = constants.poissonFactor, value.wireTension, value.frictionLimit
        half = wl / (2 * pi)
        # Equation 21
        critical = ((half * half) * ti * sine * cfl) / (ra * f * ef * af)
        if critical == 0:
            raise InputError(
                ["The critical amplitude is zero; check the wire tension and friction."]
            )
        ratio = amp / critical
        turn = (2 * pi) / wl
        # Factor of equation 19
        frictionConstant = ((ra * amp * f * ef * af * cosine) / constants.bearingPressure) * (
            turn * turn * turn
        )
        # Factor of equation 23
        displacementConstant = (ratio * constants.gamma * wl * pitch) / (4 * pi * cosine)
        self.constants = DeflectionConstants(
            Deflection.sinusoid, critical, ratio, frictionConstant, displacementConstant
        )
        self.stickFactor = ratio * constants.gamma  # AMPR*GAM

    def phase(self, x: np.ndarray, theta: np.ndarray) -> np.ndarray:
        return (2 * pi * x) / self.pitch + theta

    def frictionDemand(self, x: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """Equation 19: friction coefficient needed to keep the wire stuck."""
        phi = self.phase(x, theta)
        psi = (2 * pi * x) / self.wavelength
        termA = (self.wavelength / self.pitch) * np.cos(phi) * np.sin(psi)
        termB = np.sin(phi) * np.cos(psi)
        return self.constants.frictionConstant * (termA + termB)

    def stickElongation(self, x: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """Equation 22: elongation of the core surface along the contact helix."""
        return (
            self.stickFactor * np.sin(self.phase(x, theta)) * np.sin((2 * pi * x) / self.wavelength)
        )

    def coreDisplacementTerms(
        self, x: np.ndarray, theta: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """CA19 and CB19, the two brackets of equation 23."""
        wl, pitch = self.wavelength, self.pitch
        sinTheta = np.sin(theta)
        termA = (np.sin(2 * pi * x * (1 / pitch - 1 / wl) + theta) - sinTheta) / (wl - pitch)
        termB = (np.sin(2 * pi * x * (1 / pitch + 1 / wl) + theta) - sinTheta) / (wl + pitch)
        return termA, termB

    def coreDisplacement(self, x: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """Equation 23: displacement of the core surface along the contact helix."""
        termA, termB = self.coreDisplacementTerms(x, theta)
        return self.constants.displacementConstant * (termA - termB)

    def stiffness(self, momentZ: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Equation 41: EI = Mz (lambda / 2 pi)^2 / (A sin(2 pi X / lambda))."""
        half = self.wavelength / (2 * pi)
        with np.errstate(divide="ignore", invalid="ignore"):
            return (momentZ * (half * half)) / (
                self.amplitude * np.sin((2 * pi * x) / self.wavelength)
            )


class ConstantCurvatureDeflection:
    """Y = -X^2 / (2 rho): equations 9 to 17 and 40. Reads AMP as RHO."""

    deflection = Deflection.constantCurvature

    def __init__(self, value: StrandInput, constants: StrandConstants) -> None:
        self.radius = rho = value.amplitude
        self.pitch = pitch = constants.pitch
        alpha = value.helixAngle
        sine = math.sin(alpha)
        cosine = math.cos(alpha)
        ra, ef, af = value.coreRadius, value.wireModulus, constants.wireArea
        f, ti, cfl = constants.poissonFactor, value.wireTension, value.frictionLimit
        # Equation 14
        critical = (ra * f * ef * af) / (ti * sine * cfl)
        ratio = rho / critical
        # Factor of equation 10
        frictionConstant = (ra * f * ef * af * cosine * 2 * pi) / (
            constants.bearingPressure * rho * pitch
        )
        # Factor of equation 17
        displacementConstant = (constants.gamma * pitch) / (2 * pi * cosine * ratio)
        self.constants = DeflectionConstants(
            Deflection.constantCurvature, critical, ratio, frictionConstant, displacementConstant
        )
        self.stickFactor = constants.gamma / ratio  # GAM/RHOR

    def phase(self, x: np.ndarray, theta: np.ndarray) -> np.ndarray:
        return (2 * pi * x) / self.pitch + theta

    def frictionDemand(self, x: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """Equation 10."""
        return self.constants.frictionConstant * np.cos(self.phase(x, theta))

    def stickElongation(self, x: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """Equation 15."""
        return self.stickFactor * np.sin(self.phase(x, theta))

    def coreDisplacement(self, x: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """Equation 17."""
        return self.constants.displacementConstant * (np.cos(theta) - np.cos(self.phase(x, theta)))

    def stiffness(self, momentZ: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Equation 40: EI = Mz rho."""
        return momentZ * self.radius


DeflectionModel = SinusoidalDeflection | ConstantCurvatureDeflection


def makeDeflectionModel(
    deflection: Deflection, value: StrandInput, constants: StrandConstants
) -> DeflectionModel:
    if deflection is Deflection.sinusoid:
        return SinusoidalDeflection(value, constants)
    return ConstantCurvatureDeflection(value, constants)


def stiffnessPositions(value: StrandInput, step: float, limit: int) -> np.ndarray:
    """X values of the stiffness programs' loop.

    They process X, then step while X < XFINAL, so the first X at or past
    XFINAL is processed too.
    """
    positions = [value.xStart]
    x = value.xStart
    while x < value.xEnd:
        x = x + step
        positions.append(x)
        if len(positions) > limit:
            raise InputError([f"More than {limit:,} positions along X."])
    return np.array(positions)


def scanPositions(value: StrandInput, step: float, limit: int) -> np.ndarray:
    """X values of FRICTION and DEPLACE: step first, stop once X reaches XFINAL."""
    positions = [value.xStart]
    x = value.xStart + step
    while x < value.xEnd:
        positions.append(x)
        x = x + step
        if len(positions) > limit:
            raise InputError([f"More than {limit:,} positions along X."])
    return np.array(positions)
