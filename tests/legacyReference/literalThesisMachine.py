"""The DOS machine the 1992 programs ran on: COMMON blocks, screen, keyboard, files.

Part of the line-by-line transcription of the six thesis programs (annex C of
Manuel/MANUEL.MAN). Each program is a function of a Machine `M`: COMMON
variables are attributes with their Fortran names, WRITE(*,...) and READ(*,*)
go through `M.write` and `M.read`, OPEN/WRITE/CLOSE on a unit through
`M.openUnit`, `M.writeUnit` and `M.closeUnit`. The keyboard is a dict of answers
by the name of the variable read; a READ with nothing left raises NeedAnswer.

Kept independent of the application's engine on purpose: only the Fortran
edit descriptors (services/fortranFormat.py) are shared.
"""

from __future__ import annotations

import math
import struct

from strandSlip.services.fortranFormat import formatRecord, keepsLineOpen


def real4(value: float) -> float:
    """A REAL*4 constant (no D exponent) as the double it becomes in an expression."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def rpow(x: float, y: float) -> float:
    """X**Y with a real exponent; X**2.0D0 is the correctly rounded square."""
    return x * x if y == 2.0 else x**y


def dnint(x: float) -> float:
    """DNINT: nearest whole number, halves away from zero."""
    return float(math.floor(x + 0.5)) if x >= 0 else float(math.ceil(x - 0.5))


class NeedAnswer(Exception):
    """The program waits for a keyboard answer the run was not given."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.name = name


class Machine:
    NMAX = 10  # PARAMETER (NMAX=10) of the compliance model

    def __init__(self, answers: dict[str, list[str]]) -> None:
        self.answers = {name: list(values) for name, values in answers.items()}
        self.records: list[str] = []  # the screen, record by record
        self.openLine: str | None = None  # a prompt written with a backslash
        self.files: dict[str, list[str]] = {}
        self.units: dict[int, str] = {}
        # COMMON/CSTF/ (both layouts), /CSTF1/, /COMPLAIS/, /CONV/, /XCST/, /PORTION/
        self.PI = self.THETA = self.RHOB = 0.0
        self.PP = self.PPA = self.PP1 = self.PN = self.PPB = self.PN1 = 0.0
        self.WLBAR = self.ABAR = 0.0
        self.GAMEXP = self.GAM1 = self.GAMD1 = self.GAME1 = self.GAMF1 = 0.0
        self.EN = 0.0
        self.ICONVERG = 0
        self.XINF = self.XSUP = self.XM = 0.0
        self.ICOTE = 0
        self.JDIM = self.NPOINT = self.NPORTION = 0
        # COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1), 1-based
        self.ZETA = [0.0] * (self.NMAX + 1)
        self.XCOMP = [0.0] * (self.NMAX + 2)
        self.YCOMP = [0.0] * (self.NMAX + 2)
        # Static locals that outlive a call (DOS FORTRAN allocated every local statically).
        self.IT = 0  # TRAPZD
        self.QROMB_S = [0.0] * 22
        self.QROMB_H = [0.0] * 22
        # The deflection's functions, bound by each program.
        self.DEPAME = self.ELGAME = self.FRCAME = self.FRICTION = None
        self.APPBRN = self.VMIN = None
        self.DEPFIL = self.ELGFIL = self.FRCFIL = None

    # -- screen and keyboard --------------------------------------------------

    def write(self, spec: str, *values: float | int) -> None:
        text = formatRecord(spec, values)
        lines = text.split("\n")
        if self.openLine is not None:
            lines[0] = self.openLine + lines[0]
            self.openLine = None
        if keepsLineOpen(spec):
            self.openLine = lines.pop()
        self.records.extend(lines)

    def read(self, name: str) -> str:
        queue = self.answers.get(name)
        if not queue:
            raise NeedAnswer(name)
        typed = queue.pop(0)
        if self.openLine is not None:
            self.records.append(self.openLine + typed)
            self.openLine = None
        else:
            self.records.append(typed)
        return typed

    def readReal(self, name: str) -> float:
        return float(self.read(name))

    def readInteger(self, name: str) -> int:
        return int(float(self.read(name)))

    def pause(self, message: str) -> None:
        if self.openLine is not None:
            self.records.append(self.openLine)
            self.openLine = None
        self.records.append(message)

    # -- files ------------------------------------------------------------------

    def openUnit(self, unit: int, name: str) -> None:
        self.units[unit] = name
        self.files[name] = []  # STATUS='UNKNOWN' and a first WRITE: the old contents go

    def writeUnit(self, unit: int, spec: str, *values: float | int) -> None:
        self.files[self.units[unit]].extend(formatRecord(spec, values).split("\n"))

    def closeUnit(self, unit: int) -> None:
        self.units.pop(unit, None)
