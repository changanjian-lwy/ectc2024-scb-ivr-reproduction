# R04E9 - unified inductor-mediated four-phase bootstrap (BOUNDARY)

## 1. Parentage -- a synthesis, not a one-variable step

This experiment synthesizes and departs from the full R03/R04 zero-start
lineage. None of the parents below is a single "one-variable" parent in
the sense of `EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md` Section V; per
Section V's own escape clause, the explicit solve vector is named here.

- **R03A** (`paper_locked/02_ectc2024_main/STEP_07_R03_PRECHARGE_PWM_
  TAKEOVER.md`): fixed-clock PWM (no current limit) from a precharged
  ladder gets `Vout` rising, but current runs away to `884.36 A`
  (phase-current maxima `884.36/745.07/625.63/563.46 A`), because a fixed
  5 MHz period does not leave enough off-time while `Vout` is still low.
  Registry: `FAILED_FIXED_PWM_TAKEOVER / NUMERICALLY_COMPLETED`.
- **R03D** (same file; `paper_locked/02_ectc2024_main/spice/
  R03D_epe2019_duty_ramp_takeover.cir`): a gradual duty ramp (0 to the
  locked `Ton` over `TSOFT`) DOES get `Vout` up to ~1 V (`0.994-1.007 V`,
  the only prior success at reaching `Vout` in this whole track), but
  with no current limiting: phase currents swing `L1: -225.75 to 382.55
  A`, `L4: -268.49 to 390.96 A`. Registry: `PARTIAL_SUCCESS_OUTPUT /
  FAILED_CURRENT_BOUNDARY`.
- **R04E3** (`paper_locked/02_ectc2024_main/STEP_30_R04E3_ZERO_START_
  EVENT_CONTROLLER.md`): true-zero-energy start, strict event-driven
  `.machine`/`.state`/`.rule` controller. Correctly stalls because at
  `Vout~=0` the off-interval current-return slope is too shallow --
  `iL1=0` took `1.63145 us` vs the `200 ns` P24 target period, and
  current overshot the intended `10 A` limit, reaching `43.68 A`, during
  the stretched interval. Registry: `LOGIC_PASS;
  P24_ZERO_START_LOCAL_CYCLE_FAILS_BEFORE_T3`.
- **R04E4** (`paper_locked/02_ectc2024_main/STEP_31_R04E4_ZERO_START_
  GATEOFF_SWEEP.md`): swept the QH1 current-limit gate-off threshold
  (`0.1-10 A`); found the first turn-on impulse is Coss/LC-transient-
  dominated and the threshold sweep has no control authority over it
  (all seven thresholds hit the same physical peak, `14.19 A`, regardless
  of the commanded threshold). This experiment reuses R04E4's own
  validated current-limit turn-off RULE FORM (`I(Lk)>=I_LIMIT` as a
  physical-event state-transition trigger) unchanged, adapted to fire on
  each phase's own inductor current in turn -- it does not reinvent this
  mechanism.
- **R04E5** (`experiments/track_B_zero_start_extension/
  R04E5_ramped_duty_event_gated_zero_start/`): grafted R03D's ramped duty
  ceiling onto R04E3's strict controller. Confirmed the strict admission
  chain itself (not just fixed-time PWM) is the blocker: the machine
  never returns to a state where the ramp matters (parks permanently in
  state 4 waiting for a high-side `Vds=0` event that never occurs, in 9
  of 12 cells, or one stage earlier in the other 3, across `TSOFT` in
  `{50,100,200,500} us` and `I_LIMIT` in `{10,50,150} A`, tested to
  windows up to `600 us`). `README.md`'s "Lesson from R04E5" section is
  explicit: **"Do not re-attempt 'keep the strict full P24 admission
  chain, just add a ramp/timeout on top of it' as a zero-start fix -- this
  has now been tried and it cannot work by construction."** R04E9 obeys
  this: it does not graft anything onto R04E3's strict chain. It replaces
  the admission chain itself, for the bootstrap phase only, with a
  deliberately looser one (Section 2 below), exactly the kind of
  "genuinely different, deliberately looser admission rule for the
  bootstrap phase itself" that R04E5's own README lesson calls for.
- **R04E6/R04E7/R04E8** (`experiments/track_B_zero_start_extension/`):
  R04E6 tried EPE2019's borrowed switch-only charge-redistribution
  ladder (state (a) `H1+L1` alone charges `C1`, states (b)/(c) `H2+L1+L2`
  / `H3+L2+L3` redistribute charge switch-to-switch, with NO series
  inductance limiting `di/dt`) open-loop and found it drifts the wrong
  way with more cycles. R04E7 added voltage-ratio gating (a monitored
  stop condition per state) and got it to converge cleanly toward
  `36/24/12 V`. R04E8 re-ran R04E7's mechanism at a corrected `Cfly` and
  confirmed convergence quality is unaffected while peak
  capacitor-to-capacitor currents stay multi-kilo-amp regardless of
  `Cfly` (`ICS1_MAX` `4157.7-4566.9 A` across the whole `1-53.8 uF`
  range) -- a **structural** consequence of the switch-only,
  zero-dead-time, `Ron`-only idealized mechanism, not of `Cfly`. R04E9
  reuses ONLY the **conceptual shape** of R04E6/E7/E8 -- rotate through
  phases in a fixed truth-table order, monitor voltages, decide when to
  stop -- but replaces the underlying charging MECHANISM entirely: every
  phase's own series inductor `Lk` is now the current-limiting,
  charge-transferring, `Vout`-contributing element (P24's own Interval-1
  mechanism, Section 2), never a bare switch-to-switch capacitor path.
  This is the single most important departure this experiment makes from
  R04E6/E7/E8, and it is why R04E9's peak currents differ from theirs by
  roughly two orders of magnitude (Section "Comparison" in `RESULTS.md`).

## 2. The mechanism -- exact state machine

Full four-phase P24 power stage (topology/node names copied unchanged
from R04E3/R04E5/R04E8's `SCB4P_P24_*` subcircuits: `a1-a3`, `x1-x4`,
`CS1-3` flying caps, `CH1`/`CL1` device Coss, `L1-4`), but with **all
four phases actively commanded by the machine**, not one phase held
statically as R04E3/R04E5/R04E6/R04E7/R04E8 all did.

For phase `k` cycling `1->2->3->4->1...`, two states:

- **`CHARGE_k`**: `QHk` on (`gh(k)_cmd` driven high, all else for phase
  `k` low). Current rises through `Lk`, via the SAME series path P24's
  own Interval 1 uses (`PAPER_LOCKED_REPRODUCTION_BASELINE.md`: "`QH1`
  ... inductor `L1` charges through `Vin`, `QH1`, `C1`, and `Co`"),
  simultaneously charging `Ck` and contributing to `Vout` through the
  shared output rail. **Exit rule (reused unchanged from R04E3/R04E4):**
  `I(Lk)>=I_LIMIT`, a physical current-limit event, not a fixed time.
- **`FREE_k`**: `QLk` on. Current decays through `Lk`/`Ck`. **Exit rule
  (A48-style "event OR timeout, whichever first"):**
  `(I(Lk)<=0) | (V(timer)>=T_FREEWHEEL_MAX)`. The natural zero-crossing
  event is checked first in the OR (matching the project's Section VI
  physical-event-over-fixed-time preference wherever the natural event is
  fast enough); the timeout is the deliberately-added escape hatch for
  the case R04E3 already proved happens at zero start (natural
  zero-crossing taking `1.63 us`, far longer than the `200 ns` P24
  period).

One shared elapsed-time timer (`CTIMER`/`BTIMER_CHG`/`SRESET`, the same
construct R04E5 used for its own on-time ceiling, redirected here to time
FREEWHEEL duration instead of CHARGE duration) serves all four phases,
because only one state is ever active at a time: it charges only while
the machine is in ANY `FREE_k` state and resets through a low-`Ron`
switch the instant it enters ANY `CHARGE_k` state.

**Two bugs were found and fixed while building this timer** (see the
module docstring of `build_b05_r04e9_unified_inductor_mediated_bootstrap.py`
for the full diagnostic trail): (1) an early draft omitted the timer's
own storage capacitor entirely, so the timeout branch had no real
elapsed-time meaning; (2) even after adding the capacitor, the timer
counted DOWNWARD with a naive `+1p*(condition)` B-source current
coefficient (this simulator's `Bxxx n+ n- I=expr` convention sources
current OUT of `n+` for positive `expr`, the opposite of the naive
expectation) and so never crossed the positive `T_FREEWHEEL_MAX`
threshold at all -- every FREE state was silently resolving only via the
natural-event branch regardless of the commanded timeout, which produced
a first, WRONG pilot conclusion ("T_FREEWHEEL_MAX has no effect") that
was caught and discarded before any grid cell was committed. Fixed with
`I=-1p*(condition)`, confirmed directly against a diagnostic run
(`T_FREEWHEEL_MAX=50 ns` now fires the transition at `t=52.27 ns`,
matching the commanded value to the same small overshoot margin R04E3/
R04E4 already documented for their own turn-off event). **This same
latent sign issue may be present, unnoticed, in R04E5's own `ton_timer`
construct** -- R04E5's own results show its ramped-ceiling branch of the
OR-rule was never the one that actually fired in any of its 12 cells (the
current-limit branch always won the race), so R04E5 never exercised the
branch that would have exposed this. **Not fixed here** -- out of scope,
and `EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md` Section I rule 10 / this
project's ground rules prohibit editing another experiment's committed
files from inside this one. Flagged here for a future contributor.

Outputs: `gh(k)_cmd = VGATE*(state==CHARGE_k)`, `gl(k)_cmd =
VGATE*(state==FREE_k)` for `k=1..4`.

**Inactive-phase switch state, made explicit here (was not stated when this
file was first committed, added 2026-09-15 after direct review):** because
each phase's high/low gate is driven by exactly one `(state==...)`
comparison and never by an OR of multiple states, at any instant only the
single phase currently in `CHARGE_k` or `FREE_k` has a switch commanded on
-- every other phase's high AND low side are both off. This is a **third,
distinct choice**, not the same as either P24's undrawn inactive-low-side
connection or P25's explicit "all inactive low-sides on/freewheeling"
convention (`CURRENT_ASSUMPTION_CROSSCHECK.md`'s "Interleaving / event
timing" row; also central to A39/A44's findings in Track A). It is a
deliberate, defensible default *for the zero-start bootstrap phase
specifically*: there is no steady-state amp-second/charge-balance
freewheeling relationship to maintain yet at true zero energy, so leaving
uninvolved phases fully open avoids introducing an unanalyzed current path
this experiment never intended to study. **This choice is independent of,
and does not take a position on, the separate P24-vs-P25 steady-state
inactive-low-side question** -- that question only becomes meaningful once
multiple phases are genuinely interacting in periodic operation, which this
bootstrap-only experiment does not reach (no cell completes a full
rotation). Any future experiment that continues rotating past a full cycle,
or that attempts the handoff into steady-state control, must revisit this
choice explicitly rather than carrying it forward silently.

## 3. Handoff-condition monitor (measurement only -- not built/tested)

A continuously-evaluated behavioral observer (`handoff_flag`), high only
while ALL of the following hold simultaneously:

- `Vout` within `+/-5%` of `1 V` (`[0.95, 1.05] V`) -- same tolerance
  convention R04E5 already used for its own `Vout` target band.
- `VC1`, `VC2`, `VC3` each within `+/-2%` of `36/24/12 V` -- same
  tolerance convention R04E7/R04E8's own best-tested (tightest) tolerance.

`.meas tran T_HANDOFF WHEN V(handoff_flag)=2.5 RISE=1` records the first
time (if any) all conditions hold at once. Both tolerance bands are
SENSITIVITY_ONLY / engineering choices made for THIS experiment's own
measurement purpose, not paper values and not claimed as "correct."
Per the task's explicit instruction, this experiment does **not** build
or exercise the actual handoff into the existing strict event-gated
controller (the R04E3/R04E5 lineage) -- it only measures whether/when the
condition is reached and reports the full state vector at that moment (or
the closest approach, if never reached).

Per-rotation checkpoints (`rot_flag` = high during `FREE4`, `.meas ...
WHEN V(rot_flag)=2.5 FALL=j` for `j=1..8`) record `Vout`/`VC1`/`VC2`/
`VC3` at the end of each completed four-phase rotation, chosen (rather
than continuous polling) because a rotation boundary is a well-defined
physical event in this machine, matching R04E7/R04E8's own
per-cycle-boundary convention and this project's general preference for
event-anchored, not arbitrary-time, checkpoints.

## 4. Fixed values and their sourcing

| Value | Source | Category |
|---|---|---|
| `Vin=48 V`, `nP=4`, `nM=4` | P24 Table I / Sec. II-A | `P24_EXPLICIT` |
| Full four-phase P24 power-stage connectivity (`a1-a3`/`x1-x4`/`CS1-3`/`L1-4` node names, series `Lk` charging path) | Copied unchanged from R04E3/R04E5/R04E8's `SCB4P_P24_*` subcircuits; the charging path itself is P24's own Interval-1 mechanism per `PAPER_LOCKED_REPRODUCTION_BASELINE.md` | `P24_EXPLICIT` (topology) |
| `LPHASE=1.4666667 nH` | Eq.-4 branch, this project's Track-A mainline (same value R04E3-R04E8/A42-A48 all use) | `P24_EXPLICIT` (Eq.-4 branch) |
| GS61008T `CH`/`CL`/`RHS`/`RLS` (1 HS / 2 parallel LS) | GS61008T datasheet Rev 200402, unchanged from R04E3/R04E5 | `EXTERNAL_DEVICE_DATA` |
| `CFLY=3 uF` for `C1`/`C2`/`C3` | R04E8's own middle, first-principles-corrected value (`CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s `~0.6-8.7 uF` range), explicitly NOT R04E7's cross-topology-suspect `53.8 uF` (see `README.md`'s "Boundary-provenance gap" section and `CURRENT_ASSUMPTION_CROSSCHECK.md`'s "Flying capacitor" row) | first-principles-derived candidate (inherited from R04E8) |
| `COUT=4.672 mF` | EPE2019 Table I sum, the SAME still-unconfirmed cross-topology candidate flagged in `CURRENT_ASSUMPTION_CROSSCHECK.md`'s "Output capacitor value" row and `README.md`'s provenance-gap section -- **NOT corrected here**, same deliberate scope limit R04E8 declared for `Cout` (no load-transient spec exists yet to derive a first-principles value) | cross-topology candidate, flagged unconfirmed |
| `I_LIMIT` current-limit exit rule form | R04E3/R04E4's own validated rule (`I(Lk)>=I_LIMIT`), reused unchanged in form | inherited mechanism |
| `T_FREEWHEEL_MAX` event-OR-timeout exit pattern | A48's own "event OR timeout, whichever first" idea, redirected to a per-state elapsed-freewheel-time comparison via R04E5's own elapsed-time-timer circuit construct (bug-fixed here, Section 2) | inherited pattern, `NUMERICAL_IDEALIZATION` (the timer itself has no physical counterpart) |
| Handoff tolerance bands (`Vout +/-5%`, `VCk +/-2%`) | This experiment's own measurement convention, matching R04E5's and R04E7/R04E8's respective prior tolerance choices | `SENSITIVITY_ONLY` |
| `TSTOP=3 us`, `TMAX=50 ps` | Pilot-derived (Section 5) | numerical-resolution choice, not physical, not swept |

## 5. Swept grid and its justification

- `I_LIMIT` in `{10, 30, 60} A`: `10 A` is R04E3's own originally-attempted
  value; `30 A`/`60 A` extend into R04E4's own sweep range (which tested
  up to `10 A` for the FIRST pulse only) to see whether a higher
  commanded limit changes the LATER-phase behavior R04E4 never tested
  (R04E4 never looped past one pulse).
- `T_FREEWHEEL_MAX` in `{50, 200, 1000} ns`: all three are well below
  R04E3's own directly-measured `1.63 us` natural zero-crossing time at
  near-zero `Vout` -- the entire point of adding a timeout-based
  freewheel exit is to escape that specific, already-measured stall
  duration; testing values comparable to or above `1.63 us` would defeat
  the mechanism's own purpose.
- 9 cells (`3x3`), all run to a common, pilot-justified `TSTOP=3 us` /
  `TMAX=50 ps` (Section 6 of the module docstring in
  `build_b05_r04e9_unified_inductor_mediated_bootstrap.py`; also
  summarized in `RESULTS.md`).

## 6. Success condition

For a given `(I_LIMIT, T_FREEWHEEL_MAX)` cell: `T_HANDOFF` fires (the
handoff condition of Section 3 is reached) within `TSTOP`, AND no phase
current exceeds a safety bound of `+/-250 A` (the same `2x` P24 Eq.-2
peak-current safety margin R04E5 adopted) at any point in the run. Graded
`LOCAL_PASS` if both hold.

## 7. Failure conditions

- `CONTROLLER_GUARD_PASS`: the machine parks permanently in one state (or
  a repeating limited set of states) for the remainder of the run without
  chattering, diverging, or exceeding the current safety bound -- a safe
  refusal to proceed, reported honestly (matching R04E3's/R04E5's own
  convention for this exact kind of outcome).
- `PHYSICAL_BOUNDARY_FAIL`: any phase current exceeds `+/-250 A`.
- Solver non-convergence before `TSTOP` is its own outcome, reported as
  such, not retried with loosened tolerances.

## 8. What this experiment cannot prove

- It does **not** build or test the actual handoff into the existing
  strict event-gated steady-state controller (R04E3/R04E5 lineage) --
  explicitly out of scope per the task; it only measures whether/when the
  handoff CONDITION is reached.
- It does **not** establish that any tested `I_LIMIT` or `T_FREEWHEEL_MAX`
  value is "correct" -- both are declared sensitivity axes, not paper
  values or engineering recommendations.
- It does **not** validate hardware switch stress at the observed peak
  currents -- no numeric current threshold exists in any source (same
  caveat R04E6/R04E7/R04E8 already stated for their own peak currents).
- It does **not** correct or validate `Cout=4.672 mF` -- inherited
  unchanged from the whole R03A-R04E8 lineage, still flagged unconfirmed.
- A result here (positive or negative) is a single, specific
  `(I_LIMIT, T_FREEWHEEL_MAX, CFLY=3uF, COUT=4.672mF)` combination; it
  must never be read as a general statement about inductor-mediated
  bootstrap independent of these fixed values.
- It cannot claim four-phase INTERLEAVED steady-state operation (P24's
  normal periodic mode) -- this is a bootstrap transient study only, and
  (per the grid results, `RESULTS.md`) no cell in this grid ever advances
  past phase 2 of the very first rotation.
- The timer sign-convention finding (Section 2) is reported as a
  diagnostic finding about THIS experiment's own construct and a flagged
  open question for R04E5's construct; it is not a claim that R04E5's own
  committed results are wrong (R04E5's own results never exercised the
  affected branch, so they are not directly impacted either way) --
  R04E5's files are not touched, re-run, or amended by this experiment.
