# D81 - acceptance checks on the mathematical model (after an external review)

Written 2026-10-09. Scripts: `scripts/audit_floquet_fresh_jacobian.py` -> `diagnostics/D81_floquet_recheck.json`;
`scripts/audit_d63_validity.py` -> `diagnostics/D81_d63_validity.json` (+ `D81_ith_below_8v.json`). Tests:
`tests/test_p24_valley_map.py` (class Validity), `tests/test_p24_nonlinear_event_map.py` (FloquetJacobianTests).

An external review (2026-10-09) read the math-model code and found that some results lacked conditions of use and
acceptance checks: a stability matrix that may be stale, lookups and event times that leave their range without saying
so, "steady state" without a test, reduced models used beyond their assumptions, calibrated models counted as
independent evidence, and estimates written as proofs. Each point below says what the code or document showed, what
was changed, and what the change does to archived results. The review is right on every point. Where it overstates
the impact, the section says so.

## 1. Floquet moduli from Newton's chord matrix (review point 1)

**Confirmed in the code.** `orbit_chord` reuses the Jacobian it is given and recomputes it only when Newton slows.
The outer iterations of D45 (`audit_p24_nonlinear_orbits`), D46 (`audit_p24_drop_orbits`) and D47-D51
(`p24_orbit_solver.solve`) pass that matrix from one outer step to the next, while Ton and the delays change. At
the last outer step Newton starts on the previous orbit and stops at once, so the returned matrix belongs to an
earlier state and parameter set. Every `floquet_abs` in those records came from it. Not affected: D43's `orbit`
(central differences at every iterate, the converged one included) and D52-D55 (their own per-edge Jacobian at the
orbit, with a curvature check per column).

**Check.** All 36 archived orbits are rebuilt at their final parameters. The archived section is still a fixed point
(|F(s) - s| ≤ 8.8e-7). A fresh central-difference Jacobian is taken there at five relative steps,
1e-3 ... 1e-7, and the event sequence of every perturbed cycle is compared with the base cycle's.

| orbits | n | archived → fresh, largest change | largest fresh modulus | spread 1e-3..1e-5 | at 1e-6 / 1e-7 (noise) | max fixed-point residual |
|---|---|---|---|---|---|---|
| D45 nonlinear Coss (parts A-C) | 9 | 0.99034 → 0.99049 (+1.5e-04, 2.5 %) | 0.99594 | 4.0e-05 | 4.1e-03 | 8.8e-07 |
| D45 linear Co(tr) (part D) | 7 | 0.99366 → 0.99447 (+8.1e-04, 2.5 %) | 0.99479 | 2.8e-06 | 2.6e-08 | 7.7e-10 |
| D46 | 5 | 0.98669 → 0.98641 (−2.8e-04, 3 %) | 0.99058 | 3.4e-06 | 2.5e-03 | 2.1e-07 |
| D47 | 4 | 0.98867 → 0.98859 (−8.1e-05, 3 %) | 0.99269 | 2.7e-06 | 3.9e-03 | 9.5e-08 |
| D48 | 4 | 0.98842 → 0.98794 (−4.8e-04, 3 %) | 0.99186 | 7.0e-06 | 7.9e-04 | 6.7e-08 |
| D49 | 2 | 0.98597 → 0.98606 (+8.6e-05, 5 %) | 0.98606 | 2.6e-06 | 7.0e-04 | 8.5e-08 |
| D50 | 3 | 0.98616 → 0.98600 (−1.5e-04, 5 %) | 0.99296 | 1.9e-06 | 6.0e-04 | 9.4e-08 |
| D51 | 2 | 0.99286 → 0.99297 (+1.0e-04, 2 %) | 0.99297 | 8.0e-06 | 4.8e-04 | 4.3e-07 |

"Fresh" is the mean at steps 1e-4 and 1e-5. Every perturbed cycle kept the base cycle's event order at every step.
The largest residual, the D45 3 % seed orbit, is 8.8e-7 against an archived 2.1e-8; the map code has changed at the
1e-7 level since D45, and that is far below what moves a modulus.
**A second finding the review did not name: the step size matters more than the staleness.** On the
nonlinear-Coss maps (DOP853, rtol 1e-11) a step of 1e-6 or 1e-7 moves the largest modulus by up to 4e-3, because the
output-voltage coordinate (~1 V) is then perturbed by 1e-6-1e-7 V, close to the integrator's noise. orbit_chord used
forward differences at 1e-6, so the archived values also carried this noise. The linear map (exact flow) shows none.

**Fix.** `section_jacobian(emap, s)` (central differences, step 1e-4, event-order flag) is the Jacobian for stability;
`orbit_chord`'s docstring says its matrix is not. `p24_orbit_solver.solve` and the D45 / D46 scripts take the moduli
from it, and the solver records `floquet_same_order`. The D47-D51 gate (`scripts/p24_orbits.py --gate`) compares
moduli with this recheck to 1e-6, and every other key with the archive as before. The test builds the review's case:
an exact fixed point with a supplied matrix of moduli 2 returns that matrix unchanged, and section_jacobian gives 0.98607.

**What it changes.** Every archived largest modulus moves by at most 8.1e-4. At the four decimals the D-docs print, 20 of 36
change by 1-8 in the last digit (D45 2.5 % 0.9903 → 0.9905; D48 3 % 0.9884 → 0.9879; D45 part D 2.5 % 0.9937 →
0.9945; the full list is in the JSON), and the D45-D51 tables carry a note. No orbit changes from inside to outside the unit circle, and no D45-D51
conclusion changes. Two qualifiers stay:
- these are the moduli of the section map **at fixed Ton and delays**. The voltage loop and the delay correctors
  are the outer iteration and are not in this Jacobian. Closed-loop rules are D52-D55's, and controller learning
  is not in any of them (Section 3);
- the margin is small, 1 − |mu| = 0.0041 at the worst orbit (D45 1 %, restart branch), so a statement "stable" is a statement about this
  model to about three decimals, not a robustness margin.

## 2. D63: lookups, unreachable events, root finding, warm-up (review points 2 and 3)

**What the code did (confirmed):**
- `ValleyMap.ith` used `np.interp`, which returns the end value outside the table (8-17 V by default); A148 / A149's
  `_bilinear` and `np.interp` clamp the same way;
- `seg_time` returned a negative time when the level was behind the current (the log of a ratio below 1). Phase 1's
  comparator, the floor and the crossing report used it as a time;
- `seg_end` / `seg_time` divided by R, so R = 0 raised ZeroDivisionError. This was a crash, not a silent wrong
  number; the review's "直接除零" is right about the defect and the fix;
- `steady_ton` bisected 100 times on [1 ns, 1 µs] without checking that the interval holds a root or that the
  result is one;
- `simulate` called its start "a converged steady state" after a fixed 600 + 200 periods, without a test.

**Changes** (`src/scb_ivr/p24_valley_map.py`; D63 Section 11): flags in every record (`ith_rail`, `past_level`,
`von_grid`, `sh_grid`) and their counts in `metrics()["flag_periods"]`; `seg_time` returns `inf` for a level never
reached, and the comparator uses `_level_time`, which is 0 when it is already past its level; R = 0 uses the ramp
limit; `steady_ton` raises without a bracket or with a residual above 1e-6 of the phase current; `steady_check` tests
the warm-up end state, and `simulate` reports it (`rec[0]["warm"]`, `metrics()["warm_settled"]`). Inside the range
every number is unchanged.

**Added 2026-10-10 (whole-project review, Section 3):**
- `seg_time` returns `inf` when the target is the asymptote v / r (0 if the current is already there). It used to
  divide by zero.
- `steady_check` also compares the control memory: the timed edge `dlo` and the slot history `t_hist` (within
  1e-13 s), and the adaptive step's `step` / `last_up` (exactly). The audit's pass C uses the same record
  (`steady_record` / `steady_lag`).
- Rerun of the audit: every count below is unchanged (139 / 142 warm-ups periodic; A134 / A135 lags and unsettled
  arms identical). So the observables never settled while the memory still moved.

**What the archived runs show** (`D81_d63_validity.json`; D63's validation and design map, A117, A118, A124, A134,
A135; 524 outcome rows, 956,190 periods):

| check | result |
|---|---|
| values with the new code | A118, A124, A134, A135 reproduced value for value. D63: 4 design-map rows (3 µF comparator, ±4.8 V at 1-5 µs); A117: 2 rows (the same runs). All of them had already diverged |
| why those rows changed | at the first `past_level` event the old code computed a **negative period** (−0.1 to −11 µs), so the simulated time ran backwards. Phase 1's peak was already −42 to −512 A (deep runaway). The outcome "diverges" is unchanged; the divergence time moves by 0 to +1.2 µs, and the numbers past the 1000 A validity limit move |
| rail above the table (17 V) | rail 1 on rising steps and in A134 / A135's lock (up to 24.3 / 28.4 V): 18,096 phase-periods. The true threshold is higher than the end value, so the clamp can only add crossings. It added none outside runs that had already diverged (those had rails of 38-97 V) |
| rail below the table (8 V) | rail 1 on falling steps (down to 6.9 V): 1,300 phase-periods. Here the clamp hides crossings. A rerun with D57's threshold at 5.0-7.5 V (`D81_ith_below_8v.json`) changes 31 of 524 rows: in runs that did not diverge, peaks by ≤ 0.56 A, Vo extremes by ≤ 0.46 mV, recovery by ≤ +1.0 µs, phase-1 crossing depth by −0.4 to +1.1 A, and A124 p125_l_m80_10us's crossing periods from 17 to 27 at 3.1 A depth. **No outcome class changes** (A118's rule needs > 12 A for ≥ 25 periods). One design-map cell, D63 Section 4's 3 µF floor −4.8 V / 1 µs, goes from 200.13 to 199.6 A (the table prints 200 either way). D63's "phase 1 crossing ≤ 4.7 A" becomes ≤ 5.5 A (corrected in D63) |
| warm-up (simulate) | 142 runs: 41 settle to a fixed point, 98 to a quantised cycle of 2 or 4 periods. Three D63 validation rows (the 5 MHz 25 % comparator design) are not periodic within a lag of 16: Vo varies by 0.09 mV (< the 0.5 mV ADC LSB), valleys by 0.35 A |
| warm-up (A134 / A135, own loops) | 286 of 327 runs periodic before the step (lag 2, 4 or 8). L × 1.2 (arms f / z / c, 24 A134 rows): irregular within 0.26 mV and 0.55 A. **The absolute cap at L × 1.3 (f130; 8 A134 + 9 A135 rows) is already locking before the step** (valleys move 25 A per period). Those rows are not step responses from a steady state. The registered prediction "lock" stands, as the n0 row (no step) locks too |

So the review's concern was right. The old code did produce wrong numbers silently: negative periods, and
thresholds clamped on falling steps. On the archived runs, though, the wrong numbers sit in runs that had already
run away, or move results by less than an ampere and change no registered outcome.

## 3. Reduced models do not certify the final system (review point 4)

Agreed, and the repository already holds the counterexamples. D60's "the ladder only relaxes, no resonance" holds
for its averaged model: every period restarts from the fixed negative current, the timing is ideal and there are no
in-cycle dynamics. The full controller produced oscillations that this model cannot represent:
- A142: about 50 µs of oscillation after a +7.89 V step in the mode-P comparator phase;
- A143: dt_pred learning makes phases 2-4 swing with Cs (about 4.6 µs).

D63, without a dt_pred block, stays damped in both cases (D63 Section 10). D60 now carries a scope note.

The rule for the final docs: the reduced models (D58-D60, D63) explain trends, screen designs and register
predictions. Stability and limits of the final design are claimed only from co-simulation of the named plant
version (FINAL_SPEC_COVERAGE).

## 4. Evidence class of each model (review point 5)

| model | what it is | parameters | compared with | class |
|---|---|---|---|---|
| D43, D45-D51 event maps | exact piecewise / nonlinear-Coss circuit ODE with the controller's event rules | P24 circuit values, EPC2067 datasheet Coss (A59), diode drop fitted to datasheet Fig. 8 (A87) | cosim at the same parameters (A82-A93) | first principles + datasheet; the cosim comparison is **two implementations of the same physics** (implementation agreement), not hardware |
| D57 zero-voltage threshold | node charge balance with datasheet Coss | datasheet | cosim turn-on V_DS | first principles + datasheet |
| D58 start-up averaged model | mode S voltage source, mode P current source | a_s, r_s (A73 run 6, older plant), k 1.036 and t_x from the reference cosim steady state | A103 (registered); r_s refitted after the runs | **calibrated**; A103 rows c1b / c1d after the refit are in-sample |
| D59 voltage loop | sampled PI on D58 | D58's calibration | A104 load steps (registered): extremes within 7 %, recovery 4-21 % | calibrated model, **registered prediction** on new transients at the calibrated operating point |
| D60 ladder relaxation | averaged charge balance, BCM assumption | none fitted | A106 (existed), A107 (registered: structure right, rate 1.2-5.6x off) | first principles under strong assumptions; scope note (Section 3) |
| D63 valley map | cycle-by-cycle valleys, crossings, loop, ladder | I_th, t_tr from D57; v_rev from the plant and fit_fig8; the slot rule read back from cosim (A116); the outcome rule refitted after A117 | Section 3: 25 transients that existed before the map (**retrospective**); Sections 7-9: A117, A118, A124 (**registered**); known blind spots in Section 10 | reduced, partly calibrated; prospective record = Sections 7-9 only |
| D68 slow turn-on | sqrt law for the ramp + regression for Vo | slope 0.0283 V/ns and K fitted to A152 / A155 runs | A153 / A154 (registered) | **empirical fit**, then registered checks |
| D65 / D70 / D71 package | energy bounds, lumped R / L, order of magnitude | geometry from P24 Figs. 5-6, copper / via values assumed | A144 / A145 (edge bound within 1.5 V) | estimates; D71 is an order-of-magnitude priority call (Section 5) |
| D62, D72-D78, D80 loss / thermal | budgets, FD thermal solver, microchannel correlations | datasheets, literature, assumed stack | D74's solver against analytic cases (V1-V8) | **code verification** (the solver solves its equations); the physical inputs are assumed, not validated |
| D79 gate model | EPC's vendor LTspice model in the plant | vendor model | LTspice on the same model; datasheet to 1-8 % | implementation check against the vendor model |

Read "two models agree" by this table: for D43-D51 it shows that two codes solve the same physics the same way, and
it says nothing about hardware. For D58 / D59 / D68 the in-sample rows test the implementation, and only the
registered rows count as prediction.

## 5. Estimates written as conclusions (review point 6)

D71's "negligible: no plant change" is now "expected small within the stated bounds: not modelled for now", with
its assumptions listed: ideal output capacitors, modules as current sources with a common Ton, ±5 % inductor
spread, a 62.5 A step. It also notes that the mode's Q reaches 9, and that a mode the common-node loop cannot see is
not thereby stable. The same reading applies to the other order-of-magnitude statements in D65 / D70 (the
package-level loss and energy estimates). They set priorities and do not prove that an effect is absent.

## 6. Open after D81

- Scripts with their own D63 warm-up loop (A134, A135, A138, A140, A148, ml_rl*) do not call `steady_check`.
  Section 2 checked A134 / A135 from outside.
- The I_th tables of archived experiments still end at 8 / 17 V. New tables should cover the rails a study
  reaches (5-30 V); `thresholds(lf, rails=...)` takes the grid.
- The D47-D51 gate has not been rerun with the new solver (about 1 h). The recheck computes the same Jacobian at
  the same orbits, and the gate's comparison of every other key is unchanged.
