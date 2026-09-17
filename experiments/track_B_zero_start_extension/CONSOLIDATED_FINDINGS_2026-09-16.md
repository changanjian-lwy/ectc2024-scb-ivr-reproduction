# Track B zero-start: consolidated findings across R04E9-R04E17 and the
   2026-09-16/17 literature review (written 2026-09-16, updated 2026-09-17
   after R04E16/R04E17)

## Why this document exists

`R04E9` through `R04E17` and two literature reviews were produced across
two consecutive working sessions, each individually documented
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
causally isolating that soft-start mechanism, per further explicit user
direction.)

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

**Verdict on this approach**: this is now the best-substantiated, most
CAUSALLY CLEAR positive result in the entire Track-B zero-start lineage.
Unlike Approach 1 (admission-order tuning, diminishing/negative returns)
and unlike Approach 2 in isolation (ladder-only, no `Vout`/handoff
story), R04E16+R04E17 together show a real protective mechanism
(Roberts' own dissertation idea) with a directly confirmed causal role,
AND demonstrate it combines productively with Approach 2's own passive
divider (better ladder/`Vout` accuracy than either mechanism alone).
Both `Vout` and the flying-capacitor ladder bootstrap together in the
best R04E17 cell (`Vout_final=1.006 V`, within `0.6%` of target) --
the first time in this project's Track-B history that BOTH halves of the
zero-start problem (ladder AND `Vout`) have reached anywhere close to
target simultaneously, in one mechanism. This remains `SENSITIVITY_ONLY`/
`CROSS_PAPER_EXTENSION` (only two `Tramp` points and one `Cfly` value
tested in R04E17; the `Cfly`/`Tramp` boundary between runaway and safe
operation is not mapped), and still does not build or test the handoff
into the strict steady-state controller (see "What remains blocked"
below) -- but as a start-up mechanism in isolation, it is the strongest
result this project has produced.

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

## Recommended priority ranking for what to pursue next (updated after R04E17)

1. **The combined mechanism (R02B/R04E14/R04E15's corrected passive
   divider + Roberts' soft-start ramp, causally confirmed by R04E17) is
   now the clear leading candidate and the most promising open thread.**
   Concrete, well-motivated next steps for THIS combined mechanism, in
   rough order of cost:
   (a) map the actual runaway/safe boundary in `Tramp` (only `1 us` and
   `68.61 us` are tested; a bisection between them would locate the real
   threshold, which R04E17 itself flags as untested);
   (b) test whether the boundary shifts with `Cfly` (R04E17 tested only
   `Cfly=3 uF` with the divider present);
   (c) reconcile the ground-referenced-vs-floating flying-capacitor
   question that still applies to the DIVIDER's own connection (R02A's
   own simplification, inherited unchanged through R04E14/R04E15/R04E17);
   (d) begin the precharge-to-PWM handoff design into the strict
   steady-state controller -- both halves of zero-start (ladder and
   `Vout`) are now close to target simultaneously in R04E17's own best
   cell, making this the first point in the project where attempting the
   actual handoff is well-motivated rather than premature. Any such
   handoff design must still use the self-labelled-engineering-hypothesis
   discipline described above (no literature source supplies a four-phase
   release sequence).
2. **Further tuning of the R04E9-R04E13 admission-order family remains
   the lowest-priority thread** -- not because it was wrong, but because
   R04E12/R04E13 already showed it has entered diminishing/negative
   returns, and the combined mechanism above now clearly outperforms it
   on every axis (ladder error, `Vout` accuracy, current plausibility,
   and causal clarity); a topology-level change (R04E9's own option (a),
   still unstarted) would need to precede any further work in this
   specific family, and even then would need to be weighed against
   simply extending the now-leading combined mechanism instead.

This ranking is a recommendation, not a decision -- next step selection
remains the user's call, consistent with this project's standing
practice.
