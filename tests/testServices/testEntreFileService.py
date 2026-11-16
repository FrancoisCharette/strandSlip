"""ENTRE.DAT, byte for byte."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from strandSlip.models.strandPresets import allPresets, reportStrandSinusoid
from strandSlip.services.entreFileService import (
    EntreFileError,
    formatEntreText,
    parseEntreText,
    readEntreFile,
    writeEntreFile,
)

reportFile = (
    " 0.10000000D+02          Longueur du toron\n"
    "     22                  Nombre de fil\n"
    " 0.26180000D+00          Angle d helice\n"
    " 0.21350000D-02          Rayon d un fil\n"
    " 0.70000000D+11          E des fils\n"
    " 0.64350000D+03          Tension dans un fil\n"
    " 0.13530000D-01          Rayon de l ame\n"
    " 0.70000000D+11          E de l ame\n"
    " 0.30000000D+00          Coefficient de Poisson\n"
    " 0.80000000D+00          Coefficient de friction\n"
    " 0.10000000D+02          Longueur d onde\n"
    " 0.40000000D-01          Amplitude ou rayon de courbure\n"
    "    100                  Nombre de position\n"
    " 0.00000000D+00          Point de depart\n"
    " 0.10000000D+02          Point d arret\n"
)


def testTheFileIsWrittenAsEntreForWroteIt() -> None:
    assert formatEntreText(reportStrandSinusoid.input) == reportFile


@pytest.mark.parametrize("preset", allPresets, ids=lambda p: p.name)
def testPresetsSurviveARoundTrip(preset) -> None:
    result = parseEntreText(formatEntreText(preset.input))
    assert result.input == preset.input
    assert result.warnings == []


def testEightSignificantDigitsIsAllTheFileKeeps() -> None:
    exact = replace(reportStrandSinusoid.input, helixAngle=math.radians(15))
    readBack = parseEntreText(formatEntreText(exact)).input
    assert readBack.helixAngle == 0.26179939


def testWrittenWithDosLineEndings(tmp_path) -> None:
    path = tmp_path / "ENTRE.DAT"
    writeEntreFile(reportStrandSinusoid.input, path)
    raw = path.read_bytes()
    assert raw.count(b"\r\n") == 15
    assert readEntreFile(path).input == reportStrandSinusoid.input


def testUnixEndingsAndAControlZAreAccepted() -> None:
    assert parseEntreText(reportFile + "\x1a").input == reportStrandSinusoid.input


def testHandEditedValuesAreReadLikeFortranWithAWarning() -> None:
    lines = reportFile.splitlines()
    lines[0] = " 10"  # no decimal point: D14.8 reads it as 10E-8
    lines[5] = " 643.5"  # short, but with a point: fine
    result = parseEntreText("\n".join(lines))
    assert result.input.strandLength == pytest.approx(1e-7)
    assert result.input.wireTension == 643.5
    assert len(result.warnings) == 1
    assert "no decimal point" in result.warnings[0]


def testANumberPastColumnFifteenIsCut() -> None:
    lines = reportFile.splitlines()
    lines[2] = " 0.26179938779915"  # 14 characters of field, more digits beyond
    result = parseEntreText("\n".join(lines))
    assert result.input.helixAngle == 0.261799387799
    assert any("column 15" in warning for warning in result.warnings)


def testTooFewLinesNamesTheMissingValue() -> None:
    truncated = "\n".join(reportFile.splitlines()[:12])
    with pytest.raises(EntreFileError, match="Nombre de position"):
        parseEntreText(truncated)


def testGarbageNamesTheLine() -> None:
    lines = reportFile.splitlines()
    lines[4] = " seventy GPa"
    with pytest.raises(EntreFileError, match="Line 5"):
        parseEntreText("\n".join(lines))


def testAMissingFileIsAReadableError(tmp_path) -> None:
    with pytest.raises(EntreFileError, match="Could not read"):
        readEntreFile(tmp_path / "nowhere.dat")
