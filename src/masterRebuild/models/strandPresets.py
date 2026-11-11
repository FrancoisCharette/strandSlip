"""Example inputs taken from the 1991 progress reports.

Progress report no. 2 (February 1991) describes the strand the programs were
run on: 22 aluminium wires of 2.135 mm radius wound at 15 degrees on a
13.53 mm aluminium core, 643.5 N in each wire, a limit friction coefficient of
0.8, and a sinusoidal deflection of 0.04 m amplitude over a 10 m wavelength.
The helix angle is given here as 0.2618 rad because that is what was typed
into ENTRE.EXE: with exactly 15 degrees the printed SINUS.FOR results differ
in their last digit.
"""

from __future__ import annotations

from dataclasses import dataclass

from masterRebuild.models.strandInput import StrandInput


@dataclass(frozen=True)
class StrandPreset:
    name: str
    description: str
    input: StrandInput


reportStrandSinusoid = StrandPreset(
    name="1991 Strand, Sinusoidal Deflection",
    description=(
        "Progress report no. 2 (February 1991): 22 aluminium wires on a 13.53 mm core, "
        "643.5 N per wire, A = 0.04 m over λ = 10 m. Run SINUS: at X = 2.5 m the report "
        "printed a stiffness of 1671.24."
    ),
    input=StrandInput(
        strandLength=10.0,
        wireCount=22,
        helixAngle=0.2618,
        wireRadius=0.002135,
        wireModulus=70e9,
        wireTension=643.5,
        coreRadius=0.01353,
        coreModulus=70e9,
        corePoisson=0.3,
        frictionLimit=0.8,
        wavelength=10.0,
        amplitude=0.04,
        positionCount=100,
        xStart=0.0,
        xEnd=10.0,
    ),
)

reportStrandCurvature = StrandPreset(
    name="1991 Strand, Constant Curvature",
    description=(
        "The same strand bent to a constant 50 m radius (about half the critical radius, "
        "so part of each lay length slips), over one lay length in 1 mm steps. Run RAYON."
    ),
    input=StrandInput(
        strandLength=10.0,
        wireCount=22,
        helixAngle=0.2618,
        wireRadius=0.002135,
        wireModulus=70e9,
        wireTension=643.5,
        coreRadius=0.01353,
        coreModulus=70e9,
        corePoisson=0.3,
        frictionLimit=0.8,
        wavelength=0.0,
        amplitude=50.0,
        positionCount=10000,
        xStart=0.0,
        xEnd=0.32,
    ),
)

allPresets: tuple[StrandPreset, ...] = (reportStrandSinusoid, reportStrandCurvature)
defaultPreset = reportStrandSinusoid
