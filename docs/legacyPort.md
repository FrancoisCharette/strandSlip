# Porting notes: the 1990 Fortran programs

How `legacy/programmes/*.FOR` became `src/masterRebuild/services/`, what was kept on purpose,
what was not, and how the port was checked. For maintainers; users want
[`manual/README.md`](manual/README.md).

## The programs

All seven were written between June and July 1990 for report SM-90-03, *Rigidité transversale
d'un toron* (rapport #1, Université Laval for Hydro-Québec / IREQ). They carry the metacommands
`$DEBUG`, `$NOFLOATCALLS` and `$STORAGE:2` of Microsoft FORTRAN for DOS: 16-bit executables,
8087 code inline, two-byte default integers. ENTRE writes `ENTRE.DAT`; the six others read it
and write fixed file names, opened `STATUS='NEW'`.

| Slot | ENTRE label | SINUS, RAYON | BSINUS, NSINUS, FRICTION, DEPLACE | `StrandInput` |
|---|---|---|---|---|
| 1 | Longueur du toron | CL | CL | `strandLength` |
| 2 | Nombre de fil | NFIL | NFIL | `wireCount` |
| 3 | Angle d helice | ALPHA | ALPHA | `helixAngle` |
| 4 | Rayon d un fil | RF | RT | `wireRadius` |
| 5 | E des fils | EF | ET | `wireModulus` |
| 6 | Tension dans un fil | TI | TI | `wireTension` |
| 7 | Rayon de l ame | RA | RN | `coreRadius` |
| 8 | E de l ame | EA | EN | `coreModulus` (only ever printed) |
| 9 | Coefficient de Poisson | CPN | CPN | `corePoisson` |
| 10 | Coefficient de friction | CFL | CFL | `frictionLimit` |
| 11 | Longueur d onde | WL (RAYON: RIEN, unused) | WL | `wavelength` |
| 12 | Amplitude ou rayon de courbure | AMP (RAYON: RHO) | AMP | `amplitude` |
| 13 | Nombre de position | NPAS | NPAS | `positionCount` |
| 14 | Point de depart | XDEPART | XDEPART | `xStart` |
| 15 | Point d arret | XFINAL | XFINAL | `xEnd` |

SINUS and BSINUS are the same program under two readings of the inputs (wires on a core, or
strands on a core); NSINUS is BSINUS with `DX=PITCH/10000` instead of `/1000` and a
`WRITE(*,...)` per wire. One engine (`stiffnessService` + `wireStateSolver`) runs all three
and RAYON; only the deflection model differs (`strandModel.SinusoidalDeflection`,
`ConstantCurvatureDeflection`).

## Equations (numbers of report SM-90-03)

| Eq. | Quantity | Fortran | Code |
|---|---|---|---|
| 3 | f = (1 − ν tan²α) cos²α | `F` | `computeStrandConstants` |
| 12 | q = Ti sin²α / Ra | `Q` | `computeStrandConstants` |
| 13 | p = 2π Ra / tan α | `PITCH` | `computeStrandConstants` |
| 14 | ρc | `RHOC` | `ConstantCurvatureDeflection` |
| 10 | μ(X), constant curvature | `CST9*CA9` | `ConstantCurvatureDeflection.frictionDemand` |
| 15 | εs stuck, constant curvature | `EX` | `...stickElongation` |
| 17 | Da(X), constant curvature | `CST19*CA193` | `...coreDisplacement` |
| 19 | μ(X), sinusoid | `CST9*(CA9+CB9)` | `SinusoidalDeflection.frictionDemand` |
| 21 | Ac | `AMPC` | `SinusoidalDeflection` |
| 22 | εs stuck, sinusoid | `EX` | `...stickElongation` |
| 23 | Da(X), sinusoid | `CST19*(CA19-CB19)` | `...coreDisplacement` |
| 32–35 | εF in the slip zones X1..X2, X3..X4 | `EOG`, `EOD`, `EX` | `wireStateSolver._slipElongation` |
| 36–38 | Mz, My, Mx | `FMXZ`, `FMXY`, `TMX` | `stiffnessService._totals` |
| 40, 41 | EI | `RIG` | `...stiffness` |

Every expression keeps the source's operand order, and integer powers are products
(`X**3` is `X*X*X`), so each is the same IEEE computation as the listing.

## Kept on purpose

These change results, so they are reproduced, each with a test:

1. **GAM is REAL\*4.** `IMPLICIT DOUBLE PRECISION (A-F)` and `(P-X)` leave G single precision;
   Gamma is rounded to float32 when stored (`computeStrandConstants`).
2. **Accumulation.** `THETA(I)=THETA(I-1)+2*PI/NFIL` and `X=X+DXPAS` are repeated additions, not
   index × step. 0.1 added ten times is 0.9999999999999999, which decides whether a loop runs
   once more.
3. **Two loop-end rules.** SINUS, BSINUS, NSINUS and RAYON process X and then step while
   `X.LT.XFINAL`, so the first X at or past XFINAL is processed. FRICTION and DEPLACE step first
   and stop there. (`stiffnessPositions`, `scanPositions`.)
4. **The step is CL/NPAS**, the strand length over the number of positions, whatever the span.
5. **X = 0 is skipped** by `IF(X.EQ.O) GOTO 125`: the letter O, an undeclared REAL that the DOS
   runtime left at zero. The wires are still computed; the row is not written.
6. **Branch order.** `IF(CFX.LT.0)` first, then `.GE.CFLN` or `.LE.CFL` (`classifyDemand`), so
   even a NaN would take the original path (into the slip branch).
7. **Slip bounds by marching.** X4 = X4 + DX until CFX ≤ CFL, starting from X, never refined.
   The port steps all slipping wires in lockstep, each with its own repeated addition, so the
   bounds are the scalar loop's numbers.
8. **Sums in wire order.** `FXT=FXT+FX(I)` is a running sum (`np.cumsum`), not numpy's pairwise
   sum.
9. **DX in the summary** is printed even when no wire ever set it; it then reads 0
   (`StiffnessResult.searchStep`).
10. **Output formats** are the FORMAT statements copied verbatim (`legacyOutputService`), with
    the optional leading zero dropped when the field is full (`-.0087`), asterisks on overflow
    (`******`, which RESRAY.DAT really shows for FYT past −9.999), and three-digit exponents
    without the letter.
11. **ENTRE.DAT is read by column**: columns 2–15 under D14.8, blanks ignored, and without a
    decimal point the last eight digits are decimals ("10" reads 1.0E-7). The reader warns.

## Not reproduced

- **8087 80-bit intermediates.** Values stored to variables are doubles in both; expression
  temporaries were 80-bit in 1990. The last bit can differ; nothing printed does.
- **Runtime conventions the source does not fix**, taken from gfortran: leading zero printed
  when it fits, minus sign kept on a negative that rounds to zero, ties rounded away from zero.
  Only a run of the original executables (DOSBox) could settle them.
- **Carriage control on screen.** The `.OUT` file and Screen Output view drop each record's
  first character, as Fortran carriage control did on the console.
- **`STATUS='NEW'`.** The programs stopped if an output file existed; the app asks before
  replacing.

## Added guards

The originals had none: a zero wavelength divided by zero, a step of zero looped forever, 51
wires overran `DIMENSION THETA(50)`, a helix angle typed in degrees silently produced nonsense.
`inputValidation` refuses each of these with the reason, and caps a run at 200 000 positions and
2 000 000 wire states. The slip-bound march stops after 4 × divisor + 16 steps; analysis shows
the demand returns below the limit within one lay length (≤ divisor steps).

## How it was checked

- **Published values.** Rapport d'étape no. 2 (Feb. 1991) gives the strand (22 aluminium wires,
  R = 2.135 mm, 15°, on a 13.53 mm core, E = 70 GPa, ν = 0.3, μL = 0.8, Ti = 643.5 N,
  A = 0.04 m, λ = 10 m) and SINUS.FOR's results at X = 2.5 m: EI 1671.24, MX 0, MY 0.1696,
  MZ 26.391, FX 0, FY 3.358. Reproduced to every digit when the angle is entered as typed,
  0.2618 rad. The report's FZ 522.24 contradicts its own MZ (FZ/MZ is tan α / Ra for every wire,
  so 522.65); the port prints 522.655. GS.DOC (1991) gives the critical amplitude "de l'ordre de
  0.027 m"; the port computes 0.02726 m.
- **Literal transcription.** `tests/legacyReference/literalPrograms.py` is an independent,
  scalar, line-by-line transcription. The engine matches it exactly (`np.array_equal`) for
  SINUS, NSINUS, RAYON, FRICTION and DEPLACE, including slip-zone bounds and the NSINUS listing.
- **Physics.** With every wire stuck, EI equals (n/2) E a Ra² f cos α (n ≥ 3) along the whole
  strand, for both deflections.

## What the results show

The stiffness curve has jumps where a wire enters or leaves a slip zone: the 1990 model, after
Hardy, does not impose continuity of deformation at the slip bounds. The models of the 1992
thesis (continuity of deformation, compliance) addressed exactly this; their sources are in the
printed listings of `Manuel/MANUEL.MAN`, not in `Programmes/`.
