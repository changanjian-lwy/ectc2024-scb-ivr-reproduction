# A50 result - a ZVS-capable copy of the parallel math model's fast periodic solver

Track: A. Python-solver prototyping experiment, not a SPICE experiment.
Boundary: `BOUNDARY.md` in this directory (unmodified by this run).

**Verdict: BOTH acceptance gates passed.** Per `BOUNDARY.md` Section 6 point 3
the prototype may therefore be reported as validated for the single-phase local
case. The four-phase joint case was **not** attempted and remains out of scope
(Section 7).

All numbers below are produced by the four scripts in this directory and
recorded in `results.json`; nothing is quoted from memory.

---

## 0. The copy-not-modify constraint (BOUNDARY.md Section 0)

`solver_copy/` holds byte-for-byte copies of the seven named `src/scb_ivr/`
modules. The only edit applied on copying was rewriting `from scb_ivr.X import`
into the package-relative `from .X import`, plus a new `__init__.py`. Every
script asserts, before and after its run, that no module named `scb_ivr` or
`scb_ivr.*` exists in `sys.modules` and that no loaded `solver_copy` module
resolves to a file under `src/scb_ivr/`. **`src/scb_ivr/` is never opened for
writing by this experiment and is never imported by it.** `git diff` on this
branch touches zero paths under `src/scb_ivr/`.

---

## 1. Gate 1 - regression (BOUNDARY.md Section 6 point 1)

Reproduces `results/ZERO_START_AFFINE_PERIOD_FIXED_POINT.md` through the copy,
at that document's own frozen boundary -- which is exactly `ZeroStartBoundary`'s
dataclass defaults (one 250 W module, four phases, 48 V -> 1 V, 5 MHz,
`Lphase = 1.4666667 nH`, `Cfly = 3 uF`, `Cdiv = 300 uF`, 22.87 us input ramp) --
at the start time and step size used by the script that produced the published
numbers, `scripts/solve_zero_start_affine_period.py`: the first whole PWM period
at or after the end of the ramp (`23.0 us`) and `--step-ns 0.0625`.

Run: `python3 run_regression_gate.py --step-ns 0.0625 --output regression_gate.json`

| Quantity | Published | A50 `solver_copy` | Status |
|---|---:|---:|---|
| Map (fixed-point) residual, inf-norm | `2.6e-11` | `2.573585788923083e-11` | reproduced |
| One-period orbit closure, inf-norm | `2.3e-8` | `2.2228078933039797e-08` | reproduced |
| Map size / least-squares rank / nullity | 20 / 17 / 3 | 20 / 17 / 3 | exact |
| Diode complementarity over the orbit | valid | valid | exact |
| Average output voltage | `1.00601 V` | `1.0060079937506097 V` | exact to every published digit |
| Average one-module load power | `253.013 W` | `253.01302135384827 W` | exact to every published digit |
| Average flying-capacitor voltages | `35.8448 / 23.8863 / 11.9278 V` | `35.84478256507729 / 23.88631071494739 / 11.927838961696613 V` | exact to every published digit |
| Phase-current maxima | `125.879 / 125.554 / 125.554 / 125.891 A` | `125.87897118728735 / 125.5543781585899 / 125.55437480794959 / 125.89085137712313 A` | exact to every published digit |
| Phase-current minima | `0.111 / -0.214 / -0.214 / 0.123 A` | `0.11088801335147373 / -0.2136240933081225 / -0.21362071361338256 / 0.12349436705354273 A` | exact to every published digit |
| Average input-inductor current | `5.298 A` | `5.298268101741384 A` | exact to every published digit |

Two stronger statements than the table:

1. **Bit-for-bit against the live original.** `scripts/solve_zero_start_affine_
   period.py --step-ns 0.0625` was run against the real `src/scb_ivr/` and every
   one of the quantities above, plus the residual and the closure, compares
   **equal as IEEE-754 doubles** to the `solver_copy` run. The copy has no
   transcription bug.
2. **Bit-for-bit after the Section-3 extension.** The regression was re-run
   through the fully extended copy (`dead_time_s = 0.0`,
   `switch_capacitance = None`, the new three-state `Mode`, the new capacitance
   code path) and is again **bitwise identical**: residual
   `2.573585788923083e-11` and closure `2.2228078933039797e-08` to the last bit,
   with all twenty period metrics equal as doubles. The extension is an exact
   no-op at its defaults.

One documentation note, stated because it is a difference and not because it
matters: the published closure is written `2.3e-8`; the value both the original
and the copy actually produce is `2.2228e-8`, which rounds to `2.2e-8`. The
published map residual `2.6e-11` rounds correctly from `2.5736e-11`. This is a
rounding in the prose of a 2026 document, not a numerical disagreement -- the
original and the copy agree exactly.

Independent extension self-tests (`run_extension_tests.py`, all pass):

- `dead_time_s = 0` returns **bit-identical** high-side booleans to a verbatim
  transcription of the pre-A50 `commanded_pwm_mode`, with the low side exactly
  complementary and no phase ever in dead time, over 140k+ sampled instants
  (dense grids, every exact edge, and 40k reproducible random times);
- `next_pwm_edge_s` is bit-identical at `dead_time_s = 0` over the same set;
- `switch_capacitance = None` and `CommutationCapacitance(0, 0)` give bitwise
  equal `E`, `A` and `r`; with `385 pF / 770 pF` the capacitance appears on all
  eight switch branches (`vin-a1`, `a1-a2`, `a2-a3`, `a3-x4`, `x1..x4-gnd`);
- with `dead_time_s = 10 ns` the schedule is HIGH -> DEADTIME -> LOW -> DEADTIME
  with durations `Ton - d`, `T - Ton - d` and `2d`, both dead-time windows
  centered on the original `T/4`-shifted edges, and no commanded shoot-through.

**Gate 1: PASS.**

---

## 2. What was added, in the copy only (BOUNDARY.md Section 3)

1. `ZeroStartBoundary.dead_time_s: float = 0.0` and
   `ZeroStartBoundary.switch_capacitance: CommutationCapacitance | None = None`.
2. `Mode` now carries independent `high_side_on` and `low_side_on` 4-tuples;
   both `False` for a phase is dead time, both `True` is rejected as a commanded
   shoot-through. A helper `complementary_mode(...)` rebuilds the original
   strictly-complementary mode, so every pre-A50 call site keeps its exact
   original meaning. Every `Mode(` construction in the copy was updated
   (`commanded_pwm_mode`, `hybrid_step_from_named_state`, `_candidate_step`),
   and `advance_complementarity_step` / `advance_fixed_diode_step` now pass the
   commanded low side through as well.
3. `commanded_pwm_mode` emits the dead-time schedule described above when
   `dead_time_s > 0`, and takes the verbatim original code path when it is `0`.
4. `assemble_descriptor` adds parallel capacitance at every switch branch using
   the file's own existing `add_capacitance` helper, from
   `switch_capacitance.high_total_f` / `.low_total_f`, or `0.0` when `None`.
5. New `resolve_deadtime_window(...)` in `zero_start_hybrid_solver.py`: steps a
   commanded dead-time interval on a uniform sub-step grid (default `50 ps`)
   using `advance_fixed_diode_step` **unchanged**, and returns the minimum
   observed `|V(high-side node, next node)|`, the time it occurred, and whether
   it crossed below a stated tolerance (default `1 mV`) before the commanded
   window end. It additionally returns the signed minimum, the linearly
   interpolated sign-change instant (the quantity comparable with a SPICE
   `.meas ... WHEN V(...)=0`), the phase current there, and the worst normalized
   linear-system backward error over the window.

One change beyond the five listed, made because leaving it out would have left
the solver internally inconsistent with dead time: `next_pwm_edge_s` now reports
the four real gate transitions `start -/+ d/2`, `end -/+ d/2` when
`dead_time_s > 0`. It is bit-identical to the original when `dead_time_s = 0`
(verified). No function signature changed except
`hybrid_step_from_named_state`, which gained an optional trailing
`low_side_on = None` that defaults to the original complementary meaning.

---

## 3. Gate 2 - A42 single-phase validation (BOUNDARY.md Section 6 point 2)

### 3.1 The topology discrepancy, and how it was resolved

`BOUNDARY.md` Section 6 anticipated that an exact single-phase-isolated replica
might not be possible. It is not, in the naive sense: this framework's
descriptor is four-phase-only and has no way to instantiate one isolated phase.
A42's netlist is a deliberately isolated cell --

```
vin(48 V hard) --SH1--+--CH1(385p)--+ a1 --CF1(53.8u)-- x1 --CL1(770p)-- gnd
                                          x1 --SL1-- gnd
                                          x1 --L1(1.4666667 nH, Rser=1u)-- out(1 V hard)
```

-- whereas the descriptor's switch branches are the series-capacitor ladder
`vin-a1, a1-a2, a2-a3, a3-x4` (high side) and `x1..x4-gnd` (low side).

The four candidate switching nodes are **not** equivalent, and this is the key
finding of the construction step:

- Phase 1's switching node `x1` reaches `a1` through the flying capacitor, and
  `a1` carries **two** high-side switches, `CH1` (`vin-a1`) and `CH2`
  (`a1-a2`). With the `385 pF / 770 pF` plug-in, `x1` would commutate
  `770 + 385 + 385 = 1540 pF` -- a **33% capacitance excess** over A42's own
  `1155 pF`. Phases 2 and 3 are worse.
- Phase 4's switching node `x4` is touched by exactly three elements: its own
  low-side capacitance `CL4` (`x4-gnd`, 770 pF), its own high-side capacitance
  `CH4` (`a3-x4`, 385 pF) and `L4` (`x4-out`). Nothing else in the ladder
  connects to `x4`. Holding phase 3's low side on pins `x3` at the ground
  reference, which makes `a3 = x3 + Vc3` the hard node that `CH4` returns to --
  structurally what `vin` behind `CH1` is in A42 (A42's own `a1` is likewise
  pinned to `x1` by the same 53.8 uF flying capacitor value used here).

**Phase 4 is therefore an exact capacitive analog of A42's cell: 385 pF to a
hard node in series-parallel with 770 pF to ground, across a 1.4666667 nH phase
inductor into a 1 V rail, total participating capacitance 1155 pF -- identical
to A42's.** This is a property of where phase 4 sits at the bottom of the
ladder, not a tuned coincidence.

Better still, the commanded schedule produces the required state by itself. With
`dead_time_s = 10 ns`, `T = 200 ns`, `Ton = 16.6667 ns` and the unchanged `T/4`
phase shift, phase 4's turn-on dead-time window is local `[145 ns, 155 ns)`,
and the commanded state of phases 1, 2 and 3 throughout that window is
LOW - LOW - LOW. Nothing is forced by hand; the window is taken at
`t = 23.145 us`, i.e. the 116th period, safely past the 22.87 us input ramp so
the descriptor's own constant-`Vin` precondition holds.

### 3.2 What still differs from A42, honestly

1. **Switch on-resistance is a single global value** in `ZeroStartBoundary`, so
   A42's `RHS = 7 mOhm` / `RLS = 3.5 mOhm` split (confirmed here to come from
   `GS61008T_RDS_TYP_25C = 7 mOhm` in
   `paper_locked/04_component_models/GS61008T_typical_params.lib` divided by
   P25 Table III's `NHS = 1` / `NLS = 2`, matching `device_library.py`'s
   `GS61008T.rds_on(1) = 0.007` and `.rds_on(2) = 0.0035` exactly) cannot be
   expressed. **Inside the dead-time window this is irrelevant** -- both
   phase-4 switches are off for the entire window, so no on-resistance enters
   the commutation at all. It matters only in two places, handled as follows:
   - A42's low-side conduction drop at the release instant,
     `V(x1) = INEG * RLS = +33.99 mV` at 7.77%, is applied directly as the
     initial condition on `V(x4)`, which is exactly where it enters A42's own
     commutation (it shortens the required swing by that amount).
   - The three idle phases' own low-side drops would otherwise move the `a3`
     reference. The framework's own default `1 uOhm` is used instead, which
     holds `x3` (and hence `a3`) to within **8.7 uV** over the whole 10 ns
     window -- measured, not assumed.
   The one remaining consequence is that A50's own pre-window current ramp is
   slightly faster than A42's; this is quantified in Section 3.5.
2. **`out` is an ideal 1 V source in A42.** Here it is the 4.672 mF output node
   with the load resistance made negligible. Measured drift over the full 10 ns
   window: **24.5 uV**, and about 1 uV at the ~2.1 ns crossing instant.
3. **The blocking voltage** is A42's own `VIN - VA1_T2 = 11.9806137085 V`,
   mapped as `V(a3) = 11.9806137085 V` so that ZVS means `x4 -> V(a3)`, exactly
   as A42's ZVS means `x1 -> VIN - VC1_T2`. The measured starting
   `V(a3, x4)` at 7.77% is `11.946620 V` (= `11.9806137085 - 33.99 mV`).
4. The flying capacitance in the commutating position is set to A42's own
   `53.8 uF`, not the descriptor's default `3 uF`, so that the ~4.6 nC moved
   through it produces the same ~86 uV of flying-capacitor sag A42 has.

Everything else -- `CH = 385 pF`, `CL = 770 pF`, `LPHASE = 1.4666667 nH`,
`Rser = 1 uOhm`, `IPEAK = 125 A`, `Roff = 1 TOhm`, the 7.76% / 7.77% targets --
is A42's own published boundary reused verbatim.

### 3.3 The 50 ps sub-step is not adequate, and this is a real finding

`BOUNDARY.md` Section 3.5 and Section 4 set the `resolve_deadtime_window`
default sub-step at `50 ps`, citing this project's own LTspice `TMAX`
convention from R04E16-R04E26. That convention was established for LTspice's
trapezoidal integrator. `advance_fixed_diode_step` is **backward Euler**, which
is only first-order and is **numerically dissipative**: on a resonant transition
of quarter-period `2.044 ns` it damps the resonant amplitude by roughly
`(pi/4) * omega * h`, i.e. about 3% of an ~11 V amplitude at `h = 50 ps`. That is
~330 mV of artificial voltage error against a physical discrimination margin of
~7-14 mV. At 50 ps the two A42 targets are indistinguishable and **both** report
no crossing:

| Sub-step | 7.76% min `Vds` | 7.77% min `Vds` | 7.77% crossed 1 mV? | 7.77% sign change |
|---:|---:|---:|:---:|---:|
| 50 ps (`BOUNDARY.md` default) | `350.2207 mV` | `336.6219 mV` | no | - |
| 10 ps | `77.1165 mV` | `63.1693 mV` | no | - |
| 5 ps | `42.3297 mV` | `28.3430 mV` | no | - |
| 2 ps | `21.4046 mV` | `7.3941 mV` | no | - |
| 1 ps | `14.4207 mV` | `0.4022 mV` | yes | - |
| 0.5 ps | `10.9260 mV` | `-3.0969 mV` | yes | `2.12787 ns` |
| 0.25 ps | `9.1783 mV` | `-4.8469 mV` | yes | `2.12024 ns` |
| 0.125 ps | `8.3043 mV` | `-5.7220 mV` | yes | `2.11696 ns` |
| 0.0625 ps | `7.8672 mV` | `-6.1596 mV` | yes | `2.11541 ns` |
| **first-order Richardson** | **`7.4302 mV`** | **`-6.5972 mV`** | **yes** | **`2.113866 ns`** |

The successive differences halve cleanly, exactly as first-order backward Euler
requires, so the Richardson-extrapolated row is the correct step-independent
statement of what the extended model says. The worst normalized linear-system
backward error over any window was `6.5e-18`, so this is discretization error,
not a failing linear solve.

**The `50 ps` default is therefore retained as the function's default (it is
`BOUNDARY.md`'s stated value and the right order for coarse screening) but must
not be used to answer a millivolt-margin ZVS question with this integrator.**
A follow-up should either use `<= 0.25 ps` or replace backward Euler with a
non-dissipative rule; the latter is out of this prototype's scope.

### 3.4 Gate-2 outcome at A42's two targets

Run: `python3 run_a42_validation_gate.py --output a42_validation.json`

| | A50 (Richardson-extrapolated) | A42 published | Difference |
|---|---:|---:|---:|
| **7.76% (`9.7000 A`)** crossing? | **no crossing** | no crossing | agree |
| 7.76% minimum `Vds` | `7.4302 mV` | `13.924 mV` | `-6.494 mV` (`-46.6%`) |
| **7.77% (`9.7125 A`)** crossing? | **crossing** | crossing | agree |
| 7.77% commutation after release | `2.113866 ns` | `2.1551 ns` | **`-1.913%`** |
| 7.77% absolute ZVS time, A50's own ramp | `16.3576 ns` | `16.6469 ns` | **`-1.738%`** |
| 7.77% absolute ZVS time, on A42's own release instant | `16.6057 ns` | `16.6469 ns` | **`-0.248%`** |
| 7.77% phase current at crossing | `-0.3625 A` | `-33.65 mA` | see 3.6 |

Threshold location: A50's extrapolated backward-Euler threshold is
**`7.76530%`** of the 125 A peak, i.e. **inside A42's own published
`7.76%`-`7.77%` bracket**, which is the bracket gate 2 exists to reproduce.

Against `BOUNDARY.md`'s proposed `20%` timing tolerance, the achieved timing
agreement is `1.9%` on the commutation duration and `1.7%` on the absolute time
(`0.25%` if A42's own release instant is adopted rather than A50's slightly
faster ramp). The tolerance was not lowered after seeing the result: it was
`20%`, and the result is an order of magnitude better than that.

**Gate 2: PASS**, on both the no-crossing/crossing verdicts and the timing.

### 3.5 The pre-window ramp

A42 releases its low side the instant `I(L1)` reaches `-INEG`; here the release
instant is fixed by the commanded schedule, so the ramp *start* is solved for
instead. Integrating phase 4's low-side interval from `iL4 = 0` at 1 ps steps:

| Target | A50 ramp to `-INEG` | A42 release time | Difference |
|---:|---:|---:|---:|
| 7.76% | `14.225412 ns` | `14.4727 ns` | `-1.71%` |
| 7.77% | `14.243741 ns` | `14.4918 ns` | `-1.71%` |

The whole `-1.71%` is A42's `RLS = 3.5 mOhm` conduction drop, which reduces the
ramp drive from `1 V` to `1 V - I*RLS` and which this framework's single global
on-resistance cannot apply to one phase without also moving the other three
phases' switch-node references (Section 3.2). The closed-form RL ramp
`L di/dt = i*RLS - Vout` with A42's own `RLS` reproduces A42's own release times
to **`1.03 ps`** on every one of its 28 published rows (Section 3.6), which
confirms the attribution rather than assuming it.

### 3.6 The 6.5 mV offset, and an independent third reference

A50 converges to `7.4302 mV` at 7.76% where A42 reports `13.924 mV`. That gap
is `6.494 mV` on an `11.98 V` transition (`0.054%`), but it is large relative to
the quantity itself, so it must be explained rather than tolerated.

Because phase 4's cell (and A42's own cell) is an **isolated LC** during the
dead time, its lossless solution is closed form and solver-independent:
`L = 1.4666667 nH` resonating against `CH + CL = 1155 pF` about the `Vout` rail.
`run_a42_closed_form_crosscheck.py` evaluates that closed form against **every
row A42 published** (`coarse_results.json` + `refinement_results.json`, read
only; A42 is not re-run or modified):

- A50's Richardson-extrapolated minimum `Vds` agrees with the closed form to
  **`1.16%`** at 7.76% (`7.4302` vs `7.3453 mV`) and its crossing time agrees to
  **`0.011%`** at 7.77% (`2.113866` vs `2.113635 ns`). The extension reproduces
  the exact physics of the cell.
- A42's own SPICE minima sit **above** the closed form on every non-ZVS row, by
  an offset that grows smoothly with the required swing: `+0.90 mV` at 1%,
  `+4.34 mV` at 5%, `+5.84 mV` at 7%, `+6.58 mV` at 7.76%. A physics difference
  would scale with the row's current; an integration artifact scales with the
  swing and the elapsed time, which is what is observed.
- A42's own commutation durations are likewise **longer** than the closed form
  on every crossing row, by `+1.93%` at 7.77% down to `+0.14%` at 10%, i.e.
  largest exactly where the transition is slowest and damping has longest to
  act.
- A42's own release times are `1.03 ps` **earlier** than the exact RL solution
  on all 28 rows -- a clean one-to-two-timestep signature of its own
  `TMAX = 0.5 ps`, and a strong confirmation that the closed form describes
  A42's circuit correctly.

The honest conclusion is that the `6.5 mV` is consistent with numerical damping
in A42's own LTspice run, not with a topology or physics mismatch in A50's cell,
and that A50's converged answer is the one that agrees with the closed form.
This does **not** invalidate A42: its bracket, which is what it published and
what gate 2 tests, is reproduced.

The phase current at the crossing is the one quantity where A50 and A42 differ
by an order of magnitude (`-0.3625 A` vs `-33.65 mA`). This follows directly
from the same `6.5 mV`: the current at a resonant peak is proportional to
`sqrt(peak - crossing)`, so a `6.5 mV` shift in where the crossing lands changes
it by a factor of ten. A42's own 7.77% row overshoots zero by only `0.0496 mV`,
whereas A50's converged cell overshoots by `6.597 mV`. It is a hypersensitive
derived quantity, not an independent disagreement.

---

## 4. Verdict

| Gate | Result |
|---|---|
| 1 - regression against `ZERO_START_AFFINE_PERIOD_FIXED_POINT.md` | **PASS** (bit-for-bit against `src/scb_ivr/`, before and after the extension) |
| 2 - A42 single-phase local ZVS validation | **PASS** (no crossing at 7.76%, crossing at 7.77%, timing within `1.9%` / `1.7%` of A42 against a `20%` tolerance) |

Both gates passed, so per `BOUNDARY.md` Section 6 point 3 the extension is
reported as validated for the single-phase local case, and a follow-up **could**
attempt the four-phase joint case. That follow-up was **not** performed here
(Section 7).

## 5. What this does not establish

Repeating `BOUNDARY.md` Section 7 because it still binds:

- This is not a four-phase joint-periodic-ZVS answer. It certifies only that the
  single-phase local physics is now correctly represented, which is a
  prerequisite for, not the same as, the four-phase question.
- Constant `Co(tr)`-style capacitance only, matching A42's convention -- not the
  nonlinear digitized `Coss(V)` A47 used, which A47 showed makes ZVS slightly
  harder. Nonlinear capacitance would break the linear affine-map machinery and
  is out of scope.
- No P24/P25 reproduction is claimed. The device capacitance and resistance
  plug-ins are P25/external (GS61008T datasheet Rev 200402, P25 Table III
  population), inherited verbatim from A42 along with its own prohibited-claims
  list.
- `src/scb_ivr/` is not modified and is not merged into by this experiment under
  any outcome.
- One new, concrete numerical caveat is added by this run: `BOUNDARY.md`'s own
  `50 ps` sub-step, inherited from an LTspice `TMAX` convention, cannot resolve
  a millivolt-margin ZVS question under backward Euler. Any future use of
  `resolve_deadtime_window` for a feasibility verdict must state its sub-step
  and show step-size convergence.

## 6. Files

| File | Role |
|---|---|
| `solver_copy/` | byte-for-byte copy of the seven `src/scb_ivr/` modules, import-path isolated, extended per Section 2 |
| `run_regression_gate.py` | gate 1 |
| `run_extension_tests.py` | collapse / isolation / schedule self-tests |
| `a42_local_validation.py` | the phase-4 cell, its initial state, and the closed-form reference |
| `run_a42_validation_gate.py` | gate 2 and the sub-step ladder |
| `run_a42_closed_form_crosscheck.py` | closed form vs every A42 published row |
| `build_results.py` | assembles `results.json` from the two gate artifacts |
| `regression_gate.json`, `a42_validation.json`, `a42_closed_form_crosscheck.json`, `results.json` | run artifacts |
