# Master Rebuild

The seven Fortran programs written in 1990 for the master's project *Rigidité transversale
d'un toron* (Université Laval, Hydro-Québec / IREQ contract, report SM-90-03), revived as one
PySide6 desktop app. They compute the bending stiffness of a strand (wires wound on a core)
whose wires stick to or slip on the core, for a sinusoidal deflection or a constant radius of
curvature.

| 1990 program | What it did | Where it lives now |
|---|---|---|
| `ENTRE.FOR` | Asked 15 questions, wrote `ENTRE.DAT` | **Input** tab |
| `SINUS.FOR` | Strand stiffness, sinusoidal deflection | **Sinusoid** tab |
| `BSINUS.FOR` | Same equations, read as a cable of strands | **Sinusoid** tab |
| `NSINUS.FOR` | BSINUS with a 10× finer slip search and a slip-zone listing | **Sinusoid** tab |
| `RAYON.FOR` | Strand stiffness, constant radius of curvature | **Constant Curvature** tab |
| `FRICTION.FOR` | Friction coefficient each wire needs to stay stuck (eq. 19) | **Friction** tab |
| `DEPLACE.FOR` | Core surface displacement along each contact helix (eq. 23) | **Displacement** tab |

Each tab runs its program off the interface thread and shows a plot, the result table, the
summary file (`DONSIN.DAT`...) and the screen output. **Export Legacy Files** writes the same
files the 1990 program wrote, record for record (`RESSIN.DAT`, `DONSIN.DAT`, ... with DOS line
endings), plus `ENTRE.DAT` and the screen output as `<PROGRAM>.OUT`.

The original sources and DOS executables are kept unchanged in [`legacy/programmes/`](legacy/programmes/).

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
| UI | `src/masterRebuild/ui/` | `mainWindow.py`; `views/` (Input tab, one reusable analysis tab); `plotting/` (matplotlib charts); `widgets/` |
| Services | `src/masterRebuild/services/` | The port itself, no Qt widgets |
| Models | `src/masterRebuild/models/` | `StrandInput` (ENTRE.DAT), the program catalogue, result types, examples |

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

See `AGENTS.md` for architecture and naming conventions.

---
*Created from the Qt App Template.*
