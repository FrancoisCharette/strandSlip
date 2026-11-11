"""The fifteen values of ENTRE.DAT, the input file every 1990 program reads.

ENTRE.FOR asked for them one prompt at a time and wrote one value per line.
SINUS, RAYON and the rest read them back in the same order, under their own
variable names: the strand programs say RF/EF/RA/EA (a wire, the core), the
cable programs say RT/ET/RN/EN (a strand, the core) for the very same slots.
RAYON reads the wavelength slot into a variable called RIEN ("nothing") and the
amplitude slot as the radius of curvature RHO.
"""

from __future__ import annotations

from dataclasses import astuple, dataclass, fields
from enum import StrEnum

# DIMENSION THETA(50),... in every program: more wires than this overran the
# arrays, which the $DEBUG build stopped with a subscript error.
maxWireCount = 50
# $STORAGE:2 made default INTEGERs two bytes wide.
maxLegacyInteger = 32767


class FieldKind(StrEnum):
    real = "real"
    integer = "integer"


@dataclass(frozen=True)
class InputField:
    """How one ENTRE.DAT value is named, shown, and written."""

    name: str  # attribute of StrandInput
    strandName: str  # variable in SINUS.FOR / RAYON.FOR
    cableName: str  # variable in BSINUS.FOR / NSINUS.FOR / FRICTION.FOR / DEPLACE.FOR
    label: str  # what the interface calls it
    symbol: str  # symbol used in the 1990 report
    unit: str
    kind: FieldKind
    entreLabel: str  # comment ENTRE.FOR wrote after the value
    entrePrompt: str  # question ENTRE.FOR asked
    group: str


@dataclass(frozen=True)
class StrandInput:
    """One ENTRE.DAT, in SI units as the 1990 programs expected."""

    strandLength: float  # CL
    wireCount: int  # NFIL
    helixAngle: float  # ALPHA, radians
    wireRadius: float  # RF (RT)
    wireModulus: float  # EF (ET)
    wireTension: float  # TI
    coreRadius: float  # RA (RN)
    coreModulus: float  # EA (EN), only ever reported
    corePoisson: float  # CPN
    frictionLimit: float  # CFL
    wavelength: float  # WL (RIEN in RAYON)
    amplitude: float  # AMP, or RHO in RAYON
    positionCount: int  # NPAS
    xStart: float  # XDEPART
    xEnd: float  # XFINAL

    def values(self) -> tuple[float | int, ...]:
        """The values in ENTRE.DAT order."""
        return astuple(self)

    @classmethod
    def fromValues(cls, values: tuple[float | int, ...] | list[float | int]) -> StrandInput:
        names = [f.name for f in fields(cls)]
        if len(values) != len(names):
            raise ValueError(f"ENTRE.DAT holds {len(names)} values, got {len(values)}")
        converted = {
            field.name: int(value) if field.kind is FieldKind.integer else float(value)
            for field, value in zip(inputFields, values, strict=True)
        }
        return cls(**converted)


_geometry = "Strand Geometry"
_materials = "Materials and Loading"
_deflection = "Imposed Deflection"
_positions = "Positions Along X"

inputFields: tuple[InputField, ...] = (
    InputField(
        "strandLength",
        "CL",
        "CL",
        "Strand Length",
        "L",
        "m",
        FieldKind.real,
        "Longueur du toron",
        "Quelle est la longueur du toron (en metre):",
        _geometry,
    ),
    InputField(
        "wireCount",
        "NFIL",
        "NFIL",
        "Number of Wires",
        "n",
        "",
        FieldKind.integer,
        "Nombre de fil",
        "Combien de fil sont entoure autour de l ame:",
        _geometry,
    ),
    InputField(
        "helixAngle",
        "ALPHA",
        "ALPHA",
        "Helix Angle",
        "α",
        "rad",
        FieldKind.real,
        "Angle d helice",
        "Quel est l angle d helice des fils (en radians):",
        _geometry,
    ),
    InputField(
        "wireRadius",
        "RF",
        "RT",
        "Wire Radius",
        "R_F",
        "m",
        FieldKind.real,
        "Rayon d un fil",
        "Quel est le rayon d un des fils (en metre):",
        _geometry,
    ),
    InputField(
        "wireModulus",
        "EF",
        "ET",
        "Wire Young's Modulus",
        "E",
        "Pa",
        FieldKind.real,
        "E des fils",
        "Quel est le module de Young des fils (en Pascal):",
        _materials,
    ),
    InputField(
        "wireTension",
        "TI",
        "TI",
        "Tension in One Wire",
        "T_i",
        "N",
        FieldKind.real,
        "Tension dans un fil",
        "Quelle est la tension dans un fil (en Newton):",
        _materials,
    ),
    InputField(
        "coreRadius",
        "RA",
        "RN",
        "Core Radius",
        "R_a",
        "m",
        FieldKind.real,
        "Rayon de l ame",
        "Quel est le rayon de l ame (en metre):",
        _geometry,
    ),
    InputField(
        "coreModulus",
        "EA",
        "EN",
        "Core Young's Modulus",
        "E_a",
        "Pa",
        FieldKind.real,
        "E de l ame",
        "Quel est le module de Young de l ame (en Pascal):",
        _materials,
    ),
    InputField(
        "corePoisson",
        "CPN",
        "CPN",
        "Core Poisson's Ratio",
        "ν",
        "",
        FieldKind.real,
        "Coefficient de Poisson",
        "Quel est le coefficient de Poisson de l ame:",
        _materials,
    ),
    InputField(
        "frictionLimit",
        "CFL",
        "CFL",
        "Limit Friction Coefficient",
        "μ_L",
        "",
        FieldKind.real,
        "Coefficient de friction",
        "Quel est le coefficient de friction entre l ame et les fils:",
        _materials,
    ),
    InputField(
        "wavelength",
        "WL",
        "WL",
        "Wavelength",
        "λ",
        "m",
        FieldKind.real,
        "Longueur d onde",
        "Quelle est la longueur d onde de la sinusoide (en metre):",
        _deflection,
    ),
    InputField(
        "amplitude",
        "AMP",
        "AMP",
        "Amplitude or Radius of Curvature",
        "A / ρ",
        "m",
        FieldKind.real,
        "Amplitude ou rayon de courbure",
        "Quelle est l amplitude de la sinusoide ou le rayon de courbure (en metre):",
        _deflection,
    ),
    InputField(
        "positionCount",
        "NPAS",
        "NPAS",
        "Number of Positions",
        "N",
        "",
        FieldKind.integer,
        "Nombre de position",
        "Combien de position desirez-vous:",
        _positions,
    ),
    InputField(
        "xStart",
        "XDEPART",
        "XDEPART",
        "Start Position",
        "X₀",
        "m",
        FieldKind.real,
        "Point de depart",
        "Point de depart des iterations le long de X (en metre):",
        _positions,
    ),
    InputField(
        "xEnd",
        "XFINAL",
        "XFINAL",
        "End Position",
        "X_f",
        "m",
        FieldKind.real,
        "Point d arret",
        "Point d arret des iterations le long de X (en metre):",
        _positions,
    ),
)

fieldByName: dict[str, InputField] = {field.name: field for field in inputFields}
inputGroups: tuple[str, ...] = (_geometry, _materials, _deflection, _positions)
