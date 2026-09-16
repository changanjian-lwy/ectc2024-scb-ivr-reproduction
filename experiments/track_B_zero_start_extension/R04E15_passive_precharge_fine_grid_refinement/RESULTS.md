# R04E15 - fine-grid refinement of R04E14's passive-precharge PASS cells (RESULTS)

## 1. Outcome, stated first

**No cell in this experiment's 13-cell fine grid beats R04E14's own best
PASS cell (`CDIV=300uF/TRAMP=100us/CFLY=3uF`, `LADDER_ERR=0.0536`,
`IIN_PK=39.18A`) on BOTH axes simultaneously.** R04E14's own coarse-grid
optimum sits at (or very near) a genuine local trade-off frontier between
ladder error and peak current in this parameter space: every cell tested
here either improves `LADDER_ERR` at the cost of a higher `IIN_PK`, or
improves `IIN_PK` at the cost of a higher `LADDER_ERR`, relative to
R04E14's best cell. This is `BOUNDARY.md` Section 7's first anticipated
failure condition, and it is what the data shows.

That said, this experiment's own best-`LADDER_ERR`-while-still-passing-
the-current-bar cell, `CDIV=500uF/TRAMP=100us/CFLY=3uF`
(`LADDER_ERR=0.0335`, `IIN_PK=61.44A`), is a real, substantive
improvement in ladder accuracy (`37.6%` lower `LADDER_ERR` than R04E14's
best) bought at a peak current still `2.4x` below R02B's own `150.15A`
ceiling -- it does not strictly dominate R04E14's best cell (its own
`IIN_PK` is `1.57x` higher), but it is a legitimate alternative operating
point on the same Pareto-style frontier, weighted toward output-voltage
accuracy. **12 of this experiment's 13 cells (all except
`CDIV=300uF/TRAMP=20us`, which fails only the current half of the bar at
`195.90A`) simultaneously satisfy BOTH halves of the
`PASS_TOPOLOGY_PRINCIPLE`-style bar** (`LADDER_ERR<=0.236`,
`IIN_PK<=150.15A`) -- far more of this fine grid passes than R04E14's own
coarse grid (`2/14`), simply because this grid was deliberately centered
on the neighborhood R04E14 already identified as good, not because the
underlying physics changed.

**Grid C's own question -- does the PASS verdict survive across the full
`0.6-8.7 uF` `Cfly` range AT THE ACTUAL WINNING OPERATING POINT
(`CDIV=500uF/TRAMP=100us`) -- is answered YES, cleanly, unlike R04E14's
own secondary-grid check at a different point.** All three `Cfly` values
tested at this operating point (`0.6`, `3`, `8.7 uF`) pass BOTH halves of
the bar with comfortable margin (`LADDER_ERR` `0.0066-0.0956`, all far
below `0.236`; `IIN_PK` `60.48-63.68A`, all far below `150.15A`, and
nearly flat across the `14.5x` `Cfly` range). This is a materially more
robust result than R04E14's own secondary-grid finding at
`(CDIV=300uF,TRAMP=10us)`, where all three `Cfly` points FAILED the
current half of the bar outright (`382.83-412.23A`). The reason is
structural, not a new physical finding: `TRAMP=100us` (not `10us`) is
what keeps peak current low regardless of `Cfly`, exactly as R02B's own
`CDIV`/`TRAMP`-separability finding (already confirmed at the corrected
`Cfly` by R04E14 Section 7) predicts.

Grading: **`PASS_TOPOLOGY_PRINCIPLE / NOT_P24_REPRODUCTION`**, R02A's own
Step-1 language, unchanged and reused per `BOUNDARY.md` Section 6 -- not a
new category. See Section 6 below for full justification.

## 2. Method (per BOUNDARY.md, unchanged from R04E14/R02A/R02B)

All 13 cells are LTspice 26.0.2 real transient runs of the SAME byte-level
faithful copy of R02B's own circuit body
(`paper_locked/02_ectc2024_main/spice/R02B_passive_precharge_charge_ramp_sweep.cir`)
R04E14 used: four equal input-divider capacitors `CIN1-4=CDIV`, `LPAR=5
nH`/`RPAR=10 mOhm` source parasitics (IPEC 2018 Table II), three ideal
precharge diodes (`Ron=1m Roff=1T Vfwd=0`) charging `CF1-3=CFLY`
referenced to ground, `1 GOhm` DC-reference leakage, true-zero-energy
initial conditions (`UIC`, no IC statements), no PWM/switches/load, and
the identical `.meas` definitions (`VC1/2/3_FINAL`, `RATIO21`, `RATIO31`,
`LADDER_ERR`, `IIN_PK`, `ID1/2/3_PK`) R02B/R04E14 themselves use. Only
`CDIV`/`TRAMP`/`CFLY` change per cell (fixed `.param` values, one netlist
per cell, `cases/e15_c<CDIV>_t<TRAMP>_f<CFLY>.cir`), exactly matching
R04E14's own packaging pattern. Short filenames were used throughout
(longest committed path measured directly, `241` characters -- the same
order of magnitude R04E14 itself used and confirmed clean; no case in
this experiment showed the `unable to open database file` failure
signature).

Grid A (6 cells): `CFLY=3uF`, `TRAMP=100us` fixed, `CDIV` in `{150, 200,
250, 350, 400, 500} uF`. Grid B (5 cells): `CFLY=3uF`, `CDIV=300uF` fixed,
`TRAMP` in `{20, 50, 75, 150, 200} us`. Grid C (2 cells): at the winning
`(CDIV,TRAMP)` point identified from Grids A/B plus R04E14's own
`CDIV=300/TRAMP=100` cell (`CDIV=500uF`, `TRAMP=100us` -- see Section 3),
`CFLY` at `0.6uF` and `8.7uF`. All 13 LTspice runs completed without a
convergence error and produced a full `.meas` block; every number quoted
below was verified directly against each case's own raw `.log` file (spot
checks: `e15_c500_t100_f3`, `e15_c500_t100_f0p6`, `e15_c500_t100_f8p7`,
`e15_c300_t20_f3` all confirmed to match `results.json` exactly).

## 3. Full 13-cell results table

**Grid A -- CDIV refinement (CFLY=3uF, TRAMP=100us fixed)**

| `CDIV` | `TRAMP` | `CFLY` | `VC1` (V) | `VC2` (V) | `VC3` (V) | err% (VC1/VC2/VC3) | `LADDER_ERR` | `IIN_PK` (A) | `ID1_PK`/`ID2_PK`/`ID3_PK` (A) |
|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| 150 uF | 100 us | 3 uF | 35.233 | 23.104 | 11.438 | -2.13/-3.73/-4.69 | 0.1055 | 22.47 | 1.23/0.81/0.40 |
| 200 uF | 100 us | 3 uF | 35.425 | 23.326 | 11.576 | -1.60/-2.81/-3.53 | 0.0794 | 28.18 | 1.19/0.78/0.39 |
| 250 uF | 100 us | 3 uF | 35.538 | 23.458 | 11.659 | -1.28/-2.26/-2.84 | 0.0639 | 33.72 | 1.15/0.76/0.38 |
| *300 uF†* | *100 us†* | *3 uF†* | *35.611* | *23.545* | *11.714* | *-1.08/-1.90/-2.39* | *0.0536* | *39.18* | *1.12/0.74/0.37* |
| 350 uF | 100 us | 3 uF | 35.662 | 23.606 | 11.753 | -0.94/-1.64/-2.06 | 0.0464 | 44.63 | 1.10/0.73/0.36 |
| 400 uF | 100 us | 3 uF | 35.699 | 23.652 | 11.782 | -0.84/-1.45/-1.82 | 0.0411 | 50.13 | 1.09/0.72/0.36 |
| **500 uF** | **100 us** | **3 uF** | **35.752** | **23.717** | **11.823** | **-0.69/-1.18/-1.48** | **0.0335** | **61.44** | **1.08/0.71/0.36** |

`LADDER_ERR` decreases monotonically as `CDIV` increases across the whole
tested range (`150 uF` through `500 uF`), continuing R04E14's own
`100->300 uF` trend with NO plateau or reversal yet visible at `500 uF` --
`BOUNDARY.md` Section 1's gap-1 question is answered: the improving trend
continues at least to `500 uF`, it has not plateaued. `IIN_PK` also rises
monotonically with `CDIV` (`22.47A` at `150uF` to `61.44A` at `500uF`),
consistent with more stored charge requiring more peak current to
deliver, but stays comfortably under the `150.15A` bar throughout this
range. Bold row is this grid's own best cell.

**Grid B -- TRAMP refinement (CFLY=3uF, CDIV=300uF fixed)**

| `CDIV` | `TRAMP` | `CFLY` | `VC1` (V) | `VC2` (V) | `VC3` (V) | err% (VC1/VC2/VC3) | `LADDER_ERR` | `IIN_PK` (A) | `ID1_PK`/`ID2_PK`/`ID3_PK` (A) |
|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| 300 uF | 20 us | 3 uF | 35.710 | 23.610 | 11.746 | -0.80/-1.62/-2.11 | 0.0454 | 195.90 | 5.62/3.71/1.85 |
| 300 uF | 50 us | 3 uF | 35.636 | 23.561 | 11.722 | -1.01/-1.83/-2.32 | 0.0516 | 78.36 | 2.25/1.49/0.74 |
| 300 uF | 75 us | 3 uF | 35.619 | 23.550 | 11.717 | -1.06/-1.87/-2.36 | 0.0529 | 52.24 | 1.50/0.99/0.49 |
| *300 uF†* | *100 us†* | *3 uF†* | *35.611* | *23.545* | *11.714* | *-1.08/-1.90/-2.39* | *0.0536* | *39.18* | *1.12/0.74/0.37* |
| 300 uF | 150 us | 3 uF | 35.603 | 23.539 | 11.711 | -1.10/-1.92/-2.41 | 0.0543 | 26.12 | 0.75/0.50/0.25 |
| 300 uF | 200 us | 3 uF | 35.599 | 23.536 | 11.710 | -1.11/-1.93/-2.42 | 0.0547 | 19.59 | 0.56/0.37/0.18 |

(†: italicized row in each of Grid A and Grid B is R04E14's own
already-committed `CDIV=300uF/TRAMP=100us/CFLY=3uF` cell, repeated only to
show its position in the interpolated trend -- NOT re-run by this
experiment, and not counted among R04E15's own 13 cells.)

`TRAMP=20us` has a marginally better `LADDER_ERR` (`0.0454`) than
`TRAMP=100us` (`0.0536`) but its `IIN_PK` (`195.90A`) FAILS the
`150.15A` bar outright -- consistent with R04E14's own Section 1 gap-2
observation that `TRAMP=10us` at this `CDIV` also failed the current bar
(`391.80A`). `TRAMP=50us` and `75us` both pass the full bar with a
slightly BETTER `LADDER_ERR` than `TRAMP=100us` (`0.0516`/`0.0529` vs.
`0.0536`) at a HIGHER `IIN_PK` (`78.36A`/`52.24A` vs. `39.18A`) --
consistent with the trade-off, not a joint improvement.
`TRAMP=150us`/`200us` both have a slightly WORSE `LADDER_ERR`
(`0.0543`/`0.0547`) at a LOWER `IIN_PK` (`26.12A`/`19.59A`). `BOUNDARY.md`
Section 1 gap-2's question is answered: `TRAMP=100us` sits very close to
(within `~0.001` `LADDER_ERR` of) a local joint optimum on this
particular trade-off curve for `CDIV=300uF`; no intermediate `TRAMP`
value tested strictly dominates it.

**Grid C -- Cfly robustness at the winning (CDIV=500uF, TRAMP=100us) point**

Winning point derived directly from Grids A/B combined with R04E14's own
`CDIV=300uF/TRAMP=100us` cell: among every candidate satisfying
`IIN_PK<=150.15A`, the lowest `LADDER_ERR` is `CDIV=500uF/TRAMP=100us`
(`LADDER_ERR=0.0335`, `IIN_PK=61.44A`) -- the `CDIV=300uF/TRAMP=20us` cell
has a lower `LADDER_ERR` (`0.0454`) but is excluded because it fails the
current bar (`195.90A`).

| `CDIV` | `TRAMP` | `CFLY` | `VC1` (V) | `VC2` (V) | `VC3` (V) | err% (VC1/VC2/VC3) | `LADDER_ERR` | `IIN_PK` (A) | `ID1_PK`/`ID2_PK`/`ID3_PK` (A) |
|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| **500 uF** | **100 us** | **0.6 uF** | **35.952** | **23.944** | **11.965** | **-0.13/-0.23/-0.29** | **0.0066** | **60.48** | **0.22/0.14/0.07** |
| **500 uF** | **100 us** | **3 uF** | **35.752** | **23.717** | **11.823** | **-0.69/-1.18/-1.48** | **0.0335** | **61.44** | **1.08/0.71/0.36** |
| **500 uF** | **100 us** | **8.7 uF** | **35.289** | **23.190** | **11.495** | **-1.97/-3.37/-4.21** | **0.0956** | **63.68** | **3.08/2.02/1.00** |

All three rows in bold: EVERY `Cfly` point tested at this operating point
passes BOTH halves of the `PASS_TOPOLOGY_PRINCIPLE` bar. `LADDER_ERR`
still increases monotonically with `Cfly` (a `14.5x` spread in `Cfly`
producing a `14.5x` spread in `LADDER_ERR`, `0.0066` to `0.0956` -- the
same qualitative pattern R04E14 Section 8 found at its own point), but
`IIN_PK` stays nearly flat (`60.48-63.68A`, a `5.3%` spread) and never
approaches the `150.15A` ceiling at any tested `Cfly` value. This is the
key difference from R04E14's own secondary grid (run at
`CDIV=300uF/TRAMP=10us`, where `IIN_PK` was `382.83-412.23A` at every
`Cfly` point, failing the bar regardless of `Cfly`): at `TRAMP=100us`,
the current axis is decisively cleared with room to spare, so the PASS
verdict's fate rests entirely on the ladder-error axis, and that axis
passes comfortably even at the worst-case `Cfly=8.7uF` end.

Raw values are quoted directly from each case's own `.log` `.meas`
output (`results.csv`/`results.json`); err% and `LADDER_ERR` use R02B's
own published formula (`LADDER_ERR = |VC1-36|/36+|VC2-24|/24+|VC3-12|/12`)
applied to the raw `VC1/2/3_FINAL` numbers, unchanged from R04E14.

## 4. Explicit before/after comparison against R04E14's own best cell

| Quantity | R04E14 best PASS cell (`CDIV=300uF/TRAMP=100us/CFLY=3uF`) | R04E15 best-`LADDER_ERR`-while-passing cell (`CDIV=500uF/TRAMP=100us/CFLY=3uF`) | Change |
|---|---:|---:|---|
| `VC1/VC2/VC3` (V) | 35.611/23.545/11.714 | 35.752/23.717/11.823 | closer to 36/24/12 on all three |
| err% vs 36/24/12 | -1.08/-1.90/-2.39 | -0.69/-1.18/-1.48 | smaller magnitude on all three |
| `LADDER_ERR` | 0.0536 | 0.0335 | `37.6%` LOWER (better) |
| `IIN_PK` | 39.18 A | 61.44 A | `56.8%` HIGHER (worse), still `2.4x` below the `150.15A` bar |
| `ID1/2/3_PK` (A) | 1.12/0.74/0.37 | 1.08/0.71/0.36 | essentially unchanged |

Neither cell dominates the other: `CDIV=500uF/TRAMP=100us` is strictly
better on ladder accuracy and every diode/voltage metric except peak
source current, where `CDIV=300uF/TRAMP=100us` remains superior. Both
comfortably clear the `PASS_TOPOLOGY_PRINCIPLE` bar. Whether R04E14's
original best cell or this experiment's new best-`LADDER_ERR` cell is
"the" best operating point is a matter of which axis is weighted more
heavily -- this experiment does not adjudicate that weighting, only
reports both numbers plainly, per `BOUNDARY.md` Section 8's instruction
not to force a favorable reading.

Comparison against the two literature anchors R04E14 itself used (R02A's
own best passive result, `LADDER_ERR~0.236`; R02B's own best,
`IIN_PK=150.15A`) is unchanged from R04E14 Section 5/6 and not repeated
here in full -- both R04E15 cells above beat both anchors by a wide
margin, exactly as R04E14's own best cell already did.

## 5. Does any cell beat R04E14's own best cell on both axes? (BOUNDARY.md Section 6 question)

**No.** Checked directly against all 13 R04E15 cells (Section 3 tables):
every cell with a lower (better) `LADDER_ERR` than R04E14's `0.0536` has a
higher (worse) `IIN_PK` than R04E14's `39.18A`, and every cell with a
lower (better) `IIN_PK` has a higher (worse) `LADDER_ERR`, with the single
exception of `CDIV=500uF/TRAMP=100us/CFLY=8.7uF` (Grid C's high-`Cfly`
extreme), which is worse on BOTH axes relative to R04E14's best
(`LADDER_ERR=0.0956` vs `0.0536`, `IIN_PK=63.68A` vs `39.18A`) -- expected,
since it deliberately tests the least favorable `Cfly` extreme at a
`CDIV` chosen for `Cfly=3uF`. R04E14's own coarse-grid optimum
(`CDIV=300uF/TRAMP=100us`) sits at or very near a genuine local
`LADDER_ERR`-vs-`IIN_PK` trade-off frontier in this parameter space; this
fine grid maps that frontier more finely but does not find a point that
strictly dominates it. This directly answers `BOUNDARY.md` Section 6's
own framing: R04E14's own best cell already sits at or near a local joint
optimum, not one an intermediate grid point could jointly beat.

## 6. Grading

**`PASS_TOPOLOGY_PRINCIPLE / NOT_P24_REPRODUCTION`** (R02A's own Step-1
grading language, reused unchanged from R04E14, not a new category per
`BOUNDARY.md` Section 6's explicit instruction). Justification: `12` of
this experiment's `13` cells (every cell except
`CDIV=300uF/TRAMP=20us/CFLY=3uF`, which fails only the current half of
the bar at `195.90A`) simultaneously satisfy BOTH stated conditions of
the success bar -- `LADDER_ERR` at or below R02A's own best passive
result (`~0.236`) AND peak source current at or below R02B's own best
(`150.15A`). Grid C additionally establishes that this PASS verdict is
ROBUST across the full `0.6-8.7uF` `Cfly` first-principles range AT THE
ACTUAL WINNING OPERATING POINT (`CDIV=500uF/TRAMP=100us`), which R04E14's
own secondary grid (run at a different, `TRAMP=10us` point) did not show
-- a meaningfully stronger and more complete robustness result than
R04E14 itself established. This remains explicitly NOT a `P24`
reproduction claim, for the same reasons R04E14 Section 9/`BOUNDARY.md`
Section 8 already state: the `N=4` divider topology is IPEC 2018's own
extension generalized by R02A as a test hypothesis; the flying-capacitor-
to-ground reference is R02A's own "all-low-side-on" simplification; and
`CDIV`/`TRAMP`/`Cfly` all remain `SENSITIVITY_ONLY` values, not confirmed
components. This is NOT a claim that R04E14's own committed grid,
results, or grading are superseded -- per `BOUNDARY.md` Section 8, a
result here does not change R04E14's own committed numbers, this is a
separately-numbered refinement.

## 7. What this does and does not establish

- It does not combine precharge with PWM/the P24 switching stage --
  unaffected, same standing block as R02A/B/R04E14, pending the Roberts &
  Prodić 2024 literature review.
- It does not reconcile the ground-referenced flying-capacitor
  simplification with the real floating adjacent-capacitor connection --
  inherited unchanged from R02A/R04E14.
- It does not establish a single "correct" `CDIV`/`TRAMP`/`Cfly` value --
  all three remain `SENSITIVITY_ONLY`; this experiment only maps the
  response surface more finely within the range R04E14 already
  established as worth exploring, per `BOUNDARY.md` Section 8.
- It does not address `Vout`/handoff bootstrap at all -- this module has
  no output stage, exactly as R02A/B/R04E14 themselves did not.
- It does not modify, overwrite, or invalidate R04E14's own committed
  grid, results, or grading -- R04E14's `CDIV=100uF`/`CDIV=300uF`
  (`TRAMP=100us`) cells remain its own correct record; this is an
  additional, separately-numbered refinement.
- It does not establish that `CDIV=500uF/TRAMP=100us` is strictly
  "better" than R04E14's own `CDIV=300uF/TRAMP=100us` -- the two trade
  ladder accuracy against peak current, and this experiment does not
  adjudicate which axis should be weighted more heavily (Section 4/5).
- Grid C's robustness finding is specific to the `CDIV=500uF/TRAMP=100us`
  operating point; it does not claim `Cfly`-robustness holds at every
  `(CDIV,TRAMP)` point in the grid (R04E14's own `CDIV=300uF/TRAMP=10us`
  point remains `Cfly`-sensitive AND current-bar-failing, as R04E14
  Section 8 already found and this experiment does not re-test).

## 8. Provenance and classification (BOUNDARY.md Section 5)

| Value | Source | Category |
|---|---|---|
| `CDIV` new values `{150,200,250,350,400,500} uF` (Grid A) | New for this experiment: fills the gap between R04E14's own tested `100`/`300 uF` points and extends beyond `300 uF` | `SENSITIVITY_ONLY` |
| `TRAMP` new values `{20,50,75,150,200} us` (Grid B) | New for this experiment: fills the gap between R04E14's own tested `10`/`100 us` points | `SENSITIVITY_ONLY` |
| `CFLY=0.6 uF`, `8.7 uF` (Grid C) | `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own derived range extremes, re-tested at a different (the actual winning, `CDIV=500uF/TRAMP=100us`) operating point than R04E14's own secondary grid used | `SENSITIVITY_ONLY`, inherited |
| `CFLY=3 uF` (Grids A/B) | R04E8's own corrected middle value | `SENSITIVITY_ONLY`, inherited |
| `LPAR=5 nH`, `RPAR=10 mOhm`, topology, diode model, ground reference | Unchanged from R02A/B/R04E14 | see R04E14 `BOUNDARY.md` Section 5 for original provenance |

No new paper-sourced, cross-paper, or external-device data is introduced.
This experiment only adds grid resolution within an already-classified
parameter space, exactly per `BOUNDARY.md` Section 5.

## 9. Files

- `cases/e15_c*.cir` -- 13 netlists (6 Grid A + 5 Grid B + 2 Grid C),
  byte-level faithful copies of R02B/R04E14's own circuit body with only
  `CFLY`/`CDIV`/`TRAMP` changed to fixed per-cell `.param` values.
- `scripts/build_r04e15.py` -- generates the 11 Grid A + Grid B netlists.
- `scripts/build_r04e15_gridc.py` -- generates the 2 Grid C netlists at
  the winning `(CDIV,TRAMP)` point identified from Grid A/B results.
- `scripts/analyze_r04e15.py` -- parses all 13 `.log` files and writes
  `results.csv`/`results.json`.
- `results.csv` / `results.json` -- the full 13-row table (Section 3).
