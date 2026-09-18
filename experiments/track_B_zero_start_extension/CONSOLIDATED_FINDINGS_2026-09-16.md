# Track B zero-start: consolidated findings across R04E9-R04E20 and the
   2026-09-16/17/18 literature review (written 2026-09-16, updated
   2026-09-18 after R04E16-R04E20)

## Why this document exists

`R04E9` through `R04E20` and two literature reviews were produced across
three consecutive working sessions, each individually documented
(`BOUNDARY.md`/`RESULTS.md` per experiment, two review notes under
`paper_locked/00_boundaries/`). This document does not add new results;
it synthesizes what is already committed into one coherent picture, and
was written only after re-checking every carried-forward number/assumption
against its original source (see "Boundary re-audit" below). Read the
individual `BOUNDARY.md`/`RESULTS.md` files for full detail and caveats --
this is a map, not a replacement. (`R04E15` was added as a same-day
follow-up on 2026-09-16 per explicit user direction to pursue R04E14's own
refinement before the higher-setup-cost Roberts soft-start mechanism;
`R04E16` and `R04E17` were added on 2026-09-17, building and then
causally isolating that soft-start mechanism; `R04E18` (Tramp-boundary
localization), `R04E19` (Cfly sensitivity), and `R04E20` (testing a
charge-conservation law derived by a separate, parallel math-model effort
in this same repository) were added across 2026-09-17/18, all per
explicit user direction at each step.)

## The problem, restated

Zero-start has two parts: (1) bootstrap the flying-capacitor ladder from
0 V to `36/24/12 V`, and (2) bootstrap `Vout` and hand off safely to the
existing strict steady-state controller. This session's work is entirely
about part (1) plus, for R04E9-R04E13, a combined attempt at both parts
at once via one mechanism. No experiment in this session builds or tests
the actual handoff into the steady-state controller.

## Three live approaches, and where each one stands

### Approach 1: active, inductor-mediated charging with admission-order tricks (R04E9-R04E13)

- **R04E9**: replaced EPE2019's switch-only ladder mechanism (which needed
  4.2-4.6 kA peak currents, R04E6-E8) with P24's own native inductor-
  mediated charging path. Peak currents dropped to plausible levels
  (<61 A) but the mechanism stalls permanently at phase 2 in all 9 tested
  cells (0 rotations ever complete) because `CHARGE_k` had no timeout
  fallback.
- **R04E10**: added a timeout fallback, symmetric with the existing
  freewheel timer. 6/9 cells now complete 4-17 rotations with `Vout`
  rising monotonically, but no cell reaches handoff (best cell 1.4-5.5%
  of target), and two new problems appeared: a retry/chatter dynamic that
  makes `T_CHARGE_MAX=5 ns` stall completely (reproducing R04E9's own
  failure), and a solver artifact inflating `ICS1-3` (flying-capacitor
  branch current) readings up to ~500 kA -- not physical, confirmed by
  `IL1-4` staying bounded and by the raw-trace fingerprint (identical
  timestamps, non-integer state values).
- **R04E11** (diagnostic only): root-caused the retry/chatter dynamic by
  direct raw-trace instrumentation. Two plausible internal-logic causes
  (a race between the two reset-gate booleans; the reset switches'
  zero-hysteresis comparators) were both directly tested and refuted. The
  actual cause is the raw `.machine` state variable itself sweeping
  backward through several state-code boundaries during a genuinely
  stiff, sub-picosecond-timestep solver episode -- a limitation of
  LTspice's own event resolution in this regime, not a defect in this
  project's constructed logic. No fix was found or forced (Ground Rule
  7); R04E10's grid remains the authoritative record.
- **R04E12** (option (c), phase 1): let phase 1 repeat its own
  charge/free cycle `N_PRECHARGE` times before ever admitting phase 2.
  `Vout` improved monotonically (+40% at `N=20`), but `VC2` improved
  non-monotonically (best at `N=3` and `N=20`, worse at `N=5`), and the
  best-`VC2` cell (`N=20`) introduced a new trade-off: the only negative
  `VC3` value in the whole grid.
- **R04E13** (option (c), phase 2 stacked on phase 1's): generalizing the
  same gate to phase 2 was net-negative -- `Vout` worse at every tested
  value, because the extra admission stage costs 2 completed rotations
  within the fixed observation window, and that lost rotation budget is
  worth more than the extra front-loaded charge.

**Verdict on this whole approach**: the underlying mechanism (inductor-
mediated, current-limited charging) is physically plausible on current
magnitude but fundamentally rate-limited -- R04E10's own Section 10 found
it converges far slower per cycle than the switch-only mechanism it
replaced. R04E12/R04E13 show that reordering admission (option (c)) has
hit diminishing and then negative returns; further tuning within this
same construct family is unlikely to close the ~95%+ remaining gap to
handoff. This does not mean the mechanism is wrong -- it means admission-
order tuning alone is not the remaining lever.

### Approach 2: passive divider precharge, isolated from PWM (R02A/B, redone as R04E14)

- **R02A/B** (pre-existing, `paper_locked/02_ectc2024_main`) tested an
  IPEC-2018-style passive input-divider-plus-diode network using the
  since-corrected `Cfly=53.8 uF`, and found it badly undercharges
  (`FAILED_CAPACITANCE_TRANSFER`, best case only 34/22/11 V at 150 A peak
  current).
- **R04E14** re-ran the SAME unmodified circuit with `Cfly` corrected to
  this project's own `3 uF` first-principles candidate (and `CDIV`
  re-scaled to match). Result: **the verdict reverses**. 2 of 14 cells
  (`CDIV=100/300 uF`, `TRAMP=100 us`) reach a ladder error 4.4x better
  than R02A's own best passive result, at 6.5x lower peak current
  (16-39 A vs. 150-257 A) -- using a much smaller, more plausible divider
  capacitance than R02B ever needed. Graded `PASS_TOPOLOGY_PRINCIPLE /
  NOT_P24_REPRODUCTION` (not a uniform pass: fast-ramp cells still spike
  to 500-2500 A, and the answer is sensitive to exactly which `Cfly` in
  the `0.6-8.7 uF` range is used).
- **R04E15** (fine-grid follow-up on R04E14, per explicit user direction
  2026-09-16) mapped the neighborhood around R04E14's two PASS cells more
  finely: `CDIV` refined/extended to `500 uF` (ladder error keeps
  improving monotonically, no plateau yet -- `0.0335` at `500 uF` vs.
  `0.0536` at R04E14's own `300 uF`, at a still-safe `61.44 A` peak
  current), `TRAMP` refined between `10` and `100 us` (confirms R04E14's
  own `100 us` sits at or very near a genuine local trade-off frontier
  between ladder error and peak current -- no intermediate value strictly
  beats it), and critically, the `Cfly` robustness check was REDONE at the
  actual winning operating point (`CDIV=500 uF`/`TRAMP=100 us`) rather
  than R04E14's own secondary grid's `TRAMP=10 us` point. **At this
  correct operating point, all three `Cfly` values across the full
  `0.6-8.7 uF` range pass BOTH halves of the bar cleanly** (peak current
  stays `60-64 A` regardless of `Cfly`) -- a materially more robust result
  than R04E14's own secondary check, which had failed the current bar at
  every `Cfly` value because it was run at the wrong `TRAMP`. `12/13`
  fine-grid cells now pass (vs. R04E14's own `2/14`), simply because this
  grid was deliberately centered on an already-good neighborhood, not
  because the underlying physics changed.

**Verdict on this approach**: genuinely revived by the `Cfly` correction,
and R04E15 shows the result is not a fragile, single-lucky-cell artifact
-- it holds across a widened operating-point neighborhood and across the
entire first-principles `Cfly` range when tested at the correct `TRAMP`.
This is currently the single most successful and best-substantiated
zero-start-adjacent result in this project's history by ladder-error/
peak-current combination, but it remains isolated from PWM (see "What
remains blocked" below) and only addresses part (1) of the zero-start
problem (the flying-capacitor ladder), not `Vout`/handoff.

### Approach 3: input-voltage soft-start ramp (built, tested, and causally
   isolated -- R04E16/R04E17, 2026-09-17)

- The Roberts & Prodić 2024 OJPEL paper P25 cites for phase-activation
  modulation (PHACTS/star-sequencing) does **not** address start-up at
  all -- full-text-confirmed; it is a steady-state, `N>=5`-only
  conversion-ratio-extension technique, explicitly stating it provides
  zero benefit for this project's own `N=4` case.
- Roberts' PhD dissertation (obtained separately), Chapter 3 Section 3.5
  "Converter Start-Up," describes a THIRD, different mechanism from
  Approaches 1/2 above: ramp `Vin` itself slowly through an eFuse
  (bandwidth kept well below the flying-capacitor LC resonance, per an
  explicit design rule using the same chapter's own `N`-inductor
  resonance formula) while the converter's normal multiphase switching
  pattern runs unchanged. `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`
  applied this formula to P24's own `LOCKED` operating point (validated
  first against Roberts' own worked example, reproducing his stated
  `65.7 kHz` resonance to printed precision), giving a P24-specific
  candidate ramp-time range of `~31-117 us` depending on `Cfly`.
- **R04E16** built and ran this mechanism for the first time: R03A's own
  fixed-timing, non-event-gated four-phase PWM (explicitly NOT R04E9-
  R04E13's admission-order machine, and NOT a repeat of R04E5's already-
  falsified "ramp grafted onto the strict event-gated controller"
  combination), with `TSTART=0` and R02B's passive-divider network
  REMOVED entirely, `Vin` ramped per the derived candidate range. Across
  a `6`-cell grid (`Cfly` in `{0.6,3,8.7} uF`, margin factor in
  `{10x,30x,100x}`, plus a near-instantaneous-ramp control cell), NONE
  showed R03A's own catastrophic runaway -- but the control cell (fast
  ramp) ALSO avoided it, undermining a clean "the ramp is what saved it"
  claim (BOUNDARY.md's own Section 10 had explicitly anticipated this
  possible outcome). A secondary, genuine finding survived: peak current
  decreases monotonically with margin factor (`150.07 -> 111.59 -> 86.94
  -> 75.05 A` at `10x/30x/50x-equivalent/100x`), so the ramp does have a
  real, confirmed effect on transient MAGNITUDE even when it does not
  determine whether runaway occurs.
- **R04E17** resolved the ambiguity R04E16 left open with a `2x2`
  factorial crossing `{divider present, divider absent}` x `{fast ramp,
  slow ramp}`, reusing R04E16's own two divider-absent cells and adding
  two new divider-present cells (R03A's own divider wiring, reintroduced
  at R04E15's own corrected `CDIV=300 uF`/`Cfly=3 uF`, not the old
  cross-topology `1.076 mF`/`53.8 uF`). **Result: the clean pattern
  occurred.** With the divider physically present, a fast ramp (`Tramp=
  1 us`) reproduces R03A's own runaway (`813-1046 A` across all four
  phases, the same order of magnitude as R03A's original `563-884 A`),
  while a `68.61x`-slower ramp avoids it entirely (`141-155 A`). This
  cleanly isolates the two factors R04E16 could not: **the `Vin` ramp
  causally matters specifically when there is a precharged-ladder/cold-
  `Vout` mismatch (the divider's own doing) for it to protect against; if
  that mismatch is removed some other way (R04E16's own divider deletion),
  the ramp's protective role becomes moot, not wrong.** R04E16 and R04E17
  are a coherent, non-contradictory pair, not two conflicting results.
- A further, unplanned positive finding from R04E17: with the divider
  reintroduced, BOTH ramp speeds reach `LADDER_ERR` around `0.024-0.029`
  and `Vout_final` within `0.6%` of target -- `46-56x` better than either
  of R04E16's own divider-absent cells. The divider's own precharge work
  is not merely "safe if the ramp is slow enough," it is actively more
  effective than the ramp-only mechanism at achieving the ladder/output
  target, provided the ramp is slow enough not to trigger runaway.
- **R04E18** located the runaway/safe `Tramp` boundary (at `Cfly=3 uF`,
  divider present) to a narrow `5-22.87 us` sub-interval -- `5-6x`
  narrower than R04E17's own untested `1-68.61 us` gap. The complete
  5-point `max{|IL1-4|}` sequence (`1046/652/205/170/155 A` at
  `Tramp=1/5/22.87/40/68.61 us`) is smoothly monotonic-decreasing, not a
  sharp cliff -- the `+/-250 A` engineering bound simply happens to be
  crossed within that sub-interval. `LADDER_ERR`/`Vout_final` stay
  essentially flat across the whole range; only the transient peak
  magnitude varies with `Tramp`.
- **R04E19** tested whether this boundary scales with `Cfly` the way the
  underlying `1/√Cfly` resonance-frequency law predicts, holding
  `CDIV=300 uF` fixed. **The result did not confirm the simple
  prediction cleanly.** At `Cfly=0.6 uF`, the fast `Tramp=5 us` point
  (unsafe at `Cfly=3 uF`) remained unsafe on ALL FOUR phases -- one
  phase (`1022 A`) actually WORSE than the `Cfly=3 uF` reference
  (`652 A`), the opposite of "smaller `Cfly` = safer." At `Cfly=8.7 uF`,
  the previously-safe `Tramp=22.87 us` point DID become unsafe (2 of 4
  phases), consistent with "larger `Cfly` needs more margin." Both
  `30x`-margin model-recommended cells were only marginally or partially
  safe, not comfortably so. A NEW finding not seen at `Cfly=3 uF`: real
  PER-PHASE asymmetry (a `2.2x` spread across phases at the same
  `Cfly`/`Tramp`), unexplained. Separately, `Cfly=8.7 uF` reached
  `LADDER_ERR=0.00947` -- the best value anywhere in this project's
  Track-B lineage to date, independent of the current-safety question.
  `BOUNDARY.md`'s own pre-run caveat (added by the delegated agent
  before running anything) already flagged that holding `CDIV` fixed
  while varying `Cfly` cannot isolate the pure resonance law from the
  simultaneously-changing `CDIV/Cfly` charge-sharing ratio -- exactly
  what R04E20 (below) went on to investigate directly.
- **A parallel, independently-developed effort** in this same repository
  (`results/ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md`, backed by a
  hybrid-DAE solver in `src/scb_ivr/zero_start_descriptor.py`/
  `zero_start_hybrid_solver.py` -- built and maintained separately from
  this Track-B SPICE lineage, not touched or modified by it) derived,
  from first principles, a simple charge-conservation explanation for
  R04E18's own boundary: the four `CDIV` divider capacitors present a
  `CDIV/4` series equivalent to `Vin`, so a linear ramp demands an
  unavoidable `Idiv=(CDIV/4)*Vin/Tramp`. Solved for the `+/-250 A`
  screen, this predicts `Tramp_threshold=CDIV*Vin/(4*250A)` -- `14.4 us`
  at `CDIV=300 uF`, matching R04E18's own `5-22.87 us` bracket. Their
  own 10-period hybrid-DAE solve at this exact operating point
  independently produced `170.7 A` input current, closely matching
  R04E18's own SPICE `IIN_PK=173.98 A` at the same point -- a genuine
  cross-validation between two completely independent methods.
- **R04E20** tested this law prospectively, holding `Cfly=3 uF` FIXED
  (directly addressing R04E19's own attribution confound by varying the
  actually-hypothesized mechanism, `CDIV`/`Tramp`, instead of `Cfly`) at
  two new `CDIV` values (`100 uF`, `500 uF`), each bracketed at `0.5x`/
  `2x` its own law-predicted threshold. **The result is genuinely mixed,
  not a clean confirmation.** At `CDIV=100 uF`: the `0.5x` point matched
  dramatically (all four phases far over `250 A`), but the `2x` point
  did NOT match -- still unsafe on all four phases (`261-332 A`),
  directly contradicting the law's own prediction. At `CDIV=500 uF`: the
  `0.5x` point matched only marginally (just one of four phases barely
  over `250 A`), and the `2x` point matched cleanly (all four phases
  comfortably safe, `143-155 A`). **Conclusion: the law's qualitative
  DIRECTION (larger `CDIV` needs more `Tramp` margin) holds across this
  `5x` `CDIV` range, but the specific threshold FORMULA is not an
  accurate quantitative predictor away from `CDIV=300 uF`** -- it fails
  outright at the low end. A plausible but explicitly unverified
  hypothesis (a roughly `CDIV`-independent switching-stage current term
  becoming proportionally more significant as `CDIV` shrinks) is offered
  without being claimed as established. All four R04E20 cells show the
  same phase-SYMMETRIC pattern R04E17/R04E18 found (unlike R04E19's own
  phase-asymmetric `Cfly`-sweep result) -- the asymmetry appears to be
  specific to varying `Cfly`, not `CDIV`.

**Verdict on this approach**: this is now the best-substantiated, most
CAUSALLY CLEAR positive result in the entire Track-B zero-start lineage,
though the picture has grown MORE textured (not less) as R04E18-R04E20
mapped it more finely. R04E16+R04E17 established a real, causally
confirmed protective mechanism (Roberts' own dissertation idea) that
combines productively with Approach 2's own passive divider (better
ladder/`Vout` accuracy than either mechanism alone) -- both `Vout` and
the flying-capacitor ladder bootstrap together in the best R04E17 cell
(`Vout_final=1.006 V`, within `0.6%` of target), the first time in this
project's Track-B history that BOTH halves of the zero-start problem
have reached anywhere close to target simultaneously, in one mechanism.
R04E18 shows this safety margin is a smooth, gradual function of `Tramp`,
not a fragile knife-edge. But R04E19 shows the picture is NOT simply
"more margin is always better, scaling predictably with `Cfly`" -- there
is genuine, unexplained per-phase asymmetry away from `Cfly=3 uF`, and
neither the `1/√Cfly` resonance law (R04E19) nor the simpler `CDIV`
charge-conservation law (R04E20, independently derived by the parallel
math-model effort) is a fully accurate quantitative predictor on its
own, though the charge-conservation law does capture the qualitative
direction reliably and explains R04E18's own `CDIV=300 uF` result
closely. This remains `SENSITIVITY_ONLY`/`CROSS_PAPER_EXTENSION`
throughout, and still does not build or test the handoff into the
strict steady-state controller (see "What remains blocked" below) -- but
as a start-up mechanism in isolation, it remains the strongest,
best-characterized result this project has produced, now with an
honest, textured picture of where its simple predictive models break
down rather than a falsely clean one.

## What remains blocked regardless of which approach is pursued further

`paper_locked/02_ectc2024_main/STEP_06_R02_LITERATURE_STARTUP_MODULE.md`'s
own "Next hard gate - PWM takeover" explicitly blocks combining ANY
precharge/start-up module with the P24 switching stage until a literature-
grounded four-phase release/handoff sequence is reviewed. That review
(`paper_locked/00_boundaries/ROBERTS_PRODIC_2024_LITERATURE_REVIEW.md`)
is now complete, with a **negative** finding: no paper in this project's
currently-reviewed source set (P24, P25, EPE2019, IPEC 2018, APEC 2016,
Roberts & Prodić 2024) supplies an explicit four-phase zero-energy
release sequence. Consequently, this gate is not "passed" -- it is
resolved into a standing requirement that **any future precharge-to-PWM
handoff experiment must use an explicitly self-labelled engineering
hypothesis** (`NUMERICAL_IDEALIZATION`/`CROSS_PAPER_EXTENSION`), never a
claimed literature-derived rule. R04E9-R04E14 already follow this
discipline for their own admission-order constructs; it must continue.

## Boundary re-audit performed 2026-09-16 (per explicit request) -- result: no error found

Checked directly against source, not from memory:

1. `CFLY=3 uF`'s provenance: confirmed R04E8's own `BOUNDARY.md` justifies
   it as a deliberately-chosen "representative mid point" of the
   `CFLY_FIRST_PRINCIPLES_ESTIMATE.md` range, and R04E8's own `RESULTS.md`
   found the ratio-gated mechanism is Cfly-scale-invariant across
   `{1,3,8.7} uF` (`LADDER_ERR` within `0.0442-0.0448` regardless) --
   so picking the middle value for R04E9-R04E14 is a defensible,
   correctly-labelled choice, not an arbitrary or silently-drifted one.
2. `COUT=4.672 mF`'s "still-unconfirmed cross-topology candidate, NOT
   corrected" flag: confirmed present and worded consistently in every
   one of R04E9/R04E10/R04E11/R04E12/R04E13's own `BOUNDARY.md` (R04E14's
   precharge-only circuit correctly has no `Cout` at all, since R02A/B's
   own module never included an output stage).
3. `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own arithmetic re-derived by hand
   (`dQ=62.5 A * 16.667 ns=1.0417 uC`; `C=dQ/(V*ripple%)` for each of
   `C1=36V`/`C3=12V` at `1%`/`5%`): every table value matches to the
   printed precision.
4. Every R02A/R02B number quoted in R04E14's `RESULTS.md` (voltages,
   `LADDER_ERR`, peak currents, for both R02A's Step 1/2 and R02B's own
   12-cell table) checked directly against
   `STEP_06_R02_LITERATURE_STARTUP_MODULE.md`'s own text: exact match,
   zero transcription errors found.
5. `paper_locked/00_boundaries/EXPERIMENT_REGISTRY.md`: confirmed one row
   exists for every experiment `R04E5` through `R04E14`, none missing.
6. `CURRENT_ASSUMPTION_CROSSCHECK.md`: contains no stale claim about
   R02A/B's old verdict that R04E14 would have made outdated (it does not
   reference R02A/B numbers at all, so no update was needed there).
7. The Roberts dissertation quotes in
   `ROBERTS_PRODIC_2024_LITERATURE_REVIEW.md` were extracted directly
   from the source PDF's own text layer (not summarized from memory or a
   secondary source) and re-checked against the saved extraction before
   being written into that document.

No numeric or provenance error was found in this pass. This is reported
as a genuine (clean) audit outcome, not a formality -- the check was
performed, not assumed.

## Verification performed on R04E16/R04E17 (2026-09-17, at merge time)

Each R04E16/R04E17 result was independently checked against its own raw
`.log` `.meas` output (not just the delegated agent's own summary) before
being merged into `main`, following the same discipline as the audit
above:

1. R04E16's own self-correction (an arithmetic slip claiming "`5.9x`
   below R03A's smallest peak" that did not reconcile with its own
   table) was independently re-derived by hand (`563.46/[each cell's own
   max current]`) and confirmed to match the corrected `3.75x-7.51x`
   range exactly.
2. R04E16's `results.csv`/`results.json` were confirmed to contain all 6
   grid rows (a prior revision's analysis script would have silently
   dropped the first 4 cells; this was caught and the fix verified).
3. R04E17's two new cells' `VC1-3_final`, `Vout_final/pk`, `IL1-4_max/
   min`, and `LADDER_ERR` were read directly from each cell's own `.log`
   and matched the committed `RESULTS.md`/`results.csv` exactly, including
   the `1046.42 A` runaway peak and the `0.0242`/`0.0291` `LADDER_ERR`
   values (hand-recomputed from `VC1-3_final` and confirmed).
4. R04E17's netlist was checked directly to confirm `CDIV=300 uF` (the
   corrected value) was actually used, not R03A's own `1.076 mF`.
5. R04E17's reuse of R04E16's own `e16_ctrl_f3_t1`/`e16_g1_f3_t68p61`
   numbers was checked against R04E16's own already-verified committed
   values -- copied verbatim, not silently altered.

No error was found in this pass either.

## Verification performed on R04E18/R04E19/R04E20 (2026-09-17/18, at
   merge time, and once directly by the orchestrating session itself)

Same discipline applied to each: independently checked against raw
`.log` `.meas` output (not just each delegated agent's own summary)
before merging into `main`:

1. R04E18's three new cells' `IL1-4_max/min`, `VC1-3_final`, and
   `LADDER_ERR` were read directly from each `.log` and matched the
   committed `results.csv` exactly; the `max(|IL_min|,IL_max)` sequence
   (`1046/652/205/170/155 A`) was independently recomputed and confirmed
   monotonic across all five points.
2. R04E19's fourth cell (`Cfly=8.7uF`/`Tramp=116.84us`) was run directly
   by the orchestrating session itself (not a subagent) after the user
   explicitly paused and later resumed the experiment across two worktree
   sessions; its `LADDER_ERR=0.00947` claim was hand-recomputed from
   `VC1-3_final` and confirmed. A first analysis pass's own error (using
   `IL_max` alone instead of the correct `max(|IL_min|,IL_max)`, which
   understated one cell's hazard) was caught and corrected before this
   document's own text was written, not silently inherited.
3. R04E20's four new cells were checked in real time, cell by cell, as
   each completed (not only at final merge) -- every `max(|IL_min|,
   IL_max)` value quoted in this document's own Approach-3 section was
   independently read from each cell's raw `.log` before the delegated
   agent's own final write-up was trusted, including the two cells that
   contradicted the tested law's own prediction (not silently smoothed
   over).

No error was found in this pass either. The parallel math-model effort's
own audit document and derived numbers (Section "Approach 3", the
charge-conservation-law paragraph) were read directly from
`results/ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md` and
`results/ZERO_START_TEN_PERIOD_CONVERGENCE.md` -- quoted, not
paraphrased from memory -- but that effort's own underlying Python code
(`src/scb_ivr/zero_start_descriptor.py`/`zero_start_hybrid_solver.py`)
was not independently re-verified by this session, since it is a
separate track maintained by a different effort; only the numbers this
document explicitly quotes from their own published `results/*.md` files
were checked for faithful transcription.

## Recommended priority ranking for what to pursue next (updated after
   R04E20)

The three lowest-cost items from the previous ranking (localize the
`Tramp` boundary, test `Cfly` sensitivity, test the parallel math-model's
own charge-conservation law) are now DONE (R04E18/R04E19/R04E20) --
each produced a genuinely informative, honestly-reported result, though
none resolved into a single clean quantitative model. What remains:

1. **Deeper characterization of WHY the simple predictive models break
   down is now higher-cost, lower-marginal-value SPICE work** -- R04E19's
   own unexplained per-phase asymmetry and R04E20's own unexplained
   `CDIV=100uF` breakdown are both real open questions, but each would
   need a new round of targeted cells (and, given this session's own
   observed `20-45`-minute-per-cell real LTspice runtime, non-trivial
   wall-clock cost) to investigate further via SPICE alone. **The
   parallel math-model effort's own hybrid-DAE solver is now a
   genuinely faster, complementary tool for this specific kind of
   question** (its own 10-period solve took seconds, not the `~20-45`
   minutes a single new SPICE cell requires) -- coordinating with that
   effort (e.g. handing over this session's own raw per-phase current
   traces for their solver to attempt reproducing) is a lower-SPICE-cost
   way to keep making progress on the "why" question than further
   bracketing sweeps in LTspice alone.
2. **Reconciling the ground-referenced-vs-floating flying-capacitor
   simplification that still applies to the DIVIDER's own connection**
   (R02A's own simplification, inherited unchanged through R04E14-R04E20)
   remains open and untouched by any of R04E18-R04E20.
3. **Beginning the precharge-to-PWM handoff design into the strict
   steady-state controller** remains the single biggest unstarted
   structural step -- both halves of zero-start (ladder and `Vout`) are
   close to target simultaneously in R04E17's own best cell, and R04E18
   confirms this holds with real margin (not a fragile knife-edge) across
   a usable `Tramp` range, making this well-motivated rather than
   premature. Any such handoff design must still use the self-labelled-
   engineering-hypothesis discipline described above (no literature
   source supplies a four-phase release sequence) -- unchanged by
   anything found in R04E18-R04E20.
4. **Further tuning of the R04E9-R04E13 admission-order family remains
   the lowest-priority thread**, unchanged from the previous ranking --
   the combined divider+ramp mechanism continues to outperform it on
   every axis.

This ranking is a recommendation, not a decision -- next step selection
remains the user's call, consistent with this project's standing
practice.

## R04E21-R04E25: minimal-scope phase-1 handoff test into R04E3's
   controller (added 2026-09-18, per explicit user direction to test
   "only whether phase 1 can avoid R04E3's stall point")

This is a separate, narrower thread from R04E9-R04E20 above: instead of
testing zero-start bootstrap mechanisms, it feeds R04E17's own best
bootstrapped phase-1 state (`VC1=35.86 V`, `IL1=75.97 A`, extracted from
`e17_div_f3_t68p61`) into `R04E3`'s own pre-existing single-phase-isolated
event-driven state machine (`paper_locked/02_ectc2024_main/spice/
R04E3_P24_minimal_zero_start_event_cycle.cir`) to see whether a realistic
starting current/voltage, rather than true zero energy, lets that
machine's own documented ZVS stall be avoided. Phases 2-4 stay hardcoded
at R04E3's own zero-energy configuration throughout -- this is NOT a
four-phase handoff test.

- **R04E21**: the bootstrapped state alone does not avoid the stall --
  same permanent parking at state `COMMUTATE_HIGH_TO_ZVS` R04E3/R04E5
  already documented from zero energy.
- **R04E22**: diagnosed cause -- R04E3's own `I_LIMIT=10 A`/`I_NEG=0.2 A`
  are leftover true-zero-energy-era values, mismatched to the bootstrapped
  state's much larger (`~76 A`) scale. Rescaling to P24's own real
  `I_LIMIT=125 A` and testing two established `NEG_FRAC` values (`2%`,
  `7.77%`) turned out inconclusive: neither cell's own `I_NEG` target was
  reached within the inherited `TSTOP=20 us`.
- **R04E23**: extending `TSTOP` to `100 us` revealed why -- `IL1` does not
  keep ramping negative, it peaks at `-2.215 A` near `t=2.82 us` then
  relaxes back toward zero. Neither original target (`2.5 A`, `9.7125 A`)
  is reachable at all from this bootstrapped state; TSTOP was never the
  limiting factor.
- **R04E24**: using a reachable target (`I_NEG=2.0 A`, `NEG_FRAC=1.6%`)
  let the machine progress for the first time in this chain -- state 3
  exits into state 4 (`COMMUTATE_HIGH_TO_ZVS`). But state 4 also stalls:
  the resonant ring there only pulls `V(vin,xmod:a1)` down to `9.66 V`,
  nowhere near the `<=0 V` ZVS threshold.
- **R04E25**: sweeping `I_NEG` across the full reachable range
  (`0.5-2.15 A`, plus R04E24's `2.0 A` point) shows the ring's closest
  approach to `0 V` scales almost exactly linearly with `I_NEG`
  (`R^2=0.99999998`). Extrapolating, reaching `0 V` would need
  `I_NEG~=10.6 A` -- about `4.78x` above the `~2.215 A` ceiling this
  bootstrapped state can naturally reach (R04E23). Every cell's current
  stayed within the `+/-250 A` safety bound; every `.raw` trace passed
  the solver-corruption fingerprint check; every number in this
  five-experiment chain was independently re-derived from raw `.log`/
  `.raw` data before merging, not merely trusted from agent summaries.

**Conclusion of this five-experiment chain**: for R04E17's specific
bootstrapped operating point, R04E3's phase-1 ZVS stall is not an
`I_LIMIT`/`I_NEG` tuning problem -- it is a genuine, quantified (`~4.78x`)
energy shortfall in the state-4 resonant commutation. Closing it would
need a circuit-level change (larger `LPHASE`, a different negative-
current-build mechanism, or additional stored energy from elsewhere),
which is a new design decision outside this experiment's own minimal
scope ("test only whether phase 1 can avoid the stall"), not a further
parameter sweep. This chain is intentionally stopped here per R04E25's
own boundary.

## Cross-check against the parallel math-model effort's newly-found
   periodic orbit (2026-09-18) -- an important, partially unresolved
   discrepancy

Independently, and on a different timeline from R04E21-R04E25, the
parallel math-model effort (`results/`, `src/scb_ivr/`) landed two new
results after this document's previous update: `ZERO_START_POST_RAMP_
POINCARE_AUDIT.md` (a 1000-period damped approach toward a candidate
periodic regime after the ramp) and `ZERO_START_AFFINE_PERIOD_FIXED_
POINT.md` (solving that regime's fixed point directly via a one-period
affine Poincare map). The latter reports a genuinely self-consistent
result for one 250 W module under their **ideal-switch, ideal-diode**
boundary: map residual `2.6e-11`, one-period closure error `2.3e-8`,
diode complementarity satisfied throughout -- this is the "single-module
already self-consistent" result.

**Its headline numbers**: `VC1/VC2/VC3 = 35.8448/23.8863/11.9278 V`,
`Vout=1.006 V`, average phase currents `~63 A`, phase-current **maxima**
`125.6-125.9 A`, phase-current **minima only `0.111` to `-0.214 A`**.

**The discrepancy worth flagging plainly**: this periodic orbit's own
natural per-phase current minimum (`~0.1-0.2 A` magnitude) is roughly
**50x smaller** than the `~10.6 A` R04E25 found would be needed to close
its own observed ZVS-ring gap, and is even smaller than the `2.0-2.15 A`
R04E24/R04E25 actually tested. Two explanations are both plausible and
have NOT been distinguished yet:

1. **The two models are testing genuinely different commutation
   mechanisms, not the same one at different operating points.** The
   affine-map result is an *ideal*-switch model -- switches transition
   instantaneously regardless of voltage, so it structurally cannot need
   or show a "ZVS gap" at all; its own document explicitly disclaims any
   hardware-ZVS claim ("cannot establish hardware ZVS...without the real
   device capacitance"). R04E3's own `.machine` construct, by contrast,
   models a *real* half-bridge resonant commutation that genuinely needs
   stored inductor energy to swing a real switching-node capacitance down
   to `0 V`. If this is the right explanation, the two results are not
   in tension -- they answer different questions -- but it also means
   R04E25's own `4.78x` shortfall says nothing about whether the real
   converter's *actual* periodic-orbit-adjacent ZVS transition would face
   a similar shortfall, since that transition's own real current minimum
   might naturally be much smaller than what R04E17's bootstrap state
   produces.
2. **Alternatively, R04E17's own zero-start bootstrap trajectory (used as
   the starting point for the entire R04E21-R04E25 chain) may simply not
   be representative of the true periodic orbit's own state at any
   comparable phase.** Some rough support for this: the math model's own
   end-of-`22.87 us`-ramp reference state (`ZERO_START_FULL_RAMP_
   REFERENCE.md`) has `VC1=34.27 V` (close to R04E17's `35.86 V`, but at
   a *different* `Tramp=22.87 us` vs R04E17's own `68.61 us`) alongside
   phase currents `IL1..IL4 ~= 161.7/197.6/73.6/95.8 A` -- individually
   much larger, and far less uniform across phases, than either the
   periodic orbit's own `~63 A` average or R04E17's single-phase `76 A`.
   No experiment in this project has yet bootstrapped R04E3's controller
   from a state actually confirmed to lie on or near this periodic orbit
   -- R04E17's own state was derived from a single-phase-only zero-
   energy SPICE ramp, not from this cross-track periodic solution.

**This is not yet resolved and should not be treated as resolved.**
Both explanations are consistent with everything committed so far; they
have different implications (the first says R04E21-R04E25's negative
result is scoped correctly and simply doesn't generalize; the second
says R04E21-R04E25 may have tested the wrong starting state entirely).
Distinguishing them would need either (a) confirming whether R04E3's own
`.machine` mechanism is even the right model of commutation near the true
periodic orbit, or (b) bootstrapping R04E3's controller from a state
actually taken from/near the affine-map periodic solution instead of
R04E17's zero-energy-ramp state, and rerunning an R04E24-style single
cell. This cross-check was performed by reading the parallel effort's own
already-published `results/*.md` files directly
(`ZERO_START_AFFINE_PERIOD_FIXED_POINT.md`, `ZERO_START_POST_
RAMP_POINCARE_AUDIT.md`, `ZERO_START_FULL_RAMP_REFERENCE.md`) -- quoted,
not paraphrased from memory -- but, consistent with this project's
standing practice, their underlying Python solver code was not
independently re-verified; only the numbers explicitly quoted here were
checked for faithful transcription against the source files.

## A49 (Track A): the larger, four-phase version of option (b) was
   attempted, and made things worse, not better (added 2026-09-18, per
   explicit user direction)

Per explicit user direction ("那就来吧 做好分类就行" -- proceed with the
larger option, keep the provenance classification rigorous), option (b)
above was attempted in its full four-phase form: the periodic orbit's own
state (flying-capacitor voltages at their period averages, phase 1's
current at its own period minimum -- physically motivated, since A37's
own construct samples `T0` exactly at phase 1's own post-commutation
instant -- phases 2-4's currents at their own period averages, the
weakest approximation here, explicitly flagged in advance) was fed into
`A37` (`experiments/track_A_periodic_steady_state/A37_p25_9pct_joint_
seven_state_200ns_periodic_solve/`), this project's own best prior
real-device, real-event-driven-dead-time four-phase periodic-seed
construct, as `experiments/track_A_periodic_steady_state/
A49_math_model_affine_periodic_seed_crosscheck/`.

**Result: worse than A37's own best optimizer-found candidate, not
comparable.** A37's own 174-point search found 3 of 15 residuals
converged with phase 1's own admission into phase 2 succeeding (though
H3/H4 never admitted). A49's imported seed converged only 1 of 15
residuals (a near-trivial `VC3` residual) and phase 1 never even admits
into phase 2 -- the state machine permanently stalls one step earlier
than A37's own stall point, at `t=106.65 ns` (state `P1_M5`, waiting on
phase 2's own `Vds<=0` event). Every number in this result was
independently re-derived from the raw `.raw` trace before merging
(state-transition timestamps, the `Vds(H2)` minimum of `0.252 V` at
`t=109.14 ns`, all four phase-current safety bounds, and the `DIL2`
residual), not merely trusted from the delegated agent's own summary.

**Direct mechanistic cause, confirmed from the raw trace, not inferred**:
phase 2's own imported current (`62.724 A`, its OWN period average) takes
until `t~=107 ns` just to decay down to its own negative-current
admission threshold (`-11.25 A`) -- by which point `V(a1,a2)` has already
passed its own natural closest approach to zero (`0.252 V` at `109.14
ns`) and is rising back up, so the timing never lines up. **This is a
direct, observed symptom of the exact approximation A49's own BOUNDARY.md
flagged in advance as its weakest assumption** (phases 2-4's own
period-average current substituting for their true instantaneous value at
`T0`) -- not necessarily evidence that the periodic orbit's own TRUE
instantaneous state (if it were available) would also fail this way. This
result should therefore be read narrowly: **it shows the specific
approximation used here performs worse than an arbitrary optimizer seed,
not that the underlying periodic orbit itself is physically incompatible
with real ZVS commutation.** It does not cleanly favor explanation 1 or 2
above -- resolving that still requires the true simultaneous four-phase
snapshot `MINIMUM_INFORMATION_REQUEST.md` Item 9 already asks for, which
remains unavailable from the parallel math-model effort's own published
outputs.
