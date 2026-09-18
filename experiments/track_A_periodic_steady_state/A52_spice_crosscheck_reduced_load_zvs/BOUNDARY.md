# A52 - SPICE cross-check of A51's four-phase joint ZVS state (BOUNDARY)

Track: A (periodic steady-state reproduction). Direct continuation per
explicit user direction 2026-09-18 ("要不试一下 数学上都成立 那物理上可以
试一下 主要是那个switching sequence一定要符合要求" -- since it holds up
mathematically, try it physically; the switching sequence above all must
be faithful to what was actually solved).

## 0. Scope statement

This is the first attempt in this project's history to build a real
SPICE netlist that reproduces a four-phase joint periodic ZVS state
found by A51's own fast Python solver -- not a new search, a
**faithfulness check**: does the same physical assumptions (real device
capacitance, genuine event-driven dead time, the same fixed-Ton timing),
implemented independently in LTspice, reproduce the same ZVS verdicts
A51 found? A negative result (SPICE disagrees with A51) is exactly as
valuable as a positive one -- it would mean A51's own descriptor
model has a bug or a missing physical effect, which is important to
know regardless. This does not, on its own, constitute a P24
reproduction claim even if it succeeds (Section 7).

## 1. Why a corrected initial state is used, not A51's own headline 190 W state

A51's headline 190 W result used `switch_on_resistance_ohm=1e-6`
(near-ideal) for BOTH high and low sides -- not GS61008T's own real
`RDS(on)=7 mOhm`. Before designing this SPICE check, this was tested
directly (not assumed): re-solving A51's own fixed point with
`switch_on_resistance_ohm=0.007` (GS61008T's real value) at the SAME
`module_power_w=190` **nominal** target converges to a DIFFERENT
self-consistent state, at **89.92 W actual delivered power** (real
`I^2R` conduction loss means the same `RLOAD` sizing no longer delivers
the nominal figure once realistic resistance is present) -- but **still
with all four phases achieving natural ZVS**, in fact converging more
tightly (relative residual `6.615932e-09` vs the idealized case's
`4.778832e-07`). **This corrected, realistic-resistance state is what
this experiment reproduces in SPICE**, not the idealized-resistance 190 W
state, so the SPICE build's own physics (which will necessarily use a
real device on-resistance) matches what was actually verified in Python,
not a state that used a resistance SPICE cannot reproduce.

This corrected state's own key numbers (`switch_on_resistance_ohm=
0.007` applied uniformly to BOTH high and low sides -- see Section 2 for
why this, not GS61008T's real asymmetric `RHS=7 mOhm`/`RLS=3.5 mOhm`,
is what must be reproduced):

- Converged relative residual: `6.615932e-09`
- All four `natural_zvs_flags`: `True`
- Average output: `0.687944 V`
- Average load power: `89.9207 W`
- Flying-capacitor voltages at `z*`: `36.26436257816223 / 24.057883410105077 /
  11.848978820087002 V`
- Phase-current minima: `-17.166145365989944 / -17.645141090205275 /
  -17.644991611244066 / -16.48984425591089 A`
- Phase-current maxima: `100.2496806732419 / 99.10677593353833 /
  99.10590262704727 / 97.81474727796696 A`
- Full 20-variable state vector (`solver_copy`'s own `variable_names`
  order): `['src','src_r','vin','tap3','tap2','tap1','a1','a2','a3','x1',
  'x2','x3','x4','out','LPAR_IN','L1','L2','L3','L4','I_VSTEP']` =
  `[48.00000000687211, 47.96569022236729, 47.969789939303524, 36.0, 24.0,
  12.0, 48.00677396673983, 24.036209731129393, 11.636445707833776,
  11.742411388577601, -0.02167367897568295, -0.21253311225322608,
  -0.4715756542261936, 0.6878908393606893, 3.4309784504693295,
  -5.202377626634099, 3.07242026743103, 30.358686656836504,
  67.36321312878287, -3.43097845046932]`

Independently re-verified per-phase (step-size-converged, matching A51's
own established discipline) via `run_final_verification.py` pointed at
this state before this boundary was finalized -- see Section 4 for the
per-phase crossing targets this experiment's own SPICE result must be
compared against.

## 2. What "the switching sequence must be faithful" means precisely, and the known simplification carried over from A51

Per the user's own explicit emphasis, this section is the most important
one in this document.

**A51's own model** (`solver_copy/zero_start_descriptor.py`'s extended
`commanded_pwm_mode`) commands, per phase, with `d=dead_time_s`, `Ton`
fixed, `T=200 ns` the period, and each phase's own `T/4`-staggered
nominal edge:

```
local in [0, d/2)              DEADTIME  (turn-on window, tail)
local in [d/2, Ton-d/2)         HIGH
local in [Ton-d/2, Ton+d/2)     DEADTIME  (turn-off window)
local in [Ton+d/2, T-d/2)       LOW
local in [T-d/2, T)             DEADTIME  (turn-on window, head)
```

with BOTH dead-time windows centered exactly on the original, unmodified
`T/4`-shifted edges (verified by direct code reading, Section 3 of A50's
own `BOUNDARY.md`, re-confirmed here). **Within a dead-time window, the
NEXT state (LOW after turn-off, HIGH after turn-on) is entered at
whichever comes first: a natural zero-voltage crossing of the relevant
switching node, or the window's own commanded end** (`resolve_deadtime_
window`'s own logic, reused unchanged throughout A50/A51). This is
EXACTLY the behavior the SPICE netlist must reproduce -- not an
approximation of it. The implementer must build this as a genuinely
event-gated transition (natural crossing OR commanded timeout, whichever
is first), not a fixed-delay approximation of one or the other.

**One known, deliberate simplification is carried over unchanged from
A51, not silently "fixed" here**: A51's `ZeroStartBoundary` has a single
scalar `switch_on_resistance_ohm` applied to BOTH high and low sides
identically -- unlike A37/A42/A49's own more physically detailed
`RHS=7 mOhm` (1 high-side device) / `RLS=3.5 mOhm` (2 parallel low-side
devices, per P25 Table III's own population). **This experiment's SPICE
netlist must use the SAME uniform `Ron=7 mOhm` for every switch (high and
low, all four phases)** -- NOT the asymmetric `RHS`/`RLS` A37/A42/A49
use -- because Section 1's own initial state was solved under that exact
uniform-resistance assumption. Using the more realistic asymmetric values
here would silently test a DIFFERENT physical model than the one whose
state is being reproduced, defeating the entire purpose of a faithfulness
check. Testing the asymmetric, more realistic `RHS`/`RLS` combination is
a legitimate and likely valuable follow-up, but it requires FIRST
re-solving A51's own fixed point under that assumption (a cheap Python
re-run) to get a self-consistent state to seed -- not performed here,
explicitly out of scope (Section 7).

**Switch capacitance remains correctly asymmetric** (unlike resistance):
`CH=385 pF` (one high-side device's own `Co(tr)`, `GS61008T_COTR_0_50V`
from `paper_locked/04_component_models/GS61008T_typical_params.lib`),
`CL=770 pF` (two low-side devices in parallel, `2 x CH`) -- this matches
A42/A37/A49/A51 exactly and must not be changed.

**Before building the full four-phase netlist, the implementer must
pilot-test whatever LTspice mechanism they choose for the "natural event
OR commanded timeout, whichever first" transition** on a small, isolated
single-transition case (mirroring this project's own established
`R04E16` "pilot-first" discipline) -- confirm via `.meas` that: (a) a
forced/timeout transition at the correct commanded instant occurs when
the natural crossing does NOT happen before it, and (b) an early,
event-triggered transition at the correct crossing instant occurs when
it DOES. Do not proceed to the full build until both are confirmed
working correctly in the pilot.

**Derive the exact numerical window boundaries in Python, not by hand.**
To eliminate any risk of a manual arithmetic/offset-sign transcription
error, the implementer must import `solver_copy` directly and call
`commanded_pwm_mode`/inspect `ZeroStartBoundary`'s own `on_time_s`/
`period_s` to PRINT the exact absolute-time HIGH/DEADTIME/LOW window
boundaries for all four phases over the specific period being built,
and use those printed numbers directly in the netlist's own `.param`
values -- do not re-derive the `T/4`-offset formula independently by
hand.

## 3. What this experiment cannot reuse from A37/A42/A49's own `.machine`

A37/A49's own `.machine` construct gates LOW-to-HIGH commutation on a
NEGATIVE-CURRENT THRESHOLD (`I(Lk)<=-INEG`), not a fixed dead-time
duration -- a structurally different model A51 does not use at all (A51
has no `INEG`/current-threshold concept anywhere). **Do not reuse A37/
A49's own `.machine` state structure** -- it encodes the wrong physical
assumption for this specific cross-check. A new, simpler machine (per
Section 2's fixed-Ton-plus-symmetric-dead-time schedule) is required.

## 4. Validation target -- A51's own per-phase predictions at the corrected state

Produced by `run_final_verification.py` (A51's own already-committed
script, reused read-only) run against Section 1's own corrected state,
with step-size convergence (`50 ps` down to `0.0625 ps`) on every phase
before trusting any crossing claim, per A50/A51's own established
discipline. **All four phases independently confirmed to achieve natural
ZVS** at this state:

| Phase | Window start (abs, s) | Window end (abs, s) | `iL` at window entry (A) | Initial `Vds` (V) | Natural ZVS | Crossing time (relative to window start, ns) | Min `\|Vds\|` at finest sub-step (V) |
|---|---:|---:|---:|---:|:---:|---:|---:|
| 1 | `2.319892500e-05` | `2.320107500e-05` | `-17.157444` | `11.579036` | **True** | `1.128389` | `0.000114` |
| 2 | `2.304892500e-05` | `2.305107500e-05` | `-17.636990` | `11.822603` | **True** | `1.122660` | `0.000239` |
| 3 | `2.309892500e-05` | `2.310107500e-05` | `-17.636853` | `11.822824` | **True** | `1.122732` | `0.000153` |
| 4 | `2.314892500e-05` | `2.315107500e-05` | `-16.483221` | `11.472413` | **True** | `0.858292` | `0.000233` |

(Each window is `2.15 ns` long, i.e. `dead_time_s`; the crossing time
column is the natural zero-voltage-crossing instant, measured from the
window's own start, at which the relevant switching node's `Vds`
reaches zero -- comfortably inside each `2.15 ns` window with `0.6-1.0 ns`
of margin remaining. Phase 4 crosses earliest, consistent with A51's own
finding that phase 4's own participating capacitance is smaller than
phases 1-3's.)

**Comparison tolerance, pre-declared before the SPICE run**: a crossing
time agreement within `20%` (matching A50's own pre-declared tolerance
against A42, which the actual result beat by roughly `10x`) is treated as
confirming agreement; a larger deviation must be reported plainly, not
explained away. All four phases must independently show a natural
crossing (not a forced/hard turn-on) for this experiment's own headline
success condition (Section 6) to be met.

Full state-space sensitivity data, free-resonance probes (confirming no
longer dead time would change any phase's own crossing status), and
measured per-phase participating capacitance (phases 1-3: not shown here
for brevity, see the verification's own JSON; phase 4: `1054.5 pF`,
consistent with A51's own `~1155 pF` structural estimate for phase 4 to
`~10%`) are available in `/tmp/final_verify_realistic_rds.json` at the
time this boundary was written -- the implementer should re-run
`run_final_verification.py` against Section 1's own state fresh if a
complete, permanent copy of this data is needed (not copied into this
repository here, since it is fully reproducible from Section 1's already-
quoted state plus A51's own already-committed script).

Safety at this state (already independently confirmed): max `|iL|` =
`100.2497 A`, well within the `+/-250 A` bound.

## 5. Provenance of every value

| Value | Source | Category |
|---|---|---|
| Initial state (Section 1) | A51's own re-solve (this document, Section 1), independently re-verified before this boundary was finalized | `CROSS_PAPER_EXTENSION`-adjacent, `SENSITIVITY_ONLY` (not a P24 operating point -- reduced-load state) |
| `CH=385 pF`, `CL=770 pF` | GS61008T datasheet `Co(tr)`, `paper_locked/04_component_models/GS61008T_typical_params.lib` | `EXTERNAL_DEVICE_DATA` |
| `Ron=7 mOhm` (uniform, both sides) | A51's own simplification (Section 2), deliberately NOT corrected to the more realistic asymmetric `RHS`/`RLS` here | `NUMERICAL_IDEALIZATION`, inherited, explicitly not the more detailed A37/A42 convention |
| `CFLY=3 uF` | `R04E8`/`A49`/`A51`'s own already-established correction | `NUMERICAL_IDEALIZATION`-adjacent |
| `dead_time_s=2.15 ns`, `Ton=16.6667 ns`, `T=200 ns` | A51's own boundary, `A48`'s own practical bracket | `SENSITIVITY_ONLY`, inherited |
| Everything else | See A37/A42/A48/A50/A51 `BOUNDARY.md` for original provenance | unchanged |

## 6. Success/failure conditions

- **SPICE independently confirms all four phases achieve natural ZVS,
  at crossing times/voltages matching A51's own predictions (Section 4)
  within a stated, pre-declared tolerance**: this would be the first
  SPICE-confirmed four-phase joint ZVS periodic state in this project's
  history. Report prominently.
- **SPICE confirms ZVS for some but not all phases, or at materially
  different times/voltages than predicted**: report exactly which
  phase(s) disagree and by how much -- this would identify a genuine gap
  between A51's own descriptor-model physics and real SPICE physics
  (e.g. a modeling simplification in the descriptor that matters more
  than expected), which is important and reportable regardless of being
  a "negative" result for A51.
- **SPICE fails to reproduce the periodicity itself** (state drifts
  materially over the tested period, not just the ZVS verdicts): would
  suggest the seed state itself (Section 1) was not accurately
  transcribed, or a genuine physics gap between the two models beyond
  just the switching event -- investigate and report which, not both is
  assumed silently.
- Every phase current must stay within `+/-250 A` throughout (Section 1's
  own state already has all currents well under `120 A`; not expected to
  differ materially).

## 7. What this experiment cannot prove

- Does not test the more realistic asymmetric `RHS`/`RLS` (Section 2) --
  a natural, valuable follow-up requiring its own fresh Python re-solve
  first, not performed here.
- Does not test P24's own rated 250 W operating point (Section 1's own
  state is `SENSITIVITY_ONLY`, not a P24 operating point).
- A positive result would NOT itself constitute a P24/P25 reproduction
  claim -- it would confirm the descriptor model's own physics against
  independent SPICE physics at one specific, reduced-load operating
  point, motivating further work (rated-load search, asymmetric
  resistance, nonlinear `Coss(V)`), not concluding it.
- Does not modify `src/scb_ivr/`, A37/A42/A48/A50/A51's own committed
  files -- imports A51's own already-committed `solver_copy` and result
  files read-only.
- Does not attempt any device other than GS61008T, nor the P24-primary
  `1-2%` branch (not applicable here -- A51's own model has no
  negative-current-fraction concept at all, only fixed-Ton timing).
