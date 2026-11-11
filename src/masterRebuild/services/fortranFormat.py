"""Fortran 77 formatted records, the way the 1990 programs wrote and read them.

Only what the legacy FORMAT statements use: nX, quoted text, '/', Iw, Fw.d,
Ew.d, Ew.dEe and Dw.d on output; Iw, Fw.d, Ew.d and Dw.d on input. Callers
pass the FORMAT contents exactly as they appear in the .FOR files, so each
record can be checked against the source by eye.

Conventions where Fortran leaves a choice to the compiler follow gfortran:
the optional leading zero is printed when it fits and dropped when it does
not; a value that does not fit fills the field with asterisks; a negative
value that rounds to zero keeps its minus sign. Ties round away from zero.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Context, Decimal, localcontext
from functools import lru_cache


class FortranFormatError(ValueError):
    """A FORMAT this module does not handle, or a field it cannot read."""


@dataclass(frozen=True)
class FormatItem:
    kind: str  # "X", "TEXT", "/", "I", "F", "E", "D"
    width: int = 0
    decimals: int = 0
    exponentDigits: int | None = None
    text: str = ""


_descriptorPattern = re.compile(r"^(\d*)([IFEDX])(\d*)(?:\.(\d+))?(?:E(\d+))?$")


def _tokens(spec: str) -> list[str]:
    """Split a FORMAT body into descriptors, quoted strings and slashes."""
    tokens: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(spec):
        char = spec[index]
        if char == "'":
            end = index + 1
            text: list[str] = []
            while True:
                if end >= len(spec):
                    raise FortranFormatError(f"Unterminated string in FORMAT: {spec!r}")
                if spec[end] == "'":
                    if end + 1 < len(spec) and spec[end + 1] == "'":
                        text.append("'")
                        end += 2
                        continue
                    break
                text.append(spec[end])
                end += 1
            tokens.append("'" + "".join(text))
            index = end + 1
            continue
        if char in ",/":
            if current:
                tokens.append("".join(current))
                current = []
            if char == "/":
                tokens.append("/")
        elif not char.isspace():  # Fortran ignores blanks outside strings
            current.append(char.upper())
        index += 1
    if current:
        tokens.append("".join(current))
    return tokens


@lru_cache(maxsize=256)
def parseFormat(spec: str) -> tuple[FormatItem, ...]:
    items: list[FormatItem] = []
    for token in _tokens(spec):
        if token == "/":
            items.append(FormatItem("/"))
            continue
        if token.startswith("'"):
            items.append(FormatItem("TEXT", text=token[1:]))
            continue
        match = _descriptorPattern.match(token)
        if not match:
            raise FortranFormatError(f"Unsupported edit descriptor {token!r} in {spec!r}")
        repeat, kind, width, decimals, exponentDigits = match.groups()
        if kind == "X":
            if width or decimals:
                raise FortranFormatError(f"Malformed X descriptor {token!r}")
            items.append(FormatItem("X", width=int(repeat or 1)))
            continue
        if not width:
            raise FortranFormatError(f"Missing field width in {token!r}")
        if kind in "FED" and decimals is None:
            raise FortranFormatError(f"Missing decimals in {token!r}")
        item = FormatItem(
            kind,
            width=int(width),
            decimals=int(decimals or 0),
            exponentDigits=int(exponentDigits) if exponentDigits else None,
        )
        items.extend([item] * int(repeat or 1))
    return tuple(items)


def _nonFinite(value: float, width: int) -> str:
    if math.isnan(value):
        candidates = ("NaN",)
    elif value > 0:
        candidates = ("Infinity", "Inf")
    else:
        candidates = ("-Infinity", "-Inf")
    for text in candidates:
        if len(text) <= width:
            return text.rjust(width)
    return "*" * width


def formatInteger(value: int, width: int) -> str:
    text = str(int(value))
    return text.rjust(width) if len(text) <= width else "*" * width


def _isTie(value: float, scale: int) -> bool:
    """Whether |value| * 10**scale lies exactly halfway between two integers.

    Only then does round-half-away (Fortran) differ from the round-half-even
    of Python's float formatting, which is otherwise exact and much faster.
    """
    numerator, denominator = abs(value).as_integer_ratio()
    if scale >= 0:
        doubled, divisor = numerator * 2 * 10**scale, denominator
    else:
        doubled, divisor = numerator * 2, denominator * 10**-scale
    return doubled % divisor == 0 and (doubled // divisor) % 2 == 1


def _fixedText(value: float, decimals: int) -> str:
    if not _isTie(value, decimals):
        return f"{value:.{decimals}f}"
    with localcontext(Context(prec=1000)):
        quantum = Decimal(1).scaleb(-decimals)
        return format(Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP), "f")


def _significantDigits(value: float, decimals: int) -> tuple[str, int]:
    """|value| as `decimals` digits d1d2... and the exponent of 0.d1d2... x 10^e."""
    mantissa, exponentText = f"{abs(value):.{decimals - 1}e}".split("e")
    exponent = int(exponentText)
    if _isTie(value, decimals - 1 - exponent) or _isTie(value, decimals - exponent):
        with localcontext(Context(prec=decimals, rounding=ROUND_HALF_UP)):
            rounded = +Decimal(abs(value))
        _, digitTuple, decimalExponent = rounded.as_tuple()
        digits = "".join(str(d) for d in digitTuple).ljust(decimals, "0")
        return digits, int(decimalExponent) + len(digitTuple)
    return mantissa.replace(".", ""), exponent + 1


def formatFixed(value: float, width: int, decimals: int) -> str:
    """Fw.d"""
    if not math.isfinite(value):
        return _nonFinite(value, width)
    text = _fixedText(value, decimals)
    if decimals == 0:
        text += "."
    if len(text) > width:
        if text.startswith("0."):
            text = text[1:]
        elif text.startswith("-0."):
            text = "-" + text[2:]
    return text.rjust(width) if len(text) <= width else "*" * width


def formatExponent(
    value: float,
    width: int,
    decimals: int,
    exponentDigits: int | None = None,
    letter: str = "E",
) -> str:
    """Ew.d, Ew.dEe and Dw.d: a 0.ddddE+ee mantissa between 0.1 and 1."""
    if not math.isfinite(value):
        return _nonFinite(value, width)
    if decimals < 1:
        raise FortranFormatError("Ew.d needs at least one digit after the point")
    negative = math.copysign(1.0, value) < 0
    if value == 0:
        digits, exponent = "0" * decimals, 0
    else:
        digits, exponent = _significantDigits(value, decimals)
    sign = "-" if negative else ""
    magnitude = abs(exponent)
    exponentSign = "-" if exponent < 0 else "+"
    if exponentDigits is None:
        if magnitude <= 99:
            exponentText = f"{letter}{exponentSign}{magnitude:02d}"
        elif magnitude <= 999:
            exponentText = f"{exponentSign}{magnitude:03d}"
        else:
            return "*" * width
    else:
        if magnitude >= 10**exponentDigits:
            return "*" * width
        exponentText = f"E{exponentSign}{str(magnitude).zfill(exponentDigits)}"
    text = f"{sign}0.{digits}{exponentText}"
    if len(text) > width:
        text = f"{sign}.{digits}{exponentText}"
    return text.rjust(width) if len(text) <= width else "*" * width


def _formatValue(item: FormatItem, value: float | int) -> str:
    if item.kind == "I":
        return formatInteger(int(value), item.width)
    if item.kind == "F":
        return formatFixed(float(value), item.width, item.decimals)
    letter = "D" if item.kind == "D" else "E"
    return formatExponent(float(value), item.width, item.decimals, item.exponentDigits, letter)


def formatRecord(spec: str, values: Sequence[float | int] = ()) -> str:
    """One WRITE with this FORMAT; '/' becomes a line break."""
    parts: list[str] = []
    remaining = list(values)
    for item in parseFormat(spec):
        if item.kind == "X":
            parts.append(" " * item.width)
        elif item.kind == "TEXT":
            parts.append(item.text)
        elif item.kind == "/":
            parts.append("\n")
        else:
            if not remaining:
                raise FortranFormatError(f"FORMAT ({spec}) has more descriptors than values")
            parts.append(_formatValue(item, remaining.pop(0)))
    if remaining:
        raise FortranFormatError(f"FORMAT ({spec}) has fewer descriptors than values")
    return "".join(parts)


_realFieldPattern = re.compile(r"([+-]?)(\d*)(?:\.(\d*))?(?:[EDQ]([+-]?\d+)|([+-]\d+))?")


def parseReal(field: str, decimals: int) -> float:
    """Read an Fw.d / Ew.d / Dw.d input field.

    Blanks are ignored (BLANK='NULL', the default for an OPENed file) and an
    all-blank field reads as zero. Without a decimal point the last `decimals`
    digits are the fraction: under D14.8, "10" reads as 1.0E-7.
    """
    text = "".join(field.split()).upper()
    if not text:
        return 0.0
    match = _realFieldPattern.fullmatch(text)
    if not match:
        raise FortranFormatError(f"Not a number: {field.strip()!r}")
    sign, wholeDigits, fractionDigits, exponentA, exponentB = match.groups()
    if not wholeDigits and not fractionDigits:
        raise FortranFormatError(f"Not a number: {field.strip()!r}")
    exponent = int(exponentA or exponentB or 0)
    with localcontext(Context(prec=100)):
        if fractionDigits is None:
            number = Decimal(wholeDigits).scaleb(-decimals)
        else:
            number = Decimal(f"{wholeDigits or '0'}.{fractionDigits or '0'}")
        number = number.scaleb(exponent)
    result = float(number)
    return -result if sign == "-" else result


def parseInteger(field: str) -> int:
    text = "".join(field.split())
    if not text:
        return 0
    if not re.fullmatch(r"[+-]?\d+", text):
        raise FortranFormatError(f"Not an integer: {field.strip()!r}")
    return int(text)


def readRecord(spec: str, line: str) -> list[float | int]:
    """One READ of one record with this FORMAT (X, I, F, E, D only)."""
    values: list[float | int] = []
    position = 0
    for item in parseFormat(spec):
        if item.kind == "X":
            position += item.width
            continue
        if item.kind not in "IFED":
            raise FortranFormatError(f"Input FORMAT cannot contain {item.kind!r}")
        field = line[position : position + item.width]  # short records pad with blanks
        position += item.width
        if item.kind == "I":
            values.append(parseInteger(field))
        else:
            values.append(parseReal(field, item.decimals))
    return values
