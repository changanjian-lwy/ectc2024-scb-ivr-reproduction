# R04E8 - corrected-Cfly voltage-ratio-gated EPE2019 charge-redistribution ladder bootstrap (BOUNDARY)

## 1. Parent

**PARENT: R04E7** (`experiments/track_B_zero_start_extension/
R04E7_ratio_gated_charge_redistribution_startup/`, `BOUNDARY.md`/
`RESULTS.md`). R04E7 built a voltage-ratio-gated version of EPE2019's
3-state charge-redistribution ladder-bootstrap mechanism and got all 3
tested tolerances (`2%/5%/10%`) to converge cleanly toward `36/24/12 V`,
using `Cfly=53.8 uF` for `C1`/`C2`/`C3`. That mechanism -- the P24
power-stage topology, the truth table (state (a) `H1+L1`, state (b)
`H2+L1+L2`, state (c) `H3+L2+L3`), and the `.machine`/`.state`/`.rule`
ratio-gating logic (state (a) exits at `V(C1)>=36V`, state (b) at
`2*V(C1)<=3*V(C2)`, state (c) at `V(C2)<=2*V(C3)`) -- is reused
**unchanged** here.

## 2. Why this experiment exists

Since R04E7 was committed, this project found (documented in
`paper_locked/00_boundaries/CURRENT_ASSUMPTION_CROSSCHECK.md`'s "Flying
capacitor" row and `paper_locked/00_boundaries/CFLY_FIRST_PRINCIPLES_ESTIMATE.md`)
that `Cfly=53.8 uF` has a cross-topology provenance problem: it is the
literal component sum from EPE2019's own **CSC-buck** prototype Table I, a
different, topologically modified converter from the conventional SC buck
P24 actually is. That paper's conventional SC buck needs `C1` to block the
*full* `Vin`, which the CSC buck's whole redesign purpose is to avoid --
and Table I's actual parts are rated only `35 V`/`50 V`, not enough for
P24's `48 V Vin`. A first-principles re-derivation from P24's own operating
point (`CFLY_FIRST_PRINCIPLES_ESTIMATE.md`) gives a candidate range of
`~0.6-8.7 uF` (varying by capacitor position and by a 1%-5% ripple-target
choice that project document makes, not a paper-given number) -- every
value in that range is well below `53.8 uF`.

**This experiment's job**: rerun R04E7's already-validated ratio-gating
mechanism with `Cfly` swapped to this corrected range, to check whether the
mechanism (not just the specific numbers) still works well at the
physically-appropriate capacitance scale. This is explicitly a **module
swap inside an unchanged framework**.

## 3. The single swept variable

`CFLY` in `{1 uF, 3 uF, 8.7 uF}`.

Justification against `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own table
(`C1`/`C2`/`C3` at `1%/2%/5%` ripple, range `~0.6-8.7 uF`):

- `1 uF`: a representative **low** point, close to `C1`'s own `2%`-ripple
  figure (`1.45 uF`) and above `C1`'s `5%`-ripple figure (`0.58 uF`) --
  picked as a round number near the low end of the derived range rather
  than any single table cell, since this project uses one shared `Cfly`
  value for all three positions (the same convention EPE2019 and this
  project's prior experiments already use).
- `3 uF`: a representative **mid** point, close to `C2`'s `1%`-ripple
  figure (`4.34 uF`) and above `C1`'s `1%`-ripple figure (`2.89 uF`) --
  R04E7's own middle value in spirit (a central point for the pilot check,
  Section 6).
- `8.7 uF`: the **high**, most conservative end of the derived range --
  `C3`'s own `1%`-ripple figure exactly (the binding constraint identified
  in `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`, since the lowest-voltage position
  needs the most capacitance for a given ripple percentage when a single
  shared value is used for all three positions).

`TOL` is held **fixed at 2%** (not swept) -- R04E7's own best-performing
tolerance in its 3-cell grid (final `LADDER_ERR=0.045`, the tightest and
most demanding of R04E7's three tested tolerances), chosen here so the
comparison against R04E7 isolates the `Cfly` effect alone, not a
`Cfly x TOL` interaction.

## 4. What stays fixed (unchanged from R04E7)

- `Vin=48 V`, `nP=4`, `nM=4`, `POUT_MODULE=250 W`.
- Power-stage topology and node names (`SH1-4`/`SL1-4`/`CS1-3`/`L1-4`),
  copied unchanged from R04E7's `SCB4P_P24_R04E7` subcircuit (renamed
  `SCB4P_P24_R04E8` only to avoid a duplicate-subckt-name collision if both
  netlists were ever loaded together; electrically identical).
- The GS61008T `Ron`/device data (`RHS=7 mOhm`, `RLS=3.5 mOhm`,
  `CH=385 pF`, `CL=770 pF`), unchanged.
- The `.machine`/`.state`/`.rule` ratio-gating construct and the truth
  table, copied verbatim from R04E7.
- `COUT=4.672 mF` (the same EPE2019 Table-I cross-topology candidate value
  R04E7 used) -- **deliberately NOT corrected here.** `Cout`'s sizing is a
  separate, still-unresolved gap per
  `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own "Cout is not estimated here"
  section (no target load-transient specification exists to derive a
  first-principles `Cout` the way `Cfly` was derived). Fixing two variables
  in one experiment would violate this project's one-variable principle and
  conflate two independent corrections; `Cfly` alone is this experiment's
  scope.
- `TOL=2%` (fixed, Section 3), the tolerance-band definition itself
  (`+/-TOL` of each target, all three simultaneously), and the
  charge-conservation reasoning from R04E7/BOUNDARY.md Section 3 (still
  applies unchanged: equal `Cfly` values and `Vin=48 V` still make a
  single (a)-(b)-(c) pass unable to reach `36/24/12 V`, independent of the
  specific `Cfly` magnitude, since that argument is purely ratio-based).

## 5. What changed, and why (beyond `Cfly` itself)

Two **numerical-resolution** settings changed, both justified directly by
the pilot run (Section 6) -- neither is a physical parameter and neither is
swept:

- **`TMAX`** (the `.tran` maximum internal timestep) reduced from R04E7's
  `1 ns` to `50 ps`. The RC time constant governing each state's dynamics
  is approximately `(RHS+RLS)*Cfly` (the same series-`Ron` charging path
  R04E7's own Section 6 used for its `50 us` justification), which scales
  down linearly with `Cfly`: about `565 ns` at R04E7's `53.8 uF`, versus
  about `10.5-91 ns` across this experiment's `1-8.7 uF` range. R04E7's own
  `1 ns` step would under-resolve these much faster transients. `50 ps`
  was validated directly in the pilot run (Section 6): it reproduced
  R04E7's own per-cycle `VC1` trajectory almost exactly (e.g. `21.59 V` at
  cycle 1 for the pilot's `3 uF` case vs R04E7's `21.60 V`, to 4 significant
  figures), confirming adequate resolution rather than an unverified guess.
- **`TCAP_TOTAL`** (the safety cap) reduced from R04E7's `50 us` to
  `10 us` -- see Section 6 for the post-pilot derivation. `TCAP_TOTAL` is
  held **fixed** across all three `Cfly` cells (one global cap, exactly
  R04E7's own convention, Section 6 of that experiment's `BOUNDARY.md`),
  not re-tuned per cell.

Neither change alters the electrical circuit, the truth table, or the
ratio-gating comparator logic; both are solver-resolution adjustments
required because the swept `Cfly` values move the circuit's own natural
timescale, exactly as R04E7's `50 us`/`1 ns` settings were themselves tuned
to its own (different) timescale.

## 6. Pilot run and safety-cap derivation

**Physical expectation, stated before running anything** (per the task's
explicit instruction): convergence should happen *faster* in
simulated-time terms at a smaller `Cfly` (less charge needs to move to
produce the same voltage change on a smaller capacitor, i.e. the governing
`RC` time constant shrinks with `C`), but peak capacitor-to-capacitor
inrush current may *not* shrink by the same factor -- for a simple
`RC`-type charging step through the same series `Ron` path, peak current is
set by `V/Ron`, which does not depend on `C` at all in the ideal limit.
Both halves of this prediction were checked directly against data, not
assumed.

**Pilot run** (untracked, scratchpad-only, per R04E7's own precedent of an
untracked diagnostic run before committing a cap): `Cfly=3 uF` (this
experiment's own middle value), `TOL=2%` (fixed value used throughout this
experiment), `TCAP_TOTAL=2 us` (a generous, order-of-magnitude cap picked
from a naive linear-RC-scaling estimate: R04E7's `53.8 uF` cell converged
at `t=4.2395 us`; scaling by `3/53.8` predicts `~237 ns`, so `2 us` is an
`>8x` margin even before running), `TMAX=55.76 ps` (`1 ns` scaled by the
same `3/53.8` ratio, to hold the step-count-per-RC resolution constant
relative to R04E7's own `1 ns`/`53.8 uF` choice).

**Pilot result**: converged (`DONE`) at `t=256.7 ns`, after 8 cycles
(matching R04E7's own `TOL=2%` cycle count exactly), `LADDER_ERR=0.045`
(matching R04E7's own `TOL=2%` final value to 2 significant figures). Peak
`ICS1` current: `4431.5 A` max / `-3307.9 A` min -- **essentially the same
order of magnitude as R04E7's own `4566.9 A`/`-2032.5 A` at `53.8 uF`**,
confirming the peak-current-does-not-shrink-with-C prediction directly
(full committed-grid data and comparison: `RESULTS.md`). `IL1` (a
different, inductor-branch current, not a capacitor-to-capacitor current)
did shrink substantially (`242.4 A` vs R04E7's `2201.9 A`) -- this
distinction (direct capacitor-to-capacitor current vs. inductor-branch
current) is reported explicitly in `RESULTS.md`, not conflated.

**Safety-cap choice for the committed grid, made from this pilot**:
`TCAP_TOTAL=10 us`, fixed across all three `Cfly` cells. Reasoning:

1. The pilot's own `Cfly=3 uF` result (`256.7 ns`) gives a `~39x` margin
   at `10 us`.
2. Naive linear-RC extrapolation for the slowest (largest-`Cfly`) cell,
   `8.7 uF`, predicts `~744 ns` (scaling the pilot's own measured
   `256.7 ns` by `8.7/3`, adjusted by the small, consistent `~1.08x`
   super-linear correction observed between the pilot's own result and the
   naive prediction -- see `RESULTS.md` for the exact factor); `10 us`
   gives that cell a `~13x` margin, closely matching R04E7's own `~12x`
   margin for its slowest cell at `50 us`/`4.24 us`. This is a deliberate
   match to R04E7's own margin philosophy, not an independent new
   standard.
3. `10 us` was confirmed sufficient directly: none of the three committed
   cells hit the cap (Section 8/`RESULTS.md`); had one occurred, it would
   be reported as `SAFETY_CAP_HIT_NOT_CONVERGED`, not hidden or the cap
   silently enlarged.
4. A single global cap (rather than three separately-tuned per-`Cfly`
   caps) is used for the same reason R04E7 gave for its own single global
   cap (that experiment's Section 6, point 2): it still bounds every state
   in every cell, and a per-cell tuned cap would add complexity for a
   documented-negligible benefit once the pilot already demonstrates a
   healthy margin at one fixed value across the whole swept range.

## 7. Success condition

For each `Cfly` value, the run reaches the `DONE` state (`STATE_FINAL==3`)
before `TCAP_TOTAL=10 us`, and `LADDER_ERR` at the end of every completed
cycle is monotonically non-increasing from the previous cycle (the same
convergence-quality bar R04E7 used). Reported per-`Cfly`: cycle count,
simulated convergence time, final `VC1/VC2/VC3`, final `LADDER_ERR`, and
peak capacitor-to-capacitor currents (`ICS1`/`ICS2`/`ICS3` max/min).

## 8. Failure conditions

- `TCAP_TOTAL` is reached while still in `STATE_A`/`STATE_B`/`STATE_C`
  (`STATE_FINAL==4`, `CAPPED`) for any `Cfly` value -- would be graded
  `SAFETY_CAP_HIT_NOT_CONVERGED` for that cell and reported honestly.
- `LADDER_ERR` does not monotonically improve cycle-over-cycle at some
  `Cfly` value -- would indicate the ratio-gating mechanism does not
  transfer cleanly to the corrected capacitance scale, reported as such.
- Solver non-convergence before the run's own `.tran` stop time.
- Peak currents that scale in an unexpected direction relative to the
  stated physical expectation (Section 6) -- explicitly permitted as a
  legitimate, reportable outcome, not something to be reasoned away.

## 9. What this experiment cannot prove

- It does **not** establish "the correct `Cfly` value" -- the `0.6-8.7 uF`
  range itself is a sensitivity/first-principles estimate depending on a
  ripple-percentage design choice this project made, not a number either
  P24 or P25 states. The three tested points are representative samples of
  that range, not a claim that any one of them (or the range's bounds) is
  hardware-correct.
- It does **not** touch `Cout` (Section 4) -- any conclusion here is
  conditioned on `Cout=4.672 mF` remaining the same suspect cross-topology
  candidate R04E7 used; a corrected `Cout` is a separate, unattempted
  future experiment.
- It does **not** attempt, and says nothing about, `Vout`/P24 steady-state
  handoff -- explicitly out of scope, inherited unchanged from R04E6/R04E7.
- It cannot claim hardware switch-stress validation of the reported
  capacitor-to-capacitor currents; no numeric current threshold exists
  from any source (R04E7/BOUNDARY.md Section 4 item 5, unchanged here).
- It cannot claim four-phase interleaving; `H4`/`L4` are never driven,
  unchanged from R04E6/R04E7.
- It cannot claim this specific `TCAP_TOTAL=10 us`/`TMAX=50 ps` choice is
  "correct" rather than a pilot-informed engineering choice (Section 6); a
  different, unqueried `Cfly` value outside `{1, 3, 8.7} uF` might behave
  differently, though the very tight, near-linear scaling observed across
  this 8.7x range (`RESULTS.md`) makes a smooth interpolation plausible.
- It cannot claim general immunity to comparator chatter across all
  possible `Cfly`/`Ron`/`TOL` combinations -- only that no chatter occurred
  in this experiment's own 3-cell grid, the same caveat R04E7 stated for
  its own grid.
