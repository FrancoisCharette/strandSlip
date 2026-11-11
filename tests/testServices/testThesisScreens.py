"""Every FORMAT the engine prints must be one the 1992 listings print.

The listings are read as the compiler read them: statements are columns 7-72
of their lines, each line padded to 72 columns, so a string closed at the end
of a line and one opened on the next stay two strings (ECRZETA 41). Formats
are compared item by item (`parseFormat`), which ignores blanks outside
strings and keeps them inside.
"""

from __future__ import annotations

import re

import pytest

from listingReader import listingRoot, statements
from masterRebuild.services import thesisScreens
from masterRebuild.services.fortranFormat import FormatItem, parseFormat


def characterConstant(text: str) -> str:
    """The value of the Fortran character constant at the start of `text`."""
    value, index = [], 1
    while True:
        if text[index] == "'":
            if index + 1 < len(text) and text[index + 1] == "'":
                value.append("'")
                index += 2
                continue
            return "".join(value)
        value.append(text[index])
        index += 1


def formatsIn(text: str) -> list[str]:
    """The format of a FORMAT statement or of any WRITE with an inline format in `text`."""
    stripped = text.strip()
    if re.match(r"FORMAT\s*\(", stripped):
        return [stripped[stripped.index("(") + 1 : stripped.rindex(")")]]
    found = []
    for match in re.finditer(r"WRITE\s*\(\s*[*0-9]+\s*,\s*'", stripped):
        value = characterConstant(stripped[match.end() - 1 :]).strip()
        found.append(value[1:-1] if value.startswith("(") and value.endswith(")") else value)
    return found


def listingFormats(commented: bool = False) -> set[tuple[FormatItem, ...]]:
    found = set()
    for path in listingRoot.rglob("*.FOR"):
        for _number, _label, text in statements(path, commented):
            for spec in formatsIn(text):
                found.add(parseFormat(spec))
    return found


printed = listingFormats()
commentedOut = listingFormats(commented=True)
engineFormats = {
    name: value
    for name, value in vars(thesisScreens).items()
    if isinstance(value, str) and not name.startswith("_") and name != "pressEnter"
}


def testTheListingsYieldTheirFormats() -> None:
    assert len(printed) == 96  # distinct formats in the 66 listings
    assert parseFormat("1X,'REG.',I3,'=',E16.8") in printed


@pytest.mark.parametrize("name", sorted(engineFormats))
def testEngineFormatIsInTheListings(name: str) -> None:
    items = parseFormat(engineFormats[name])
    if name == "unknownsRadius":  # INCONNUS's block for the constant radius is commented out
        assert items in commentedOut
    else:
        assert items in printed


def testEcrzeta41KeepsTwoStrings() -> None:
    """'Les valeurs des ' ends one line and 'inconnues ...' starts the next: no apostrophe."""
    texts = [i.text for i in parseFormat(thesisScreens.radiusResultsCompliance) if i.kind == "TEXT"]
    assert "Les valeurs des " in texts and any(t.startswith("inconnues") for t in texts)
