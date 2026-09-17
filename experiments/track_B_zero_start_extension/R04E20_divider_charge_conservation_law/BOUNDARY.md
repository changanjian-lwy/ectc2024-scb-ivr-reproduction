# R04E20 - testing the divider charge-conservation law across `CDIV` (BOUNDARY)

## 1. Parent and why this experiment exists

A parallel, independently-developed analytical/numerical effort in this
same repository (`results/ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md`,
`results/ZERO_START_TEN_PERIOD_CONVERGENCE.md`, backed by
`src/scb_ivr/zero_start_descriptor.py`/`zero_start_hybrid_solver.py` --
a hybrid-DAE model of the SAME divider-present/Roberts-ramp/fixed-PWM
system this project's own R04E16-R04E19 built in SPICE) derived a
simple, falsifiable charge-conservation law from first principles: the
four equal `CDIV` divider capacitors present a `CDIV/4` series
equivalent to the input, so a linear `0-Vin` ramp of duration `Tramp`
demands an UNAVOIDABLE base charging current

```
Idiv = (CDIV/4) * Vin / Tramp
```

independent of `Cfly`. Solving for the `Tramp` at which this current
equals this project's own `+/-250 A` engineering screen gives

```
Tramp_threshold = CDIV * Vin / (4 * 250 A)
```

At `CDIV=300 uF` (this project's own standard value throughout
R04E17-R04E19), this predicts `Tramp_threshold=14.4 us` -- which the
audit document itself notes "falls inside the independently observed
LTspice transition bracket of `5-22.87 us`" (R04E18's own already-
committed result) and close to R04E18's own informal `~17.6 us` log-log
interpolation. **This is independent, analytically-derived corroboration
of an already-observed SPICE result, not yet a prospectively-tested
prediction at any OTHER `CDIV` value.**

This experiment tests the law prospectively: does
`Tramp_threshold=CDIV*Vin/(4*250A)` correctly predict the runaway/safe
crossing at `CDIV` values OTHER than `300 uF`, where no SPICE data yet
exists? This also directly addresses R04E19's own documented attribution
limit (holding `CDIV` fixed while varying `Cfly` could not isolate the
resonance law from the `CDIV/Cfly` ratio) by doing the reverse: holding
`Cfly` FIXED at its standard `3 uF` value and varying `CDIV`/`Tramp`
together, isolating the divider's own charge-demand mechanism cleanly.

Per explicit user direction 2026-09-17 (approving this as the most
valuable SPICE-side next step to support the parallel math-model effort).

## 2. What changed relative to R04E17/R04E18, exactly

**No mechanism or topology change.** Reuses R04E17/R04E18's own
byte-level-faithful netlist (R04E16's fixed-timing four-phase power
stage + R03A's divider network, `TSTART=0`, `LPHASE=1.4666667 nH`,
`Cfly=3 uF` FIXED throughout, `solver=alt cshunt=1e-15 plotwinsize=0`,
`TMAX=50 ps`) completely unchanged. Only `CDIV` and `Tramp` are swept
together, at values chosen to bracket the LAW's OWN predicted threshold
at each `CDIV` (Section 3), not an arbitrary grid.

## 3. Swept grid -- four new cells, plus two reused reference cells

| Cell | `CDIV` | Predicted threshold | `Tramp` tested | Prediction |
|---|---:|---:|---:|---|
| (reused) `e18_div_f3_t5` | `300 uF` | `14.4 us` | `5 us` (`0.35x`) | unsafe |
| (reused) `e18_div_f3_t22p87` | `300 uF` | `14.4 us` | `22.87 us` (`1.59x`) | safe |
| `e20_c100_t2p4` | `100 uF` | `4.8 us` | `2.4 us` (`0.5x`) | unsafe |
| `e20_c100_t9p6` | `100 uF` | `4.8 us` | `9.6 us` (`2x`) | safe |
| `e20_c500_t12` | `500 uF` | `24 us` | `12 us` (`0.5x`) | unsafe |
| `e20_c500_t48` | `500 uF` | `24 us` | `48 us` (`2x`) | safe |

The two `CDIV=300 uF` cells are REUSED BY REFERENCE from R04E18's own
already-committed results (not re-run) -- they already happen to bracket
their own predicted threshold (`5 us < 14.4 us < 22.87 us`) and already
confirm the predicted direction at this one `CDIV` value. The four NEW
cells extend this same bracketing test to two OTHER `CDIV` values
(`100 uF`, a `3x` smaller divider; `500 uF`, a `1.67x` larger one),
each tested at `0.5x` and `2x` its own law-predicted threshold -- a
genuine prospective test, not a re-confirmation of an already-known
point. `TSTOP=Tramp+300 us` per new cell, matching this track's own
convention.

## 4. What did not change

Everything else, copied byte-for-byte from R04E17/R04E18's own
netlists: four-phase power-stage connectivity, `TSTART=0` fixed-timing
gate B-sources, `LPHASE=1.4666667 nH`, `Cfly=3 uF` (FIXED, not swept --
the key difference from R04E19), `COUT=4.672 mF`, `RLOAD=Vout^2/Pout`,
ideal `SWI` switch model, `RLDAMP=1u`, true-zero-energy IC (`UIC`),
`TMAX=50 ps`, `solver=alt cshunt=1e-15 plotwinsize=0`, R03A's own
divider-network topology (`CIN1-4`/`RLEAK1-4`/`DPC1-3`, `IPEC2018
LPAR=5n`/`RPAR=10m`, `RLEAK=1G`, ideal diode model).

## 5. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| The charge-conservation law itself (`Idiv=(CDIV/4)*Vin/Tramp`, `Tramp_threshold=CDIV*Vin/(4*Ilimit)`) | `results/ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md`'s own first-principles derivation (a parallel, independently-developed effort in this repository) | `CROSS_PAPER_EXTENSION`-adjacent engineering derivation; NOT a P24/P25 value, an analytical consequence of the divider topology this project's own R02A/R03A already carry |
| `CDIV=100 uF`, `500 uF` | New for this experiment: chosen to bracket the law's own predicted threshold, one below and one above R04E17-R04E19's own standard `300 uF` | `SENSITIVITY_ONLY` |
| `Tramp=2.4/9.6/12/48 us` | New for this experiment: `0.5x`/`2x` the law's own predicted threshold at each new `CDIV`, not independently chosen | derived from the tested law, `SENSITIVITY_ONLY` |
| `Cfly=3 uF` (fixed, not swept) | R04E8's own corrected middle value, held fixed here specifically to avoid R04E19's own documented `Cfly`/`CDIV-ratio` attribution confound | `SENSITIVITY_ONLY`, inherited |
| Everything else | See R04E17/R04E18 `BOUNDARY.md` for original provenance | unchanged |

No new paper-sourced, cross-paper, or external-device data is
introduced. The `250 A` screen itself remains this project's own
engineering choice (`CURRENT_ASSUMPTION_CROSSCHECK.md`'s own already-
documented status), not a P24/P25 value.

## 6. What question this experiment is meant to answer

Does the simple charge-conservation law `Tramp_threshold=CDIV*Vin/
(4*250A)`, derived independently from first principles by the parallel
math-model effort and already found consistent with ONE existing SPICE
data point (`CDIV=300uF`), correctly predict the runaway/safe direction
at TWO OTHER `CDIV` values it was not fitted to? If so, this is strong
evidence the divider's own charge demand -- not the flying-capacitor
resonance frequency `1/√Cfly` R04E19 tested -- is the first-order driver
of this boundary, explaining why R04E19's own Cfly-only sweep (with
`CDIV` held fixed) produced a confusing, non-monotonic, per-phase-
asymmetric result: it was not varying the dominant mechanism.

## 7. Success/failure conditions

Every outcome is informative, per this project's own Ground Rule 7:

- If all four new cells match their own prediction (`0.5x` unsafe, `2x`
  safe, at BOTH new `CDIV` values): strong, prospective confirmation of
  the charge-conservation law across a `5x` `CDIV` range, and a direct,
  well-supported explanation for R04E19's own confusing result.
- If the law's direction holds at one new `CDIV` but not the other: a
  genuinely informative partial result, localizing where the simple law
  breaks down (e.g. possibly at very small `CDIV`, where switching-stage
  dynamics might dominate over pure divider charge demand) -- report
  plainly, do not force a uniform verdict.
- If the law fails at both new `CDIV` values: the `CDIV=300uF`
  agreement was likely coincidental or the law needs a correction term
  (e.g. the audit document's own noted `8.5%` gap between the pure
  charge-conservation estimate and the actual solved/simulated current) --
  reported as a genuine negative finding, valuable for redirecting the
  parallel math-model effort's own next steps.
- Note "safe"/"unsafe" is judged the same way as R04E17-R04E19: whether
  ANY phase's `max(|IL_min|,IL_max)` exceeds `250 A` (the corrected
  per-phase measure R04E19 established, not `IL_max` alone).

## 8. What this experiment cannot prove

- It does not test `CDIV` values beyond `{100, 300, 500} uF`, nor
  `Cfly` values other than `3 uF` -- a claim that the law holds
  universally across the full parameter space is not established by
  four bracketing points at two new `CDIV` values.
- It does not explain the per-phase asymmetry R04E19 found (some phases
  exceed `250A`, others do not, at the same cell) -- the charge-
  conservation law predicts a single scalar `Idiv`, not a per-phase
  breakdown; if this experiment's own cells also show per-phase
  asymmetry, that remains a separate, unexplained phenomenon.
- It does not validate the parallel math-model effort's own hybrid-DAE
  solver beyond the single already-published cross-check point
  (`CDIV=300uF`/`Tramp=22.87us`) -- extending that cross-validation to
  these new cells is a natural follow-up but not performed here (this
  experiment produces SPICE data only; comparing it against the other
  effort's own solver output, if desired, is a separate task for
  whoever maintains that codebase).
- It does not modify, overwrite, or invalidate R04E16/R04E17/R04E18/
  R04E19's own committed results -- the two `CDIV=300uF` cells are
  reused here strictly by citation.
- It does not modify, read from, or depend on anything under
  `src/scb_ivr/` or `results/` (the parallel math-model effort's own
  work area) -- this experiment's own scope is entirely within
  `experiments/track_B_zero_start_extension/`, consistent with this
  project's own established boundary discipline of not touching another
  track's files.
- A P24 reproduction claim of any kind remains out of scope, the same
  standing Track-B limitation as every other experiment in this lineage.
