# A56 - equal-power (regulated 250 W) comparison of the A55 L/dead-time candidates (BOUNDARY)

Track: A (periodic steady-state reproduction). Classification:
`SENSITIVITY_ONLY`, a control-boundary extension of A51/A55. Not a P24/P25
reproduction. Per explicit user direction 2026-09-28 to continue the
"system-level" question with an equal-power comparison.

## 0. Why this experiment exists

A53, A54 and the first version of A55 compared partial losses between
operating points that delivered DIFFERENT output power. A55's own later
work (committed `29c0152`) showed this directly:

- At nominal `LPHASE=1.466667 nH`, the inherited A51 scheduler delivers
  `~192 W` at `2.15 ns` dead time and `~144 W` at `4.3 ns` dead time --
  lengthening dead time shortens the actual high-side conduction window
  (`JOINT_GRID_RESULTS.md`, "Timing mechanism identified").
- The all-eight-ZVS points (`L~=0.6215 nH`) deliver `~220 W`, not 250 W.

A loss comparison across unequal delivered power is not an efficiency
ranking. Separately, A55 found the old `I_rms^2*Ron` inductor-current
proxy undercounts actual switch-branch dissipation in this series-
capacitor network (`RESULTS_2026-09-26.md`). **Consequently, the
"net-Watts negative" conclusions reported for A53 and A54 are not
established** -- they rest on an unequal-power comparison and a biased
loss meter. This experiment is the first comparison at equal delivered
power, with the corrected meter.

## 1. The declared output-regulation boundary (a PROJECT_DECISION)

A55's own boundary warns: do not silently change duty or load to force
250 W. This experiment changes duty **openly**, as its single declared
control degree of freedom:

- **Regulated variable**: the commanded high-side window width
  `Ton_cmd`, per the terminology of
  `symbolic_derivations/D01_TIMING_DEFINITION_CONTRACT.md` ("命令导通区间",
  command on-interval) -- NOT the nominal P24 interval and NOT the
  effective gate interval. Same `Ton_cmd` for all four phases; phase
  offsets stay at `T/4`; dead-time windows stay centered on the command
  edges exactly as in A50/A51/A55.
- **Held fixed**: load resistance `4 mOhm` (`= 1 V^2 / 250 W`, the P24
  rated-point load), `Vin=48 V`, `f_sw=5 MHz`, device population, every
  passive value. Load is never retuned.
- **Regulation target**: mean output power `mean(Vout^2/R) = 250 W`,
  equivalently mean `Vout = 1 V` at this load. Numerical solve tolerance
  `|P-250|/250 <= 1e-3` -- a solver convergence tolerance only, NOT a
  paper-acceptance tolerance.
- This is what a real voltage-mode regulation loop would adjust. It is a
  `PROJECT_DECISION` about the control boundary, not a paper-specified
  controller; P24's native negative-current-threshold controller is still
  not implemented (inherited A51 limitation).
- **Report `Ton_cmd` and its deviation from P24's nominal
  `D*T = 16.6667 ns` for every point.** A point that reaches 250 W only
  with a large on-time change departs further from the paper's timing and
  that must be visible, not hidden.

Implementation note (verify, don't assume): in A50's `solver_copy`,
`ZeroStartBoundary.on_time_s` is a derived property (`duty*period`), and
`load_resistance_ohm` is derived from `vout_target_v` and
`module_power_w`. Expose `Ton_cmd` by subclassing the A55
`AsymmetricRonBoundary` to override `on_time_s` only, leaving
`vout_target_v`/`module_power_w` (hence the 4 mOhm load) untouched. Then
**prove** with a test that every scheduler code path used by the solve
(`commanded_pwm_mode`, `next_pwm_edge_s`, A51 `period_intervals`, A55
metering) reads the overridden value, and that the load resistance is
exactly `0.004 Ohm` in every regulated boundary.

## 2. Candidates

A55's own 3x3 local grid, unchanged, each now regulated to 250 W:

- `LPHASE` in `{0.6215240418, 0.6274059728, 1.4666667} nH`
- dead time in `{1.075, 2.15, 4.3} ns`

The baseline for every comparison is **nominal L, 2.15 ns, regulated to
250 W** -- not A54's unregulated 192 W point.

## 3. Method

1. Reuse A55's committed modules read-only: `asymmetric_ron_dynamics.py`
   (population-corrected high `0.775 mOhm` / low `0.5167 mOhm`),
   `audit_accepted_orbit.py` (`metered_orbit`, branch power
   `integral(v_branch^2/R_branch)/T`), and A53's `a53_solve.py`
   (`solve_fixed_point`). Do not modify A51/A53/A54/A55 files.
2. For each candidate: outer 1D root-find on `Ton_cmd` (secant or
   bracketed bisection -- implementer's choice) for `P_load = 250 W`;
   inner periodic fixed-point solve with continuation from the previous
   converged `z*` (A55's own seeding discipline; no raw A37 re-seeding).
   Cap the outer search (propose 15 iterations) and report non-converged
   candidates as such -- a candidate that cannot reach 250 W is a result,
   not a failure to be patched.
3. At each regulated state, meter with A55's `metered_orbit`: all high-
   and low-side natural-ZVS verdicts, per-phase current extrema, current
   at high-side dead-time entry, negative-entry ratio (observational, not
   a commanded threshold), mean `Vout`, `P_load`, actual branch channel
   dissipation, peak `|iL|`, actual modeled channel-active durations.
4. **Hard-switch capacitive energy accounting check (required).** For
   hard-switched transitions the node capacitance discharges through the
   enabled branch resistor with `tau ~= Ron*C ~= 7 ps`, well below the
   coarse step. Determine explicitly whether A55's branch metering
   captures this discharge energy (compare metered branch energy against
   `0.5*C_node*Vres^2` per hard-switched event, at two step sizes). If
   captured, do NOT add it again; if not captured, add it separately and
   say so. Either way, state which, with the numbers.
5. Step refinement: re-solve the baseline and the lowest-loss
   all-eight-ZVS regulated point (if any) at halved steps (31.25 ps /
   2.5 ps) and confirm ZVS verdicts, `Ton_cmd`, and loss are stable.
6. Safety: `+/-250 A` project screen (not device SOA) on every accepted
   orbit and every Newton/line-search probe, separately reported.

## 4. Provenance

| Value | Source | Category |
|---|---|---|
| Regulation boundary (`Ton_cmd` free, load fixed, target 250 W) | This document | `PROJECT_DECISION` (control boundary) |
| `4 mOhm` load, `250 W`, `48 V`, `5 MHz`, `nP=4` | P24 rated point | `P24_EXPLICIT` |
| EPC2067 Ron/Coss, `NHS=2`/`NLS=3` | `src/scb_ivr/device_library.py` (`EPC2067`, `P24_EPC2067_POPULATION`) | `EXTERNAL_DEVICE_DATA` / `P24_EXPLICIT` |
| L and dead-time grid values | A55 `JOINT_GRID_BOUNDARY.md` | `SENSITIVITY_ONLY`, inherited |
| `1e-3` power tolerance, `1e-6` closure, step sizes | This document / A55 | `NUMERICAL_IDEALIZATION` |

## 5. What the result can and cannot decide

Decides: at EQUAL delivered power (250 W), under the declared scheduler
and regulation boundary, whether any candidate keeps all-eight ZVS within
the current screen, and how its partial electrical loss compares with the
regulated nominal baseline.

Outcomes, all valid and to be reported plainly:

- **A ZVS candidate reaches 250 W within the current screen with lower
  partial loss than the regulated baseline** -> first equal-power
  evidence that rated-load ZVS can pay for itself in this model.
- **ZVS candidates reach 250 W but with higher partial loss** -> the
  equal-power answer is "not worth it" in this model; A53/A54's
  conclusion is then supported on correct grounds for the first time.
- **ZVS is lost, or the current screen is violated, when regulated to
  250 W** -> the ~220 W ZVS points do not extend to rated load under this
  scheduler; report which gate fails first and at what power.
- **Mixed** -> report per candidate; no single verdict forced.

Cannot decide: gate-drive, realistic third-quadrant/reverse-conduction,
magnetic, thermal or package loss (still absent -- the objective remains
a **partial electrical-loss proxy**, not total loss); the native P24
controller; hardware efficiency; paper reproduction. No SPICE
confirmation in this experiment.

## 6. Constraints

Do not modify `src/scb_ivr/`, `results/`, `paper_locked/02_ectc2024_main/`,
or any A37-A55 committed file. Never overwrite an existing result JSON
(A55's own convention). Retain failed and non-converged candidates in the
record.
