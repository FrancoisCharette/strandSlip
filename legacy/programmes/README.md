# The 1990 originals

Copied unchanged on 2026-11-10 from
`Proton Drive\...\publications\Selected Work\Master\Programmes`. File dates are the originals'
(June–July 1990). `.gitattributes` keeps them byte for byte (CR LF line endings, binaries).

| Source | Executable | Dated | Writes |
|---|---|---|---|
| `ENTRE.FOR` | `ENTRE.EXE` | 1990-07-15 | `ENTRE.DAT` |
| `SINUS.FOR` | `SINUS.EXE` | 1990-07-18 | `RESSIN.DAT`, `DONSIN.DAT` |
| `BSINUS.FOR` | `BSINUS.EXE` | 1990-06-12 | `RESFIN.DAT`, `DONNE1.DAT` |
| `NSINUS.FOR` | `NSINUS.EXE` | 1990-06-21 | `RESFIN.DAT`, `DONNE1.DAT` |
| `RAYON.FOR` | `RAYON.EXE` | 1990-07-19 | `RESRAY.DAT`, `DONRAY.DAT` |
| `FRICTION.FOR` | `FRICTION.EXE` | 1990-06-21 | `F_RESFIN.DAT`, `F_DONNE1.DAT` |
| `DEPLACE.FOR` | `DEPLACE.EXE` | 1990-06-21 | `D_RESFIN.DAT` |

The executables are 16-bit DOS programs (Microsoft FORTRAN, judging by the `$DEBUG`,
`$NOFLOATCALLS` and `$STORAGE:2` metacommands). 64-bit Windows cannot run them; DOSBox can.
Each reads `ENTRE.DAT` from the current folder and stops if its output files already exist.

The Python port is in `src/masterRebuild/services/`; [`docs/legacyPort.md`](../../docs/legacyPort.md)
maps every equation and quirk to its new home.
