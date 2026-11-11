"""Fortran edit descriptors, as the 1990 records need them."""

from __future__ import annotations

import random
from decimal import ROUND_HALF_UP, Context, Decimal, localcontext

import pytest

from masterRebuild.services import fortranFormat
from masterRebuild.services.fortranFormat import (
    FortranFormatError,
    formatExponent,
    formatFixed,
    formatInteger,
    formatRecord,
    parseFormat,
    parseInteger,
    parseReal,
    readRecord,
)


@pytest.mark.parametrize(
    ("value", "width", "decimals", "expected"),
    [
        (0.1696, 6, 4, "0.1696"),
        (-0.1696, 6, 4, "-.1696"),  # no room for the optional leading zero
        (-0.17, 7, 4, "-0.1700"),
        (1671.24334, 10, 4, " 1671.2433"),
        (2.5, 8, 4, "  2.5000"),
        (-11.712, 6, 3, "******"),  # does not fit: asterisks, as RESRAY.DAT shows
        (-1e-12, 6, 4, "-.0000"),  # a negative that rounds to zero keeps its sign
        (0.125, 5, 2, " 0.13"),  # an exact tie rounds away from zero
        (-0.125, 5, 2, "-0.13"),
        (3.0, 4, 0, "  3."),
        (float("nan"), 6, 4, "   NaN"),
    ],
)
def testFixed(value: float, width: int, decimals: int, expected: str) -> None:
    assert formatFixed(value, width, decimals) == expected


@pytest.mark.parametrize(
    ("value", "width", "decimals", "digits", "letter", "expected"),
    [
        (643.5, 9, 4, None, "E", ".6435E+03"),
        (0.04, 9, 4, None, "E", ".4000E-01"),
        (0.03724521, 12, 7, None, "E", ".3724521E-01"),
        (3185.98, 9, 4, 2, "E", ".3186E+04"),
        (10.0, 14, 8, None, "D", "0.10000000D+02"),
        (-10.0, 14, 8, None, "D", "-.10000000D+02"),
        (0.0, 14, 8, None, "D", "0.00000000D+00"),
        (0.99996, 10, 4, None, "E", "0.1000E+01"),  # rounding carries into the exponent
        (-643.5, 9, 4, None, "E", "*********"),
        (1e120, 11, 4, None, "E", " 0.1000+121"),  # three-digit exponents drop the E
        (1e120, 11, 4, 2, "E", "***********"),
        (12.345, 12, 5, None, "E", " 0.12345E+02"),
    ],
)
def testExponent(value, width, decimals, digits, letter, expected) -> None:
    assert formatExponent(value, width, decimals, digits, letter) == expected


def _exactFixed(value: float, decimals: int) -> str:
    with localcontext(Context(prec=1000)):
        quantum = Decimal(1).scaleb(-decimals)
        return format(Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP), "f")


def _exactDigits(value: float, decimals: int) -> tuple[str, int]:
    with localcontext(Context(prec=decimals, rounding=ROUND_HALF_UP)):
        rounded = +Decimal(abs(value))
    _, digits, exponent = rounded.as_tuple()
    return "".join(map(str, digits)).ljust(decimals, "0"), exponent + len(digits)


def testTheFastPathsRoundExactlyLikeDecimalHalfUp() -> None:
    """Python's float formatting is used except at exact ties; check it everywhere."""
    rng = random.Random(1990)
    values = [rng.uniform(-1e4, 1e4) for _ in range(3000)]
    values += [rng.uniform(-1, 1) * 10.0 ** rng.randint(-15, 15) for _ in range(3000)]
    values += [k / 2**m for k in range(-40, 41) for m in range(0, 9)]  # dyadic: real ties
    values += [9.9995, 0.99995, 999.95, 0.5, 1.5, 2.5, -2.5, 0.125, 1234.5625]
    for value in values:
        for decimals in (0, 1, 2, 3, 4, 5, 7):
            assert fortranFormat._fixedText(value, decimals) == _exactFixed(value, decimals)
        if value != 0:
            for decimals in (1, 3, 4, 5, 8):
                assert fortranFormat._significantDigits(value, decimals) == _exactDigits(
                    value, decimals
                ), (value, decimals)


def testInteger() -> None:
    assert formatInteger(22, 2) == "22"
    assert formatInteger(123, 2) == "**"
    assert formatInteger(-5, 3) == " -5"


def testRecordFromTheSinusResultFormat() -> None:
    spec = "1X,F8.4,1X,F10.4,2X,F6.4,1X,F6.4,1X,F8.3,2X,F6.4,1X,F6.3,1X,F8.3"
    values = [2.5, 1671.2433, 0.0, 0.1696, 26.391, 0.0, 3.358, 522.655]
    assert formatRecord(spec, values) == (
        "   2.5000  1671.2433  0.0000 0.1696   26.391  0.0000  3.358  522.655"
    )


def testSlashesAndTextAndLowercaseExponent() -> None:
    spec = "2X,'PRESSION D APPUI=',E9.4e2,/,2X,'LONGUEUR D ONDE=',F5.2"
    assert formatRecord(spec, [3185.98, 10.0]) == (
        "  PRESSION D APPUI=.3186E+04\n  LONGUEUR D ONDE=10.00"
    )
    assert formatRecord("'L''AME'") == "L'AME"


def testValueCountMustMatch() -> None:
    with pytest.raises(FortranFormatError):
        formatRecord("1X,F8.4,F8.4", [1.0])
    with pytest.raises(FortranFormatError):
        formatRecord("1X,F8.4", [1.0, 2.0])


def testUnsupportedDescriptorIsRefused() -> None:
    with pytest.raises(FortranFormatError):
        parseFormat("1X,G12.4")


def testRepeatCounts() -> None:
    assert formatRecord("2F5.1", [1.0, 2.0]) == "  1.0  2.0"


@pytest.mark.parametrize(
    ("field", "decimals", "expected"),
    [
        (" 0.10000000D+02", 8, 10.0),
        ("0.26180000D+00", 8, 0.2618),
        ("10", 8, 1e-7),  # no decimal point: the last 8 digits are the fraction
        ("1.5+03", 8, 1500.0),  # exponent sign without a letter
        ("-.5E1", 8, -5.0),
        ("1 0.5", 8, 10.5),  # blanks are ignored
        ("   ", 8, 0.0),  # an all-blank field is zero
        ("2.", 8, 2.0),
    ],
)
def testParseReal(field: str, decimals: int, expected: float) -> None:
    assert parseReal(field, decimals) == pytest.approx(expected, rel=1e-15)


@pytest.mark.parametrize("field", ["abc", ".", "+", "1.2.3", "1E"])
def testParseRealRejects(field: str) -> None:
    with pytest.raises(FortranFormatError):
        parseReal(field, 8)


def testParseInteger() -> None:
    assert parseInteger("    22") == 22
    assert parseInteger("") == 0
    with pytest.raises(FortranFormatError):
        parseInteger("2.5")


def testReadRecordUsesOnlyTheFieldColumns() -> None:
    assert readRecord("1X,D14.8", " 0.26180000D+00          Angle d helice") == [0.2618]
    assert readRecord("1X,I6", "     22                  Nombre de fil") == [22]
    assert readRecord("1X,D14.8", " 2.5") == [2.5]  # a short record pads with blanks
