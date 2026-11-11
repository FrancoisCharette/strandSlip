"""The legacy files, record by record."""

from __future__ import annotations

from dataclasses import replace

import pytest

from masterRebuild.models.legacyProgram import BSINUS, NSINUS, RAYON, SINUS
from masterRebuild.models.strandPresets import reportStrandCurvature, reportStrandSinusoid
from masterRebuild.services import legacyOutputService
from masterRebuild.services.displacementService import runDisplacement
from masterRebuild.services.frictionService import runFriction
from masterRebuild.services.stiffnessService import runStiffness

example = reportStrandSinusoid.input

donsin = (
    "  AMPLITUDE=.4000E-01\n"
    "  R. DU NOYEAU=0.014\n"
    "  COEFFICIENT DE POISSON=0.300\n"
    "  ANGLE D ENROULEMENT=0.26180\n"
    "  R. DU TORON=.2135E-02\n"
    "  MODULE DE YOUNG DU TORON=.7000E+11\n"
    "  PRESSION D APPUI=.3186E+04\n"
    "  LONGUEUR D ONDE=10.00\n"
    "  LONGUEUR DU CABLE=   10.000\n"
    "  AMPL. CRITIQUE=.2726E-01\n"
    "  COEFF. F= 0.8000\n"
    "  PITCH= 0.3173\n"
    "  AIRE DU TORON=.1432E-04\n"
    "  INCREMENT EN X=  0.10000\n"
    "  INCREMENT EN XPAS=  0.00032\n"
    "  CONSTANTE EQ9=.3724521E-01\n"
    "  NOMBRE DE FIL:22\n"
    "  MOD. DE YOUG DU NOYEAU=.7000E+11\n"
    "  F SELON EQUATION 2b=.9129E+00\n"
    "  TENSION DANS LE FIL=.6435E+03\n"
    "  RAPPORT D AMP.=.1467E+01\n"
    "  GAMMA SELON EQUATION 17=.1329E-03\n"
)


@pytest.fixture(scope="module")
def sinusResult():
    return runStiffness(example, SINUS)


def testTheResultRecordOfTheReportedPosition(sinusResult) -> None:
    rows = legacyOutputService.stiffnessRows(sinusResult)
    assert len(rows) == 101  # X = 0 is not written
    assert rows[24] == "   2.5000  1671.2433  0.0000 0.1696   26.391  0.0000  3.358  522.655"


def testTheSummaryFile(sinusResult) -> None:
    assert legacyOutputService.legacyFiles(sinusResult)["DONSIN.DAT"] == donsin


@pytest.mark.parametrize(
    ("program", "names"),
    [
        (SINUS, ["RESSIN.DAT", "DONSIN.DAT", "ENTRE.DAT", "SINUS.OUT"]),
        (BSINUS, ["RESFIN.DAT", "DONNE1.DAT", "ENTRE.DAT", "BSINUS.OUT"]),
    ],
)
def testEachProgramWritesItsOwnFileNames(program, names) -> None:
    result = runStiffness(replace(example, xEnd=1.0), program)
    assert list(legacyOutputService.legacyFiles(result)) == names


def testFrictionAndDisplacementFiles() -> None:
    friction = legacyOutputService.legacyFiles(runFriction(replace(example, xEnd=0.25)))
    assert list(friction) == ["F_RESFIN.DAT", "F_DONNE1.DAT", "ENTRE.DAT", "FRICTION.OUT"]
    assert friction["F_RESFIN.DAT"].splitlines()[60] == "      0.2000     -0.0632929    17"
    assert friction["F_DONNE1.DAT"].splitlines()[-1] == "  TENSION DANS LE FIL=.6435E+03"
    displacement = legacyOutputService.legacyFiles(runDisplacement(replace(example, xEnd=0.25)))
    assert list(displacement) == ["D_RESFIN.DAT", "ENTRE.DAT", "DEPLACE.OUT"]
    assert displacement["D_RESFIN.DAT"].splitlines()[60] == (
        "  0.2000    0.13719E-01    17   0.19023E+00   0.16332E+00"
    )


def testRayonSummaryAndOverflowingFields() -> None:
    result = runStiffness(replace(reportStrandCurvature.input, xEnd=0.01), RAYON)
    files = legacyOutputService.legacyFiles(result)
    summary = files["DONRAY.DAT"].splitlines()
    assert summary[0] == "  RAYON DE COUR.=   50.000"
    assert summary[8] == "  RAYON CRITIQUE=.9293E+02"
    # FYT passes -9.999 and no longer fits F6.3: the original printed asterisks too.
    assert "******" in files["RESRAY.DAT"]


def testScreenStartsWithTheThetasWithoutCarriageControl(sinusResult) -> None:
    screen = legacyOutputService.screenText(legacyOutputService.consoleRecords(sinusResult))
    lines = screen.splitlines()
    assert lines[0] == "   2         0.2856"
    assert lines[20] == "  22         5.9976"
    assert lines[21] == "  0.1000  1779.9448  -.0000 0.0000    1.765  -.0000  0.000   34.952"


def testNsinusListsEveryWireBeforeEachRow() -> None:
    result = runStiffness(replace(example, xStart=2.5, xEnd=2.5), NSINUS)
    lines = legacyOutputService.screenText(legacyOutputService.consoleRecords(result)).splitlines()
    wireLines = lines[21:43]
    assert wireLines[0] == (
        "  2.50000    1  2.4966687  2.5794752  -.696E-05  -.698E-05  -.100E-03"
    )  # format 333: slipping above the limit
    assert wireLines[6] == "  2.50000    7  0.160E-03"  # 331: stuck, demand >= 0
    assert wireLines[9] == "0.25000E+01   10  0.189E-03"  # 332: stuck, demand < 0
    assert wireLines[11].startswith("0.25000E+01   12  2.4966687")  # 334: slipping below
    assert lines[43] == "  2.5000  1671.3207  0.0000 0.1683   26.392  0.0000  3.334  522.679"


def testTheScreenViewIsCappedButTheFileIsNot() -> None:
    result = runStiffness(replace(example, xEnd=2.0), NSINUS)
    capped = legacyOutputService.screenText(legacyOutputService.consoleRecords(result), limit=50)
    assert capped.splitlines()[-1].startswith("... (stopped after 50 lines")
    full = legacyOutputService.legacyFiles(result)["NSINUS.OUT"]
    assert len(full.splitlines()) == 21 + 21 * 22 + 20


def testWritingUsesDosLineEndingsAndRefusesToOverwrite(tmp_path, sinusResult) -> None:
    paths = legacyOutputService.writeLegacyFiles(sinusResult, tmp_path)
    assert sorted(p.name for p in paths) == ["DONSIN.DAT", "ENTRE.DAT", "RESSIN.DAT", "SINUS.OUT"]
    raw = (tmp_path / "DONSIN.DAT").read_bytes()
    assert raw == donsin.replace("\n", "\r\n").encode("ascii")
    with pytest.raises(FileExistsError, match="RESSIN.DAT"):
        legacyOutputService.writeLegacyFiles(sinusResult, tmp_path)
    legacyOutputService.writeLegacyFiles(sinusResult, tmp_path, overwrite=True)
