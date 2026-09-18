# R04E26 - swapping R04E21's own initial condition for the math model's periodic-orbit state (RESULTS)

See `BOUNDARY.md` for the full scope statement, provenance and explicit
limitations. This document reports what actually happened; read Section 0
of `BOUNDARY.md` before interpreting anything below.

## 1. Outcome, stated plainly, first

**The pre-registered structural expectation (BOUNDARY.md Section 3) HOLDS
for the headline question, with an important quantitative caveat that is
reported plainly rather than smoothed over.**

Swapping only `VC1_IC` (`35.85894624845418V -> 35.8448V`, a `0.039%`
change) and `IL1_IC` (`75.96527862548828A -> 0.111A`, a `99.85%` change,
i.e. essentially a different starting regime -- below `I_LIMIT=10A`
instead of far above it) on R04E21's own exact netlist, with nothing else
touched (confirmed by `diff`, Section 2), reproduces R04E21's own
documented outcome at the structural level: **`STATE_FINAL=4`
(`COMMUTATE_HIGH_TO_ZVS`) at `TSTOP=20us`, and `T_HIGH_SIDE_ZVS` FAILs to
trigger, identical to R04E21.** The permanent stall recurs. This directly
confirms the pre-registered structural-insensitivity finding: the exact
starting value of `IL1_IC` does not determine WHETHER the machine parks
at state 4, because state `ENERGY`'s own unconditional exit rule
(`I(XMOD:L1)>=I_LIMIT`) gates every trajectory through the same `I_LIMIT
=10A` threshold before the interesting states begin, regardless of
whether the bootstrap starts far above it (R04E21, `75.97A`) or well
below it (R04E26, `0.111A`).

**However**, BOUNDARY.md Section 6's first bullet also anticipated "all
measured values within a fraction of a percent of R04E21's own committed
numbers" if this outcome held -- **that specific, stronger claim is NOT
accurate.** Several measurements diverge substantially from R04E21's own
values, most importantly `IL1_MAX` (`75.967A` vs `14.663A`, an `80.7%`
relative difference, `61.3A` absolute), `IL1_ENERGY_END` (`75.955A` vs
`10.016A`, `86.8%`), `VOUT_FINAL` (`80.9%`), and `T_NEG_TARGET` (`24.2%`
relative, `408ns` absolute -- not a rounding-level difference). This is
explained, not merely observed, in Section 4 below: starting BELOW
`I_LIMIT` (R04E26) versus already ABOVE it (R04E21) produces genuinely
different charge-up trajectories through states 0-1 even though both
trajectories are gated through the same `I_LIMIT=10A` threshold. The
"erasure" argument in BOUNDARY.md Section 3 is correct about the FINAL
STATE (state 4 is reached either way) but was not a claim that every
intermediate/early-transient quantity would also converge -- and indeed
several do not. This nuance is reported explicitly per the task's
instruction, not glossed over as a clean "everything matches."

## 2. The R04E26 netlist and its diff against R04E21

`experiments/track_B_zero_start_extension/R04E26_periodic_orbit_ic_swap/
cases/r04e26_periodic_orbit_ic.cir` was created as a byte-for-byte copy
of R04E21's own committed netlist (`R04E21_phase1_handoff_into_r04e3_
stall/cases/r04e21_phase1_handoff.cir`), then ONLY the `.param VC1_IC=...
IL1_IC=...` line was edited. `diff` against R04E21's own file confirms
exactly one changed line and nothing else:

```
49c49
< .param VC1_IC=35.85894624845418 IL1_IC=75.96527862548828
---
> .param VC1_IC=35.8448 IL1_IC=0.111
```

`I_LIMIT=10`, `NEG_FRAC=.02` (`I_NEG=0.2A`), `TSTOP=20u`, `CFLY=3u`, the
5-state `.machine` block, phases 2-4's hardcoded gate configuration
(`ic=0` on `CH1/CL1/CS2/CS3/L2/L3/L4`, `VGL2=VGATE` fixed ON, `VGH2/VGH3/
VGH4/VGL3/VGL4=0` fixed OFF), all 13 `.meas` statements, `.options`, and
`.tran 0 20u 0 1n UIC` are all unchanged from R04E21's own file, exactly
as BOUNDARY.md Section 2 specifies.

## 3. Run

Run via `tools/ltspice_runner.sh run` (the project's standard macOS/wine
LTspice launcher), one process at a time, confirmed via a blocking
`pgrep -f "LTspice.exe.*r04e26"` wait loop before proceeding. `.log`
confirms `Total elapsed time: 33.112 seconds` -- close to R04E21's own
`35.444 seconds` and, as expected, far under a minute (`I_LIMIT=10A`,
`TSTOP=20us`, not the `100us`/`125A` regime of R04E24/R04E25). The full
`.meas` block printed directly in the `.log` (no post-processing hiccup
this run, unlike R04E21's own Step-1 staging run).

Full `.meas` output (`cases/r04e26_periodic_orbit_ic.log`):

```
t_energy_end: V(state_mon)=.5  AT 1.22179360512e-09
il1_energy_end: I(XMOD:L1) =10.0157430792 at 1.22179360512e-09
t_low_side_zvs: V(state_mon)=1.5  AT 2.28994133495e-09
t_il1_zero: V(state_mon)=2.5  AT 1.63157274983e-06
t_neg_target: V(state_mon)=3.5  AT 2.09463020044e-06
Measurement "t_high_side_zvs" FAIL'ed
state_final: V(state_mon) =4 at 2e-05
il1_min: MIN(I(XMOD:L1) )=-0.200000599027 FROM 0 TO 2e-05
il1_max: MAX(I(XMOD:L1) )=14.6630678177 FROM 0 TO 2e-05
vout_final: V(out) =0.000123416466522 at 2e-05
vc1_final: V(xmod:a1,xmod:x1) =35.8512362662 at 2e-05
vc2_final: V(xmod:a2,xmod:x2) =-2.69210431725e-09 at 2e-05
vc3_final: V(xmod:a3,xmod:x3) =-3.18686943501e-09 at 2e-05
```

## 4. Full comparison table against R04E21's own committed values

| Measurement | R04E21 (published) | R04E26 (this cell) | Absolute diff | Relative diff | Note |
|---|---|---|---|---|---|
| `t_energy_end` (s) | `2.98294522065e-13` | `1.22179360512e-09` | `+1.2215e-09` | `+4.10e+05 %` | Both sub-ns, negligible vs `TSTOP=20us` (`~6e-5%` of the window either way). R04E26 takes longer because `IL1` must actually rise from `0.111A` up through `I_LIMIT=10A`; R04E21's own `IL1_IC=75.97A` already satisfied the rule at `t=0`. |
| `il1_energy_end` (A) | `75.9550563853` | `10.0157430792` | `-65.9393` | `-86.81%` | This IS the `I(XMOD:L1)` value at the `0->1` transition. R04E26's value (`~10.02A`) sits right at `I_LIMIT=10A` as expected (it had to charge up to the gate); R04E21's value reflects its already-elevated `IL1_IC` (no charging needed, transition instantaneous). This is the clearest direct evidence of the "erasure" mechanism working as BOUNDARY.md Section 3 predicted -- both trajectories are funneled through `~10A` at this transition regardless of starting point, just via different physical routes. |
| `t_low_side_zvs` (s) | `1.39754948686e-12` | `2.28994133495e-09` | `+2.2885e-09` | `+1.64e+05 %` | Both sub-ns, negligible vs `20us` window either way. |
| `t_il1_zero` (s) | `1.63068387739e-06` | `1.63157274983e-06` | `+8.889e-10` | `+0.0545%` | Close match -- by this point both trajectories have converged onto the same `IL1` decay-through-zero dynamics. |
| `t_neg_target` (s) | `1.68678613822e-06` | `2.09463020044e-06` | `+4.0784e-07` | `+24.18%` | Meaningful divergence, not a rounding artifact: R04E26 takes `~408ns` longer to build `IL1` down to `-I_NEG=-0.2A` after crossing zero. |
| `t_high_side_zvs` | FAIL (never) | FAIL (never) | -- | -- | **Identical outcome**: the `4->5` transition never fires in either cell. |
| `state_final` | `4` | `4` | `0` | `0%` | **Identical** -- both park at `COMMUTATE_HIGH_TO_ZVS`. |
| `il1_min` (A) | `-0.200048059225` | `-0.200000599027` | `+4.746e-05` | `-0.0237%` | Close match -- both sit essentially exactly at the `-I_NEG=-0.2A` threshold, as the `.machine` rule requires by construction. |
| `il1_max` (A) | `75.9670639038` | `14.6630678177` | `-61.3040` | `-80.70%` | Large, real divergence (not just relative -- `61.3A` absolute). R04E21's max is essentially its own elevated `IL1_IC`; R04E26's max is the overshoot reached while/just-after charging up through `I_LIMIT=10A` during the fast `0->1->2` transition sequence. |
| `vout_final` (V) | `0.000644895655569` | `0.000123416466522` | `-0.000521479` | `-80.86%` | Both numerically near-zero relative to the `1V` nominal `VOUT_REF` (no full P24 cycle occurs in this short, phase-1-only window either way), but not equal to each other. |
| `vc1_final` (V) | `35.86026322` | `35.8512362662` | `-0.0090270` | `-0.0252%` | Close match -- the flying capacitor holds its (slightly different) initial charge through the short run, as expected; tracks the `0.039%` `VC1_IC` input difference closely. |
| `vc2_final` (V) | `-1.60653144121e-08` | `-2.69210431725e-09` | `+1.337e-08` | `-83.24%` | Both numerically zero (nanovolt scale) -- phase 2 stays at R04E3's own hardcoded zero-energy configuration in both cells; the large relative-percent figure is an artifact of comparing two near-zero floating-point noise floors, not a meaningful physical difference. |
| `vc3_final` (V) | `-1.65891833603e-08` | `-3.18686943501e-09` | `+1.340e-08` | `-80.79%` | Same as `vc2_final` -- both numerically zero, relative-percent figure not physically meaningful. |

## 5. Discussion: which BOUNDARY.md Section 6 outcome was actually met

BOUNDARY.md Section 6 posed two outcomes:

- **"Outcome matches R04E21 closely (permanent stall at state 4, `T_HIGH_
  SIDE_ZVS` never fires, all measured values within a fraction of a
  percent of R04E21's own committed numbers)"** -- the FIRST half of this
  (permanent stall at state 4, `T_HIGH_SIDE_ZVS` never fires) is **exactly
  what happened**, and directly confirms the pre-registered structural-
  insensitivity expectation from Section 3: the specific value of
  `IL1_IC` does not determine whether the stall occurs, because state
  `ENERGY`'s own unconditional `I(XMOD:L1)>=I_LIMIT` exit rule gates every
  trajectory through the same current threshold regardless of starting
  point. This is the headline result and it is reported plainly as
  expected, not as a failed experiment, per the task's instruction.
- **The SECOND half of that same bullet ("all measured values within a
  fraction of a percent") does NOT hold** for several measurements
  (`il1_max`, `il1_energy_end`, `vout_final`, `t_neg_target` -- Section 4
  above), which diverge by `24%` to `87%`. This is reported explicitly,
  not smoothed over: BOUNDARY.md Section 3's own "erasure" argument was
  specifically about the FINAL STATE reached (both trajectories are gated
  through `I_LIMIT=10A`), not a claim that every intermediate quantity
  would also numerically converge -- and several genuinely do not,
  because charging up TO `I_LIMIT` from below (R04E26) is a physically
  different process from already starting ABOVE it and needing no
  charging at all (R04E21), even though both processes end at the same
  gate value and the same final parked state.
- **This is NOT the second bullet's "genuine surprise" either** (different
  final state, or ZVS reached) -- `state_final` and `t_high_side_zvs`'s
  FAIL status are identical between the two cells. The correct summary is
  a **partial/nuanced confirmation**: the structural claim (which state
  the machine ends up in) holds exactly; the stronger quantitative claim
  (near-identical values throughout) does not hold uniformly, and the
  reason it does not is itself informative (it shows precisely where the
  "erasure" argument is valid -- the final gated state -- and where it is
  not -- the early-transient trajectory shape and a few downstream
  quantities like `T_NEG_TARGET` and `IL1_MAX` that depend on that
  trajectory's details).

**Bottom line for the cross-track question this experiment was built to
probe (BOUNDARY.md Section 1)**: swapping in the periodic orbit's own
much smaller `IL1_IC=0.111A` value, instead of R04E17's own zero-start-
ramp-derived `75.97A`, does NOT change whether R04E3's own phase-1-only
controller reaches state 4 and stalls there -- the same permanent stall
recurs. This small-scope IC swap therefore cannot resolve the cross-track
discrepancy documented in `CONSOLIDATED_FINDINGS_2026-09-16.md`; as
BOUNDARY.md Section 3 anticipated, the larger, full-four-phase, real-
instantaneous-checkpoint alternative (not chosen this round) remains the
next step if that discrepancy is still worth pursuing.

## 6. Current-safety check (+/-250A bound)

Per BOUNDARY.md Section 6's explicit requirement, reported regardless of
outcome. Over the full `20us` run (all `189,804` saved points scanned
directly from the `.raw` trace, `scripts/check_fingerprint.py`, adapted
unchanged from R04E21's own script):

- `IL1_MAX = 14.663067817687988 A`
- `IL1_MIN = -0.20000059902668 A`
- `max(|IL1|) = 14.663 A`, comfortably inside `+/-250A` (and, notably,
  far smaller than R04E21's own `75.967A` peak -- see Section 4's
  discussion of `il1_max`).
- `0` points anywhere in the trace exceed `|I(xmod:L1)|>250A`.

**Phase 1's own current stays well within the `+/-250A` engineering bound
throughout this run**, exactly as BOUNDARY.md Section 6's third bullet
anticipated.

## 7. Solver-corruption fingerprint check

`scripts/check_fingerprint.py` (copied unchanged from R04E21's own
script, which itself reuses `ltspice_raw_parser.py`) directly, byte-level
parsed `cases/r04e26_periodic_orbit_ic.raw`:

```
points: 189804
rows_scanned: 189804
dt_nonpos_count: 0
dt_nonpos_examples: []
vin_min: 0.0
vin_max: 48.0
implausible_vin_count: 0
il1_min: -0.20000059902668
il1_max: 14.663067817687988
il1_max_abs: 14.663067817687988
il1_over_250a_count: 0
il1_over_250a_examples: []
```

Zero non-monotonic or duplicate timestamps across all `189,804` points;
`V(vin)` stays exactly within its own commanded `0-48V` step (no
overshoot, no undershoot, no orders-of-magnitude-impossible value); no
point anywhere exceeds the `+/-250A` current bound. **The trace is
confirmed free of the documented solver-corruption fingerprint (R04E10,
R04E16-R04E21).**

## 8. What this does and does not show (BOUNDARY.md Section 0/7, restated)

**What it shows**: swapping R04E21's own bootstrapped `VC1_IC`/`IL1_IC`
for the parallel math-model effort's own newly-solved periodic orbit's
reported average `VC1` and phase-current minimum, on R04E3's own
unmodified phase-1-only event-gated controller (`I_LIMIT=10A`,
`NEG_FRAC=.02` unchanged), does not avoid the documented
`COMMUTATE_HIGH_TO_ZVS` permanent stall. The pre-registered structural
explanation (state `ENERGY`'s own unconditional `I_LIMIT` exit gate)
is directly confirmed by the `il1_energy_end` values in Section 4: R04E26
climbs up TO `~10.02A` from `0.111A` at the `0->1` transition, while
R04E21 was already there. Both funnel through the same gate and both
subsequently park at the same state 4, waiting for the same `V(vin,
xmod:a1)<=0` event that never occurs in either cell (nor in R04E3's own
zero-start cell, nor in R04E5's own `600us` extension of it).

**What it does NOT show** (same standing limitations as R04E21-R04E25,
restated because they bear directly on how this result should be read):

- **Not a P24 periodicity result.** No genuinely closed periodic orbit
  has been found anywhere in this project by any method (BOUNDARY.md
  Section 0/R04E21 BOUNDARY.md Section 0); this experiment's negative
  result neither worsens nor improves that independent, unresolved
  question.
- **Not a four-phase handoff test.** Phases 2-4 were kept at R04E3's own
  hardcoded, zero-energy, single-phase-isolation configuration throughout
  -- their own real states (whether R04E17-bootstrapped or periodic-
  orbit-derived) were not fed in. A genuine four-phase handoff remains
  unbuilt and untested anywhere in this project.
- **Not a validation of R04E3's own controller as "the" P24 controller.**
  Unchanged limitation from R04E21.
- **Does not use the periodic orbit's own exact instantaneous state.**
  Only its period-averaged/extremal summary statistics were available
  (BOUNDARY.md Section 7); `IL1_IC=0.111A` is a stated approximation
  (the period MINIMUM used as a proxy for the pre-commutation
  instantaneous value), not an exact checkpoint match. If this
  approximation matters, only the larger, full-four-phase,
  real-checkpoint-data alternative (the option not chosen this round)
  can resolve it.
- **A positive result would not have meant more than it plainly said**,
  and this negative/partial result likewise should not be read as
  falsifying anything beyond this one narrow construction (IC-swap-only,
  into R04E3's own unmodified single-phase controller). Per this
  project's own Ground Rule 7, it is reported as-is, with the same weight
  a positive result would have received.

## 9. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `VC1_IC=35.8448 V` | `results/ZERO_START_AFFINE_PERIOD_FIXED_POINT.md`, "Average flying-capacitor voltages" row, quoted verbatim | `CROSS_PAPER_EXTENSION`-adjacent, from the parallel math-model effort's own already-published, self-consistency-checked result (map residual `2.6e-11`); not independently re-derived by this session |
| `IL1_IC=0.111 A` | Same source document, "Phase-current minima" row, quoted verbatim | Same category; additionally `SENSITIVITY_ONLY` in the sense that this is an approximation (period minimum used as a proxy for the pre-commutation instantaneous value), explicitly flagged (BOUNDARY.md Section 7) |
| Everything else (`I_LIMIT`, `NEG_FRAC`, `CFLY`, `TSTOP`, `.machine` block, phases 2-4 hardcoded config, all `.meas` statements) | R04E21's own already-committed netlist, unchanged | inherited, unchanged from R04E21 |

No new paper-sourced or external-device data is introduced. Neither
R04E21's, R04E17's, nor R04E3's own committed files or results were
modified.
