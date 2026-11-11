# The 1992 thesis programs, recovered from the program manual

The six Fortran programs of the 1992 master's thesis survive only as printed listings: annex C
of the program manual, `Manuel/MANUEL.MAN` (WordPerfect 5.1 for DOS, saved 14 April 1992, 133
pages), prints all 66 source files. The diskettes it came with (3.5" and 5.25", with the `.EXE`
files and each program's `MAIN.LNK` and `MAKEFILE`) are lost. The files here are the listings'
text, recovered on 2026-11-11 by [`tools/recoverManuel1992.py`](../../tools/recoverManuel1992.py)
from the WordPerfect file itself.

## Layout: the diskettes' directories

The manual lists, for each program, the files its diskette directory held (chapters 1 and 2);
each directory below holds exactly those, so it is a whole program (the tests check that
everything called is there and everything there is called). A routine several programs use is
the same printed listing copied into each directory, as on the diskettes. The deflection's own
functions (`APPBRN`, `DEPAME`, `DEPFIL`, `ELGAME`, `ELGFIL`, `FRCAME`, `FRCFIL`, `FRICTION`) have
one listing for the constant radius (section C.4) and one for the sinusoid (C.5).

| Directory | Program | Model | Files | Main listing |
|---|---|---|---|---|
| `RAYON/HARDY` | `HARDRHOB` | Hardy, constant radius of curvature | 15 | page 41 |
| `RAYON/CNTDEF` | `CONTRHOB` | Continuity of deformation, constant radius | 22 | page 38 |
| `RAYON/COMPLAIS` | `ZETARHOB` | Compliance, constant radius | 30 | page 44 |
| `SINUS/HARDY` | `HARDSIN` | Hardy, sinusoid | 17 | page 42 |
| `SINUS/CNTDEF` | `CONTSIN` | Continuity of deformation, sinusoid | 22 | page 39 |
| `SINUS/COMPLAIS` | `ZETASIN` | Compliance, sinusoid | 31 | page 46 |

The page of every listing is in `tools/recoverManuel1992.py` (`commonPages`, `deflectionPages`).
The programs were compiled with Microsoft FORTRAN 5.0 on a PC XT compatible (manual, p. 2).

## How the text was read

- **Characters** are the document's: accented letters from WordPerfect's character set 1, the
  one Greek letter (δ, in a comment of `COMP.FOR`) from set 8. The files are UTF-8 with DOS line
  endings; the diskettes held a DOS code page (437, 850 and 863 agree on every letter used).
- **Tabs.** WordPerfect stores a tab as the absolute position of the next character. The listing
  font prints 12 characters per inch with the left margin at 1.3 inch, so a tab to 2160/1200 inch
  is column 7; each tab is written as the blanks that reach its column. Every one lands on a
  character cell and none moves backwards.
- **Trailing blanks** are dropped (they do not print, and the compiler pads lines to column 72),
  as are the page headings `Section C.1` to `C.5`. One soft return on page 71, where trailing
  tabs overfilled a line, was WordPerfect's word wrap and is not a line break.
- **Checked against the Word conversion** (`MANUEL.docx`): every listing line has the same text,
  blanks aside. The conversion's known defects (Greek letters, overstrikes, fonts) do not reach
  the listings; its hyphens are `noBreakHyphen` elements.

## Two lines the compiler cannot have seen as printed

Both programs ran in 1992, so the diskette files differed from the page by a blank or a tab:

- `RAYON/COMPLAIS/ZETARHOB.FOR`, line 86: with the tab printed as twelve blanks, the closing
  parenthesis falls in column 73, which a fixed-form compiler ignores. The file most likely had
  a tab there.
- `INCONNUS.FOR`, line 34: `  10 FORMAT(` prints the `F` in column 6, the continuation column.
  One blank was lost in printing.

They are kept as printed. The port reads them as the program evidently compiled them.

## Blocks switched by comments

Several shared routines carry two `COMMON/CSTF/` lines, one commented out: the sinusoid's
(`PI,THETA,PP,...,WLBAR,ABAR`) and the constant radius' (`PI,THETA,RHOB`). The printed copies are
not all set the same way (`VECB` and `JACOB` for the constant radius, `SORTIE`, `DEPH`, `DR2H`,
`JACO`, `DISPENRG`, `DMICRO`, `SORTZETA` and `INCONNUS` for the sinusoid), which only matters in
`INCONNUS`: its parameter record is the sinusoid's (`ABAR`, `WLBAR`, `GAM1`, `THETAi`), with the
constant radius' (`GAM1`, `RHOB`, `THETAi`) commented out below it. The port writes the latter
for ZETARHOB; every other routine reads only `PI` from the block either way.

The Python port is in `src/masterRebuild/services/`; [`docs/legacyPort.md`](../../docs/legacyPort.md)
explains what was kept, what could not be, and how it was checked.
