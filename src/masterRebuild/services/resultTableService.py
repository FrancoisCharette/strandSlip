"""Each program's result file as columns, and CSV export at full precision."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import numpy as np

from masterRebuild.models.analysisResults import (
    AnalysisResult,
    DisplacementResult,
    FrictionResult,
    ResultColumn,
    ResultTable,
    StiffnessResult,
)

logger = logging.getLogger(__name__)


def stiffnessTable(result: StiffnessResult) -> ResultTable:
    """RESSIN.DAT's columns, for the rows the program wrote."""
    rows = result.written
    return ResultTable(
        (
            ResultColumn("X (m)", "X", result.positions[rows]),
            ResultColumn("Stiffness EI (N·m²)", "RIG", result.stiffness[rows]),
            ResultColumn("Torsion Mx (N·m)", "TMXT", result.torsion[rows]),
            ResultColumn("Moment My (N·m)", "FMXYT", result.momentY[rows]),
            ResultColumn("Moment Mz (N·m)", "FMXZT", result.momentZ[rows]),
            ResultColumn("Force Fx (N)", "FXT", result.forceX[rows]),
            ResultColumn("Force Fy (N)", "FYT", result.forceY[rows]),
            ResultColumn("Force Fz (N)", "FZT", result.forceZ[rows]),
        )
    )


def _longFormat(positions: np.ndarray, wireCount: int) -> tuple[np.ndarray, np.ndarray]:
    """X repeated per wire, and wire numbers 1..n: the order the programs wrote."""
    return np.repeat(positions, wireCount), np.tile(np.arange(1, wireCount + 1), len(positions))


def frictionTable(result: FrictionResult) -> ResultTable:
    x, wire = _longFormat(result.positions, result.input.wireCount)
    return ResultTable(
        (
            ResultColumn("X (m)", "X", x),
            ResultColumn("Required Friction μ", "CFX", result.frictionDemand.ravel()),
            ResultColumn("Wire", "I", wire, integer=True),
        )
    )


def displacementTable(result: DisplacementResult) -> ResultTable:
    x, wire = _longFormat(result.positions, result.input.wireCount)
    return ResultTable(
        (
            ResultColumn("X (m)", "X", x),
            ResultColumn("Displacement × 10⁴ (m)", "DX", result.displacementScaled.ravel()),
            ResultColumn("Wire", "I", wire, integer=True),
            ResultColumn("Bracket CA19 (1/m)", "CA19", result.termA.ravel()),
            ResultColumn("Bracket CB19 (1/m)", "CB19", result.termB.ravel()),
        )
    )


def resultTable(result: AnalysisResult) -> ResultTable:
    if isinstance(result, StiffnessResult):
        return stiffnessTable(result)
    if isinstance(result, FrictionResult):
        return frictionTable(result)
    return displacementTable(result)


def writeCsv(table: ResultTable, path: Path) -> None:
    """Every value at full precision (shortest text that reads back the same double)."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([f"{c.header} [{c.legacyName}]" for c in table.columns])
        for row in range(table.rowCount):
            writer.writerow(
                [
                    int(c.values[row]) if c.integer else repr(float(c.values[row]))
                    for c in table.columns
                ]
            )
    logger.info("Wrote %d rows to %s", table.rowCount, path)
