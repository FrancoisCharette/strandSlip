"""ENTRE.DAT, written exactly as ENTRE.FOR wrote it and read the way SINUS.FOR read it.

Each value is one record. ENTRE.FOR wrote reals with FORMAT(1X,D14.8,10X,'...')
and integers with FORMAT(1X,I6,18X,'...'), the text after the value being a
comment for whoever opened the file. The programs read them back with
FORMAT(1X,D14.8) and FORMAT(1X,I6): only columns 2-15 (or 2-7) count.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from strandSlip.models.strandInput import FieldKind, StrandInput, inputFields
from strandSlip.services import fortranFormat

logger = logging.getLogger(__name__)

realWriteFormat = "1X,D14.8,10X,'{label}'"
integerWriteFormat = "1X,I6,18X,'{label}'"
realReadFormat = "1X,D14.8"
integerReadFormat = "1X,I6"
# The 1990 files were written by DOS: CR LF after every record.
recordSeparator = "\r\n"


class EntreFileError(ValueError):
    """ENTRE.DAT could not be read the way the programs read it."""


@dataclass(frozen=True)
class EntreReadResult:
    input: StrandInput
    warnings: list[str] = field(default_factory=list)


def formatEntreRecords(value: StrandInput) -> list[str]:
    """The fifteen records of ENTRE.DAT, without line terminators."""
    records = []
    for inputField, number in zip(inputFields, value.values(), strict=True):
        spec = (
            integerWriteFormat if inputField.kind is FieldKind.integer else realWriteFormat
        ).format(label=inputField.entreLabel)
        records.append(fortranFormat.formatRecord(spec, [number]))
    return records


def formatEntreText(value: StrandInput) -> str:
    return "\n".join(formatEntreRecords(value)) + "\n"


def writeEntreFile(value: StrandInput, path: Path) -> None:
    records = formatEntreRecords(value)
    path.write_bytes((recordSeparator.join(records) + recordSeparator).encode("ascii"))
    logger.info("Wrote %s", path)


def _splitRecords(text: str) -> list[str]:
    # A DOS editor may have left a Ctrl-Z end-of-file mark.
    return text.replace("\x1a", "").splitlines()


def parseEntreText(text: str) -> EntreReadResult:
    records = _splitRecords(text)
    if len(records) < len(inputFields):
        raise EntreFileError(
            f"ENTRE.DAT needs {len(inputFields)} lines, one per value; this one has "
            f"{len(records)}. The programs would have stopped with an end-of-file error "
            f"while reading '{inputFields[len(records)].entreLabel}'."
        )
    values: list[float | int] = []
    warnings: list[str] = []
    for lineNumber, (inputField, record) in enumerate(
        zip(inputFields, records, strict=False), start=1
    ):
        isInteger = inputField.kind is FieldKind.integer
        spec = integerReadFormat if isInteger else realReadFormat
        fieldEnd = 7 if isInteger else 15
        try:
            (number,) = fortranFormat.readRecord(spec, record)
        except fortranFormat.FortranFormatError as error:
            raise EntreFileError(
                f"Line {lineNumber} ({inputField.entreLabel}): {error}. The value must sit "
                f"in columns 2 to {fieldEnd}, as ENTRE.EXE wrote it."
            ) from error
        if len(record) > fieldEnd and not record[fieldEnd].isspace():
            warnings.append(
                f"Line {lineNumber} ({inputField.entreLabel}): the number runs past column "
                f"{fieldEnd}; like the 1990 programs, only columns 2-{fieldEnd} were read."
            )
        if not isInteger and "." not in record[1:fieldEnd]:
            stripped = record[1:fieldEnd].strip()
            if stripped:
                warnings.append(
                    f"Line {lineNumber} ({inputField.entreLabel}): '{stripped}' has no decimal "
                    "point, so D14.8 read its last 8 digits as decimals."
                )
        values.append(number)
    if len(records) > len(inputFields):
        extra = [r for r in records[len(inputFields) :] if r.strip()]
        if extra:
            warnings.append(f"{len(extra)} line(s) after the fifteenth were ignored.")
    return EntreReadResult(StrandInput.fromValues(values), warnings)


def readEntreFile(path: Path) -> EntreReadResult:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise EntreFileError(f"Could not read {path}: {error.strerror or error}") from error
    # cp437 decodes any byte, as the DOS programs would have accepted them.
    return parseEntreText(raw.decode("cp437"))
