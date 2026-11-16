"""Shows a ResultTable in a QTableView without copying its arrays."""

from __future__ import annotations

import math

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from strandSlip.models.analysisResults import ResultTable

Index = QModelIndex | QPersistentModelIndex


class ResultTableModel(QAbstractTableModel):
    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)
        self.table: ResultTable | None = None

    def setTable(self, table: ResultTable | None) -> None:
        self.beginResetModel()
        self.table = table
        self.endResetModel()

    def rowCount(self, parent: Index = QModelIndex()) -> int:
        return 0 if parent.isValid() or self.table is None else self.table.rowCount

    def columnCount(self, parent: Index = QModelIndex()) -> int:
        return 0 if parent.isValid() or self.table is None else len(self.table.columns)

    def data(self, index: Index, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if self.table is None or not index.isValid():
            return None
        column = self.table.columns[index.column()]
        value = column.values[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            if column.integer:
                return str(int(value))
            number = float(value)
            if not math.isfinite(number):
                return str(number)
            return f"{number:.4f}" if column.legacyName == "X" else f"{number:.6g}"
        if role == Qt.ItemDataRole.ToolTipRole and not column.integer:
            return repr(float(value))  # every digit, on demand
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        if self.table is None or role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            column = self.table.columns[section]
            return f"{column.header}\n{column.legacyName}"
        return str(section + 1)
