# Master Rebuild

The Fortran programs of the master's project on strands (wires wound on a core) at Université
Laval for Hydro-Québec / IREQ, revived as one PySide6 desktop app:

- the seven programs of 1990 (*Rigidité transversale d'un toron*, report SM-90-03), which
  compute the bending stiffness of a strand whose wires stick to or slip on the core;
- the six programs of the 1992 thesis, which compute the energy a wire dissipates by slipping
  and its relative displacement, with Hardy's model, continuity of deformation, and compliance.

Both kinds work for a sinusoidal deflection or a constant radius of curvature.

| 1990 program | What it did | Where it lives now |
|---|---|---|
| `ENTRE.FOR` | Asked 15 questions, wrote `ENTRE.DAT` | **Input** tab |
| `SINUS.FOR` | Strand stiffness, sinusoidal deflection | **Sinusoid** tab |
| `BSINUS.FOR` | Same equations, read as a cable of strands | **Sinusoid** tab |
| `NSINUS.FOR` | BSINUS with a 10× finer slip search and a slip-zone listing | **Sinusoid** tab |
| `RAYON.FOR` | Strand stiffness, constant radius of curvature | **Constant Curvature** tab |
| `FRICTION.FOR` | Friction coefficient each wire needs to stay stuck (eq. 19) | **Friction** tab |
| `DEPLACE.FOR` | Core surface displacement along each contact helix (eq. 23) | **Displacement** tab |

| 1992 program | Model | Where it lives now |
|---|---|---|
| `HARDRHOB.FOR` | Hardy's model, constant radius of curvature | **Thesis · Constant Curvature** tab |
| `CONTRHOB.FOR` | Continuity of deformation, constant radius | **Thesis · Constant Curvature** tab |
| `ZETARHOB.FOR` | Compliance (micro- and macro-slip), constant radius | **Thesis · Constant Curvature** tab |
| `HARDSIN.FOR` | Hardy's model, sinusoid | **Thesis · Sinusoid** tab |
| `CONTSIN.FOR` | Continuity of deformation, sinusoid | **Thesis · Sinusoid** tab |
| `ZETASIN.FOR` | Compliance, sinusoid | **Thesis · Sinusoid** tab |

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
cd W:\projects\26masterRebuild
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Daily workflow

```powershell
cd W:\projects\26masterRebuild
.\.venv\Scripts\Activate.ps1
master-rebuild
```

Or `python -m masterRebuild.main`, or double-click **`runApp.cmd`**. The user manual is under
**Help > User Manual** (F1), from [`docs/manual/README.md`](docs/manual/README.md).

## Tests and lint

```powershell
pytest
ruff check src tests
```

## Structure

| Layer | Folder | Purpose |
|-------|--------|---------|
| Entry | `src/masterRebuild/main.py` | Start `QApplication`, show main window |
| Config | `src/masterRebuild/appConfig.py` | Paths, defaults, app metadata |
| UI | `src/masterRebuild/ui/` | `mainWindow.py`; `views/` (Input tab, one reusable analysis tab, one thesis tab per deflection); `plotting/` (matplotlib charts); `widgets/` |
| Services | `src/masterRebuild/services/` | The port itself, no Qt widgets |
| Models | `src/masterRebuild/models/` | `StrandInput` (ENTRE.DAT), `ThesisInput` (the 1992 keyboard answers), the program catalogues, result types, examples |
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
