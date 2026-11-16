"""The 1992 programs: the application's engine against the line-by-line transcription.

`legacyReference.literalThesis*` transcribes every listing of annex C as it
is printed (Fortran names, GOTOs as loops, COMMON blocks as attributes). The
engine in `services/` is written for reading. Both must print the same screen
and write the same files, record for record: equal text means the same
doubles to the last digit printed (D16.10 for INCONNUS.DAT).
"""

from __future__ import annotations

import pytest

from legacyReference.literalThesisCompliance import ZETARHOB
from legacyReference.literalThesisComplianceSinus import ZETASIN
from legacyReference.literalThesisMachine import NeedAnswer
from legacyReference.literalThesisRadius import CONTRHOB, HARDRHOB
from legacyReference.literalThesisSinus import CONTSIN, HARDSIN
from strandSlip.models.thesisInput import SinusoidChoice, ThesisInput
from strandSlip.models.thesisProgram import thesisProgramByKey
from strandSlip.services.thesisRunner import runThesisProgram
from strandSlip.services.thesisSession import typedText

oracles = {
    "HARDRHOB": HARDRHOB,
    "CONTRHOB": CONTRHOB,
    "ZETARHOB": ZETARHOB,
    "HARDSIN": HARDSIN,
    "CONTSIN": CONTSIN,
    "ZETASIN": ZETASIN,
}


def oracleAnswers(key: str, value: ThesisInput) -> dict[str, list[str]]:
    """The keyboard, by the variable each READ fills, as someone would have typed it."""
    t = typedText
    profile = [t(0 if value.profile else 1)]
    approximations = [t(a) for a in value.approximations]
    if key == "HARDRHOB":
        return {"RHOB": [t(value.radius)], "ISORTIE": profile}
    if key == "CONTRHOB":
        return {"RHOB": [t(value.radius)], "ISORTIE": profile, "XB1": approximations}
    if key == "ZETARHOB":
        return {
            "GAM1": [t(value.compliance)],
            "RHOB": [t(value.radius)],
            "ISORTIE": profile,
            "XB1C": approximations,
        }
    answers = {
        "ICHOIX": [t(int(value.choice))],
        "WLBAR": [t(value.wavelength)],
        "ABAR": [t(value.amplitude)],
        "XTOUR": [t(value.turns)],
        "ISORTIE": profile,
    }
    if key == "CONTSIN":
        answers["XB1"] = approximations[0::2]
        answers["XB2"] = approximations[1::2]
    if key == "ZETASIN":
        answers["GAM1"] = [t(value.compliance)]
        answers["XB1C"] = approximations
    return answers


whole, ratio, one = (
    SinusoidChoice.wholeWavelength,
    SinusoidChoice.displacementRatio,
    SinusoidChoice.oneHalfPitch,
)
cases = [
    ("HARDRHOB", ThesisInput(radius=0.8)),
    ("HARDRHOB", ThesisInput(radius=0.6, profile=False)),
    ("CONTRHOB", ThesisInput(radius=0.8)),
    ("CONTRHOB", ThesisInput(radius=0.66, profile=False)),
    ("ZETARHOB", ThesisInput(radius=0.8, compliance=0.06)),
    ("ZETARHOB", ThesisInput(radius=1.0, compliance=0.06)),
    ("ZETARHOB", ThesisInput(radius=0.7, compliance=0.06, approximations=(0.10,))),
    ("ZETARHOB", ThesisInput(radius=1.5, compliance=0.03, profile=False)),
    ("HARDSIN", ThesisInput(choice=whole, amplitude=1.3)),
    ("HARDSIN", ThesisInput(choice=ratio, amplitude=1.3)),
    ("HARDSIN", ThesisInput(choice=one, amplitude=2.0, turns=6.5)),
    ("CONTSIN", ThesisInput(choice=whole, amplitude=1.3)),
    ("CONTSIN", ThesisInput(choice=ratio, amplitude=1.4)),
    ("CONTSIN", ThesisInput(choice=one, amplitude=1.4, turns=6.5)),
    ("ZETASIN", ThesisInput(choice=one, amplitude=1.4, turns=6.5)),
    ("ZETASIN", ThesisInput(choice=whole, amplitude=1.0)),
    ("ZETASIN", ThesisInput(choice=ratio, amplitude=1.3, profile=False)),
    ("ZETASIN", ThesisInput(choice=whole, amplitude=1.3, approximations=(0.149174136, 0.205))),
    ("ZETASIN", ThesisInput(choice=one, amplitude=2.0, turns=2.5, approximations=(0.19,))),
]


@pytest.mark.parametrize(
    ("key", "value"), cases, ids=[f"{k}-{i}" for i, (k, _) in enumerate(cases)]
)
def testEngineMatchesTheTranscriptionRecordForRecord(key: str, value: ThesisInput) -> None:
    oracle = oracles[key](oracleAnswers(key, value))
    result = runThesisProgram(thesisProgramByKey[key], value)
    assert result.pendingQuestion is None
    assert list(result.console) == oracle.records
    assert {name: list(records) for name, records in result.files.items()} == oracle.files


waitingCases = [
    ("HARDRHOB", ThesisInput(radius=1.2), "RHOB"),  # no macro-slip: asks for another radius
    ("CONTRHOB", ThesisInput(radius=0.6), "RHOB"),  # below 0.65: asks again
    ("ZETARHOB", ThesisInput(radius=0.7, compliance=0.06), "XB1C"),  # Newton fails
    ("HARDSIN", ThesisInput(choice=one, amplitude=1.3, turns=0.5), "XTOUR"),  # no macro-slip
    ("HARDSIN", ThesisInput(choice=one, amplitude=0.9), "ABAR"),  # refused, asked again
    ("ZETASIN", ThesisInput(choice=one, amplitude=2.0, turns=6.5), "XB1C"),
]


@pytest.mark.parametrize(("key", "value", "asked"), waitingCases)
def testBothStopWhereTheProgramAsksForMore(key: str, value: ThesisInput, asked: str) -> None:
    with pytest.raises(NeedAnswer) as stopped:
        oracles[key](oracleAnswers(key, value))
    assert stopped.value.name == asked
    result = runThesisProgram(thesisProgramByKey[key], value)
    assert result.pendingQuestion
    assert result.console[-1].strip().endswith(":")  # the question is on the screen, unanswered
