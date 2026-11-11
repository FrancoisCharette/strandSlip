"""The dimensionless equations of annex A, one class per imposed deflection.

`ConstantRadius` holds the constant-radius functions of the 1992 programs
(section C.4 of the manual: DEPAME, ELGAME, FRCAME, FRICTION, APPBRN, DEPFIL,
ELGFIL, FRCFIL), `Sinusoid` the sinusoidal ones (section C.5, plus VMIN).
Positions are in lay lengths (ξ = X/p), along the half-pitch the wire `i`
crosses. Each expression is the listing's, operand for operand.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

pi = math.acos(-1.0)  # PI=DACOS(-UN)


def square(value: float) -> float:
    """X**2.0D0: the correctly rounded square (the 8087's result; Windows' pow differs)."""
    return value * value


@dataclass(frozen=True)
class HalfPitch:
    """XINF, XSUP, XM and ICOTE: the half lay length analysed and its side of the plane."""

    start: float
    end: float
    middle: float
    side: int  # +1 or -1: the sign of cos(2 pi XM + THETA) (convention of page 41)

    @classmethod
    def starting(cls, start: float, theta: float) -> HalfPitch:
        end = start + 0.5
        middle = (start + end) / 2.0
        side = 1 if math.cos(2.0 * pi * middle + theta) > 0.0 else -1
        return cls(start, end, middle, side)


@dataclass(frozen=True)
class Compliance:
    """COMMON/CSTF1/ and EN: the compliance model's constants."""

    gamma: float  # GAM1, γ1
    exponent: float  # GAMEXP = 4 pi^2 / GAM1
    displacementFactor: float  # GAMD1
    strainFactor: float  # GAME1
    curvatureFactor: float  # GAMF1
    en: float = 2.0 / 3.0  # EN, the exponent of the compliance curve


@dataclass(frozen=True)
class ConstantRadius:
    """Deflection with a constant radius of curvature ρ̄ = RHOB."""

    radius: float  # RHOB
    theta: float  # THETA, the wire's angle at the origin

    def coreDisplacement(self, x: float) -> float:  # DEPAME, equation A.1
        return (math.cos(self.theta) - math.cos(2.0 * pi * x + self.theta)) / (
            2.0 * pi * self.radius
        )

    def coreStrain(self, x: float) -> float:  # ELGAME, A.3
        return math.sin(2.0 * pi * x + self.theta) / self.radius

    def coreCurvature(self, x: float) -> float:  # FRCAME, A.5
        return (2.0 * pi * math.cos(2.0 * pi * x + self.theta)) / self.radius

    def frictionMargin(self, x: float, side: int) -> float:  # FRICTION
        return (math.cos(2.0 * pi * x + self.theta) / self.radius) - side * 1.0

    def boundEquation(self, x: float, half: HalfPitch) -> float:  # APPBRN
        stuck = math.sin(2.0 * pi * x + self.theta) / self.radius
        slipping = -(half.side * 2.0 * pi * (half.middle - x))
        return stuck - slipping

    def compliance(self, gamma: float) -> Compliance:  # ENTZETA
        displacement = 1.0 / (2.0 * pi * self.radius)
        strain = 2.0 * pi * displacement
        return Compliance(
            gamma, (4.0 * square(pi)) / gamma, displacement, strain, 2.0 * pi * strain
        )

    def wireDisplacement(self, c: Compliance, side, xComp, yComp, zeta, beta, eta, x):
        """DEPFIL, A.17: the wire in a micro-slip region of compliance zeta."""
        root = math.sqrt(c.exponent / zeta)
        tmp1 = beta * math.exp(x * root)
        tmp2 = eta * math.exp(-(x * root))
        tmp3 = c.displacementFactor * math.cos(self.theta)
        tmp4 = (c.displacementFactor / (c.gamma * zeta + 1)) * math.cos((2.0 * pi * x) + self.theta)
        return (
            tmp1
            + tmp2
            + tmp3
            - tmp4
            + side * 2.0 * (c.gamma / (4.0 * pi)) * xComp
            - side * 2.0 * (c.gamma / (4.0 * pi)) * zeta * yComp
        )

    def wireStrain(self, c: Compliance, zeta, beta, eta, x):  # ELGFIL, A.23
        root = math.sqrt(c.exponent / zeta)
        tmp1 = beta * root * math.exp(x * root)
        tmp2 = eta * root * math.exp(-(x * root))
        tmp3 = (c.strainFactor / (c.gamma * zeta + 1)) * math.sin(2.0 * pi * x + self.theta)
        return tmp1 - tmp2 + tmp3

    def wireCurvature(self, c: Compliance, zeta, beta, eta, x):  # FRCFIL, A.24
        ratio = c.exponent / zeta
        root = math.sqrt(c.exponent / zeta)
        tmp1 = beta * ratio * math.exp(x * root)
        tmp2 = eta * ratio * math.exp(-(x * root))
        tmp3 = (c.curvatureFactor / (c.gamma * zeta + 1)) * math.cos(2.0 * pi * x + self.theta)
        return tmp1 + tmp2 + tmp3


@dataclass(frozen=True)
class Sinusoid:
    """Sinusoidal deflection of amplitude Ā = ABAR over Λ = WLBAR lay lengths."""

    amplitude: float  # ABAR
    wavelength: float  # WLBAR: lay lengths per wavelength
    theta: float

    @property
    def plusOne(self) -> float:  # PP
        return self.wavelength + 1.0

    @property
    def minusOne(self) -> float:  # PN
        return self.wavelength - 1.0

    @property
    def plusRatio(self) -> float:  # PPA
        return self.plusOne / self.wavelength

    @property
    def minusRatio(self) -> float:  # PPB
        return self.minusOne / self.wavelength

    @property
    def plusFrequency(self) -> float:  # PP1
        return 2.0 * pi * self.plusRatio

    @property
    def minusFrequency(self) -> float:  # PN1
        return 2.0 * pi * self.minusRatio

    def coreDisplacement(self, x: float) -> float:  # DEPAME, A.30
        tmp3a = math.sin(x * self.minusFrequency + self.theta) - math.sin(self.theta)
        tmp3b = math.sin(x * self.plusFrequency + self.theta) - math.sin(self.theta)
        return ((self.wavelength * self.amplitude) / (4.0 * pi)) * (
            tmp3a / self.minusOne - tmp3b / self.plusOne
        )

    def coreStrain(self, x: float) -> float:  # ELGAME, A.31
        return (
            self.amplitude
            * math.sin(2.0 * pi * x + self.theta)
            * math.sin((2 * pi * x) / self.wavelength)
        )

    def _demandTerms(self, x: float) -> tuple[float, float]:
        tmp1 = math.cos(2.0 * pi * x + self.theta) * math.sin((2.0 * pi * x) / self.wavelength)
        tmp2 = math.sin(2.0 * pi * x + self.theta) * math.cos((2.0 * pi * x) / self.wavelength)
        return tmp1, tmp2

    def coreCurvature(self, x: float) -> float:  # FRCAME, A.32
        tmp1, tmp2 = self._demandTerms(x)
        return ((2.0 * pi * self.amplitude) / self.wavelength) * (self.wavelength * tmp1 + tmp2)

    def frictionMargin(self, x: float, side: int) -> float:  # FRICTION
        tmp1, tmp2 = self._demandTerms(x)
        return (self.amplitude / self.wavelength) * (self.wavelength * tmp1 + tmp2) - side * 1.0

    def frictionPeak(self, x: float, side: int) -> float:  # VMIN: minimal where |demand| peaks
        tmp1, tmp2 = self._demandTerms(x)
        return -(side * (self.amplitude / self.wavelength) * (self.wavelength * tmp1 + tmp2))

    def boundEquation(self, x: float, half: HalfPitch) -> float:  # APPBRN
        stuck = (
            self.amplitude
            * math.sin(2.0 * pi * x + self.theta)
            * math.sin((2 * pi * x) / self.wavelength)
        )
        slipping = half.side * 2.0 * pi * (half.middle - x)
        return stuck + slipping

    def compliance(self, gamma: float) -> Compliance:  # ENSNZETA
        displacement = (self.amplitude * self.wavelength) / (4.0 * pi)
        strain = displacement * ((2.0 * pi) / self.wavelength)
        curvature = strain * ((2.0 * pi) / self.wavelength)
        return Compliance(gamma, (4.0 * square(pi)) / gamma, displacement, strain, curvature)

    def _waveDenominators(self, c: Compliance, zeta: float) -> tuple[float, float]:
        return (
            c.gamma * zeta * square(self.minusRatio) + 1.0,
            c.gamma * zeta * square(self.plusRatio) + 1.0,
        )

    def wireDisplacement(self, c: Compliance, side, xComp, yComp, zeta, beta, eta, x):
        """DEPFIL, A.39."""
        root = math.sqrt(c.exponent / zeta)
        tmp1 = beta * math.exp(x * root)
        tmp2 = eta * math.exp(-(x * root))
        minus, plus = self._waveDenominators(c, zeta)
        tmp3a = math.sin(x * self.minusFrequency + self.theta) / minus - math.sin(self.theta)
        tmp3b = math.sin(x * self.plusFrequency + self.theta) / plus - math.sin(self.theta)
        tmp3 = c.displacementFactor * (tmp3a / self.minusOne - tmp3b / self.plusOne)
        return (
            tmp1
            + tmp2
            + tmp3
            + 2.0 * (c.gamma / (4.0 * pi)) * side * xComp
            - 2.0 * (c.gamma / (4.0 * pi)) * side * zeta * yComp
        )

    def wireStrain(self, c: Compliance, zeta, beta, eta, x):  # ELGFIL, A.40
        root = math.sqrt(c.exponent / zeta)
        tmp1 = beta * root * math.exp(x * root)
        tmp2 = eta * root * math.exp(-(x * root))
        minus, plus = self._waveDenominators(c, zeta)
        tmp3a = math.cos(x * self.minusFrequency + self.theta) / minus
        tmp3b = math.cos(x * self.plusFrequency + self.theta) / plus
        return tmp1 - tmp2 + c.strainFactor * (tmp3a - tmp3b)

    def wireCurvature(self, c: Compliance, zeta, beta, eta, x):  # FRCFIL, A.41
        ratio = c.exponent / zeta
        root = math.sqrt(c.exponent / zeta)
        tmp1 = beta * ratio * math.exp(x * root)
        tmp2 = eta * ratio * math.exp(-(x * root))
        minus, plus = self._waveDenominators(c, zeta)
        tmp3a = -(self.minusOne * math.sin(x * self.minusFrequency + self.theta) / minus)
        tmp3b = self.plusOne * math.sin(x * self.plusFrequency + self.theta) / plus
        return tmp1 + tmp2 + c.curvatureFactor * (tmp3a + tmp3b)


Deflection = ConstantRadius | Sinusoid


def macroDisplacement(x: float, start: float, slope: float, offset: float, side: int) -> float:
    """DEPH (A.7, A.12, A.25...): the wire in the macro-slip region from XB1."""
    return (side * pi) * ((x - start) * (x - start)) + (slope * (x - start)) + offset


def macroStrain(x: float, start: float, slope: float, side: int) -> float:  # DR2H
    return (side * 2.0 * pi) * (x - start) + slope


def decayPlus(c: Compliance, x: float, zeta: float) -> float:  # F1D
    return math.exp(x * math.sqrt(c.exponent / zeta))


def decayPlusSlope(c: Compliance, x: float, zeta: float) -> float:  # F1E
    return math.sqrt(c.exponent / zeta) * math.exp(x * math.sqrt(c.exponent / zeta))


def decayMinus(c: Compliance, x: float, zeta: float) -> float:  # F2D
    return math.exp(-(x * math.sqrt(c.exponent / zeta)))


def decayMinusSlope(c: Compliance, x: float, zeta: float) -> float:  # F2E
    return -(math.sqrt(c.exponent / zeta) * math.exp(-(x * math.sqrt(c.exponent / zeta))))
