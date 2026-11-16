"""Result tables and CSV export."""

from __future__ import annotations

import csv
from dataclasses import replace

import numpy as np

from strandSlip.models.legacyProgram import SINUS
from strandSlip.models.strandPresets import reportStrandSinusoid
from strandSlip.services.displacementService import runDisplacement
from strandSlip.services.frictionService import runFriction
from strandSlip.services.resultTableService import resultTable, writeCsv
from strandSlip.services.stiffnessService import runStiffness

example = replace(reportStrandSinusoid.input, xEnd=1.0)


def testStiffnessTableHasTheResultFileColumns() -> None:
    table = resultTable(runStiffness(example, SINUS))
    assert [c.legacyName for c in table.columns] == [
        "X",
        "RIG",
        "TMXT",
        "FMXYT",
        "FMXZT",
        "FXT",
        "FYT",
        "FZT",
    ]
    # 0.1 added ten times is 0.9999999999999999 < 1.0, so the loop also runs
    # X = 1.1; X = 0 is not a row, as in RESSIN.DAT.
    assert table.rowCount == 11
    assert table.columns[0].values[-1] > 1.0


def testWireTablesAreInTheOrderTheProgramsWrote() -> None:
    friction = resultTable(runFriction(example))
    assert [c.legacyName for c in friction.columns] == ["X", "CFX", "I"]
    assert friction.columns[2].values[:3].tolist() == [1, 2, 3]
    assert friction.rowCount == 11 * 22  # X = 0 to 0.9999999999999999
    displacement = resultTable(runDisplacement(example))
    assert [c.legacyName for c in displacement.columns] == ["X", "DX", "I", "CA19", "CB19"]


def testCsvKeepsEveryDigit(tmp_path) -> None:
    table = resultTable(runStiffness(example, SINUS))
    path = tmp_path / "sinus.csv"
    writeCsv(table, path)
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0][1] == "Stiffness EI (N·m²) [RIG]"
    readBack = np.array([[float(v) for v in row] for row in rows[1:]])
    original = np.column_stack([c.values for c in table.columns])
    assert np.array_equal(readBack, original)
