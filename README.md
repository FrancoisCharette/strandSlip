# Strand Slip

The Fortran programs of the master's project on strands (wires wound on a core) at Université
Laval for Hydro-Québec / IREQ, revived as one PySide6 desktop app:

- the seven programs of 1990 (*Rigidité transversale d'un toron*, report SM-90-03), which
  compute the bending stiffness of a strand whose wires stick to or slip on the core;
- the six programs of the 1992 thesis, which compute the energy a wire dissipates by slipping
  and its relative displacement, with Hardy's model, continuity of deformation, and compliance.

Both kinds work for a sinusoidal deflection or a constant radius of curvature. The tabs follow
the thesis (*Analysis of the Damping Characteristics of a Stranded Cable under Vibration*,
Université Laval, 1992): **Strand** (chapters 1 and 5), **No Slip** (sections 1.2 and 2.2.1),
**Constant Radius of Curvature** and **Sinusoidal Deflection** (chapters 2 to 4 and 6), and last
**Bending Stiffness (1990 Report)**, the work that came before it.

| 1990 program | What it did | Where it lives now |
|---|---|---|
| `ENTRE.FOR` | Asked 15 questions, wrote `ENTRE.DAT` | **Strand** tab, which also draws the strand (the span between two posts, and its section) and gives the thesis's ρc, Ac, λ/p and γ1 |
| `SINUS.FOR` | Strand stiffness, sinusoidal deflection | **Bending Stiffness (1990 Report)** tab |
| `BSINUS.FOR` | Same equations, read as a cable of strands | **Bending Stiffness (1990 Report)** tab |
| `NSINUS.FOR` | BSINUS with a 10× finer slip search and a slip-zone listing | **Bending Stiffness (1990 Report)** tab |
| `RAYON.FOR` | Strand stiffness, constant radius of curvature | **Bending Stiffness (1990 Report)** tab |
| `FRICTION.FOR` | Friction coefficient each wire needs to stay stuck (eq. 19; thesis §2.2.1) | **No Slip** tab |
| `DEPLACE.FOR` | Core surface displacement along each contact helix (eq. 23; thesis §1.2) | **No Slip** tab |

| 1992 program | Model | Where it lives now |
|---|---|---|
| `HARDRHOB.FOR` | Hardy's model, constant radius of curvature | **Constant Radius of Curvature** tab |
| `CONTRHOB.FOR` | Continuity of deformation, constant radius | **Constant Radius of Curvature** tab |
| `ZETARHOB.FOR` | Compliance (micro- and macro-slip), constant radius | **Constant Radius of Curvature** tab |
| `HARDSIN.FOR` | Hardy's model, sinusoid | **Sinusoidal Deflection** tab |
| `CONTSIN.FOR` | Continuity of deformation, sinusoid | **Sinusoidal Deflection** tab |
| `ZETASIN.FOR` | Compliance, sinusoid | **Sinusoidal Deflection** tab |

Each tab runs its program off the interface thread and shows a plot, the result table, the
summary file (`DONSIN.DAT`...) and the screen output. **Export Legacy Files** writes the same
files the program wrote, record for record (`RESSIN.DAT`, `DONSIN.DAT`, `ENERGY.DAT`,
`INCONNUS.DAT`, ... with DOS line endings), plus the screen output as `<PROGRAM>.OUT`. The 1992
programs were interactive: their tabs take the keyboard answers as a form, and when a program
asks for something the form did not give (an approximation for Newton's method, typically), the
run stops there and shows the question.

The 1990 sources and DOS executables are kept unchanged in [`legacy/programmes/`](legacy/programmes/).
The 1992 sources exist only as listings printed in the program manual; they were recovered from
the WordPerfect file into [`legacy/manuel1992/`](legacy/manuel1992/), one folder per program as
on the 1992 diskettes.

## How faithful is it

- **Against the 1991 record.** Progress report no. 2 (February 1991) printed SINUS.FOR's results
  at X = 2.5 m for the 22-wire aluminium strand: stiffness 1671.24, MY 0.1696, MZ 26.391,
  FY 3.358. The port prints the same digits (`testTheRowPrintedInProgressReportTwo`).
- **Against the source.** `tests/legacyReference/literalPrograms.py` transcribes each program line
  by line (scalar math, GOTO loops, Fortran names). The application's vectorized engine agrees
  with it **bit for bit** on every case tested, slip-zone bounds included.
- **Quirks kept on purpose**, so old results reproduce: Gamma rounded to single precision
  (`GAM` falls outside `IMPLICIT DOUBLE PRECISION (A-F),(P-X)`), angles and X accumulated by
  repeated addition, sums taken in wire order, the `IF(X.EQ.O)` skip of X = 0 (letter O, an
  uninitialised variable), each program's own loop-end rule, and Fortran field formatting down
  to `-.0087` and `******`. See [`docs/legacyPort.md`](docs/legacyPort.md).
- **The 1992 programs against the thesis.** Tables 6.1 and 6.2 of the thesis (bounds of the
  macro-slip region, energies dissipated) and the approximations the program manual quotes come
  out of the port digit for digit, apart from two misprints and two roundings in the thesis that
  the tests point out, and one sum that differs by 0.14 %. A line-by-line transcription of the 66 listings
  (`tests/legacyReference/literalThesis*.py`) prints the same screen and writes the same files as
  the app, record for record. REAL\*4 constants, the integer `0001` in `IF(XINF.LT.0001)`, Newton's
  exits and the order of every operation are kept.

## One-time setup

```powershell
cd W:\projects\26strandSlip
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Daily workflow

```powershell
cd W:\projects\26strandSlip
.\.venv\Scripts\Activate.ps1
strand-slip
```

Or `python -m strandSlip.main`, or double-click **`runApp.cmd`**. The user manual is under
**Help > User Manual** (F1): [`docs/manual/README.md`](docs/manual/README.md) as GitHub shows
it in this repository, or the copy in the checkout when GitHub does not answer within 3 s.
**Help > Legacy Fortran Sources** opens [`legacy/`](legacy/) the same way.

## Tests and lint

```powershell
pytest
ruff check src tests
```

## App icon

The icon is the section of a strand, a steel core ringed by aluminium wires, with one wire in
coral, the one that slips, and an arrow beside it. It is drawn in code, like Wager Book's:
`tools/makeIcons.py` paints it separately at each size from 16 to 256 px, with fewer wires as it
shrinks, and packs them into `src/strandSlip/resources/strandSlip.ico`. Startup sets it on every
window and gives the app its own Windows taskbar ID, so a window started by `pythonw.exe` is not
filed under Python. To redraw it after changing the design:

```powershell
python tools/makeIcons.py
```

## Structure

| Layer | Folder | Purpose |
|-------|--------|---------|
| Entry | `src/strandSlip/main.py` | Start `QApplication`, show main window |
| Config | `src/strandSlip/appConfig.py` | Paths, defaults, app metadata |
| UI | `src/strandSlip/ui/` | `mainWindow.py`; `views/` (the Strand tab with its Numerical Entries and Schematics pages, one reusable analysis tab for the No Slip and Bending Stiffness tabs, one thesis tab per deflection); `plotting/` (matplotlib charts); `widgets/` (among them the program tabs and the tabs inside a page, which mark the open tab as Wager Book and The One Assets do: `tabStyling.py`) |
| Services | `src/strandSlip/services/` | The port itself, no Qt widgets |
| Models | `src/strandSlip/models/` | `StrandInput` (ENTRE.DAT), `ThesisInput` (the 1992 keyboard answers), the program catalogues, result types, examples |
| Tools | `tools/` | `recoverManuel1992.py`: the 1992 listings from the WordPerfect manual |

The services, in the order a run uses them:

| Service | Role |
|---|---|
| `entreFileService` | Read and write `ENTRE.DAT` exactly as the programs did |
| `inputValidation` | Refuse inputs the originals crashed or looped on, with a reason |
| `strandModel` | Equations 3 to 41: constants, sinusoidal and constant-curvature models |
| `wireStateSolver` | Stick or slip for every wire at every X, slip-zone bounds by p/1000 steps |
| `stiffnessService`, `frictionService`, `displacementService` | The six analysis programs |
| `fortranFormat`, `legacyOutputService` | Fortran edit descriptors and the legacy files |
| `analysisRunner`, `analysisWorker` | Run a program off the interface thread |
| `strandGeometry` | What the Strand tab's schematics draw: the span between two posts, and the section |
| `thesisParameters` | The thesis's ρ/ρc, λ/p, A/Ac and γ1 from the strand (chapter 5), for the Strand tab and the thesis tabs |

And for the 1992 programs:

| Service | Role |
|---|---|
| `thesisNumerics` | The Numerical Recipes routines as printed: Romberg, secant, false position, golden section, LU |
| `thesisDeflections` | Annex A's equations for the constant radius and the sinusoid |
| `macroSlipModels` | Hardy's model and continuity of deformation (NEWT) |
| `complianceSystem`, `complianceModel` | The compliance model: curve, residuals, Jacobian, Newton, energies |
| `thesisProfiles` | Displacement, strain and friction ratio along the half lay length |
| `thesisPrograms`, `thesisSinusoidPrograms` | The six programs, step for step |
| `thesisSession`, `thesisScreens` | Keyboard, screen and files; every FORMAT the programs printed |
| `thesisRunner`, `thesisTables` | Run, refuse impossible inputs, export; tables and summary |

See `AGENTS.md` for architecture and naming conventions.

---
*Created from the Qt App Template.*
