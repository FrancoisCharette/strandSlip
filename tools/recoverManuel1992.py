"""Recover the 1992 Fortran listings from annex C of the program manual.

The manual, `Manuel/MANUEL.MAN`, is a WordPerfect 5.1 (DOS) document. Its
annex C prints the 66 source files of the six thesis programs. This script
reads the WordPerfect file directly (no conversion) and writes each listing to
`legacy/manuel1992/<RAYON|SINUS>/<HARDY|CNTDEF|COMPLAIS>/<NAME>.FOR`, the
directory tree of the 1992 diskettes, one copy per directory that held it.

    python tools/recoverManuel1992.py "<...>/Master/Manuel/MANUEL.MAN"

How the text is read:
- Characters are the document's own; accented letters are WordPerfect
  character set 1 (multinational), Greek set 8.
- A tab is a WordPerfect code holding the absolute position, in 1/1200 inch,
  where the next character printed. The listing font is 12 characters per
  inch (100 units) with the left margin at 1560 units, so 2160 is column 7.
  Tabs are written as the spaces that reach that column.
- One soft return (page 71, after trailing tabs that overfilled the line) is
  WordPerfect's word wrap, not a line break of the source.
- Trailing blanks are dropped: they do not print, and a fixed-form compiler
  pads every line to column 72 anyway.
"""

from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

leftMargin = 1560
pitch = 100
firstListingPage = 38
lastListingPage = 133

fixedSizes = {
    0xC0: 4, 0xC1: 9, 0xC2: 11, 0xC3: 3, 0xC4: 3, 0xC5: 5, 0xC6: 6, 0xC7: 7,
    0xC8: 4, 0xC9: 5, 0xCA: 6, 0xCB: 7, 0xCC: 8, 0xCD: 9, 0xCE: 10, 0xCF: 11,
}  # fmt: skip
multinational = dict(zip(range(26, 74), "ÁáÂâÄäÀàÅåÆæÇçÉéÊêËëÈèÍíÎîÏïÌìÑñÓóÔôÖöÒòÚúÛûÜüÙù"))
greek = {7: "γ", 9: "δ", 17: "θ", 35: "ρ"}

# Page of each listing, from the file tables in chapters 1 and 2 of the manual.
commonPages = {
    "CONTRHOB": 38, "CONTSIN": 39, "HARDRHOB": 41, "HARDSIN": 42, "ZETARHOB": 44,
    "ZETASIN": 46, "APPROX": 49, "APPSIN": 51, "COMP": 53, "DISPENRG": 54, "DLUBKSB": 57,
    "DLUDCMP": 58, "ECRCONT": 60, "ECRHARD": 61, "ECRZETA": 62, "ECSNCONT": 63,
    "ECSNHARD": 65, "ECSNZETA": 67, "ENSNCONT": 69, "ENSNHARD": 70, "ENSNZETA": 71,
    "ENTCONT": 73, "ENTHARD": 74, "ENTZETA": 75, "INCONNUS": 76, "JACO": 78, "JACOB": 79,
    "NEWT": 86, "NEWTON": 88, "PBCONV": 91, "POLINT": 92, "QROMB": 93, "SORTIE": 94,
    "SORTZETA": 95, "TRAPZD": 99, "UNRES": 100, "VCB": 101, "VECB": 102, "DEPH": 106,
    "DMACRO": 107, "DMICRO": 108, "DR2H": 109, "F1D": 110, "F1E": 111, "F2D": 112,
    "F2E": 113, "GOLDEN": 114, "RTFLSP": 115, "RTSEC": 116,
}  # fmt: skip
deflectionPages = {  # sections C.4 (constant radius) and C.5 (sinusoid)
    "RAYON": {"APPBRN": 117, "DEPAME": 118, "DEPFIL": 119, "ELGAME": 120, "ELGFIL": 121,
              "FRCAME": 122, "FRCFIL": 123, "FRICTION": 124},
    "SINUS": {"APPBRN": 125, "DEPAME": 126, "DEPFIL": 127, "ELGAME": 128, "ELGFIL": 129,
              "FRCAME": 130, "FRCFIL": 131, "FRICTION": 132, "VMIN": 133},
}  # fmt: skip

# The files of each diskette directory, as the manual lists them.
directories = {
    "RAYON/HARDY": "DEPAME DEPH DMACRO DR2H ECRHARD ELGAME ENTHARD FRCAME FRICTION HARDRHOB "
    "POLINT QROMB RTSEC SORTIE TRAPZD",
    "RAYON/CNTDEF": "APPBRN CONTRHOB DEPAME DEPH DLUBKSB DLUDCMP DMACRO DR2H ECRCONT ELGAME "
    "ENTCONT FRCAME FRICTION JACO NEWT PBCONV POLINT QROMB RTFLSP SORTIE TRAPZD VCB",
    "RAYON/COMPLAIS": "APPROX COMP DEPAME DEPFIL DEPH DISPENRG DLUBKSB DLUDCMP DMACRO DMICRO "
    "DR2H ECRZETA ELGAME ELGFIL ENTZETA F1D F1E F2D F2E FRCAME FRCFIL INCONNUS JACOB NEWTON "
    "POLINT QROMB SORTZETA TRAPZD VECB ZETARHOB",
    "SINUS/HARDY": "DEPAME DEPH DMACRO DR2H ECSNHARD ELGAME ENSNHARD FRCAME FRICTION GOLDEN "
    "HARDSIN POLINT QROMB RTFLSP SORTIE TRAPZD VMIN",
    "SINUS/CNTDEF": "APPBRN CONTSIN DEPAME DEPH DLUBKSB DLUDCMP DMACRO DR2H ECSNCONT ELGAME "
    "ENSNCONT FRCAME GOLDEN JACO NEWT POLINT QROMB RTFLSP SORTIE TRAPZD VCB VMIN",
    "SINUS/COMPLAIS": "APPSIN COMP DEPAME DEPFIL DEPH DISPENRG DLUBKSB DLUDCMP DMACRO DMICRO "
    "DR2H ECSNZETA ELGAME ELGFIL ENSNZETA F1D F1E F2D F2E FRCAME FRCFIL INCONNUS JACOB NEWTON "
    "POLINT QROMB SORTZETA TRAPZD UNRES VECB ZETASIN",
}


def readPages(path: Path) -> dict[int, list[str]]:
    """Every page of the document as lines of text."""
    data = path.read_bytes()
    if data[:4] != b"\xffWPC":
        raise ValueError(f"{path} is not a WordPerfect document")
    index = struct.unpack_from("<I", data, 4)[0]
    page, current = 1, []
    pages: dict[int, list[str]] = {1: []}

    def endLine() -> None:
        pages[page].append("".join(current))
        current.clear()

    while index < len(data):
        code = data[index]
        if 0x20 <= code <= 0x7E:
            current.append(chr(code))
            index += 1
        elif code == 0x0A:  # hard return
            endLine()
            index += 1
        elif code == 0x0D:  # soft return: word wrap
            if page < firstListingPage:
                current.append(" ")
                endLine()
            index += 1
        elif code in (0x0B, 0x0C, 0x8C):  # soft page, hard page, hard return + soft page
            endLine()
            page += 1
            pages[page] = []
            index += 1
        elif code < 0xC0:  # other single-byte codes print nothing here
            index += 1
        elif code <= 0xCF:
            size = fixedSizes[code]
            if code == 0xC0:  # extended character: C0 char set C0
                table = {1: multinational, 8: greek}.get(data[index + 2], {})
                current.append(table.get(data[index + 1], "?"))
            elif code == 0xC1:  # tab to an absolute position
                column = (struct.unpack_from("<H", data, index + 4)[0] - leftMargin) // pitch
                current.append(" " * max(0, column - len("".join(current))))
            index += size
        else:  # variable-length group: code, subcode, length, data, length, subcode, code
            index += 4 + struct.unpack_from("<H", data, index + 2)[0]
    endLine()
    return pages


def listingText(pages: dict[int, list[str]], first: int, last: int) -> str:
    lines = [line.rstrip() for number in range(first, last + 1) for line in pages[number]]
    while lines and (not lines[0] or re.fullmatch(r"Section C\.\d", lines[0])):
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\r\n".join(lines) + "\r\n"


def recoverListings(pages: dict[int, list[str]]) -> dict[str, dict[str, str]]:
    """Listing text by group ('common', 'RAYON', 'SINUS') and file name."""
    starts = [(page, "common", name) for name, page in commonPages.items()]
    for group, names in deflectionPages.items():
        starts += [(page, group, name) for name, page in names.items()]
    starts.sort()
    texts: dict[str, dict[str, str]] = {"common": {}, "RAYON": {}, "SINUS": {}}
    for position, (page, group, name) in enumerate(starts):
        last = starts[position + 1][0] - 1 if position + 1 < len(starts) else lastListingPage
        texts[group][name] = listingText(pages, page, last)
    return texts


def main(manualPath: str) -> None:
    texts = recoverListings(readPages(Path(manualPath)))
    root = Path(__file__).resolve().parents[1] / "legacy" / "manuel1992"
    for directory, names in directories.items():
        deflection = directory.split("/")[0]
        target = root / directory
        target.mkdir(parents=True, exist_ok=True)
        for name in names.split():
            text = texts[deflection].get(name) or texts["common"][name]
            (target / f"{name}.FOR").write_bytes(text.encode("utf-8"))
    count = sum(len(group) for group in texts.values())
    print(f"{count} listings written under {root}")


if __name__ == "__main__":
    main(sys.argv[1])
