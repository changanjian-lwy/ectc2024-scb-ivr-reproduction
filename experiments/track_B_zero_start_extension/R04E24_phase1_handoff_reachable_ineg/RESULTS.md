# R04E24 - using a reachable I_NEG target so state 4 is actually entered (RESULTS)

See `BOUNDARY.md` for the full scope statement, provenance and explicit
limitations. This document reports what actually happened; read Section 0
of `BOUNDARY.md` before interpreting anything below.

## 1. Outcome, stated plainly, first

**State 3 (`LOW_BUILD_NEGATIVE`) DOES exit this time.** `t_neg_target`
(the `3->4` transition, `I(L1)<=-I_NEG`) **PASSES** at
`t=2.2888839867e-06s` (`~2.29us`) -- the first time in the R04E21-R04E24
chain that this transition has ever fired. State 4
(`COMMUTATE_HIGH_TO_ZVS`) **is entered**, directly confirming R04E23's own
diagnosis: `I_NEG=2.0A` (`NEG_FRAC=.016`) sits below R04E23's own
observed natural peak (`-2.2150912284851074A`), so it is reached while
the earlier `-2.5A`/`-9.7125A` targets were not.

**But the SAME documented stall recurs, one state further in.**
`t_high_side_zvs` `FAIL`s. `STATE_FINAL=4` at `t=100us` -- the machine
never advances to state 5 (`BLOCK_P24_HANDOFF_UNKNOWN`). This is
BOUNDARY.md Section 6's **SECOND** anticipated outcome ("state 3 exits,
state 4 entered, but the SAME stall recurs"), not the first
(stall avoided) or third (state 3 still does not exit).

**Per BOUNDARY.md Section 6's own explicit instruction, this refutes
R04E21's own diagnosed hypothesis**, rather than confirming it: reaching
state 4 at all, with a reachable, correctly-scaled, nonzero `I_NEG` that
is now directly confirmed to fire the `3->4` rule, is **not sufficient**
to unblock the state-4 ZVS event (`V(vin,xmod:a1)<=0`). Something else
blocks it.

## 2. Mechanistically, verified directly from the full `.raw` trace, WHY state 4 stalls

Direct byte-level parsing of the full `465,821`-point `.raw` trace (`4.6x`
more points than R04E23's own `100,356` at the identical `.options`
settings -- state 4's own resonant ring forces the solver to a much finer
time step than state 3's smoother trajectory did) shows:

- Immediately after state-4 entry (`t~2.29us`), there is a brief damped
  ring: `I(XMOD:L1)` oscillates roughly between `-2.0A` and `+2.0A`, and
  `V(vin,xmod:a1)` (the state-4 exit condition's own quantity)
  oscillates roughly between `9.66V` and `14.16V`, over approximately
  `t=2.29us` to `t=5us`.
- This ring then **damps out**, monotonically decaying to a near-DC
  steady state by `~20-30us`: `I(XMOD:L1)` relaxes toward `~0A`, and
  `V(vin,xmod:a1)` settles at `~11.92V` for the entire remainder of the
  `100us` window (both gate commands are off in state 4 per the
  `.machine` block's own `.output` rules, so nothing drives further
  switching once this DC point is reached).
- **The minimum value `V(vin,xmod:a1)` EVER reaches, anywhere in the
  full `100us` run, is `9.662612915039062 V` at
  `t=2.2909270415129772e-06 s`** -- the very first trough of the initial
  ring, immediately after state-4 entry, not a late near-miss. This is
  nowhere near the `<=0V` threshold the `4->5` rule
  (`.rule COMMUTATE_HIGH_TO_ZVS BLOCK_P24_HANDOFF_UNKNOWN
  V(vin,xmod:a1)<=0`, confirmed identical in this project's own source
  netlist, `paper_locked/02_ectc2024_main/spice/
  R04E3_P24_minimal_zero_start_event_cycle.cir` line 31) requires.

**Which specific sub-condition it stalls at**: the `4->5` rule's own
condition is `V(vin,xmod:a1)<=0`. State 4 leaves both `SH1` and `SL1`
open (both `gh1_cmd`/`gl1_cmd` are `0` per the `.output` block, since
neither `state==ENERGY` nor `state==LOW_FREEWHEEL_TO_ZERO` nor
`state==LOW_BUILD_NEGATIVE` holds), so node `a1` is meant to resonate up
toward `vin` on its own via the stored `I(L1)` energy ringing through
`CH1`/`CS1`/`CL1`. With only `I_NEG=2.0A` of stored negative current
available at the handoff instant, the resulting ring's amplitude is far
too small: it only pulls `V(vin,xmod:a1)` down to `9.66V` before damping,
roughly `9.66V` short of the `0V` crossing the rule needs, and then
settles at a DC operating point (`~11.92V`) still far from the threshold.
Increasing `I_NEG` within the reachable range (`up to ~2.215A`, per
R04E23's own observed ceiling) is not expected to close a `~9.66V` gap
based on this run's own observed ring amplitude, though this report does
not run a sweep to confirm that quantitatively -- see Section 7.

## 3. The one netlist built

Built from `experiments/track_B_zero_start_extension/
R04E23_phase1_handoff_extended_tstop/cases/r04e23_neg2pct_t100us.cir`
(read-only, never modified) as the literal starting template. A `diff`
against it (comment lines excluded) confirms EXACTLY the ONE change
BOUNDARY.md Section 2 specifies, and nothing else:

```
< .param I_LIMIT=125 NEG_FRAC=.02 I_NEG={NEG_FRAC*I_LIMIT}
---
> .param I_LIMIT=125 NEG_FRAC=.016 I_NEG={NEG_FRAC*I_LIMIT}
```

`TSTOP=100u`, `I_LIMIT=125`, the bootstrapped initial conditions
(`VC1_IC=35.85894624845418`, `IL1_IC=75.96527862548828`), `CFLY=3u`, the
5-state `.machine` block's own rule structure, phases 2-4's own hardcoded
R04E3 configuration, the `WHEN`-based `.meas` lines, the `IL1_MIN`/
`IL1_MAX` `FROM 0 TO 20u` window, and `.options` are all byte-identical
to R04E23's own file (only the header/provenance comments carry no
simulated behavior).

A full run (not a separate truncated pilot, since this is a single cell
and R04E23's own two cells already confirmed the netlist family loads and
runs cleanly) completed with no topology/syntax error:
`Total elapsed time: 101.778 seconds` (LTspice-reported solver time,
longer than R04E23's own `~14s` cells because state 4's own resonant ring
forces a much finer solver step for roughly `80us` of the `100us` window,
not because of any error).

## 4. Full `.meas` output and state-transition timeline

Full `.meas` output, `cases/r04e24_neg1p6pct_t100us.log`:

```
t_energy_end: V(state_mon)=.5  AT 6.3702883197e-09
il1_energy_end: I(XMOD:L1) =125.01597397 at 6.3702883197e-09
t_low_side_zvs: V(state_mon)=1.5  AT 6.47330761463e-09
t_il1_zero: V(state_mon)=2.5  AT 1.63197919454e-06
t_neg_target: V(state_mon)=3.5  AT 2.2888839867e-06
Measurement "t_high_side_zvs" FAIL'ed
state_final: V(state_mon) =4 at 0.0001
il1_min: MIN(I(XMOD:L1) )=-2.00000190735 FROM 0 TO 2e-05
il1_max: MAX(I(XMOD:L1) )=125.390205383 FROM 0 TO 2e-05
vout_final: V(out) =1.77769621246e-08 at 0.0001
vc1_final: V(xmod:a1,xmod:x1) =36.0756149115 at 0.0001
vc2_final: V(xmod:a2,xmod:x2) =-2.78807852361e-08 at 0.0001
vc3_final: V(xmod:a3,xmod:x3) =-3.02944034303e-08 at 0.0001
```

State-transition timeline (directly from the `.raw` trace's own
`V(state_mon)` bucketing, cross-checked against the `.meas` output
above):

| Transition | State | Time | Note |
|---|---|---|---|
| `ENERGY -> HS_OFF_COMMUTATE_LOW` | `0->1` | `6.370e-9 s` | Identical to R04E22/R04E23's own value (unaffected by `NEG_FRAC`). |
| `HS_OFF_COMMUTATE_LOW -> LOW_FREEWHEEL_TO_ZERO` | `1->2` | `6.473e-9 s` | Identical to R04E22/R04E23's own value. |
| `LOW_FREEWHEEL_TO_ZERO -> LOW_BUILD_NEGATIVE` | `2->3` | `1.632e-6 s` | Identical to R04E22/R04E23's own value. |
| `LOW_BUILD_NEGATIVE -> COMMUTATE_HIGH_TO_ZVS` | `3->4` | **`2.289e-6 s`** | **NEW** -- `t_neg_target` PASSES for the first time in this experiment chain; `I(L1)` reaches `-I_NEG=-2.0A`, essentially exactly at R04E23's own observed natural peak (`-2.215A`, with the chosen `~10%` margin absorbed by solver-step/interpolation precision). |
| `COMMUTATE_HIGH_TO_ZVS -> BLOCK_P24_HANDOFF_UNKNOWN` | `4->5` | **never** (within `100us`) | `t_high_side_zvs` `FAIL`s. `V(vin,xmod:a1)` rings down to a minimum of `9.66V` immediately after state-4 entry, then damps to a `~11.92V` steady state -- never within `9.66V` of the `<=0V` threshold. |

**`STATE_FINAL=4`** at `t=100us`, confirming the machine is parked one
state further in than R04E22/R04E23's own state-3 parking, but still
short of state 5.

## 5. Current-safety check (`+/-250 A` bound)

Per BOUNDARY.md Section 6's explicit requirement, reported regardless of
outcome. Byte-level `.raw` scan (`scripts/check_fingerprint.py`, copied
from R04E23's own reference script, reusing `scripts/
ltspice_raw_parser.py` unchanged), all `465,821` saved points (the full
`100us` window):

| Quantity | Value |
|---|---:|
| `IL1_MAX` (full window) | `125.39020538330078 A` |
| `IL1_MIN` (full window) | `-2.000001907348633 A` |
| `max\|IL1\|` | `125.390 A` |
| Points `>250A` | `0` |

**Phase 1's own current stays well within the `+/-250A` engineering
bound throughout the full `100us` window.** The peak (`~125.4A`, at the
state-0/state-1 transition, identical to R04E22/R04E23's own value) and
trough (`-2.000A`, at `~2.29us`, now at the `I_NEG` target itself rather
than an unconstrained natural minimum) are both consistent with this
experiment's own design (BOUNDARY.md Section 6: "not expected to differ
materially on the positive side").

## 6. Solver-corruption fingerprint check

`scripts/check_fingerprint.py` (copied from R04E23's own reference
script, reusing `scripts/ltspice_raw_parser.py` unchanged) directly,
byte-level parsed the `.raw` file:

```
cases/r04e24_neg1p6pct_t100us.raw
  points: 465821
  rows_scanned: 465821
  dt_nonpos_count: 0
  dt_nonpos_examples: []
  vin_min: 0.0
  vin_max: 48.0
  implausible_vin_count: 0
  il1_min: -2.000001907348633
  il1_max: 125.39020538330078
  il1_max_abs: 125.39020538330078
  il1_over_250a_count: 0
  il1_over_250a_examples: []
```

Zero non-monotonic or duplicate timestamps across all `465,821` points
(`4.6x` more points than R04E23's own `100,356`, reflecting the much
finer solver step state 4's own resonant ring requires, not a
data-integrity issue); `V(vin)` stays exactly within its own commanded
`0-48V` step; no point exceeds the `+/-250A` current bound. **This trace
is confirmed free of the documented solver-corruption fingerprint
(R04E10, R04E16-R04E23).**

## 7. Discussion -- what this establishes about R04E21's own original hypothesis

**R04E21's diagnosed hypothesis (restated, unchanged since R04E21
BOUNDARY.md Section 1)**: the original `I_NEG=0.2A` (from R04E3's own
leftover zero-start-era `I_LIMIT=10A`) was too small to store meaningful
magnetic energy for the state-4 resonant ZVS ring, and rescaling
`I_LIMIT`/`I_NEG` to P24's own real `125A` scale might let the state-4
`V(vin,a1)<=0` event actually fire.

**This run finally exercises the mechanism the hypothesis is about, and
the result is a clean REFUTATION, not a confirmation.** With a directly
reachable, correctly-scaled `I_NEG=2.0A` (`125A` scale, `NEG_FRAC=.016`),
state 4 is entered for the first time in this chain -- yet the same
documented `V(vin,a1)<=0` stall recurs. The state-4 resonant ring's own
observed amplitude (`V(vin,xmod:a1)` reaching only `9.66V` at its
closest approach to the `0V` threshold) shows that the blocking factor is
not simply "not enough stored negative current" in the sense R04E21
diagnosed -- `I_NEG=2.0A` IS enough to exit state 3, but the resulting
ring is roughly `9.66V` short of what state 4's own exit condition
requires. Consequently:

- **It IS evidence against the hypothesis**: a reachable, non-trivial,
  correctly-`125A`-scaled `I_NEG` was directly exercised in the state-4
  ring, and it did not come close to unblocking the ZVS event.
- **It does NOT establish what WOULD unblock it.** This single cell does
  not test whether a larger (but still-reachable, i.e. within R04E23's
  own observed `~2.215A` natural ceiling) `I_NEG`, a different `CFLY`,
  different device capacitances, or a genuinely different circuit-level
  intervention would close the `~9.66V` gap. BOUNDARY.md Section 7 is
  explicit that this cell alone does not establish behavior across the
  full range of reachable targets.
- Per this project's own Ground Rule 7, this result is reported exactly
  as found: state 4 IS reached (a genuine, new, positive step relative
  to every prior cell in this chain), but the state-4 stall is NOT
  avoided, and the specific mechanism responsible (why the ring's
  amplitude falls so far short of the `0V` threshold) is described here
  only empirically (Section 2), not derived from a resonance-frequency/
  characteristic-impedance analysis, which this experiment does not
  attempt.

## 8. Explicit adherence to BOUNDARY.md Section 0/7 -- what this does NOT show

Same standing limitations as R04E21/R04E22/R04E23's own Section 7/8:

- **Not a P24 periodicity result.** This experiment says nothing about
  whether P24's own periodic steady-state is reachable; that question
  remains independently unresolved (R04E21 BOUNDARY.md Section 0),
  unaffected either way by this run's own outcome.
- **Not a four-phase handoff test.** Phases 2-4 were deliberately held
  at R04E3's own hardcoded, zero-energy, single-phase-isolation
  configuration throughout (unchanged from R04E21/R04E22/R04E23, per
  this experiment's own stated scope, BOUNDARY.md Section 0/3) --
  `VC2_FINAL`/`VC3_FINAL` both `~-3e-8 V` (numerically zero) at `100us`,
  consistent with this.
- **Not a validation of R04E3's own controller as "the" P24
  controller.** R04E3 itself is a phase-1-only local commutation test;
  this experiment inherits that same limitation unchanged.
- **Not a claim about what happens past state 5** -- state 5 is never
  reached here either.
- **Not a full characterization of the reachable `I_NEG` range**
  (`0` to `~2.2A`, per BOUNDARY.md Section 7). A single cell at
  `I_NEG=2.0A` refutes R04E21's own specific diagnosed hypothesis at
  this one point, but does not establish whether every reachable
  `I_NEG` value produces the same `~9.66V`-short stall, or whether some
  other reachable value (or a circuit-level change) behaves
  differently. A follow-up sweep within the reachable range, or a
  circuit-level intervention, is a natural next step, per BOUNDARY.md
  Section 7 -- not performed here, not assumed necessary in advance.
- Per Ground Rule 7, this result (state 4 reached, but the same stall
  recurring) carries the same reporting weight a "hypothesis confirmed"
  result would have received -- it is reported plainly, not minimized or
  dressed up.

## 9. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `NEG_FRAC=.016` (`I_NEG=2.0A`) | New for this experiment: derived directly from R04E23's own committed SPICE result (natural peak `-2.215A` at the bootstrapped operating point), chosen with `~10%` margin below that ceiling (BOUNDARY.md Section 4) | `SENSITIVITY_ONLY`, derived from this project's own prior committed result, not an external or paper-sourced value |
| Everything else (`I_LIMIT=125`, `TSTOP=100u`, `VC1_IC`, `IL1_IC`, `CFLY=3uF`, R04E3's own machine structure, phases 2-4's own hardcoded config, `IL1_MIN`/`IL1_MAX`'s own `FROM 0 TO 20u` window, `.options`) | Copied unchanged from R04E23's own already-verified netlist | inherited, unchanged (see R04E22/R04E23 `BOUNDARY.md`/`RESULTS.md` for original provenance) |

No new paper-sourced, cross-paper, or external-device data is
introduced. Neither R04E23's, R04E22's, R04E21's, nor R04E3's own
committed files or results were modified.

## 10. Classification

`SENSITIVITY_ONLY`, `NOT_P24_REPRODUCTION`, negative result (state 4
reached for the first time in this chain; R04E21's own diagnosed
hypothesis -- that a correctly-scaled, reachable `I_NEG` would unblock
the state-4 ZVS event -- is REFUTED, per BOUNDARY.md Section 6's second
anticipated outcome).
