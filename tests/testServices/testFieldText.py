"""Typed values in, displayed values out."""

from __future__ import annotations

import pytest

from masterRebuild.models.strandInput import FieldKind
from masterRebuild.services.fieldText import FieldTextError, formatFieldValue, parseFieldText


@pytest.mark.parametrize(
    ("text", "expected"),
    [("0.2618", 0.2618), ("70e9", 7e10), ("0.7D+11", 7e10), ("0,3", 0.3), (" 643.5 ", 643.5)],
)
def testReals(text: str, expected: float) -> None:
    assert parseFieldText(text, FieldKind.real) == expected


@pytest.mark.parametrize("text", ["", "abc", "1,000.5", "inf", "nan"])
def testRealsRejected(text: str) -> None:
    with pytest.raises(FieldTextError):
        parseFieldText(text, FieldKind.real)


def testIntegers() -> None:
    assert parseFieldText("22", FieldKind.integer) == 22
    with pytest.raises(FieldTextError):
        parseFieldText("22.5", FieldKind.integer)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (10.0, "10"),
        (0.0, "0"),
        (0.2618, "0.2618"),
        (7e10, "7e10"),
        (1e-7, "1e-7"),
        (643.5, "643.5"),
        (0.002135, "0.002135"),
        (22, "22"),
        (-1.5, "-1.5"),
        (2.5e-5, "2.5e-5"),
    ],
)
def testDisplay(value, expected: str) -> None:
    assert formatFieldValue(value) == expected
    kind = FieldKind.integer if isinstance(value, int) else FieldKind.real
    assert parseFieldText(expected, kind) == value
