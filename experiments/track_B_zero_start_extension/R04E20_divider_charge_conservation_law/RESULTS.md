# R04E20 result - testing the divider charge-conservation law across `CDIV`

## 1. Outcome, stated first

**The charge-conservation law's qualitative DIRECTION (larger `CDIV`
needs a longer `Tramp` for the same margin) is broadly supported across
the tested range, but the specific `0.5x`/`2x`-of-predicted-threshold
bracketing test was NOT uniformly successful at either new `CDIV` value
-- this is a genuinely mixed result, reported plainly rather than forced
into "confirmed" or "refuted," per `BOUNDARY.md` Section 7's own explicit
anticipation of this possibility.**

Using the corrected per-phase hazard measure `max(|IL_min|,IL_max)`
(R04E19's own Section 3 correction -- checking only `IL_max` understates
hazard for phases whose largest excursion is negative) across all six
rows (four new cells plus the two `CDIV=300uF` cells reused by reference
from R04E18):

- `e20_c100_t2p4` (`CDIV=100uF`, `Tramp=2.4us`, `0.5x` the `4.8us`
  predicted threshold, predicted **unsafe**): **confirmed, dramatically**
  -- all four phases far exceed `250A` (`851/884/855/942A`).
- `e20_c100_t9p6` (`CDIV=100uF`, `Tramp=9.6us`, `2x` the `4.8us`
  predicted threshold, predicted **safe**): **NOT confirmed** -- all four
  phases still exceed `250A` (`332/288/261/309A`). The law's own
  prediction fails outright at this point.
- `e20_c500_t12` (`CDIV=500uF`, `Tramp=12us`, `0.5x` the `24us` predicted
  threshold, predicted **unsafe**): **weakly/marginally confirmed** --
  only one of four phases (`IL4`) exceeds `250A` (`237/248/237/318A`;
  `IL2` is close, `248.0A`, but does not itself cross the bound). Far
  less dramatic than the `CDIV=100uF` unsafe case.
- `e20_c500_t48` (`CDIV=500uF`, `Tramp=48us`, `2x` the `24us` predicted
  threshold, predicted **safe**): **confirmed cleanly** -- all four
  phases comfortably safe (`149/155/144/143A`).

So of the four new cells, two match their own prediction cleanly
(`e20_c100_t2p4`, `e20_c500_t48`), one matches only marginally
(`e20_c500_t12`, unsafe by a single phase, barely), and one fails the
prediction outright (`e20_c100_t9p6`, still unsafe on all four phases at
`2x` the predicted threshold). Combined with the two already-known
`CDIV=300uF` reference points (both of which matched cleanly, reused by
citation, not re-run here), **the simple first-order charge-conservation
law `Tramp_threshold=CDIV*Vin/(4*250A)` is directionally useful but not
sufficient on its own to precisely predict the runaway/safe boundary at
`CDIV` values away from `300uF`** -- see Section 4 for what the pattern
of failure suggests, without overclaiming an explanation not directly
verified here.

## 2. Cells run and their history

All four new cells were run strictly one at a time on real LTspice
(never concurrently, per R04E16's own documented `~20x` concurrent-run
throughput collapse on this machine), each confirmed complete via its
own `.log` `Total elapsed time` line before the next was launched, in
the exact order specified by `BOUNDARY.md`:

| Cell | `Total elapsed time` (s) | Wall-clock (min) |
|---|---:|---:|
| `e20_c100_t2p4` | `1263.475` | `21.1` |
| `e20_c100_t9p6` | `1189.768` | `19.8` |
| `e20_c500_t12` | `1371.986` | `22.9` |
| `e20_c500_t48` | `1606.826` | `26.8` |

Total new-cell wall-clock: `5432.06s` (`~90.5` minutes) across the four
cells, consistent with this netlist family's documented `1179-2525s`
range (`R04E16` `RESULTS.md` Section 3b). The two `CDIV=300uF` cells
(`e18_div_f3_t5`: `1179.814s`; `e18_div_f3_t22p87`: `1341.366s`) are
reused strictly by reference from R04E18's own already-committed
results, not re-run here.

## 3. Complete 6-row table

All values are the CORRECTED per-phase hazard measure
`max(|IL_min|,IL_max)`, not `IL_max` alone (R04E19's own Section 3
finding: for several rows here, e.g. `e20_c100_t2p4`'s own `IL1`, the
most extreme excursion is on the negative side -- `IL1_min=-680.5A` vs
`IL1_max=851.3A` -- so the correct hazard value, `851.3A`, is the `MAX`
side here, but this is not guaranteed in general and must be checked
per phase, per cell). `Cfly=3uF` fixed throughout; sorted by `CDIV` then
`Tramp`.

| Cell | `CDIV` (uF) | `Tramp` (us) | Predicted threshold (us) | Predicted direction | IL1 hazard (A) | IL2 hazard (A) | IL3 hazard (A) | IL4 hazard (A) | Any phase `>250A`? | Actual direction | Matched? |
|---|---:|---:|---:|---|---:|---:|---:|---:|---|---|---|
| `e20_c100_t2p4` | `100` | `2.4` | `4.8` | unsafe | `851.34` | `884.45` | `855.34` | `942.32` | ALL FOUR | unsafe | **YES** |
| `e20_c100_t9p6` | `100` | `9.6` | `4.8` | safe | `332.41` | `287.88` | `260.57` | `309.09` | ALL FOUR | unsafe | **NO** |
| (reused) `e18_div_f3_t5` | `300` | `5.0` | `14.4` | unsafe | `472.70` | `508.64` | `505.85` | `651.55` | ALL FOUR | unsafe | YES |
| (reused) `e18_div_f3_t22p87` | `300` | `22.87` | `14.4` | safe | `203.21` | `205.07` | `179.72` | `168.73` | none | safe | YES |
| `e20_c500_t12` | `500` | `12.0` | `24.0` | unsafe | `237.21` | `247.96` | `237.10` | `318.07` | IL4 only | unsafe | YES (marginal) |
| `e20_c500_t48` | `500` | `48.0` | `24.0` | safe | `149.47` | `154.78` | `143.99` | `142.92` | none | safe | YES |

`VC1/VC2/VC3_final` and `Vout_final` (all four new cells, directly from
each `.log`):

| Cell | `VC1_final` (V) | `VC2_final` (V) | `VC3_final` (V) | `Vout_final` (V) | `LADDER_ERR` |
|---|---:|---:|---:|---:|---:|
| `e20_c100_t2p4` | `35.7747` | `23.8093` | `11.8724` | `1.00625` | `0.02484` |
| `e20_c100_t9p6` | `35.7499` | `23.7690` | `11.8113` | `1.00615` | `0.03230` |
| `e20_c500_t12` | `35.7404` | `23.8259` | `11.8679` | `1.00596` | `0.02547` |
| `e20_c500_t48` | `35.7519` | `23.7759` | `11.8289` | `1.00572` | `0.03049` |

All four reach `Vout_final` within `0.63%` of the `1V` target and
`LADDER_ERR` in the tight `0.0248-0.0323` range -- essentially
`Tramp`/`CDIV`-insensitive within this grid, consistent with R04E17/
R04E18's own finding (ramp speed and `CDIV` affect the transient's peak
current, not the divider's own end-state charging accuracy).

## 4. Does the law hold? A genuinely mixed answer, localized as far as this data allows

- **At `CDIV=100uF` (the smaller new value), the law fails at its own
  `2x`-margin point.** `Tramp=2.4us` (`0.5x` threshold) is unsafe as
  predicted, dramatically so. But `Tramp=9.6us` (`2x` threshold) is
  STILL unsafe on all four phases, not merely marginally -- `332/288/
  261/309A`, all comfortably above `250A`. The true runaway/safe
  crossing at `CDIV=100uF` is somewhere beyond `9.6us`, at LEAST `2x`
  further out than the pure charge-conservation law predicts (possibly
  much further -- this experiment does not test a third, larger `Tramp`
  point at `CDIV=100uF` to localize it, per `BOUNDARY.md`'s own 4-cell
  scope).
- **At `CDIV=500uF` (the larger new value), the law's direction holds at
  both tested points, but the "unsafe" point is only marginally over the
  bound.** `Tramp=12us` (`0.5x` threshold) has only one of four phases
  (`IL4=318.07A`) over `250A`; the other three (`237.2/248.0/237.1A`)
  are under, with `IL2` close but not over. This is a qualitatively
  correct but much weaker "unsafe" signal than either `CDIV=100uF`'s own
  unsafe cell or R04E18's own `CDIV=300uF` unsafe cell (`e18_div_f3_t5`,
  all four phases well over `250A`). `Tramp=48us` (`2x` threshold) is
  comfortably, uniformly safe (`149-155A`), a clean confirmation.
- **The already-known `CDIV=300uF` points (reused, not re-run) matched
  cleanly on both sides** -- but these are the SAME points the law was
  originally checked against before this experiment (`BOUNDARY.md`
  Section 1's own framing: "independent, analytically-derived
  corroboration of an already-observed SPICE result, not yet a
  prospectively-tested prediction"), so they carry less weight as a test
  of the law than the four genuinely new points.
- **A plausible, but NOT independently verified, pattern in the
  mismatches**: the law under-predicts the required margin more severely
  at the SMALLER `CDIV` (`100uF`, where `2x` the predicted threshold is
  still badly unsafe) than at the LARGER `CDIV` (`500uF`, where `0.5x`
  the predicted threshold is only marginally unsafe). One candidate
  explanation, consistent with but not proven by this data: if some
  part of the peak transient current has a component that does NOT
  scale down with `CDIV` (e.g. a roughly fixed switching-stage
  charging/inrush contribution, independent of the divider's own charge
  demand), that fixed term would become proportionally MORE significant
  relative to the shrinking `Idiv=(CDIV/4)*Vin/Tramp` term as `CDIV`
  drops -- which would explain why the pure charge-conservation law
  (a single term, scaling linearly with `CDIV`) increasingly
  under-predicts the danger at smaller `CDIV`, while doing comparatively
  better at larger `CDIV` where the divider term dominates. This
  experiment's own 4-cell design cannot confirm or rule out this
  specific mechanism (it would require, at minimum, a third `CDIV=100uF`
  point well beyond `9.6us` to see whether the actual crossing point is
  merely shifted or the whole functional form is wrong, and a direct
  measurement of the non-divider current contribution) -- offered here
  as a plausible next hypothesis for the parallel math-model effort, not
  as an established finding.
- **This does directly address the question BOUNDARY.md Section 6 asked
  about R04E19's own confusing per-phase-asymmetric result**: unlike
  R04E19 (where `CDIV` was held fixed and `Cfly` varied, producing
  genuinely per-phase-asymmetric, non-monotonic results), all six rows
  here show the SAME phase-symmetric pattern R04E17/R04E18 already
  established at `CDIV=300uF` -- when a cell is unsafe, it tends to be
  unsafe on most or all phases together (`e20_c100_t2p4`,
  `e20_c100_t9p6`, `e18_div_f3_t5`: all four phases), with `e20_c500_t12`
  the only partial exception (`3` of `4` phases still under, `1` over).
  This is consistent with the divider's own charge demand (varied here)
  being a more phase-symmetric driver than the flying-capacitor
  resonance mechanism R04E19 tested (varied there) -- supporting, though
  not proving beyond this data, BOUNDARY.md Section 6's own hypothesis
  that the divider's charge demand, not the `1/sqrt(Cfly)` resonance, is
  the first-order, more phase-uniform driver of this boundary.

## 5. Solver-corruption fingerprint check (all four new cells)

Per this project's own standing discipline (R04E16-R04E19), all four new
cells' raw `.raw` binary traces were directly, byte-level parsed in full
(`scripts/ltspice_raw_parser.py`, unchanged from R04E11-R04E19's own
committed parser; `scripts/check_fingerprint.py`, copied unchanged from
R04E19's own script) and checked for the documented two-part corruption
signature: non-monotonic/duplicate timestamps, and the independent,
state-independent `V(vin)` PWL source reading a value implausible for
its own commanded `0-48V` ramp.

| Cell | Points parsed | `dt<=0` count | `V(vin)` range (V) | Max deviation from rail |
|---|---:|---:|---|---:|
| `e20_c100_t2p4` | `6,656,296` | `0` | `[0.0, 50.29]` | `2.29V` (`4.77%`) |
| `e20_c100_t9p6` | `6,919,342` | `0` | `[0.0, 48.60]` | `0.60V` (`1.25%`) |
| `e20_c500_t12` | `6,964,803` | `0` | `[0.0, 48.03]` | `0.03V` (`0.06%`) |
| `e20_c500_t48` | `7,769,253` | `0` | `[0.0, 47.96]` | `0.0V` (`0%`, never exceeds rail) |

**Zero non-monotonic timestamps and zero implausible `V(vin)` values in
any of the four cells.** The largest observed deviation (`e20_c100_t2p4`,
`4.77%` overshoot) is a small, physically explicable ringing artifact
from the `RPAR_IN`/`LPAR_IN`/divider-capacitance filter (this cell has
the fastest `Tramp` and largest divider-charging transient of the four,
so more ringing is expected), many orders of magnitude below the
documented corruption signature (R04E16's own `-20885V`/`5.33e24V`).
**The solver-corruption fingerprint is absent from all four cells; the
large currents reported in Section 1/3 are confirmed real, not numerical
artifacts.**

## 6. What this does and does not establish

**Established:**
- The charge-conservation law's qualitative direction (larger `CDIV`
  needs proportionally more `Tramp` margin for the same current bound)
  is supported at both new `CDIV` values tested, in the sense that the
  `0.5x`-threshold cell is always worse (more phases/margin over `250A`)
  than the `2x`-threshold cell at the same `CDIV`.
- The law's SPECIFIC threshold value (`Tramp_threshold=CDIV*Vin/
  (4*250A)`) is NOT confirmed as an accurate predictor at `CDIV=100uF`
  -- `2x` that threshold remains unsafe on all four phases, a clear
  quantitative failure of the simple formula at this `CDIV`.
- At `CDIV=500uF`, the law's threshold is qualitatively closer to
  correct but the `0.5x` point is only marginally unsafe (`1` of `4`
  phases), suggesting the true threshold at this `CDIV` may be close to,
  perhaps even below, `12us` -- narrower than a clean `0.5x`/`2x`
  bracket would suggest.
- All four new cells' raw traces are confirmed free of the documented
  solver-corruption fingerprint (Section 5).
- All six rows (new and reused) show the same phase-symmetric pattern
  (when unsafe, usually unsafe on most/all phases together), unlike
  R04E19's own `Cfly`-sweep result, consistent with (not proof of) the
  divider-charge-demand mechanism being the more phase-uniform driver.

**NOT established:**
- The exact location of the runaway/safe crossing at `CDIV=100uF`
  (known only to be beyond `9.6us`) or at `CDIV=500uF` (known only to be
  between `12us` and `48us`, and likely closer to `12us` given how
  marginal that cell's own single-phase excess is) -- this 4-cell design
  brackets but does not localize either crossing precisely.
- Any specific correction term or improved functional form for the
  charge-conservation law -- Section 4's "fixed non-divider current
  contribution" hypothesis is offered as a plausible explanation for the
  observed pattern, not as a verified mechanism; testing it would
  require additional cells and/or a direct current-component breakdown
  not performed here.
- `CDIV` values beyond `{100, 300, 500}uF`, or `Cfly` values other than
  `3uF` -- the same explicit scope limit `BOUNDARY.md` Section 8 already
  states.
- Why `e20_c500_t12` shows a partial (`1` of `4` phases) rather than
  uniform crossing, while every other unsafe cell in this experiment and
  its R04E17/R04E18 predecessors shows all four phases together -- a
  new, small-scale asymmetry noted here but not diagnosed further.
- Any modification, overwrite, or invalidation of R04E16/R04E17/R04E18/
  R04E19's own committed results -- the two `CDIV=300uF` cells are
  reused here strictly by citation.
- Any cross-validation of the parallel math-model effort's own
  hybrid-DAE solver against these four new SPICE points -- this
  experiment produces SPICE data only, per `BOUNDARY.md` Section 8.
- A P24 reproduction claim of any kind -- the same standing Track-B
  limitation as every other experiment in this lineage.

## 7. Provenance and classification

| Value | Source | Category |
|---|---|---|
| The charge-conservation law itself (`Idiv=(CDIV/4)*Vin/Tramp`,
  `Tramp_threshold=CDIV*Vin/(4*Ilimit)`) | `results/
  ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md`'s own first-principles
  derivation (a parallel, independently-developed effort in this
  repository) | `CROSS_PAPER_EXTENSION`-adjacent engineering derivation;
  NOT a P24/P25 value |
| `CDIV=100uF`, `500uF` | New for this experiment: chosen to bracket the
  law's own predicted threshold, one below and one above R04E17-R04E19's
  own standard `300uF` | `SENSITIVITY_ONLY` |
| `Tramp=2.4/9.6/12/48us` | New for this experiment: `0.5x`/`2x` the
  law's own predicted threshold at each new `CDIV` | derived from the
  tested law, `SENSITIVITY_ONLY` |
| `Cfly=3uF` (fixed, not swept) | R04E8's own corrected middle value,
  held fixed here specifically to avoid R04E19's own documented
  `Cfly`/`CDIV`-ratio attribution confound | `SENSITIVITY_ONLY`,
  inherited |
| `CDIV=300uF` cells (reused) | R04E18's own already-committed
  `e18_div_f3_t5`/`e18_div_f3_t22p87` results, reused by citation, not
  re-run | inherited |
| Everything else | See R04E17/R04E18 `BOUNDARY.md` for original
  provenance | unchanged |

No new paper-sourced, cross-paper, or external-device data is
introduced. Classification, following this track's own established
language: **`SENSITIVITY_ONLY` / `NOT_P24_REPRODUCTION`** -- a
mechanism-sensitivity finding about this project's own Track-B
constructs, not a claim about P24's own reported behavior. Per
`BOUNDARY.md` Section 7, this is reported as a genuinely mixed,
partially-confirming/partially-disconfirming result across the two new
`CDIV` values, not forced into either a clean "law confirmed" or "law
refuted" verdict.

## 8. Files

- `cases/e20_c100_t2p4.cir`, `cases/e20_c100_t9p6.cir`,
  `cases/e20_c500_t12.cir`, `cases/e20_c500_t48.cir` -- the four new
  netlists (`.log`/`.raw` gitignored per this project's convention).
- `scripts/ltspice_raw_parser.py`, `scripts/check_fingerprint.py` --
  copied unchanged from R04E19's own committed scripts.
- `scripts/analyze_r04e20.py` -- new for this experiment: parses the
  four new cells' `.log` measurements, merges in R04E18's own two
  reused `CDIV=300uF` cells by reference (read from R04E18's own
  committed `results.json`, not re-run), computes the corrected
  per-phase `max(|IL_min|,IL_max)` hazard measure and predicted-vs-
  actual direction columns for all six rows, and writes
  `results.csv`/`results.json`.
- `results.csv`/`results.json` -- the complete 6-row table, including
  `reused_by_reference` (`true` for the two R04E18 rows), per-phase
  `il{1-4}_hazard`/`il{1-4}_over_250` columns using the corrected
  `max(|min|,max)` definition, and `predicted_threshold_us`/
  `predicted_direction`/`actual_direction`/`prediction_matched` columns.
