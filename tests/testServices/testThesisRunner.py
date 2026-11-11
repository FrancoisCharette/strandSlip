"""Running the 1992 programs: inputs refused, questions left open, files written."""

from __future__ import annotations

from pathlib import Path

import pytest

from masterRebuild.models.thesisInput import SinusoidChoice, ThesisInput
from masterRebuild.models.thesisProgram import (
    HARDRHOB,
    HARDSIN,
    ZETARHOB,
    ZETASIN,
    allThesisPrograms,
)
from masterRebuild.services.analysisErrors import AnalysisError, InputError
from masterRebuild.services.thesisRunner import (
    legacyFiles,
    runThesisProgram,
    thesisScreenText,
    validationIssues,
    writeLegacyFiles,
)
from masterRebuild.services.thesisSession import ThesisSession, typedText


def testTypedTextReadsBackTheSameValue() -> None:
    assert typedText(28.0) == "28"
    assert typedText(0.8) == "0.8"
    assert typedText(1) == "1"
    assert typedText(0.149174136) == "0.149174136"
    assert float(typedText(1 / 3)) == 1 / 3


def testTheDefaultsRunEveryProgram() -> None:
    for program in allThesisPrograms:
        assert validationIssues(ThesisInput(), program) == []


@pytest.mark.parametrize(
    ("program", "value"),
    [
        (HARDRHOB, ThesisInput(radius=0.0)),
        (ZETARHOB, ThesisInput(compliance=-0.06)),
        (HARDSIN, ThesisInput(wavelength=1.0)),
        (HARDSIN, ThesisInput(wavelength=1000.0)),
        (HARDSIN, ThesisInput(amplitude=0.0)),
        (HARDSIN, ThesisInput(choice=SinusoidChoice.oneHalfPitch, turns=-1.0)),
    ],
)
def testInputsTheProgramsCouldNotRunOnAreRefused(program, value) -> None:
    assert validationIssues(value, program)
    with pytest.raises(InputError):
        runThesisProgram(program, value)


def testAQuestionLeftOpenKeepsWhatWasDone() -> None:
    """ZETASIN over the wavelength at Ā = 1.3 needs typed help at half-pitch 4.5."""
    value = ThesisInput(choice=SinusoidChoice.wholeWavelength, amplitude=1.3)
    result = runThesisProgram(ZETASIN, value)
    assert result.pendingQuestion and "XB1C" in result.pendingQuestion
    assert [h.start for h in result.halfPitches] == [0.5 * k for k in range(9)]
    assert result.totalEnergy is None
    assert result.console[-1].endswith("Entrez la nouvelle approximation de XB1C:")
    helped = runThesisProgram(ZETASIN, ThesisInput(**{**vars(value), "approximations": (0.15,)}))
    assert helped.approximationsUsed[:1] == (0.15,)


def testWhatAskedWhereSaysWhatToChange() -> None:
    result = runThesisProgram(HARDRHOB, ThesisInput(radius=1.2))
    assert "no macro-slip" in result.pendingQuestion
    assert not result.halfPitches


def testOverflowBecomesAnExplanation() -> None:
    far = ThesisInput(choice=SinusoidChoice.oneHalfPitch, wavelength=200.0, turns=40.0)
    with pytest.raises(AnalysisError, match="overflowed"):
        runThesisProgram(ZETASIN, far)


def testScreenTextDropsTheCarriageControlColumn() -> None:
    result = runThesisProgram(HARDRHOB, ThesisInput(radius=0.8, profile=False))
    text = thesisScreenText(result)
    assert "Entrez le rayon de courbure adim.:0.8" in text
    assert "\n  XB1=0.14758362D+00  XB2=0.35241638D+00\n" in text  # 3X, less one column


def testLegacyFilesAreDosTextInCodePage437(tmp_path: Path) -> None:
    result = runThesisProgram(ZETARHOB, ThesisInput(radius=0.8, compliance=0.06))
    names = set(legacyFiles(result))
    assert names == {
        "ENERGY.DAT", "INCONNUS.DAT", "ZETADEP.DAT", "ZETAELG.DAT", "ZETAFRC.DAT",
        "ZETADEPX.DAT", "ZETAELGX.DAT", "ZETAFRCX.DAT", "ZETARHOB.OUT",
    }  # fmt: skip
    paths = writeLegacyFiles(result, tmp_path)
    assert len(paths) == len(names)
    unknowns = (tmp_path / "INCONNUS.DAT").read_bytes()
    assert unknowns.startswith(b" Les param\x8atres impos\x82s sont:\r\n")  # è, é in CP437
    assert b" GAM1=0.60000000E-01   RHOB= 0.800000   THETAi= 1.570796\r\n" in unknowns
    with pytest.raises(FileExistsError):
        writeLegacyFiles(result, tmp_path)
    assert writeLegacyFiles(result, tmp_path, overwrite=True)


def testSessionHoldsThePromptUntilTheAnswer() -> None:
    session = ThesisSession(approximations=(0.25,))
    session.write("/,3X,'Entrez:',\\")
    assert session.records == [""] and session.openLine == "   Entrez:"
    assert session.askApproximation("1X,'XB1C:',\\", "?") == 0.25
    assert session.records == ["", "   Entrez: XB1C:0.25"]  # the next WRITE continues the line
