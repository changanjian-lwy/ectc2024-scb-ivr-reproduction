# R04E15 - fine-grid refinement of R04E14's passive-precharge PASS cells (BOUNDARY)

## 1. Parent and why this experiment exists

**R04E14** (`experiments/track_B_zero_start_extension/
R04E14_corrected_cfly_passive_precharge_replay/`) replayed R02A/R02B's
own passive-divider-plus-diode precharge module with `CFLY` corrected
from the cross-topology-suspect `53.8 uF` to this project's own `3 uF`
first-principles candidate, and found 2 of 14 coarse-grid cells
(`CDIV=100 uF` and `CDIV=300 uF`, both `TRAMP=100 us`) satisfy BOTH
halves of the `PASS_TOPOLOGY_PRINCIPLE` bar (ladder error at or below
R02A's own best passive result, peak source current at or below R02B's
own best). This reversed R02A/B's own `FAILED_CAPACITANCE_TRANSFER`
verdict for this module.

R04E14's own 12-point coarse grid (`CDIV` in `{10,30,100,300} uF` x
`TRAMP` in `{1,10,100} us`) left three specific gaps this experiment
fills, per explicit user direction 2026-09-16 (pursue R04E14's own
follow-up before the higher-setup-cost Roberts soft-start mechanism):

1. **No `CDIV` values were tested between `100` and `300 uF`, or above
   `300 uF`.** Since R02A/B's own finding ("increasing `CDIV`
   monotonically improves the charge available") already established a
   monotonic-in-`CDIV` trend at the OLD `Cfly`, it is unknown whether an
   intermediate or larger `CDIV` value (at the corrected `Cfly=3 uF`)
   beats R04E14's own best cell (`CDIV=300 uF`, `LADDER_ERR=0.0536`) by a
   meaningful margin, or whether the improvement has already plateaued.
2. **`TRAMP=10 us` at `CDIV=300 uF` actually achieved a BETTER ladder
   error (`0.0351`) than the `TRAMP=100 us` PASS cell (`0.0536`)** --
   R04E14's own Section 3 table -- but MISSED the peak-current half of the
   bar (`391.80 A` vs. the `150.15 A` R02B-derived ceiling). Only three
   `TRAMP` points (`1, 10, 100 us`) were tested, so the actual trade-off
   curve between ladder error and peak current across this range is
   unmapped; an intermediate `TRAMP` might jointly beat R04E14's own best
   cell on BOTH axes simultaneously.
3. **R04E14's own `CFLY` sensitivity check (Section 8 of its `RESULTS.md`)
   was run at `(CDIV=300 uF, TRAMP=10 us)`, NOT at the actual winning
   `TRAMP=100 us` point.** Whether the `PASS_TOPOLOGY_PRINCIPLE` verdict
   is robust across the full `0.6-8.7 uF` first-principles range AT THE
   ACTUAL PASS-GRADE OPERATING POINT has never been tested.

## 2. What changed relative to R04E14, exactly

**No mechanism, topology, or parameter-model change of any kind.** This
experiment reuses R04E14's own byte-level-faithful copy of R02A/R02B's
circuit (four equal input-divider capacitors, `LPAR=5 nH`/`RPAR=10 mOhm`
source parasitics, three ideal precharge diodes, ground-referenced flying
capacitors, true-zero-energy initial conditions, no PWM/switches/load)
completely unchanged. The ONLY thing this experiment does is run
ADDITIONAL grid POINTS within the same, already-validated construct and
parameter space -- filling in the three gaps in Section 1, not testing
anything new in kind.

## 3. Swept grid (three sub-grids, each targeting one gap from Section 1)

**Grid A -- CDIV refinement** (fills gap 1): `CFLY=3 uF`, `TRAMP=100 us`
fixed (R04E14's own winning `TRAMP`), `CDIV` in `{150, 200, 250, 350,
400, 500} uF` (6 cells) -- three points between the two known PASS values
(`100`/`300 uF`) and two points beyond `300 uF`, to check whether the
improving trend continues, plateaus, or reverses.

**Grid B -- TRAMP refinement** (fills gap 2): `CFLY=3 uF`, `CDIV=300 uF`
fixed (R04E14's own best-`LADDER_ERR` divider value), `TRAMP` in `{20,
50, 75, 150, 200} us` (5 cells) -- mapping the ladder-error-vs-peak-
current trade-off between the known `10 us` (best ladder error, fails
current) and `100 us` (passes both) points, to check whether an
intermediate value passes both axes with a better margin than `100 us`
achieves, or whether `100 us` already sits at or near the joint optimum.

**Grid C -- Cfly robustness at the actual PASS point** (fills gap 3): at
whichever single `(CDIV, TRAMP)` cell is THIS experiment's own
best-`LADDER_ERR`-while-still-passing-the-current-bar result (from Grids
A/B combined with R04E14's own `CDIV=300/TRAMP=100` cell), re-run at
`CFLY=0.6 uF` and `CFLY=8.7 uF` (2 cells) -- the two extremes of the
first-principles range, at the ACTUAL winning operating point this time,
not the `TRAMP=10 us` point R04E14's own secondary grid used.

Total: 6 + 5 + 2 = 13 cells.

## 4. What must not change

- The circuit topology, parasitics, diode model, ground reference, and
  initial conditions -- copied byte-for-byte from R04E14/R02A/R02B.
- `CFLY=3 uF` for Grids A/B (R04E8's own corrected middle value, same as
  R04E14's primary grid) -- only Grid C varies `CFLY`, and only at the
  two first-principles-range extremes already established, not new values.
- No PWM, switches, or output load -- this remains an isolated
  precharge-module-only test, exactly as R02A/B/R04E14 all were. Combining
  with PWM remains blocked pending the (now-resolved-negative) Roberts &
  Prodić 2024 literature-review gate (`ROBERTS_PRODIC_2024_LITERATURE_
  REVIEW.md`) -- unaffected by this experiment.
- R04E14's own `.meas` definitions and `LADDER_ERR` formula
  (`|VC1-36|/36+|VC2-24|/24+|VC3-12|/12`) -- reused unchanged for direct
  comparability.
- The short-filename convention R04E14's own Section 4 established
  (`e15_c<CDIV>_t<TRAMP>_f<CFLY>.cir` or similar, well under the
  ~239-character safe path length R04E14 empirically found) -- to avoid
  repeating the silent-measurement-database-failure tooling issue R04E14
  diagnosed and fixed.

## 5. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `CDIV` new values `{150,200,250,350,400,500} uF` (Grid A) | New for this experiment: fills the gap between R04E14's own tested `100`/`300 uF` points and extends beyond `300 uF` | `SENSITIVITY_ONLY` |
| `TRAMP` new values `{20,50,75,150,200} us` (Grid B) | New for this experiment: fills the gap between R04E14's own tested `10`/`100 us` points | `SENSITIVITY_ONLY` |
| `CFLY=0.6 uF`, `8.7 uF` (Grid C) | `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own derived range extremes, re-tested at a different (the actual winning) `(CDIV,TRAMP)` operating point than R04E14's own secondary grid used | `SENSITIVITY_ONLY`, inherited |
| `CFLY=3 uF` (Grids A/B) | R04E8's own corrected middle value | `SENSITIVITY_ONLY`, inherited |
| `LPAR=5 nH`, `RPAR=10 mOhm`, topology, diode model, ground reference | Unchanged from R02A/B/R04E14 | see R04E14 `BOUNDARY.md` Section 5 for original provenance |

No new paper-sourced, cross-paper, or external-device data is introduced.
This experiment only adds grid resolution within an already-classified
parameter space.

## 6. Success condition

`PASS_TOPOLOGY_PRINCIPLE`-style success (same bar as R04E14 Section 7):
`LADDER_ERR` at or below R02A's own best (`~0.236`) AND peak source
current at or below R02B's own best (`150.15 A`). This experiment's own
specific question: does ANY cell in Grids A/B beat R04E14's own best
PASS cell (`CDIV=300 uF/TRAMP=100 us`, `LADDER_ERR=0.0536`,
`IIN_PK=39.18 A`) on BOTH axes simultaneously, or does R04E14's own best
cell already sit at or near a local joint optimum? For Grid C: does the
PASS verdict at the actual best operating point survive across the full
`0.6-8.7 uF` `Cfly` range, or does it narrow/fail at either extreme?

## 7. Failure conditions

- No cell in Grids A/B improves on R04E14's own best PASS cell -- a
  legitimate, informative negative result establishing R04E14's own
  coarse-grid optimum was already close to a local best, not a reason to
  keep expanding the grid further in search of an improvement.
- Grid C shows the PASS verdict fails at one or both `Cfly` extremes --
  reported plainly; this would mean R04E14's own positive result is
  fragile to the still-unconfirmed `Cfly` choice, an important honest
  caveat, not a reason to discard R04E14's own finding (which remains
  valid at `Cfly=3 uF` regardless).
- Solver non-convergence, or the path-length measurement-database failure
  R04E14 diagnosed recurring despite the short-filename precaution --
  reported as its own outcome, not silently worked around differently.

## 8. What this experiment cannot prove

- It does not combine precharge with PWM -- unaffected, same standing
  block as R04E14.
- It does not reconcile the ground-referenced flying-capacitor
  simplification with the real floating adjacent-capacitor connection --
  inherited unchanged from R02A/R04E14.
- It does not establish a single "correct" `CDIV`/`TRAMP`/`Cfly` -- all
  three remain `SENSITIVITY_ONLY` values; this experiment only maps the
  response surface more finely within the range already established as
  worth exploring.
- It does not address `Vout`/handoff bootstrap at all -- this module has
  no output stage, exactly as R02A/B/R04E14 themselves did not.
- A result here does not change R04E14's own committed grid, results, or
  grading -- this is an additional, separately-numbered refinement, not a
  correction of R04E14's numbers.
