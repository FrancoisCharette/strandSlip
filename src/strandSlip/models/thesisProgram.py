"""The six Fortran programs of the 1992 master's thesis and what each one does.

They are the final models of the thesis (Charette, Université Laval, 1992;
final report "Analyse des caractéristiques d'amortissement d'un câble toronné
en régime vibratoire", March 1992). Each solves one wire of a strand over a
half lay length, in the dimensionless form of annex A, for an imposed
deflection with a constant radius of curvature (RAYON) or a sinusoid (SINUS),
and three models: Hardy's, continuity of deformation, and compliance. The
sources survive only as the printed listings of the program manual
(Manuel/MANUEL.MAN, annex C), recovered into legacy/manuel1992/.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ThesisModel(StrEnum):
    hardy = "hardy"  # macro-slip with strain jumps at its bounds (reactions)
    continuity = "continuity"  # macro-slip with continuous strain
    compliance = "compliance"  # micro-slip everywhere, macro-slip where it saturates


class ThesisDeflection(StrEnum):
    constantRadius = "constantRadius"
    sinusoid = "sinusoid"


@dataclass(frozen=True)
class ThesisProgramSpec:
    key: str
    directory: str  # on the 1992 diskettes, and under legacy/manuel1992/
    page: int  # of the main program's listing in the manual
    title: str
    summary: str
    model: ThesisModel
    deflection: ThesisDeflection

    @property
    def sourceFile(self) -> str:
        return f"{self.key}.FOR"


HARDRHOB = ThesisProgramSpec(
    key="HARDRHOB",
    directory="RAYON/HARDY",
    page=41,
    title="Hardy Model, Constant Radius of Curvature",
    summary="One half lay length of a wire bent to a constant radius of curvature: the "
    "macro-slip bounds where friction reaches its limit, the energy dissipated and the "
    "relative displacement difference. The strain jumps at the bounds (Hardy's model).",
    model=ThesisModel.hardy,
    deflection=ThesisDeflection.constantRadius,
)

CONTRHOB = ThesisProgramSpec(
    key="CONTRHOB",
    directory="RAYON/CNTDEF",
    page=38,
    title="Continuity of Deformation, Constant Radius of Curvature",
    summary="The same half lay length with the wire's strain continuous at the macro-slip "
    "bounds: four equations solved by Newton's method. The radius must lie between 0.65 "
    "and 1.0.",
    model=ThesisModel.continuity,
    deflection=ThesisDeflection.constantRadius,
)

ZETARHOB = ThesisProgramSpec(
    key="ZETARHOB",
    directory="RAYON/COMPLAIS",
    page=44,
    title="Compliance Model, Constant Radius of Curvature",
    summary="Micro-slip on a compliance curve cut into ten linear portions, with as many "
    "regions as the deflection needs (up to ten each side of a macro-slip region): the "
    "energy of every region and all the unknowns (ENERGY.DAT, INCONNUS.DAT).",
    model=ThesisModel.compliance,
    deflection=ThesisDeflection.constantRadius,
)

HARDSIN = ThesisProgramSpec(
    key="HARDSIN",
    directory="SINUS/HARDY",
    page=42,
    title="Hardy Model, Sinusoidal Deflection",
    summary="Hardy's model along a sinusoid: the energy over a whole wavelength (half lay "
    "length by half lay length up to λ/4, times four), the relative displacement "
    "difference at λ/4, or one half lay length chosen by its number of turns.",
    model=ThesisModel.hardy,
    deflection=ThesisDeflection.sinusoid,
)

CONTSIN = ThesisProgramSpec(
    key="CONTSIN",
    directory="SINUS/CNTDEF",
    page=39,
    title="Continuity of Deformation, Sinusoidal Deflection",
    summary="Continuity of deformation along a sinusoid, with the same three calculations "
    "as HARDSIN. The amplitude must lie between 1.0 and about 1.5 (for 28 lay lengths "
    "per wavelength).",
    model=ThesisModel.continuity,
    deflection=ThesisDeflection.sinusoid,
)

ZETASIN = ThesisProgramSpec(
    key="ZETASIN",
    directory="SINUS/COMPLAIS",
    page=46,
    title="Compliance Model, Sinusoidal Deflection",
    summary="The compliance model along a sinusoid, with the same three calculations; "
    "the number of regions found for one half lay length is where the next one starts.",
    model=ThesisModel.compliance,
    deflection=ThesisDeflection.sinusoid,
)

radiusPrograms: tuple[ThesisProgramSpec, ...] = (HARDRHOB, CONTRHOB, ZETARHOB)
sinusoidPrograms: tuple[ThesisProgramSpec, ...] = (HARDSIN, CONTSIN, ZETASIN)
allThesisPrograms = radiusPrograms + sinusoidPrograms
thesisProgramByKey: dict[str, ThesisProgramSpec] = {p.key: p for p in allThesisPrograms}
