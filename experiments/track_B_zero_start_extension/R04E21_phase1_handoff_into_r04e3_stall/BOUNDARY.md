# R04E21 - does a Track-B-bootstrapped phase-1 state avoid R04E3's own
   documented zero-energy stall? (BOUNDARY)

## 0. Scope statement -- read this section first, it governs everything below

**This experiment does NOT test, claim, or imply that P24's periodic
steady-state (Track A's own reproduction target) is reached, reachable,
or even proven to exist.** A dedicated research pass (2026-09-18,
recorded here for provenance) established that **no genuinely closed
periodic orbit (`x(T)=x(0)` for the full state vector) has EVER been
found anywhere in this project, by either SPICE or symbolic methods.**
The best SPICE candidate (`A37`, `P25_DEVICE_AUGMENTED`, `9%`
negative-current branch, labelled `LOCAL_SOLVED_SEED` not
`VALID_PERIODIC_INITIAL_STATE`) fails structurally at `H3` (high-side 3
never achieves ZVS admission in any of `174` evaluated points) with
phase-current mismatches up to `134 A`. The best symbolic candidate
(`symbolic_derivations/03_P24_primary_P25_supplement/21_
CONTINUATION_AND_SECOND_RING_FAILURE.md`) explicitly states it "found a
feasible one-ring descent candidate, not found a solution satisfying
periodic regression, target power, and admission robustness." **The
main-line reproduction target (Track A's own P24 periodic ZVS boundary-
mode operation) therefore remains unresolved independent of anything
Track B does** -- Track B (zero-start) is a supporting/subordinate
effort, not a substitute for Track A's own unfinished work, and this
experiment must not be read as advancing Track A's own periodicity
question.

**What this experiment actually, narrowly tests**: R04E3
(`paper_locked/02_ectc2024_main/spice/
R04E3_P24_minimal_zero_start_event_cycle.cir`) already established that
its own 5-state, physical-event-gated controller for phase 1's LOCAL
commutation chain -- `ENERGY -> HS_OFF_COMMUTATE_LOW ->
LOW_FREEWHEEL_TO_ZERO -> LOW_BUILD_NEGATIVE -> COMMUTATE_HIGH_TO_ZVS ->
[stuck]` -- permanently stalls at state `COMMUTATE_HIGH_TO_ZVS`, waiting
forever for the event `V(vin,xmod:a1)<=0` (the high-side drain-source
voltage reaching zero), when started from true zero energy (`ic=0`
everywhere). R04E5 confirmed this stall is permanent, not timing-
dependent, across a 12-cell grid out to `600 us`. **This experiment asks
one specific, narrow, well-defined question: does the SAME event-gated
controller, given phase 1's own REAL bootstrapped state from R04E17's
own safe cell (instead of zero energy) as its initial condition, avoid
that specific documented stall?** Nothing more is claimed.

## 1. Parent

- `paper_locked/02_ectc2024_main/spice/
  R04E3_P24_minimal_zero_start_event_cycle.cir` -- the exact controller
  construct and stall being tested (read-only reference, protected
  directory, never modified).
- `experiments/track_B_zero_start_extension/
  R04E17_divider_ramp_factorial_isolation/cases/
  e17_div_f3_t68p61.cir` -- the source of the bootstrapped initial
  condition (the SAFE cell: divider present, `Tramp=68.61 us`,
  `IL1_max=154.73 A`, no runaway, `Vout_final=1.006 V`). The RUNAWAY
  cell (`e17_div_f3_t1`) is deliberately NOT used as a source state here
  -- feeding a state that already violates the `+/-250 A` engineering
  bound into a new experiment would conflate "does the controller avoid
  its own stall" with "what happens when you start from an already-
  unsafe state," two different questions.
- The 2026-09-18 research pass (Section 0 above) establishing the
  absence of any proven periodic orbit anywhere in this project.

## 2. What changed relative to R04E3, exactly

- **`CFLY` corrected from R04E3's own `4*10u+2*4.7u+2*2.2u=53.8 uF`
  (the cross-topology-suspect EPE2019 value) to `3 uF`** (R04E8's own
  corrected middle value, the SAME value R04E16/R04E17's own bootstrap
  was built with) -- a direct module swap, precisely matching R04E8's
  own precedent (R04E8 did this exact same swap for R04E7's construct).
  This is REQUIRED, not optional: feeding a state bootstrapped under one
  `Cfly` value into a circuit built with a different `Cfly` value would
  make the initial condition physically inconsistent with the circuit
  receiving it.
- **Phase 1's own initial conditions** (`VC1` = the `a1`-`x1` flying-
  capacitor voltage, `IL1` = the `L1` inductor current) are set from
  R04E17's own `e17_div_f3_t68p61` cell's actual state AT `TSTOP`
  (`368.61 us`), instead of R04E3's own `ic=0`. **R04E17's own committed
  `.meas` set captured `VC1_FINAL` but not an instantaneous `IL1` at
  `TSTOP`** (only `IL1_MAX`/`IL1_MIN`, the envelope over the whole run) --
  this experiment's own build step re-runs R04E17's own UNMODIFIED
  `e17_div_f3_t68p61.cir` with ONE added `.meas` line
  (`IL1_AT_TSTOP FIND I(L1) AT 368.61u`) to obtain this value. This is a
  measurement addition only, not a physics change -- the underlying
  circuit and its results are byte-identical to R04E17's own already-
  committed, already-verified cell; re-running it must reproduce every
  one of R04E17's own already-published `.meas` values exactly, verified
  before the extracted `IL1_AT_TSTOP` value is trusted.
- **All other capacitors/inductors** in the receiving circuit (`CH1`,
  `CL1`, `CS2`, `CS3`, `CCO`, `L2-4`) remain at R04E3's own `ic=0` --
  see Section 4 for why, and the explicit limitation this creates.

## 3. What did not change

- R04E3's own event-gating logic, unchanged in every detail: the
  5-state machine, all `.rule` transition conditions, `I_LIMIT=10 A`,
  `NEG_FRAC=.02` (`I_NEG=0.2 A`), the `.output` gate-drive expressions.
- R04E3's own phase-1-only power-stage construct
  (`SCB4P_P24_EVENT`), including its hardcoded phase 2-4 gate drives
  (`VGL2=VGATE` fixed ON, `VGH2/VGH3/VGH4=0` fixed OFF, `VGL3/VGL4=0`
  fixed OFF) -- UNCHANGED, per the explicit minimal-scope decision
  (Section 4).
- `COUT=4.672 mF` -- unchanged; R04E3 already used this same value, and
  it remains this project's still-unconfirmed cross-topology candidate
  either way (correcting it is out of scope here, same standing
  limitation as every other Track-B experiment).
- `LPHASE=1.4666667 nH`, GS61008T device data (`CH`/`CL`/`RHS`/`RLS`),
  `TRAIL=10p` input-rail rise time, `solver=alt cshunt=1e-15`,
  `TMAX` convention -- unchanged from R04E3's own netlist.
- R04E17's own `e17_div_f3_t68p61.cir` itself -- read and re-run
  UNMODIFIED except the one added `.meas` line (Section 2); not
  otherwise edited, and its own committed results are not altered.

## 4. Why phases 2-4 keep R04E3's own hardcoded configuration --
   explicit, deliberate scope limit, not an oversight

R04E17's own bootstrapped state has REAL, substantial current in ALL
FOUR phases at `TSTOP` (not just phase 1) -- feeding phase 1's own
bootstrapped state into R04E3's construct while phases 2-4 keep their
own zero-energy initial conditions AND R04E3's own hardcoded gate drives
is a genuine inconsistency: phases 2-4's own real bootstrapped currents
are simply DISCARDED here, and their own gate states are held at
whatever R04E3's original single-phase-isolation design already fixed
them to (phase 2 low-side latched on, phases 3-4 fully off), regardless
of what those phases were actually doing in R04E17's own bootstrap.

**This is accepted deliberately for this experiment's own minimal scope**
(per explicit user direction 2026-09-18: test whether phase 1 ALONE can
avoid its own documented stall, before attempting a full four-phase
handoff, which would require building a new four-phase event-gated
controller that does not currently exist anywhere in this project --
Track A's own A24-A48 controllers are each independently built for
their own specific experiments, not a shared, reusable four-phase
construct ready to receive arbitrary initial conditions). **A genuinely
correct four-phase handoff is explicitly NOT what this experiment
attempts**, and no result here should be read as testing it.

## 5. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `CFLY=3 uF` (corrected from R04E3's own `53.8 uF`) | R04E8's own corrected middle value; this exact correction pattern (swap `Cfly` for an existing controller/mechanism, nothing else) already validated by R04E8's own precedent on R04E7's construct | `SENSITIVITY_ONLY`, inherited |
| Phase-1 initial conditions (`VC1`, `IL1` at `TSTOP=368.61us`) | R04E17's own already-committed, already-verified `e17_div_f3_t68p61` cell, re-run unmodified except one added `.meas` line to extract the missing instantaneous `IL1` value | inherited, re-measured not re-derived |
| R04E3's own event-gating logic, `I_LIMIT`, `NEG_FRAC` | `paper_locked/02_ectc2024_main/spice/R04E3_...cir`, unchanged | `P24_EXPLICIT`-adjacent engineering construct (the negative-current convention itself is P24's own `1-2%`; the state-machine construct is this project's own, not P24-published) |
| Phases 2-4 kept at R04E3's own hardcoded configuration and zero-energy IC | R04E3's own original single-phase-isolation design, deliberately not changed (Section 4) | scope decision, not a paper value |

No new paper-sourced, cross-paper, or external-device data is
introduced. This experiment recombines two already-existing, already-
justified constructs (R04E3's own controller, R04E17's own bootstrap
state) with one corrected parameter (`Cfly`) and one added measurement;
nothing here is claimed as P24-published behavior.

## 6. What question this experiment is meant to answer

Does phase 1's own event-gated local commutation chain (R04E3's own
construct, `Cfly`-corrected) progress PAST state `COMMUTATE_HIGH_TO_ZVS`
-- i.e. does the high-side ZVS event `V(vin,a1)<=0` actually occur --
when phase 1 starts from R04E17's own real bootstrapped state instead of
true zero energy? Three possible outcomes, all informative (Section 7):
the stall is avoided entirely (reaches state 5, `BLOCK_P24_HANDOFF_
UNKNOWN` -- R04E3's own deliberate stopping point, not a claim of
further success); the SAME stall recurs at state 4 despite the
bootstrapped starting condition; or a DIFFERENT stall/divergence occurs
that neither R04E3 nor R04E17 individually showed.

## 7. Success/failure conditions

- **Stall avoided**: phase 1 reaches state 5 (`BLOCK_P24_HANDOFF_
  UNKNOWN`) within a reasonable window. This would show R04E17's own
  bootstrap supplies enough real current/voltage for phase 1's own local
  ZVS event to actually occur -- a genuinely positive, narrowly-scoped
  result. It does NOT mean four-phase handoff, Vout regulation, or P24
  periodicity is solved (Section 0/4).
- **Same stall recurs**: phase 1 still parks at state 4, waiting
  forever for `V(vin,a1)<=0`. This would show the bootstrapped current/
  voltage magnitude alone is not sufficient -- the physical mechanism
  blocking this event must depend on something else (e.g. the specific
  trajectory/phase relationship, not just the state magnitude at the
  handoff instant) -- a genuinely informative negative result, not a
  failure requiring rework.
- **A different failure mode** (e.g. phase current runaway, a new stall
  at an earlier/later state, solver non-convergence): reported plainly
  per Ground Rule 7, not forced into either of the above categories.
- Phase 1's own current must stay within this project's `+/-250 A`
  engineering bound throughout -- if the handoff instant itself produces
  a current spike (from phases 2-4's own artificial gate-state
  discontinuity, Section 4), this must be reported explicitly, not
  silently absorbed into the "did it avoid the stall" verdict.

## 8. What this experiment cannot prove

- It does not test, establish, or claim P24 periodic steady-state
  reachability -- explicitly out of scope (Section 0), independent of
  this experiment's own outcome.
- It does not test a genuine four-phase handoff -- phases 2-4 keep
  R04E3's own hardcoded, single-phase-isolation configuration
  (Section 4), not their own real R04E17-bootstrapped state.
- It does not validate R04E3's own controller as "the" P24 steady-state
  controller -- R04E3 itself is a phase-1-only local commutation test,
  not a claimed reproduction of P24's own full control law.
- A positive result (stall avoided) would not, by itself, establish that
  continuing past state 5 (`BLOCK_P24_HANDOFF_UNKNOWN`, R04E3's own
  deliberate stopping point) leads anywhere sustainable -- state 5 exists
  specifically because R04E3 itself does not define what happens next.
- It does not modify, overwrite, or invalidate R04E3's, R04E17's, or any
  other experiment's own committed results -- R04E17's own cell is
  re-run unmodified (Section 2) purely to extract a missing measurement,
  not to change its own record.
- A P24 reproduction claim of any kind remains out of scope, the same
  standing Track-B limitation as every other experiment in this lineage.
