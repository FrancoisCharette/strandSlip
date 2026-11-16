"""Read the recovered 1992 listings as a fixed-form Fortran compiler would.

A statement is columns 7-72 of its initial line and of its continuation lines
(a mark in column 6), each line padded to 72 columns. A line with a label in
columns 1-5 always starts a statement: INCONNUS.FOR prints `  10 FORMAT(`
with the F in column 6, a blank the printing lost, and its text starts there.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from strandSlip import appConfig

listingRoot = appConfig.projectRoot / "legacy" / "manuel1992"


def statements(path: Path, commented: bool = False) -> Iterator[tuple[int, str, str]]:
    """(first line, label, text) of each statement; with `commented`, of the
    WRITE and FORMAT statements commented out with a C in column 1."""
    current: list | None = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if commented:
            if not re.match(r"[Cc] {3}\d|[Cc]\s+(WRITE|FORMAT)", line):
                continue
            line = " " + line[1:]
        elif not line or line[0] in "Cc*$":
            continue
        padded = line.ljust(72)[:72]
        label = padded[:5].strip()
        marked = padded[5] not in " 0"
        if marked and not label.isdigit() and current is not None:
            current[2] += padded[6:72]
            continue
        if current is not None:
            yield (current[0], current[1], current[2])
        current = [number, label, padded[5:72] if marked else padded[6:72]]
    if current is not None:
        yield (current[0], current[1], current[2])
