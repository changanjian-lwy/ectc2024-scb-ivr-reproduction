# R04E21 - phase-1 handoff into R04E3's own documented stall (RESULTS)

See `BOUNDARY.md` for the full scope statement, provenance and explicit
limitations. This document reports what actually happened; read Section 0
of `BOUNDARY.md` before interpreting anything below.

## 1. Outcome, stated plainly, first

**The same stall recurs.** Phase 1's own event-gated local commutation
chain, started from R04E17's own real bootstrapped state (`VC1_IC=
35.85894624845418 V`, `IL1_IC=75.96527862548828 A`) instead of true zero
energy, still parks permanently at state `4` (`COMMUTATE_HIGH_TO_ZVS`) --
the exact same state R04E3's own zero-start cell gets stuck at. `.log`
confirms `state_final: V(state_mon) =4 at 2e-05` (i.e. `STATE_FINAL=4` at
`TSTOP=20us`), and the measurement for the `4->5` transition itself
explicitly fails to trigger: `Measurement "t_high_side_zvs" FAIL'ed`.
The event this state is waiting for, `V(vin,xmod:a1)<=0` (the high-side
drain-source voltage reaching zero), never occurs anywhere in the
`20us` window, exactly as it never occurs anywhere in R04E3's own `20us`
window or R04E5's own `600us` extension of the same zero-start test.

This is one of the three outcomes BOUNDARY.md Section 6/7 explicitly
anticipated and treats as informative either way (Ground Rule 7): **the
bootstrapped current/voltage magnitude alone is not sufficient to unblock
the high-side ZVS event; whatever physically blocks it must depend on
something else** (the specific trajectory/phase relationship at the
handoff instant, not just the state magnitude) -- a genuinely informative
negative result, not a failure requiring rework, and not overridden by
how quickly the bootstrapped cell reaches the stall point (see Section 4
below).

## 2. Step 1: re-running R04E17's own cell to extract IL1_AT_TSTOP

`experiments/track_B_zero_start_extension/R04E17_divider_ramp_factorial_
isolation/cases/e17_div_f3_t68p61.cir` (protected, read-only) was copied
unmodified except ONE added line, `.meas tran IL1_AT_TSTOP FIND I(L1) AT
368.61u`, to
`experiments/track_B_zero_start_extension/R04E21_phase1_handoff_into_
r04e3_stall/staging_step1/e17_div_f3_t68p61_plus_il1_at_tstop.cir`. A
`diff` against R04E17's own original file confirms the only differences
are one added provenance comment line and the one `.meas` line -- no
circuit element, topology, parameter, or other `.meas` statement differs.

This copy was run in real LTspice (`Total elapsed time: 1625.463
seconds`, matching R04E17's own original `1641.488s` run of this exact
cell to within normal run-to-run variance). **The re-run's own `.log`
file did not print any `.meas` results** -- it ends with `unable to open
database file` immediately after `Total elapsed time`, an LTspice/wine
post-processing hiccup, not a simulation failure (the `.raw` trace itself
was fully written: `623,865,768` bytes, and independently parsing it
gives `no_points=8,208,737`, EXACTLY matching R04E17's own already-
published point count for `e17_div_f3_t68p61` -- direct confirmation the
underlying transient computation is byte-identical to R04E17's own
original run, only the `.log`'s own post-processing step misbehaved).

Because the `.log` was empty of `.meas` results, every one of R04E17's
own 18 already-published scalar `.meas` values was independently
recomputed directly from the `.raw` trace (`scripts/
extract_meas_from_raw.py`, reusing `scripts/ltspice_raw_parser.py`
copied unchanged from R04E20's own reference script), reproducing
LTspice's own `FIND ... AT` (linear interpolation between the two
straddling stored time points) and `MAX/MIN FROM 0 TO T` semantics. The
comparison against R04E17's own committed `results.json`:

| Value | Re-run (raw-extracted) | R04E17's own published | Match |
|---|---|---|---|
| `VC1_FINAL` | `35.85894624845418` | `35.8589462485` | exact (to published precision) |
| `VC2_FINAL` | `23.798443662380787` | `23.7984436624` | exact |
| `VC3_FINAL` | `11.857047256378324` | `11.8570472564` | exact |
| `VOUT_FINAL` | `1.005894050468494` | `1.00589405047` | exact |
| `VC1_AT_TRAMP` | `35.4370641708374` | `35.4370641708` | exact |
| `VC2_AT_TRAMP` | `23.4337670193745` | `23.4337670194` | exact |
| `VC3_AT_TRAMP` | `11.667610394535586` | `11.6676103945` | exact |
| `VOUT_AT_TRAMP` | `0.9901008009910583` | `0.990100800991` | exact |
| `IL1_MAX` | `154.7286834716797` | `154.728683472` | exact |
| `IL1_MIN` | `-22.616397857666016` | `-22.6163978577` | exact |
| `IL2_MAX`/`IL2_MIN` | `147.8518829345703`/`-21.16446876525879` | `147.851882935`/`-21.1644687653` | exact |
| `IL3_MAX`/`IL3_MIN` | `140.7939453125`/`-15.654163360595703` | `140.793945312`/`-15.6541633606` | exact |
| `IL4_MAX`/`IL4_MIN` | `143.34262084960938`/`-15.345710754394531` | `143.34262085`/`-15.3457107544` | exact |
| `VOUT_PK`/`VOUT_MIN` | `1.0254360437393188`/`0.0` | `1.02543604374`/`0.0` | exact |

**All 18 already-published values reproduce exactly**, confirming this
re-run is a faithful, byte-identical reproduction of R04E17's own
committed cell before the new value is trusted, satisfying BOUNDARY.md
Section 2's own requirement.

The one genuinely new value, not previously published anywhere in this
project:

**`IL1_AT_TSTOP = 75.96527862548828 A`** (interpolated `I(L1)` at
`t=368.61us`, i.e. `TSTOP` itself -- R04E17's own committed set only
had the `IL1_MIN`/`IL1_MAX` envelope over the whole run, not this
instantaneous value).

R04E17's own original file and committed `results.csv`/`results.json`
were not modified or re-run in place -- only this separate staging copy
was executed.

## 3. Step 2: the R04E21 handoff netlist

`experiments/track_B_zero_start_extension/R04E21_phase1_handoff_into_
r04e3_stall/cases/r04e21_phase1_handoff.cir` was built from `paper_locked/
02_ectc2024_main/spice/R04E3_P24_minimal_zero_start_event_cycle.cir`
(read-only, never modified) as the literal starting template. A `diff`
against R04E3's own file shows exactly the changes BOUNDARY.md Section 2
specifies and nothing else:

- `CFLY` changed from `{4*10u+2*4.7u+2*2.2u}` (`53.8uF`) to `3u`.
- One new `.param VC1_IC=35.85894624845418 IL1_IC=75.96527862548828`
  line added.
- `CS1 a1 x1 {CFLY} ic=0` -> `CS1 a1 x1 {CFLY} ic={VC1_IC}`.
- `L1 x1 out {LPHASE} Rser={RLDAMP} ic=0` -> `L1 x1 out {LPHASE}
  Rser={RLDAMP} ic={IL1_IC}`.
- The `.include` path, necessarily rewritten (different file location)
  but pointing to the SAME `GS61008T_typical_params.lib`.
- Header/provenance comments.

Everything else -- the 5-state `.machine` block, `I_LIMIT=10`,
`NEG_FRAC=.02`, `LPHASE`, `COUT=4.672m` (via R04E3's own
`8*220u+32*47u+64*22u` expression), GS61008T device data, `TRAIL=10p`,
all phase 2-4 hardcoded gate drives (`VGL2=VGATE` fixed ON, `VGH2/VGH3/
VGH4=0` fixed OFF, `VGL3/VGL4=0` fixed OFF), all `.meas` statements,
`.options`, `.tran 0 20u 0 1n UIC` -- is byte-identical to R04E3's own
file. `CH1`, `CL1`, `CS2`, `CS3`, `L2`, `L3`, `L4` all keep `ic=0`,
unchanged, per BOUNDARY.md Section 4's explicit scope decision.

A truncated-`TSTOP` pilot (`.tran` shortened to `200n`, not committed)
confirmed the netlist loads and simulates with no topology/syntax error
before the full run -- it already showed the immediate rapid initial
transitions consistent with `IL1_IC` starting well above `I_LIMIT`.

## 4. Step 3: full run, `.meas` output and state-transition timeline

Full run (`TSTOP=20us`, R04E3's own value, unchanged): `Total elapsed
time: 35.444 seconds` -- as expected, far shorter than the multi-hour
`TSTOP=300-370us` Track-B divider/ramp cells (R04E16-R04E20), since this
reuses R04E3's own short local-commutation timescale.

Full `.meas` output (`cases/r04e21_phase1_handoff.log`):

```
t_energy_end: V(state_mon)=.5  AT 2.98294522065e-13
il1_energy_end: I(XMOD:L1) =75.9550563853 at 2.98294522065e-13
t_low_side_zvs: V(state_mon)=1.5  AT 1.39754948686e-12
t_il1_zero: V(state_mon)=2.5  AT 1.63068387739e-06
t_neg_target: V(state_mon)=3.5  AT 1.68678613822e-06
Measurement "t_high_side_zvs" FAIL'ed
state_final: V(state_mon) =4 at 2e-05
il1_min: MIN(I(XMOD:L1) )=-0.200048059225 FROM 0 TO 2e-05
il1_max: MAX(I(XMOD:L1) )=75.9670639038 FROM 0 TO 2e-05
vout_final: V(out) =0.000644895655569 at 2e-05
vc1_final: V(xmod:a1,xmod:x1) =35.86026322 at 2e-05
vc2_final: V(xmod:a2,xmod:x2) =-1.60653144121e-08 at 2e-05
vc3_final: V(xmod:a3,xmod:x3) =-1.65891833603e-08 at 2e-05
```

State-transition timeline:

| Transition | State | Time | Note |
|---|---|---|---|
| `ENERGY -> HS_OFF_COMMUTATE_LOW` | `0->1` | `2.983e-13 s` | Fires essentially instantly: `IL1_IC=75.97A` already exceeds `I_LIMIT=10A` at `t=0`. |
| `HS_OFF_COMMUTATE_LOW -> LOW_FREEWHEEL_TO_ZERO` | `1->2` | `1.398e-12 s` | Also essentially instant (`V(xmod:x1)<=0` already satisfied by the bootstrapped state). |
| `LOW_FREEWHEEL_TO_ZERO -> LOW_BUILD_NEGATIVE` | `2->3` | `1.631e-6 s` | `IL1` decays from `~76A` through `0` over `~1.63us`. |
| `LOW_BUILD_NEGATIVE -> COMMUTATE_HIGH_TO_ZVS` | `3->4` | `1.687e-6 s` | `IL1` reaches `-I_NEG=-0.2A` (`il1_min=-0.200048059225A` matches this threshold almost exactly). |
| `COMMUTATE_HIGH_TO_ZVS -> BLOCK_P24_HANDOFF_UNKNOWN` | `4->5` | **never** | `t_high_side_zvs` FAILs; `V(vin,xmod:a1)<=0` never occurs through `t=20us`. |

**`STATE_FINAL=4`** confirms the machine is parked at
`COMMUTATE_HIGH_TO_ZVS` at `TSTOP`, the same state R04E3's own zero-start
cell parks at (and R04E5 confirmed persists to at least `600us` from true
zero energy). The bootstrapped cell reaches this SAME parked state far
faster (`~1.69us`, vs. R04E3's own zero-start cell needing to first build
up `IL1` from `0` to `I_LIMIT=10A` before even starting the chain) --
but arriving at the stall faster does not mean the stall is avoided; it
is the identical blocking condition.

`VC1_FINAL=35.860V` at `t=20us` is close to the bootstrapped
`VC1_IC=35.859V`, consistent with the flying capacitor holding its
charge through this short, phase-1-only local commutation (no full P24
cycle occurs). `VC2_FINAL`/`VC3_FINAL` are both `~1.6e-8 V`, i.e.
numerically zero -- consistent with phases 2/3 being held at R04E3's own
zero-energy, hardcoded-gate configuration throughout (BOUNDARY.md
Section 4; their own real R04E17-bootstrapped states were deliberately
not fed in, per this experiment's stated scope limit).

## 5. Current-safety check (`+/-250 A` bound)

Per BOUNDARY.md Section 7's explicit requirement, this is reported
regardless of outcome. Over the full `20us` run (all `193,606` saved
points scanned directly from the `.raw` trace):

- `IL1_MAX = 75.9670639038086 A`
- `IL1_MIN = -0.2000480592250824 A`
- `max(|IL1|) = 75.967 A`, comfortably inside `+/-250A`.
- `0` points anywhere in the trace exceed `|I(xmod:L1)|>250A`.

**Phase 1's own current stays well within the `+/-250A` engineering
bound throughout this run.** No handoff-instant current spike was
observed (the state-1/2 transitions occur at sub-picosecond timescales
purely because the bootstrapped state already satisfies their trigger
conditions, not because of a numerical discontinuity artifact -- `IL1`
itself simply continues its already-in-progress decay from `~76A`
smoothly, as the timeline in Section 4 shows).

## 6. Solver-corruption fingerprint check

`scripts/check_fingerprint.py` (adapted from R04E19/R04E20's own
reference script, reusing `scripts/ltspice_raw_parser.py` copied
unchanged from R04E20) directly, byte-level parsed
`cases/r04e21_phase1_handoff.raw`:

```
points: 193606
rows_scanned: 193606
dt_nonpos_count: 0
dt_nonpos_examples: []
vin_min: 0.0
vin_max: 48.0
implausible_vin_count: 0
il1_min: -0.2000480592250824
il1_max: 75.9670639038086
il1_max_abs: 75.9670639038086
il1_over_250a_count: 0
il1_over_250a_examples: []
```

Zero non-monotonic or duplicate timestamps across all `193,606` points;
`V(vin)` stays exactly within its own commanded `0-48V` step (no
overshoot, no undershoot, no orders-of-magnitude-impossible value); no
point anywhere exceeds the `+/-250A` current bound. **The trace is
confirmed free of the documented solver-corruption fingerprint
(R04E10, R04E16-R04E20).** The Step-1 re-run's `.raw` trace was
similarly confirmed intact via its exactly-matching point count against
R04E17's own published figure (Section 2); a full fingerprint scan of
that trace was not separately re-run here since Step 1 is a pure
re-measurement of an already-fingerprint-checked R04E17 cell, not a new
circuit.

## 7. Discussion -- what this does and does not show (BOUNDARY.md Section 0/4/8)

**What it shows, narrowly**: when phase 1's event-gated local
commutation controller (R04E3's own exact construct, `Cfly`-corrected to
`3uF`) is started from R04E17's own real, substantial bootstrapped state
(`VC1=35.86V`, `IL1=75.97A`) instead of true zero energy, it still parks
permanently at state `COMMUTATE_HIGH_TO_ZVS`, waiting for the same event
(`V(vin,xmod:a1)<=0`) that never occurs in R04E3's own zero-start cell
either. The bootstrap changes HOW FAST the chain reaches the stall point
(`~1.69us` instead of needing to first build current from zero) but does
not change WHETHER the stall occurs. This directly answers this
experiment's own narrow question (BOUNDARY.md Section 6) in the
negative: **bootstrapped current/voltage magnitude alone, at the handoff
instant, is not sufficient to unblock the high-side ZVS event.**
Whatever physically blocks `V(vin,a1)` from reaching zero must depend on
something else -- most plausibly the specific state trajectory or
phase relationship among all four phases at the moment high-side turn-on
is attempted, not simply "is there enough current/voltage present."
This experiment does not identify what that "something else" is; it
only demonstrates that this one specific candidate explanation (raw
magnitude) is not it.

**What it does NOT show** (BOUNDARY.md Section 0/4/8, restated because it
bears directly on how this negative result should be read):

- **Not a P24 periodicity result.** This experiment says nothing about
  whether P24's own periodic steady-state is reachable; per the 2026-
  09-18 research pass recorded in BOUNDARY.md Section 0, no genuinely
  closed periodic orbit has been found anywhere in this project by any
  method, and this experiment's own negative result neither worsens nor
  improves that independent, unresolved question.
- **Not a four-phase handoff test.** Phases 2-4 were deliberately held
  at R04E3's own hardcoded, zero-energy, single-phase-isolation
  configuration throughout (Section 4/BOUNDARY.md Section 4) -- their
  own real R04E17-bootstrapped currents were discarded, not fed in. A
  genuine four-phase handoff, where all four phases' own real states and
  a shared four-phase controller interact, remains unbuilt and untested
  anywhere in this project. It is entirely possible (untested here) that
  a real four-phase handoff, where phases 2-4 also carry real current and
  their own gate states are not artificially frozen, behaves differently
  -- this experiment cannot speak to that either way.
- **Not a validation of R04E3's own controller as "the" P24 controller.**
  R04E3 itself is a phase-1-only local commutation test, not a claimed
  reproduction of P24's own full control law; this experiment inherits
  that same limitation unchanged.
- **A positive result would not have meant more than it plainly said**,
  and this negative result should likewise not be read as "the handoff
  concept is falsified" -- only that this one specific, narrow
  construction of it (bootstrap magnitude alone, into R04E3's own
  unmodified single-phase controller) does not unblock the stall. Per
  Ground Rule 7, this negative result is reported as-is, with the same
  weight as a positive one would have received.

## 8. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `CFLY=3uF` | R04E8's own corrected value, matching R04E16/R04E17's own bootstrap `Cfly` | `SENSITIVITY_ONLY`, inherited (per BOUNDARY.md Section 5) |
| `VC1_IC=35.85894624845418`, `IL1_IC=75.96527862548828` | R04E17's own `e17_div_f3_t68p61` cell, re-run unmodified except one added `.meas` line (this document's Section 2); `VC1_IC` cross-verified against R04E17's own already-published `VC1_FINAL` value to full precision; `IL1_IC` newly extracted, not previously published | inherited, re-measured not re-derived |
| R04E3's own event-gating logic, `I_LIMIT`, `NEG_FRAC`, all phase 2-4 hardcoded gate drives | `paper_locked/02_ectc2024_main/spice/R04E3_...cir`, unchanged | scope decision / this project's own construct, not a paper value (unchanged from R04E3's own classification) |
| Phases 2-4 kept at `ic=0` and R04E3's own hardcoded config | Explicit BOUNDARY.md Section 4 scope decision, not a paper value | scope decision |

No new paper-sourced, cross-paper, or external-device data is
introduced. This experiment recombines R04E3's own controller and
R04E17's own bootstrap state (both already-existing, already-justified
constructs) with one corrected parameter (`Cfly`) and one newly-measured
initial condition; nothing here is claimed as P24-published behavior.
Neither R04E3's nor R04E17's own committed files or results were
modified.
