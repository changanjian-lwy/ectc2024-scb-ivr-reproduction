# R04E23 - extending TSTOP so R04E22's own question can actually be tested (RESULTS)

See `BOUNDARY.md` for the full scope statement, provenance and explicit
limitations. This document reports what actually happened; read Section 0
of `BOUNDARY.md` before interpreting anything below.

## 1. Outcome, stated plainly, first (BOTH cells)

**`I_NEG` is STILL not reached in EITHER cell, even at `TSTOP=100us` (a
`5x` extension over R04E22's own `20us`).** Both cells remain parked at
state `3` (`LOW_BUILD_NEGATIVE`) at `TSTOP=100us`; `t_neg_target` (the
`3->4` transition, `I(L1)<=-I_NEG`) `FAIL`s in both. This is the THIRD
outcome BOUNDARY.md Section 6 explicitly anticipated ("`I_NEG` still not
reached even at `100 us`"), not the first (stall avoided) or second (same
state-4 stall recurs) -- neither swept `NEG_FRAC` cell even progresses far
enough to test R04E21's own state-4 ZVS question. Per BOUNDARY.md Section
6's own explicit instruction, this is reported plainly and this result
does NOT extrapolate further (does not attempt, recommend, or silently
run a third, longer `TSTOP`).

**Why, mechanistically, verified directly from the full `.raw` traces
(not assumed from the `.meas` output alone):** `IL1` does not continue
decreasing monotonically past `20us` the way BOUNDARY.md Section 2's own
"naive linear extrapolation" reasoning assumed. Direct byte-level parsing
of both full `100,356`-point `.raw` traces shows `IL1` reaches its GLOBAL
minimum of `-2.2150912284851074 A` at `t=2.817428674148355e-06 s`
(`~2.82us` into the run) -- essentially the SAME value R04E22's own
`20us`-window `IL1_MIN` measurement already captured -- and from there
**decays back toward zero** (a damped relaxation, not a continued
negative ramp): `IL1=-0.098A` at `t=20us`, `-0.0024A` at `t=40us`,
`-0.00003A` at `t=90us`, and `-0.0000236A` at the final point,
`t=100us`. Extending `TSTOP` to `100us` did not give the negative-current
build "more time to reach the target" in the way BOUNDARY.md Section 2
anticipated, because state 3's own `IL1(t)` trajectory is not still
ramping at `t=20us` -- it already peaked negative by `~2.82us` and has
been relaxing back toward `0` for the entire remainder of both the
original `20us` window and this experiment's own extended `80us`
addition. Both swept `I_NEG` targets (`-2.5A`, `-3.5%` more negative than
the observed peak; `-9.7125A`, `4.4x` more negative) remain entirely out
of reach under this trajectory, regardless of how far `TSTOP` is
extended, unless something else about the circuit or its initial
conditions changes.

**Both cells are confirmed numerically IDENTICAL, exactly as R04E22 found
at `20us` and for the same reason.** A full-trace point-by-point
comparison of `I(xmod:L1)` and `time` between the two `100,356`-point
`.raw` files shows `0` differing rows out of `100,356` in either
quantity. Because the `3->4` rule never fires in either cell, `NEG_FRAC`
never actually enters the simulated physics (it only gates a threshold
comparison that is never crossed) -- the two cells' trajectories remain
identical for the full `100us` window, not just the original `20us`.

## 2. The two netlists built

Both built from `experiments/track_B_zero_start_extension/
R04E22_phase1_handoff_rescaled_ilimit/cases/r04e22_neg2pct.cir` and
`r04e22_neg7p77pct.cir` (read-only, never modified) as the literal
starting templates. `diff` against each R04E22 file (comment lines
excluded) confirms EXACTLY the changes BOUNDARY.md Section 2 specifies,
and nothing else, in each cell:

- `.tran 0 20u 0 1n UIC` -> `.tran 0 100u 0 1n UIC`
- The five `AT 20u` `.meas` lines (`STATE_FINAL`, `VOUT_FINAL`,
  `VC1_FINAL`, `VC2_FINAL`, `VC3_FINAL`) -> `AT 100u`

Everything else -- `I_LIMIT=125`, `NEG_FRAC` (`.02` / `.0777`), phase 1's
own bootstrapped initial conditions (`VC1_IC=35.85894624845418`,
`IL1_IC=75.96527862548828`), `CFLY=3u`, the 5-state `.machine` block's
own rule structure, phases 2-4's own hardcoded R04E3 configuration, the
`WHEN`-based `.meas` lines, `IL1_MIN`/`IL1_MAX`'s own `FROM 0 TO 20u`
window (deliberately left unchanged, per this experiment's own narrow
one-parameter-plus-its-directly-tied-measurements scope), `.options` --
is byte-identical to each corresponding R04E22 file (only the
header/provenance comments and the `.include` relative path, which
necessarily differs by directory depth, were rewritten; header comments
carry no simulated behavior).

A full run of each netlist (not a separate truncated pilot) was used as
the sanity check per Step 1: both loaded and simulated with no
topology/syntax error, and completed in `13.671s`/`14.040s` `Total
elapsed time` (LTspice-reported solver time; `~17-21s` including
Wine/app-launch overhead per the `time`-wrapped `tools/ltspice_runner.sh`
call) -- confirming both are well under a minute, as expected for a `5x`
extension of R04E22's own `~3s` cells.

## 3. Full runs: `.meas` output and state-transition timeline

Full `.meas` output, `r04e23_neg2pct_t100us.log`:

```
t_energy_end: V(state_mon)=.5  AT 6.3702883197e-09
il1_energy_end: I(XMOD:L1) =125.01597397 at 6.3702883197e-09
t_low_side_zvs: V(state_mon)=1.5  AT 6.47330761463e-09
t_il1_zero: V(state_mon)=2.5  AT 1.63197919454e-06
Measurement "t_neg_target" FAIL'ed
Measurement "t_high_side_zvs" FAIL'ed
state_final: V(state_mon) =3 at 0.0001
il1_min: MIN(I(XMOD:L1) )=-2.21509122849 FROM 0 TO 2e-05
il1_max: MAX(I(XMOD:L1) )=125.390205383 FROM 0 TO 2e-05
vout_final: V(out) =-4.38002665248e-08 at 0.0001
vc1_final: V(xmod:a1,xmod:x1) =36.075614973 at 0.0001
vc2_final: V(xmod:a2,xmod:x2) =-1.9172674115e-08 at 0.0001
vc3_final: V(xmod:a3,xmod:x3) =-2.15837978601e-08 at 0.0001
```

Full `.meas` output, `r04e23_neg7p77pct_t100us.log` (identical values,
see Section 1 for why):

```
t_energy_end: V(state_mon)=.5  AT 6.3702883197e-09
il1_energy_end: I(XMOD:L1) =125.01597397 at 6.3702883197e-09
t_low_side_zvs: V(state_mon)=1.5  AT 6.47330761463e-09
t_il1_zero: V(state_mon)=2.5  AT 1.63197919454e-06
Measurement "t_neg_target" FAIL'ed
Measurement "t_high_side_zvs" FAIL'ed
state_final: V(state_mon) =3 at 0.0001
il1_min: MIN(I(XMOD:L1) )=-2.21509122849 FROM 0 TO 2e-05
il1_max: MAX(I(XMOD:L1) )=125.390205383 FROM 0 TO 2e-05
vout_final: V(out) =-4.38002665248e-08 at 0.0001
vc1_final: V(xmod:a1,xmod:x1) =36.075614973 at 0.0001
vc2_final: V(xmod:a2,xmod:x2) =-1.9172674115e-08 at 0.0001
vc3_final: V(xmod:a3,xmod:x3) =-2.15837978601e-08 at 0.0001
```

Note: `il1_min`/`il1_max` are reported `FROM 0 TO 2e-05` (unchanged from
R04E22, per BOUNDARY.md's own narrow scope -- only `TSTOP` and the `AT
20u` measurements changed). The GLOBAL `IL1` extremum over the FULL
`100us` window was separately extracted directly from each `.raw` trace
(not a `.meas` statement) and is reported in Section 1 and the timeline
table below.

State-transition timeline (identical for both cells -- both `.raw`
traces are byte-identical in `time`/`I(xmod:L1)`, `0` of `100,356`
differing rows in either):

| Transition | State | Time | Note |
|---|---|---|---|
| `ENERGY -> HS_OFF_COMMUTATE_LOW` | `0->1` | `6.370e-9 s` | Identical to R04E22's own value (unaffected by `TSTOP`). |
| `HS_OFF_COMMUTATE_LOW -> LOW_FREEWHEEL_TO_ZERO` | `1->2` | `6.473e-9 s` | Identical to R04E22's own value. |
| `LOW_FREEWHEEL_TO_ZERO -> LOW_BUILD_NEGATIVE` | `2->3` | `1.632e-6 s` | Identical to R04E22's own value. |
| (global `IL1` minimum, not a state transition) | still state `3` | `2.817e-6 s` | `IL1=-2.215091 A` -- the trajectory's own most-negative point, reached well inside the ORIGINAL `20us` window. Confirmed by direct `.raw` scan, not a `.meas` line. |
| `LOW_BUILD_NEGATIVE -> COMMUTATE_HIGH_TO_ZVS` | `3->4` | **never** (either cell, even by `100us`) | `t_neg_target` `FAIL`s in both. After its `~2.82us` peak, `IL1` relaxes back toward `0` (`-0.098A` at `20us`, `-0.0024A` at `40us`, `-0.00002A` at `100us`) instead of continuing toward either `-2.5A` or `-9.7125A` target. |
| `COMMUTATE_HIGH_TO_ZVS -> BLOCK_P24_HANDOFF_UNKNOWN` | `4->5` | **never attempted** | State 4 is never reached in either cell, so this transition's own condition (`V(vin,xmod:a1)<=0`) is never evaluated as the machine's active rule. |

**`STATE_FINAL=3`** in both cells at `t=100us`, confirming the machine
remains parked at `LOW_BUILD_NEGATIVE` for the FULL extended window --
the SAME state R04E22 found parked at `20us`, now shown to be a stable
resting point of this trajectory (not a transient the extended window
would have moved past), not merely a point not-yet-reached at the old
`TSTOP`.

## 4. Current-safety check (`+/-250 A` bound), BOTH cells

Per BOUNDARY.md Section 6's explicit requirement, reported regardless of
outcome. Byte-level `.raw` scan (`scripts/check_fingerprint.py`, copied
from R04E22's own reference script, reusing `scripts/
ltspice_raw_parser.py` unchanged), all `100,356` saved points per cell
(the full `100us` window, not just the original `20us`):

| Cell | `IL1_MAX` (full window) | `IL1_MIN` (full window) | `max\|IL1\|` | Points `>250A` |
|---|---:|---:|---:|---:|
| `r04e23_neg2pct_t100us` | `125.390205383 A` | `-2.2150912284851074 A` | `125.390 A` | `0` |
| `r04e23_neg7p77pct_t100us` | `125.390205383 A` | `-2.2150912284851074 A` | `125.390 A` | `0` |

**Phase 1's own current stays well within the `+/-250A` engineering
bound throughout the FULL extended `100us` window, in both cells.** The
peak (`~125.4A`, at the state-0/state-1 transition) and trough
(`~-2.215A`, at `~2.82us`) are identical to R04E22's own values -- the
extended window adds no new extremum in either direction, consistent
with `IL1` having already relaxed to near-`0` well before `100us`.

## 5. Solver-corruption fingerprint check, BOTH cells

`scripts/check_fingerprint.py` (copied from R04E22's own reference
script, reusing `scripts/ltspice_raw_parser.py` unchanged) directly,
byte-level parsed both `.raw` files:

```
cases/r04e23_neg2pct_t100us.raw
  points: 100356
  rows_scanned: 100356
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

cases/r04e23_neg7p77pct_t100us.raw
  points: 100356
  rows_scanned: 100356
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

Zero non-monotonic or duplicate timestamps across all `100,356` points in
either trace (`5x` more points than R04E22's own `20,353`, reflecting the
`5x` longer window at the same solver step density); `V(vin)` stays
exactly within its own commanded `0-48V` step in both; no point in either
trace exceeds the `+/-250A` current bound. Additionally, a full
point-by-point comparison of `time` and `I(xmod:L1)` between the two
`.raw` files found `0` differing rows out of `100,356` in either quantity
-- the two cells are confirmed physically (not just `.meas`-output)
identical for the entire extended window, consistent with the Section 1
explanation (the `3->4` rule, the only place `NEG_FRAC` could enter the
dynamics, never fires in either cell). **Both traces are confirmed free
of the documented solver-corruption fingerprint (R04E10, R04E16-R04E22).**

## 6. Discussion -- what this finally establishes (or doesn't) about R04E21's own original hypothesis

**R04E21's diagnosed hypothesis (restated, unchanged since R04E21
BOUNDARY.md Section 1)**: the original `I_NEG=0.2A` (from R04E3's own
leftover zero-start-era `I_LIMIT=10A`) was too small to store meaningful
magnetic energy for the state-4 resonant ZVS ring, and rescaling
`I_LIMIT`/`I_NEG` to P24's own real `125A` scale might let the state-4
`V(vin,a1)<=0` event actually fire.

**This run STILL cannot confirm or refute that hypothesis -- even with a
`5x` `TSTOP` extension specifically built to give R04E22's own question a
real chance to be tested.** Neither cell ever reaches state 4; the
specific mechanism the hypothesis is about (does a larger `I_NEG` unblock
the state-4 ZVS event) is never exercised in either swept `NEG_FRAC`
value, because the machine never gets past state 3's own resting point
before `TSTOP=100us` runs out. This is the SAME kind of inconclusive
result R04E22 reported at `20us`, now shown to persist at `100us` too --
not because `100us` was insufficient observation time in the sense
BOUNDARY.md Section 2 anticipated (a linear ramp needing more time to
cross the target), but because the trajectory itself does not continue
toward the target at all past its own early (`~2.82us`) peak. Consequently:

- It is **not evidence that the hypothesis is correct** (no confirmation
  that a larger `I_NEG` would unblock state 4, since state 4 was never
  entered).
- It is **not evidence that the hypothesis is wrong** (no observation of
  state 4 behavior at all under the corrected `I_LIMIT`, at either
  `TSTOP`).
- What IS newly established, and was NOT known from R04E22 alone: the
  reason `I_NEG` is not reached is not a slow-but-still-progressing ramp
  (R04E22's own "naive linear extrapolation" framing, BOUNDARY.md Section
  2) -- it is that `IL1(t)` in state 3 reaches its own most-negative
  point early (`~2.82us`, well inside R04E22's own original `20us`
  window) and then relaxes back toward `0` for the remainder of the
  window, however long that window is extended. This means neither
  swept `I_NEG` target (`-2.5A`, `-9.7125A`) is close to being reached
  under THIS specific bootstrapped initial condition and `I_LIMIT=125A`
  trajectory, and per BOUNDARY.md Section 6's own explicit instruction,
  this result does not extrapolate to "a longer `TSTOP` would eventually
  reach it" -- the observed relaxation behavior argues against that,
  though this report stops at describing what was measured and does not
  claim to have proven a longer `TSTOP` could never work under some
  different, unexamined mechanism.
- A genuinely informative, if still inconclusive (relative to R04E21's
  own original question), result: it shows that testing R04E21's own
  hypothesis under this bootstrapped initial condition and `I_LIMIT=125A`
  scale requires either a different circuit-level intervention (e.g. a
  netlist-level change to how state 3's own negative-current build is
  driven or damped, not examined here) or a different `NEG_FRAC` target
  small enough to fall within the trajectory's own observed `-2.215A`
  peak -- not simply more observation time. Per this project's own Ground
  Rule 7, this is reported exactly as found -- not forced into "confirmed"
  or "refuted," and no further `TSTOP` extension is attempted or
  recommended here without a separately-justified basis for one.

## 7. Explicit adherence to BOUNDARY.md Section 0/7 -- what this does NOT show

Restated because it bears directly on how this inconclusive result should
be read, same standing limitations as R04E21's/R04E22's own Section 7/8:

- **Not a P24 periodicity result.** This experiment says nothing about
  whether P24's own periodic steady-state is reachable; that question
  remains independently unresolved (R04E21 BOUNDARY.md Section 0),
  unaffected either way by this run's own inconclusive outcome.
- **Not a four-phase handoff test.** Phases 2-4 were deliberately held
  at R04E3's own hardcoded, zero-energy, single-phase-isolation
  configuration throughout (unchanged from R04E21/R04E22, per this
  experiment's own stated scope, BOUNDARY.md Section 0/3) --
  `VC2_FINAL`/`VC3_FINAL` both `~-2e-8 V` (numerically zero) in both
  cells at `100us`, consistent with this.
- **Not a validation of R04E3's own controller as "the" P24
  controller.** R04E3 itself is a phase-1-only local commutation test;
  this experiment inherits that same limitation unchanged.
- **Not a resolution of R04E21's own diagnosed hypothesis in either
  direction** -- Section 6 above. A future follow-up would need either a
  circuit-level intervention that changes state 3's own negative-current
  trajectory (not just more observation time, which this experiment
  demonstrates does not help), or a `NEG_FRAC` target within the
  trajectory's own observed `-2.215A` reach, before the state-4 ZVS
  question can actually be exercised.
- **No further `TSTOP` extension is attempted or implied by this
  result.** Per BOUNDARY.md Section 6's own explicit instruction ("do not
  extrapolate further without another explicit, separately-justified
  `TSTOP` extension -- do not silently keep multiplying the window in
  search of a result"), this report stops at `100us` and states plainly
  that `I_NEG` is not reached, without proposing or running a `200us`,
  `500us`, etc. follow-up.
- Per Ground Rule 7, this inconclusive result carries the same reporting
  weight a clean positive or negative result would have received -- it is
  reported plainly, not minimized or dressed up as either.

## 8. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `TSTOP=100 us` | New for this experiment: a `5x`-margin extension over R04E22's own observed rate, chosen to give ample headroom for unknown nonlinear dynamics past `20us`, not a tightly-derived minimum (BOUNDARY.md Section 4) | numerical-resolution/observation-window choice, not physical, not swept |
| The five `AT 20u` -> `AT 100u` `.meas` line changes | Direct consequence of the `TSTOP` change, so the FINAL-state measurements track the new stop time rather than an arbitrary earlier point | numerical-resolution/observation-window choice, not physical, not swept |
| Everything else (`I_LIMIT=125`, `NEG_FRAC in {.02,.0777}`, `VC1_IC`, `IL1_IC`, `CFLY=3uF`, R04E3's own machine structure, phases 2-4's own hardcoded config, `IL1_MIN`/`IL1_MAX`'s own `FROM 0 TO 20u` window) | Copied unchanged from R04E22's own already-verified netlists | inherited, unchanged (see R04E22 `BOUNDARY.md`/`RESULTS.md` for original provenance) |

No new paper-sourced, cross-paper, or external-device data is
introduced -- `TSTOP=100us` is a pure observation-window choice, not a
physical or swept parameter (per BOUNDARY.md Section 4). Neither
R04E22's, R04E21's, nor R04E3's own committed files or results were
modified.

## 9. Classification

`SENSITIVITY_ONLY`, `NOT_P24_REPRODUCTION`, inconclusive result (neither
confirms nor refutes R04E21's own diagnosed hypothesis; `I_NEG` still not
reached even at the extended `TSTOP=100us`, per BOUNDARY.md Section 6's
third anticipated outcome).
