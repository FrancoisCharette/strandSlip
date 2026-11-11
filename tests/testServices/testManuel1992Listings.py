"""The 1992 sources recovered from the manual's annex C (legacy/manuel1992/).

Each diskette directory holds the files the manual lists for it; each must
then be a whole program: everything it CALLs, declares EXTERNAL or uses as a
function is defined there, and everything there is used.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path

import pytest

from listingReader import listingRoot as root
from listingReader import statements
from masterRebuild import appConfig

directories = {
    "RAYON/HARDY": "HARDRHOB",
    "RAYON/CNTDEF": "CONTRHOB",
    "RAYON/COMPLAIS": "ZETARHOB",
    "SINUS/HARDY": "HARDSIN",
    "SINUS/CNTDEF": "CONTSIN",
    "SINUS/COMPLAIS": "ZETASIN",
}
sizes = {"RAYON/HARDY": 15, "RAYON/CNTDEF": 22, "RAYON/COMPLAIS": 30}
sizes |= {"SINUS/HARDY": 17, "SINUS/CNTDEF": 22, "SINUS/COMPLAIS": 31}
deflectionSpecific = {"APPBRN", "DEPAME", "DEPFIL", "ELGAME", "ELGFIL", "FRCAME", "FRCFIL"}
deflectionSpecific |= {"FRICTION", "VMIN"}


def sources(directory: str) -> dict[str, Path]:
    return {path.stem: path for path in (root / directory).glob("*.FOR")}


def code(path: Path) -> list[str]:
    """Each statement without its character constants and its ! comment."""
    found = []
    for _number, _label, text in statements(path):
        bare = re.sub(r"'(?:[^']|'')*'", "''", text)
        found.append(bare.split("!")[0].strip())
    return found


def definitions() -> dict[str, str]:
    """Every PROGRAM, SUBROUTINE and FUNCTION name, with its kind."""
    kinds = {}
    for path in root.rglob("*.FOR"):
        text = " ".join(code(path))
        match = re.search(r"\b(PROGRAM|SUBROUTINE|FUNCTION)\s+([A-Z][A-Z0-9]*)", text)
        kinds[match.group(2)] = match.group(1)
    return kinds


@pytest.mark.parametrize("directory", sorted(directories))
def testEachDirectoryHoldsWhatTheManualLists(directory: str) -> None:
    assert len(sources(directory)) == sizes[directory]
    assert directories[directory] in sources(directory)


def testFilesAreDosTextWithoutTabsOrTrailingBlanks() -> None:
    for path in root.rglob("*.FOR"):
        raw = path.read_bytes()
        assert raw.endswith(b"\r\n") and b"\t" not in raw
        assert raw.count(b"\n") == raw.count(b"\r\n")
        text = raw.decode("utf-8")
        assert all(line == line.rstrip() for line in text.splitlines()), path


def testSharedRoutinesAreOneListing() -> None:
    """A name in two directories is the same text, except the deflection's own functions."""
    texts = defaultdict(set)
    for directory in directories:
        for name, path in sources(directory).items():
            group = directory.split("/")[0] if name in deflectionSpecific else "shared"
            texts[(group, name)].add(path.read_bytes())
    assert all(len(variants) == 1 for variants in texts.values())
    assert len(texts) == 66  # the manual's 66 listings


@pytest.mark.parametrize("directory", sorted(directories))
def testEachDirectoryIsAWholeProgram(directory: str) -> None:
    kinds = definitions()
    functions = {name for name, kind in kinds.items() if kind == "FUNCTION"}
    files = sources(directory)
    used = defaultdict(set)
    for name, path in files.items():
        for statement in code(path):
            used[name] |= set(re.findall(r"\bCALL\s+([A-Z][A-Z0-9]*)", statement))
            if statement.startswith("EXTERNAL"):
                used[name] |= {item.strip() for item in statement[8:].split(",")}
            called = re.findall(r"\b([A-Z][A-Z0-9]*)\s*\(", statement)
            used[name] |= {f for f in called if f in functions}
        used[name].discard(name)
    missing = {name: sorted(n for n in names if n not in files) for name, names in used.items()}
    assert not {k: v for k, v in missing.items() if v}
    reached, frontier = set(), [directories[directory]]
    while frontier:
        name = frontier.pop()
        if name not in reached:
            reached.add(name)
            frontier.extend(used[name])
    assert reached == set(files)


def testPrintingDefectsAreKeptAsPrinted() -> None:
    """Two lines no compiler took as printed: the diskettes' files differed by a blank."""
    zetarhob = (root / "RAYON/COMPLAIS/ZETARHOB.FOR").read_text(encoding="utf-8").splitlines()
    assert len(zetarhob[85]) == 73 and zetarhob[85].endswith("*PI)")  # ')' in column 73
    inconnus = (root / "SINUS/COMPLAIS/INCONNUS.FOR").read_text(encoding="utf-8").splitlines()
    assert inconnus[33].startswith("  10 FORMAT(")  # 'F' in column 6


manual = Path(
    os.environ.get(
        "MANUEL_MAN",
        Path.home() / "Proton Drive/charette.francois/My files/publications/Selected Work"
        "/Master/Manuel/MANUEL.MAN",
    )
)


@pytest.mark.skipif(not manual.exists(), reason="the WordPerfect manual is not on this computer")
def testRecoveryToolReproducesTheFiles() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "recoverManuel1992", appConfig.projectRoot / "tools" / "recoverManuel1992.py"
    )
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    texts = tool.recoverListings(tool.readPages(manual))
    for directory in directories:
        group = directory.split("/")[0]
        for name, path in sources(directory).items():
            expected = texts[group].get(name) or texts["common"][name]
            assert path.read_bytes() == expected.encode("utf-8"), path
