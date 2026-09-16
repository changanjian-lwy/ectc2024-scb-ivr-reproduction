# Track B zero-start: consolidated findings across R04E9-R04E14 and the
   2026-09-16 literature review (written 2026-09-16)

## Why this document exists

`R04E9` through `R04E14` and two literature reviews were all produced in
one working session, each individually documented (`BOUNDARY.md`/
`RESULTS.md` per experiment, two review notes under
`paper_locked/00_boundaries/`). This document does not add new results;
it synthesizes what is already committed into one coherent picture, and
was written only after re-checking every carried-forward number/assumption
against its original source (see "Boundary re-audit" below). Read the
individual `BOUNDARY.md`/`RESULTS.md` files for full detail and caveats --
this is a map, not a replacement.

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

**Verdict on this approach**: genuinely revived by the `Cfly` correction.
This is currently the single most successful zero-start-adjacent result
in this project's history by ladder-error/peak-current combination, but
it remains isolated from PWM (see "What remains blocked" below) and only
addresses part (1) of the zero-start problem (the flying-capacitor
ladder), not `Vout`/handoff.

### Approach 3: input-voltage soft-start ramp (found in literature, not yet built)

- The Roberts & Prodić 2024 OJPEL paper P25 cites for phase-activation
  modulation (PHACTS/star-sequencing) does **not** address start-up at
  all -- full-text-confirmed; it is a steady-state, `N>=5`-only
  conversion-ratio-extension technique, explicitly stating it provides
  zero benefit for this project's own `N=4` case.
- Roberts' PhD dissertation (obtained separately), Chapter 3 Section 3.5
  "Converter Start-Up," describes a THIRD, different mechanism from both
  approaches above: ramp `Vin` itself slowly through an eFuse (bandwidth
  kept well below the flying-capacitor LC resonance, per an explicit
  design rule using the same chapter's own `N`-inductor resonance
  formula) while the converter's normal multiphase switching pattern
  runs unchanged. The FCs are not independently precharged by any
  divider network -- they track `Vin` organically via the same charge-
  balance mechanism that holds them in steady state.

**Verdict on this approach**: a well-justified, primary-source-backed,
author-native candidate mechanism, but **not yet built or tested in this
project's own SPICE model**. The dissertation's own worked example
(2-inductor, 5 V) is illustrative, not a P24-specific number -- any future
experiment must derive P24's own ramp-rate target from the chapter's own
formula before testing, and must be labelled `CROSS_PAPER_EXTENSION`
(applying Roberts' general method to an operating point he did not
himself work out numerically).

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

## Recommended priority ranking for what to pursue next

1. **R04E14's passive-precharge success is the most promising open
   thread with the clearest next step**: it already has a well-defined,
   narrow follow-up (does the `PASS_TOPOLOGY_PRINCIPLE` result hold up
   under a finer `(CDIV,TRAMP)` grid near the two winning cells, and does
   it remain robust across the full `Cfly` range rather than only at
   `3 uF`?) that does not require inventing anything new.
2. **Roberts' soft-start mechanism is the highest-novelty candidate** but
   requires first deriving P24-specific numbers from his Chapter 3
   formula before any SPICE test is meaningful -- more setup cost, but
   potentially addresses both ladder AND Vout bootstrap simultaneously
   (unlike R04E14, which only addresses the ladder), since it does not
   change the normal switching pattern.
3. **Further tuning of the R04E9-R04E13 admission-order family is the
   lowest-priority thread for now** -- not because it was wrong, but
   because R04E12/R04E13 already show it has entered diminishing/negative
   returns; a topology-level change (R04E9's own option (a), still
   unstarted) would need to precede any further work in this specific
   family.

This ranking is a recommendation, not a decision -- next step selection
remains the user's call, consistent with this project's standing
practice.
