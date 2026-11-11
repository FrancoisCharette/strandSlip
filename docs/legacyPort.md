# Porting notes: the 1990 and 1992 Fortran programs

How `legacy/programmes/*.FOR` (1990) and `legacy/manuel1992/` (1992) became
`src/masterRebuild/services/`, what was kept on purpose, what was not, and how the port was
checked. For maintainers; users want [`manual/README.md`](manual/README.md). The 1992 programs
are [further down](#the-1992-thesis-programs).

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
thesis (continuity of deformation, compliance) addressed exactly this; they follow.

## The 1992 thesis programs

Six programs, one per model and imposed deflection, each solving one wire of a strand over a
half lay length in the dimensionless variables of annex A of the thesis: positions ξ = X/p in
lay lengths, ρ̄ = ρ/ρc, Ā = A/Ac, Λ = λ/p, the compliance factor γ1. Their sources survive only
as the listings printed in annex C of `Manuel/MANUEL.MAN`;
[`legacy/manuel1992/README.md`](../legacy/manuel1992/README.md) says how they were recovered.

| Program | Model | Deflection | Writes |
|---|---|---|---|
| HARDRHOB | Hardy: strain jumps at the macro-slip bounds | constant radius | DEP.DAT, ELG.DAT, FRC.DAT (on request) |
| CONTRHOB | continuity of deformation | constant radius | the same |
| ZETARHOB | compliance (micro- and macro-slip) | constant radius | ENERGY.DAT, INCONNUS.DAT, ZETA*.DAT |
| HARDSIN, CONTSIN, ZETASIN | the same three | sinusoid; choice 1, 2 or 3 | the same, by model |

All six were interactive. `ThesisInput` holds what they ask at the start (ρ̄, or the choice, Λ
and Ā; γ1; XTOUR; whether to compute the profiles); `approximations` answers, in order, what
they ask only when an automatic approximation fails (XB1 for CONTRHOB, XB1 then XB2 for CONTSIN,
XB1C for the compliance programs). The screen is rebuilt as the session it was: prompts, the
typed answers, Newton's iterations, PAUSE messages and results. Where the program would wait
for an answer the inputs do not give (another radius, another XTOUR, another approximation),
the run ends there and the result says what was asked (`ThesisResult.pendingQuestion`).

### Where each listing went

| Listings | Service |
|---|---|
| QROMB, TRAPZD, POLINT, RTSEC, RTFLSP, GOLDEN, DLUDCMP, DLUBKSB | `thesisNumerics` |
| DEPAME, ELGAME, FRCAME, FRICTION, APPBRN, VMIN, DEPFIL, ELGFIL, FRCFIL, DEPH, DR2H, F1D–F2E | `thesisDeflections` |
| bounds of HARDRHOB and HARDSIN, DMACRO, NEWT, VCB, JACO, PBCONV | `macroSlipModels`, `thesisPrograms` |
| COMP, VECB, JACOB | `complianceSystem` |
| NEWTON, UNRES, APPROX, APPSIN, DMICRO, DISPENRG, the portion loop of ZETA* | `complianceModel` |
| SORTIE, SORTZETA | `thesisProfiles` |
| the main programs, ENT*, ENSN*, ECR*, ECSN*, INCONNUS | `thesisPrograms`, `thesisSinusoidPrograms`, `thesisScreens` |
| keyboard, screen, files; running; tables | `thesisSession`, `thesisRunner`, `thesisTables` |

As for 1990, every expression keeps the listing's operand order and integer powers are
products, so each value is the same IEEE computation as the listing's.

### Kept on purpose

1. **REAL\*4 constants.** `EPS=1.E-6` (QROMB), `R=.61803399` and `C=.38196602` (GOLDEN) and
   `TINY=1.0E-20` (DLUDCMP) are single-precision constants in DOUBLE PRECISION names; `XM-.03`
   and `XM+0.03` (the bracket of APPBRN), `RHOB.LT.0.65` (CONTRHOB) and `WLBAR/4-.6` (the end of
   choice 1) use single-precision literals (`thesisNumerics.real4`).
2. **`IF(XINF.LT.0001)`** in APPSIN: `0001` is the integer 1, so the half lay length from 0.5
   also takes RHOBINF = 1.
3. **DLUBKSB sets `II=1`** where Numerical Recipes sets `II=I`. The extra terms multiply zeros.
4. **Newton's exits.** NEWT and NEWTON return the iterate before the last correction; NEWTON
   gives up at its 14th iteration and on the first negative transition point, leaving the
   others unchanged; a run that needs typed help asks again after every failure.
5. **One region.** ZETARHOB solves nothing for a single micro-slip region: BTM and ETM are read
   unassigned and DOS left static storage zero (for θi = 90° on the first half lay length that
   is the exact solution). ZETASIN solves it (UNRES).
6. **The portion loop.** COMP always builds ten linear portions; the number of regions grows
   from one until 2δ at the centre fits the last portion used, eleven meaning a macro-slip
   centre. ZETASIN starts each half lay length where the previous one stopped.
7. **DMICRO's clamp.** A share above 1 is rounded (DNINT); if still above 1 the program prints
   its warning, pauses, and uses 1.
8. **SORTZETA's loop** ends at `X.LE.XSUP` with no tolerance (SORTIE allows 1E-9), keeps the
   last values where X falls in no region, and sets the friction ratio of a macro-slip region
   to −1 whatever the side.
9. **Accumulations**: X=X+DX in the profiles, XTOUR=XTOUR+0.5, X=X+DEL in TRAPZD (whose IT
   survives between calls), the running sum of YCOMP in COMP, energies summed region by region.
10. **Formats**: every FORMAT as printed (`thesisScreens`), with Microsoft FORTRAN's backslash
    (the prompt line stays open for the answer) and its tolerance of `1X'text'`. ECRZETA 41
    continues `'Les valeurs des '` with `'inconnues…'` on the next line: with each line padded
    to column 72 these are two strings, not an escaped apostrophe.
11. **INCONNUS's parameter record** is printed for the sinusoid; ZETARHOB writes the block for
    the constant radius that the listing has commented out below it.

### Not reproduced

- **8087 arithmetic and the runtime's functions.** As for 1990, temporaries were 80-bit; the
  last bit of a cosine or an exponential may differ. `X**2.0D0` is the correctly rounded square
  (Windows' `pow` gives another double in 95 of 200 000 cases; the 8087 would almost always
  have rounded correctly).
- **POLINT's X.** QROMB passes the REAL\*4 constant `0.` where POLINT expects DOUBLE PRECISION:
  the high half of what POLINT read was whatever followed the constant in memory, which only the
  lost executables could tell. 0 is used.
- **Undefined values and run-time errors.** RTFLSP returns nothing after a failed bracket and
  HARDSIN carried on with it; a zero divisor, an overflowing exponential (large Λ) or DACOS of a
  value outside −1..1 stopped the DOS program with a run-time error. The port stops with an
  explanation in each case.
- **The runtime's own text** for PAUSE (the message is shown) and STOP (nothing is shown).

### How it was checked

- **Published values** (`tests/testServices/testThesisPublished.py`). Table 6.1 of the thesis
  (constant radius, γ1 = 0.06): every bound and energy of both models at ρ̄ = 1.0, 0.8 and 0.6.
  Table 6.2 (sinusoid, Λ = 28): Hardy's total energies 0.066745 and 1.20146 and its bounds;
  the compliance model's total 0.019013 at Ā = 1.0, 0.130465 at Ā = 1.3, its bounds near the
  antinode, B1 − INF = 0.10224 and SUP − B2 = 0.10129 at Ā = 1.4. The manual's examples: APPROX
  tries 0.136284 at ρ̄ = 0.7 and 0.10 converges; APPSIN tries 0.16648 and 0.12123 at Ā = 2.0
  and 0.19 and 0.10 converge.
- **Where the thesis slipped**: table 6.1(c) prints B2 = 0.39754 (the bounds are symmetric:
  0.39758); 6.2(c) prints B1 = 6.58430 for Hardy (the root is 6.584266, bisection agrees);
  6.2(b) prints 6.63290 for 6.6328945 (rounded twice); its totals are sums of rounded parts.
  Table 6.2(b) needs, at half lay length 4.5, an approximation between 0.198 and 0.211: Newton
  then finds a macro-slip region 0.0156 wide and the table's total; from 0.2 it finds a region
  of zero width. One difference is unexplained: in table 6.2(c) the micro-slip energy in the
  macro-slip regions is 0.148658 where the programs give 0.148457, and the total carries the
  same 0.0002; the macro-slip and micro-slip columns and the bounds agree.
- **Literal transcription.** `tests/legacyReference/literalThesis*.py` transcribes the 66
  listings line by line (Fortran names, GOTOs as loops, COMMON blocks as attributes, the
  keyboard as answers by variable). The engine prints the same screen and writes the same files,
  record for record, on 19 runs covering the six programs and all three choices, and stops at
  the same question on six more (`testThesisPrograms.py`).
- **Formats.** Every FORMAT in `thesisScreens` is checked against the 96 distinct formats of
  the listings (`testThesisScreens.py`).
- **Physics.** Hardy's bounds are asin(ρ̄)/2π; the continuity model's macro-slip region is
  wider than Hardy's and its strain continuous; as γ1 decreases the compliance model's bound and
  energy move steadily toward the continuity model's (section 6.1.1.4 of the thesis).
- **The sources.** Each diskette directory is a whole program, and the recovery tool rebuilds
  every file from `MANUEL.MAN` (`testManuel1992Listings.py`, run where the manual is present).
