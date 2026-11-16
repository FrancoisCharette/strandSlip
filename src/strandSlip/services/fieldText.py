"""Turning what someone types into an ENTRE.DAT value, and back.

ENTRE.FOR read its answers list-directed, so "70E9", "70.D9" and "0.2618"
were all fine. The same spellings are accepted here, plus a decimal comma
for anyone whose keyboard gives one.
"""

from __future__ import annotations

import math

from strandSlip.models.strandInput import FieldKind


class FieldTextError(ValueError):
    pass


def parseFieldText(text: str, kind: FieldKind) -> float | int:
    cleaned = "".join(text.split())
    if not cleaned:
        raise FieldTextError("is empty")
    if kind is FieldKind.integer:
        try:
            return int(cleaned)
        except ValueError as error:
            raise FieldTextError(f"'{text.strip()}' is not a whole number") from error
    cleaned = cleaned.replace("D", "E").replace("d", "e")
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError as error:
        raise FieldTextError(f"'{text.strip()}' is not a number") from error
    if not math.isfinite(value):
        raise FieldTextError(f"'{text.strip()}' is not a finite number")
    return value


def formatFieldValue(value: float | int) -> str:
    """The shortest text that reads back as exactly this value.

    Plain decimals in the usual range (10, 0.2618, 643.5); exponents for
    the very large or small, as an engineer would type them (7e10, 1e-7).
    """
    if isinstance(value, int):
        return str(value)
    if value == 0 or 1e-4 <= abs(value) < 1e6:
        text = repr(value)
        return text[:-2] if text.endswith(".0") else text
    for digits in range(17):
        mantissa, exponent = f"{value:.{digits}e}".split("e")
        if float(f"{mantissa}e{exponent}") == value:
            return f"{mantissa}e{int(exponent)}"
    return repr(value)
