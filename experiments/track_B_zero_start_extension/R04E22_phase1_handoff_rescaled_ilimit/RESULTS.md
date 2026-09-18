# R04E22 - rescaling I_LIMIT/I_NEG to P24's own real current scale (RESULTS)

See `BOUNDARY.md` for the full scope statement, provenance and explicit
limitations. This document reports what actually happened; read Section 0
of `BOUNDARY.md` before interpreting anything below.

## 1. Outcome, stated plainly, first (BOTH cells)

**Neither cell reaches state 4 (`COMMUTATE_HIGH_TO_ZVS`, R04E21's own
documented stall point) or state 5 (`BLOCK_P24_HANDOFF_UNKNOWN`).** Both
cells park one state EARLIER than R04E21's own stall, at state `3`
(`LOW_BUILD_NEGATIVE`), at `TSTOP=20us`:

- `r04e22_neg2pct` (`I_LIMIT=125`, `NEG_FRAC=.02`, `I_NEG=2.5A`):
  `STATE_FINAL=3` at `t=2e-05`. `t_neg_target` (the `3->4` transition,
  `I(L1)<=-I_NEG`) **FAILs** -- `IL1` only reaches `il1_min=
  -2.21509122849 A` by `TSTOP`, never as negative as `-2.5A`.
- `r04e22_neg7p77pct` (`I_LIMIT=125`, `NEG_FRAC=.0777`, `I_NEG=9.7125A`):
  `STATE_FINAL=3` at `t=2e-05`. `t_neg_target` **FAILs** -- `IL1` only
  reaches `il1_min=-2.21509122849 A` by `TSTOP`, never as negative as
  `-9.7125A`.

Both cells' `il1_min`, `il1_max`, `vout_final`, `vc1_final`, `vc2_final`,
`vc3_final` and every state-transition timestamp up to and including
`t_il1_zero` are **numerically identical** between the two `NEG_FRAC`
values. This is not a run error: because the `3->4` rule never fires in
EITHER cell, `NEG_FRAC`/`I_NEG` never actually enters the simulated
physics (it only gates a threshold comparison that is never crossed), so
the two cells' trajectories are identical up to `TSTOP` by construction.

**This is none of the three outcomes BOUNDARY.md Section 7 explicitly
anticipated** (stall avoided/state 5 reached; state-4 stall persists;
different outcome between the two `NEG_FRAC` values). It is a fourth,
unanticipated outcome: the corrected `I_LIMIT=125A` changes the circuit's
own trajectory enough that the negative-current-build phase (state 3)
itself becomes far slower than it was in R04E21's `I_LIMIT=10A` cell, so
`TSTOP=20us` (inherited byte-identical from R04E3/R04E21, per this
experiment's own stated scope -- Section 3/9) is not long enough to reach
EITHER swept `I_NEG` target, let alone the state-4 blocking condition
this experiment was built to test. **The diagnosed R04E21 hypothesis is
therefore UNTESTED by this run -- not confirmed and not refuted.**
Reported plainly, per this project's own Ground Rule 7: an inconclusive
result from a correctly-executed, correctly-diagnosed experiment is
reported as exactly that, not forced into a false positive or negative.

## 2. The two netlists built

Both built from `experiments/track_B_zero_start_extension/
R04E21_phase1_handoff_into_r04e3_stall/cases/r04e21_phase1_handoff.cir`
(read-only, never modified) as the literal starting template. `diff`
against R04E21's own file (comment lines excluded) confirms EXACTLY the
one changed line BOUNDARY.md Section 2 specifies, and nothing else, in
each cell:

- `cases/r04e22_neg2pct.cir`: `.param I_LIMIT=10 NEG_FRAC=.02
  I_NEG={NEG_FRAC*I_LIMIT}` -> `.param I_LIMIT=125 NEG_FRAC=.02
  I_NEG={NEG_FRAC*I_LIMIT}` (`I_NEG=2.5`).
- `cases/r04e22_neg7p77pct.cir`: `.param I_LIMIT=10 NEG_FRAC=.02
  I_NEG={NEG_FRAC*I_LIMIT}` -> `.param I_LIMIT=125 NEG_FRAC=.0777
  I_NEG={NEG_FRAC*I_LIMIT}` (`I_NEG=9.7125`).

Everything else -- phase 1's own bootstrapped initial conditions
(`VC1_IC=35.85894624845418`, `IL1_IC=75.96527862548828`), `CFLY=3u`, the
5-state `.machine` block's own rule structure, phases 2-4's own
hardcoded R04E3 configuration, all `.meas` statements, `.options`,
`.tran 0 20u 0 1n UIC` -- is byte-identical to R04E21's own file (only
the header/provenance comments and the `.include` relative path, which
necessarily differs by directory location, were rewritten; header
comments carry no simulated behavior).

A truncated-`TSTOP` pilot (`.tran` shortened to `200n`, not committed)
was run for each netlist before the full run and confirmed both load and
simulate with no topology/syntax error (early `.meas` transitions fire
correctly; later `AT 20u`-based `.meas` lines correctly `FAIL` only
because the pilot's own truncated window never reaches `20u`, as
expected).

## 3. Full runs: `.meas` output and state-transition timeline

Both full runs (`TSTOP=20us`, unchanged) completed fast, as expected:
`r04e22_neg2pct` `Total elapsed time: 2.985 seconds`; `r04e22_neg7p77pct`
`Total elapsed time: 3.072 seconds` (both from `cases/*.log`).

Full `.meas` output, `r04e22_neg2pct.log`:

```
t_energy_end: V(state_mon)=.5  AT 6.3702883197e-09
il1_energy_end: I(XMOD:L1) =125.01597397 at 6.3702883197e-09
t_low_side_zvs: V(state_mon)=1.5  AT 6.47330761463e-09
t_il1_zero: V(state_mon)=2.5  AT 1.63197919454e-06
Measurement "t_neg_target" FAIL'ed
Measurement "t_high_side_zvs" FAIL'ed
state_final: V(state_mon) =3 at 2e-05
il1_min: MIN(I(XMOD:L1) )=-2.21509122849 FROM 0 TO 2e-05
il1_max: MAX(I(XMOD:L1) )=125.390205383 FROM 0 TO 2e-05
vout_final: V(out) =0.000317616097163 at 2e-05
vc1_final: V(xmod:a1,xmod:x1) =36.0765751745 at 2e-05
vc2_final: V(xmod:a2,xmod:x2) =-2.04890966415e-08 at 2e-05
vc3_final: V(xmod:a3,xmod:x3) =-2.10129655898e-08 at 2e-05
```

Full `.meas` output, `r04e22_neg7p77pct.log` (identical values, see
Section 1 for why):

```
t_energy_end: V(state_mon)=.5  AT 6.3702883197e-09
il1_energy_end: I(XMOD:L1) =125.01597397 at 6.3702883197e-09
t_low_side_zvs: V(state_mon)=1.5  AT 6.47330761463e-09
t_il1_zero: V(state_mon)=2.5  AT 1.63197919454e-06
Measurement "t_neg_target" FAIL'ed
Measurement "t_high_side_zvs" FAIL'ed
state_final: V(state_mon) =3 at 2e-05
il1_min: MIN(I(XMOD:L1) )=-2.21509122849 FROM 0 TO 2e-05
il1_max: MAX(I(XMOD:L1) )=125.390205383 FROM 0 TO 2e-05
vout_final: V(out) =0.000317616097163 at 2e-05
vc1_final: V(xmod:a1,xmod:x1) =36.0765751745 at 2e-05
vc2_final: V(xmod:a2,xmod:x2) =-2.04890966415e-08 at 2e-05
vc3_final: V(xmod:a3,xmod:x3) =-2.10129655898e-08 at 2e-05
```

State-transition timeline (identical for both cells, up to the point
where they would diverge if either reached it):

| Transition | State | Time | Note |
|---|---|---|---|
| `ENERGY -> HS_OFF_COMMUTATE_LOW` | `0->1` | `6.370e-9 s` | `IL1` crosses the corrected `I_LIMIT=125A` (`il1_energy_end=125.016A`), starting from bootstrapped `IL1_IC=75.97A`. Genuinely dwells and charges further, exactly as BOUNDARY.md Section 2 predicted (contrast R04E21's own near-instant `2.98e-13s`, since there `IL1_IC=75.97A` already exceeded R04E21's own `I_LIMIT=10A` at `t=0`). |
| `HS_OFF_COMMUTATE_LOW -> LOW_FREEWHEEL_TO_ZERO` | `1->2` | `6.473e-9 s` | Fast local commutation (`~103 ps` after state 0 exit). |
| `LOW_FREEWHEEL_TO_ZERO -> LOW_BUILD_NEGATIVE` | `2->3` | `1.632e-6 s` | `IL1` decays from `~125A` through `0` over `~1.626us` -- close to R04E21's own `~1.63us` decay from `~76A`, i.e. a similar total zero-crossing time despite the larger starting current in this cell. |
| `LOW_BUILD_NEGATIVE -> COMMUTATE_HIGH_TO_ZVS` | `3->4` | **never** (either cell) | `t_neg_target` FAILs in both cells; `IL1` only reaches `-2.215A` by `TSTOP=20us`, far short of EITHER swept `I_NEG` target (`-2.5A` or `-9.7125A`). Contrast R04E21's own cell, where the same `3->4` transition fired in only `~56ns` after crossing zero (its `I_NEG=0.2A` target was tiny). |
| `COMMUTATE_HIGH_TO_ZVS -> BLOCK_P24_HANDOFF_UNKNOWN` | `4->5` | **never attempted** | State 4 is never reached in either cell, so this transition's own condition (`V(vin,xmod:a1)<=0`) is never even evaluated as the machine's active rule. |

**`STATE_FINAL=3`** in both cells confirms the machine is parked at
`LOW_BUILD_NEGATIVE` at `TSTOP` -- one state earlier than R04E21's own
`STATE_FINAL=4` (`COMMUTATE_HIGH_TO_ZVS`). The post-zero-crossing
negative-current-build phase is dramatically slower under this
`I_LIMIT=125A` trajectory (`-2.215A` reached over `~18.37us`, an average
rate of about `-0.12 A/us`) than under R04E21's `I_LIMIT=10A` trajectory
(`-0.2A` reached in `~56ns`, several orders of magnitude faster). This
asymmetry was not explicitly anticipated in BOUNDARY.md's own reasoning
(which focused on state 0's dwell time and the state-4 target magnitude,
not on how the corrected `I_LIMIT` would also reshape state 3's own
decay rate) and is the direct, verified cause of this run's inconclusive
outcome.

## 4. Current-safety check (`+/-250 A` bound), BOTH cells

Per BOUNDARY.md Section 7's explicit requirement, reported regardless of
outcome. Byte-level `.raw` scan (`scripts/check_fingerprint.py`, adapted
from R04E21's own reference script), all `20,353` saved points per cell:

| Cell | `IL1_MAX` | `IL1_MIN` | `max\|IL1\|` | Points `>250A` |
|---|---:|---:|---:|---:|
| `r04e22_neg2pct` | `125.390205383 A` | `-2.21509122849 A` | `125.390 A` | `0` |
| `r04e22_neg7p77pct` | `125.390205383 A` | `-2.21509122849 A` | `125.390 A` | `0` |

**Phase 1's own current stays well within the `+/-250A` engineering
bound throughout both runs.** The higher `I_LIMIT=125A` charging target
(vs. R04E21's own `10A`) raises the observed peak from R04E21's own
`~76A` to `~125.4A`, as expected, but this remains comfortably inside the
adopted safety bound with wide margin.

## 5. Solver-corruption fingerprint check, BOTH cells

`scripts/check_fingerprint.py` (copied from R04E21's own reference
script, reusing `scripts/ltspice_raw_parser.py` unchanged) directly,
byte-level parsed both `.raw` files:

```
cases/r04e22_neg2pct.raw
  points: 20353
  rows_scanned: 20353
  dt_nonpos_count: 0
  dt_nonpos_examples: []
  vin_min: 0.0
  vin_max: 48.0
  implausible_vin_count: 0
  il1_min: -2.2150912284851074
  il1_max: 125.39020538330078
  il1_max_abs: 125.39020538330078
  il1_over_250a_count: 0
  il1_over_250a_examples: []

cases/r04e22_neg7p77pct.raw
  points: 20353
  rows_scanned: 20353
  dt_nonpos_count: 0
  dt_nonpos_examples: []
  vin_min: 0.0
  vin_max: 48.0
  implausible_vin_count: 0
  il1_min: -2.2150912284851074
  il1_max: 125.39020538330078
  il1_max_abs: 125.39020538330078
  il1_over_250a_count: 0
  il1_over_250a_examples: []
```

Zero non-monotonic or duplicate timestamps across all `20,353` points in
either trace; `V(vin)` stays exactly within its own commanded `0-48V`
step in both; no point in either trace exceeds the `+/-250A` current
bound. **Both traces are confirmed free of the documented
solver-corruption fingerprint (R04E10, R04E16-R04E20, R04E21).**

## 6. Discussion -- what this confirms or refutes about R04E21's own diagnosed hypothesis

**R04E21's diagnosed hypothesis (BOUNDARY.md Section 1) was**: the
original `I_NEG=0.2A` (from R04E3's own leftover zero-start-era
`I_LIMIT=10A`) was too small to store meaningful magnetic energy for the
state-4 resonant ZVS ring, and rescaling `I_LIMIT`/`I_NEG` to P24's own
real `125A` scale might let the state-4 `V(vin,a1)<=0` event actually
fire.

**This run cannot confirm or refute that hypothesis.** Neither cell ever
reaches state 4 -- the specific mechanism the hypothesis is about (does a
larger `I_NEG` unblock the state-4 ZVS event) is never exercised, because
the machine never gets far enough to attempt the `3->4` transition
before `TSTOP=20us` runs out, in EITHER swept `NEG_FRAC`. This is
DIFFERENT from R04E21's own clean negative result (which DID reach state
4 and DID observe `t_high_side_zvs` FAIL there) -- this run does not even
reach the point R04E21 reached. Consequently:

- It is **not evidence that the hypothesis is correct** (no confirmation
  that a larger `I_NEG` would unblock state 4, since state 4 was never
  entered).
- It is **not evidence that the hypothesis is wrong** (no observation of
  state 4 behavior at all under the corrected `I_LIMIT`).
- What IS newly established: correcting `I_LIMIT` to `125A` has a
  second, previously-unexamined consequence beyond the one BOUNDARY.md
  Section 2 explicitly reasoned about (state 0's dwell time) -- it also
  substantially slows the state-3 negative-current-build rate, to the
  point that `TSTOP=20us` (a value inherited unchanged from R04E3, sized
  for the OLD `I_LIMIT=10A`/`I_NEG=0.2A` regime, not re-derived for this
  new one) is no longer long enough to observe the state-3-to-4
  transition at either swept `NEG_FRAC` value, let alone the state-4
  ZVS question itself.
- A genuinely informative, if inconclusive, result: it shows that
  testing this hypothesis properly requires either a longer `TSTOP` or a
  netlist-level accounting of how the corrected `I_LIMIT` reshapes the
  ENTIRE downstream timescale, not just the two boundary values
  (`I_LIMIT`, `I_NEG`) BOUNDARY.md Section 2 explicitly reasoned about.
  Per this project's own Ground Rule 7, this is reported exactly as
  found -- not forced into "confirmed" or "refuted."

## 7. Explicit adherence to BOUNDARY.md Section 0/8 -- what this does NOT show

Restated because it bears directly on how this inconclusive result should
be read, same standing limitations as R04E21's own Section 7:

- **Not a P24 periodicity result.** This experiment says nothing about
  whether P24's own periodic steady-state is reachable; that question
  remains independently unresolved (R04E21 BOUNDARY.md Section 0),
  unaffected either way by this run's own inconclusive outcome.
- **Not a four-phase handoff test.** Phases 2-4 were deliberately held
  at R04E3's own hardcoded, zero-energy, single-phase-isolation
  configuration throughout (BOUNDARY.md Section 1/3, R04E21 BOUNDARY.md
  Section 4) -- unchanged from R04E21, per this experiment's own stated
  scope. `VC2_FINAL`/`VC3_FINAL` both `~-2.1e-8 V` (numerically zero) in
  both cells, consistent with this.
- **Not a validation of R04E3's own controller as "the" P24
  controller.** R04E3 itself is a phase-1-only local commutation test;
  this experiment inherits that same limitation unchanged.
- **Not a resolution of R04E21's own diagnosed hypothesis in either
  direction** -- Section 6 above. A future follow-up would need to
  either extend `TSTOP` well past `20us` for this `I_LIMIT=125A`
  trajectory, or otherwise establish what a physically appropriate
  `TSTOP` is for this corrected current scale, before the state-4 ZVS
  question can actually be exercised.
- Per Ground Rule 7, this inconclusive result carries the same
  reporting weight a clean positive or negative result would have
  received -- it is reported plainly, not minimized or dressed up as
  either.

## 8. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `I_LIMIT=125 A` | P24's own `LOCKED` Table-1 peak current (`SOURCE_COVERAGE_MATRIX.md`) | `P24_EXPLICIT` |
| `NEG_FRAC=.02` (`r04e22_neg2pct`) | `CURRENT_ASSUMPTION_CROSSCHECK.md`'s own "main P24 branch" convention, already used throughout Track A (A24-A48) and R04E3/R04E21 itself | `P24_EXPLICIT`-adjacent (P24's own text states `1-2%`; this project's own standing choice is `2%`) |
| `NEG_FRAC=.0777` (`r04e22_neg7p77pct`) | A42's own found LOCAL single-phase natural-ZVS threshold, `7.76-7.77%` (A43's own precedent for testing the upper bound as one value) | `SENSITIVITY_ONLY`, inherited from A42/A43, explicitly NOT the full-four-phase-machine threshold (`9%`) per the standing warning in `CURRENT_ASSUMPTION_CROSSCHECK.md` |
| `VC1_IC=35.85894624845418`, `IL1_IC=75.96527862548828`, `CFLY=3uF`, R04E3's own machine structure, phases 2-4's own hardcoded config, `TSTOP=20us` | Copied unchanged from R04E21's own already-verified netlist | inherited, unchanged (see R04E21 `BOUNDARY.md`/`RESULTS.md` for original provenance) |

No new paper-sourced, cross-paper, or external-device data is
introduced -- both `I_LIMIT` and both `NEG_FRAC` values are reused,
already-labelled quantities from elsewhere in this project (per
BOUNDARY.md Section 5), redeployed here for a new purpose. Neither
R04E21's nor R04E3's own committed files or results were modified.
