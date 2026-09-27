# A56 - equal-power (regulated 250 W) comparison of the A55 L/dead-time candidates (RESULTS)

Track A, `SENSITIVITY_ONLY`. Boundary: `BOUNDARY.md` (commit `f0e0041`),
unmodified. Python solver only; no SPICE run. Machine-readable record:
`results.json` (aggregate), `runs/*.json` (every outer trial, Newton history,
z*, full boundary), `capacitive_accounting.json` (Section 3.4 evidence).

The objective throughout is a **partial electrical-loss proxy**, not total
loss: A55's actual enabled-branch channel dissipation plus the hard-switch
capacitive discharge energy that meter misses (Section 3 below). Gate drive,
realistic third-quadrant conduction, magnetic, thermal and package loss are
absent.

## 0. Verdict

**BOUNDARY.md Section 5, first outcome - with a narrow margin that the
omitted terms could erase.** All nine candidates reach 250 W
(`|P-250|/250 <= 4.5e-4`) inside the +/-250 A screen. All four
all-eight-ZVS candidates (L = 0.6215/0.6274 nH at 2.15/4.3 ns dead time)
have a lower partial-loss proxy than the regulated nominal baseline:

| point (all at 250 W) | Ton_cmd | ZVS H / L | A55 meter | + missed hard-switch C energy | **partial-loss proxy** |
|---|---:|---|---:|---:|---:|
| baseline: nominal L 1.4667 nH, 2.15 ns | 18.8795 ns | FFFF / TTTT | 18.408 W | 12.974 W | **31.382 W** |
| best ZVS: 0.627406 nH, 2.15 ns | 17.6919 ns | TTTT / TTTT | 28.206 W | 0 | **28.206 W** (-3.18 W, -10.1%) |

Within this model this is the first equal-power evidence that rated-load ZVS
can pay for itself. It is not a hardware efficiency result, and three
qualifications carry equal weight:

1. **The sign depends on Section 3.4.** A55's branch meter, at the 62.5 ps
   coarse step used by A55 and A56, captures only 22-31% of each of the
   baseline's hard-switched node-capacitance discharges (18-31% across all
   orbits). Read raw, it ranks the baseline 9.8 W *better*
   than the ZVS point (18.41 vs 28.21 W). That raw reading is not
   step-converged (18.41 -> 21.03 -> 23.91 W as the step halves twice). The
   corrected proxy is converged (31.382/31.379/31.377 W). A source-side
   energy balance that uses no branch metering confirms the difference:
   Richardson-extrapolated `P_in - P_load` is 31.742 W vs 28.560 W.
2. **The margin (3.18 W) is smaller than plausible values of an omitted term.**
   Under the inherited fixed, symmetric dead-time scheduler the ideal-clamp
   surrogate conducts through the channel for much longer at the ZVS point
   (6.77 A mean current-time vs 2.64 A for the baseline). For a constant
   reverse drop `Vsd`, the ranking reverses at `Vsd` ~ 0.90 V (2.15 ns point)
   and ~ 0.32 V (4.3 ns points). No EPC2067 reverse-drop value is sourced in
   this project (the locked `GaN_reverse_conduction_ideal.lib` is a
   `VFWD=0` idealization), so this is a stated decision risk, not a computed
   loss.
3. **Capacitance nonlinearity is of the same order as the margin.** The
   linear capacitors use Co(tr). A naive rescale of the whole discharge energy
   to Co(er)/Co(tr) = 1597/1860 cuts the margin to 0.64 W. The usual nonlinear
   hard-turn-on bookkeeping (Eoss of the discharged device plus
   Qoss*V - Eoss of the charged device) does not simply scale that way, and
   no 12 V Eoss/Qoss curve is locked, so even the direction is not
   established. Magnetic loss is also absent; the ZVS point carries 1.69x the
   baseline peak current (217.15 vs 128.79 A), which is unfavorable to ZVS.

Consequence for earlier records: A53/A54's "net Watts negative" conclusion
is **not reproduced** under the corrected contract (equal power,
population-correct Ron in the dynamics, branch metering plus the missed
capacitive energy). The opposite is not established as a hardware fact
either.

## 1. Regulation variable and its proof (BOUNDARY.md Section 1)

`regulated_boundary.RegulatedBoundary` subclasses A55's
`AsymmetricRonBoundary` (imported read-only). It adds one field, `ton_cmd_s`,
and overrides the `on_time_s` property only. The field is D01's command
on-interval (command_on -> command_off), the same for all four phases.
`vout_target_v=1`, `module_power_w=250`, `duty` and every other field are
unchanged.

`test_regulated_boundary.py` (11 tests, all pass;
`python3 test_regulated_boundary.py -v`) proves:

- `commanded_pwm_mode`: the high side is still on past the NOMINAL command-off
  edge, the dead window is centred on `Ton_cmd`, and the low side turns on at
  `Ton_cmd + d/2`, for every phase.
- `next_pwm_edge_s` returns `Ton_cmd -/+ d/2`.
- A51 `period_intervals` centres every turn-off window on `p*T/4 + Ton_cmd`,
  and A51 `_window_mode` is the dead mode there.
- Duty tripwire: a boundary whose `duty` property raises completes a full
  A51 period map and A55 metering. No solve or metering path derives on-time
  from duty. On that run, the verdict windows equal `period_intervals`,
  `commanded_dead_time_confirmed` is true on every turn-on window, and the
  modeled high-channel time of the hard-switched nominal case is exactly
  `Ton_cmd - d`.
- A53 `solve_fixed_point` passes the boundary object through unchanged. The
  solver and meter share the same `a51_period_map` module object.
- With `Ton_cmd = duty*T`, the period map is bitwise identical to A55's
  boundary. Every candidate's replay trial reproduced A55's committed P and
  channel loss exactly (e.g. 192.22792421032145 W / 14.904607235280604 W).
- Load: `load_resistance_ohm == 0.004` exactly for all nine (L, DT) at four
  Ton_cmd values; the assembled descriptor has `a[out,out] == 1/0.004`.

**Found and handled - one metering path does not read the override.** A55's
`audit_accepted_orbit.metered_orbit(point)` takes no boundary. It rebuilds
one from `(phase_inductance_h, dead_time_s)` via `build_epc2067_boundary`,
which re-derives `on_time_s = duty*T`, so it would silently meter a regulated
z* on the nominal 16.6667 ns schedule. The test demonstrates this defect.
The documented local fix is `regulated_boundary.regulated_metering(b)`: for
one call, it rebinds the name `build_epc2067_boundary` in the audit module's
namespace only, to return exactly `b`, after checking that L and dead time
match. It is restored in `finally`. A55's file is not edited and its
metering code runs unchanged. `meter_regulated` additionally asserts that
the metered `full_boundary` equals the regulated boundary, including
`ton_cmd_s`. Every scheduler path in the solve itself reads `on_time_s`.
Nothing recomputes on-time from duty there.

## 2. Regulated outcome of all nine candidates (62.5 ps / 5 ps)

Outer search: trial 0 replays A55's point from its committed z*. After that,
Ton/(1+h) first, then secant or Illinois regula falsi on
`h = sqrt(P/250)-1`. Every trial is seeded by the nearest converged z*. The
policy was fixed before running (`run_regulated_candidate.py` docstring).
Every candidate converged in 2-4 outer trials, with no failed trial. Every
regulated state has periodic closure <= 7.7e-7, below the 1e-6 tolerance.

| L (nH) | DT (ns) | Ton_cmd (ns) | dTon vs 16.6667 | P (W) | H1-H4 | L1-L4 | A55 meter (W) | missed C (W) | proxy (W) | peak abs iL (A) | max neg-entry ratio |
|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|
| 0.621524 | 2.150 | 17.6765 | +1.010 (+6.06%) | 250.001 | TTTT | TTTT | 28.546 | 0 | 28.546 | 218.64 | 39.14% |
| 0.621524 | 1.075 | 17.5272 | +0.860 (+5.16%) | 249.997 | FFFF | TTTT | 29.295 | 2.118 | 31.413 | 218.31 | 39.48% |
| 0.621524 | 4.300 | 17.6762 | +1.010 (+6.06%) | 250.001 | TTTT | TTTT | 28.548 | 0 | 28.548 | 218.65 | 39.14% |
| 0.627406 | 2.150 | 17.6919 | +1.025 (+6.15%) | 250.001 | TTTT | TTTT | 28.206 | 0 | **28.206** | 217.15 | 38.77% |
| 0.627406 | 1.075 | 17.5328 | +0.866 (+5.20%) | 249.997 | FFFF | TTTT | 28.991 | 2.215 | 31.205 | 216.84 | 39.12% |
| 0.627406 | 4.300 | 17.6916 | +1.025 (+6.15%) | 250.001 | TTTT | TTTT | 28.207 | 0 | 28.207 | 217.15 | 38.77% |
| 1.466667 | 2.150 | 18.8795 | +2.213 (+13.28%) | 249.982 | FFFF | TTTT | 18.408 | 12.974 | **31.382** (baseline) | 128.79 | 0.38% |
| 1.466667 | 1.075 | 17.8134 | +1.147 (+6.88%) | 250.113 | FFFF | FFFT | 18.451 | 13.118 | 31.569 | 128.85 | 0.96% |
| 1.466667 | 4.300 | 21.0808 | +4.414 (+26.48%) | 249.999 | FFFF | TTTT | 18.477 | 13.221 | 31.698 | 129.04 | 0.00% |

Observations:

- Regulation did not destroy ZVS; it helped. The 0.627406 nH / 2.15 ns point
  was `F/F/F/T` at A55's 219.5 W and is all-eight-ZVS at 250 W, because the
  longer command window deepens the negative valley. The 1.075 ns column
  still hard-switches every high side at low L. There the residual is
  ~5.3 V (2.6-2.8 V on phase 4): the resonant swing needs ~2.05 ns and the
  window is 1.075 ns. Those partial-swing points gain nothing: 31.2-31.4 W,
  essentially the baseline.
- At ZVS, 2.15 ns and 4.3 ns give the same proxy (to 0.0015 W) and the same
  Ton_cmd. Admission occurs at the state-dependent crossing ~2.05 ns after
  the window opens. Because the window is centred on the command edge, the
  effective conduction interval is identical. The dead time changes only how
  long the surrogate conducts inside the window. The high-side margin before
  window end is ~0.10 ns at 2.15 ns and ~2.25 ns at 4.3 ns. So the 2.15 ns
  ZVS is timing-marginal, and the 4.3 ns ZVS is robust but has 2.6x the
  surrogate exposure.
- Paper-timing departure is visible: the ZVS points need +6.1% Ton_cmd, the
  baseline +13.3%, nominal/4.3 ns +26.5%. The ZVS points' negative
  dead-time-entry currents are ~38-39% of the positive peaks, far from P24's
  1-2% condition (observational, not commanded). Baseline 0.4%.
- Per-phase detail for the two decisive points (A; entry = current at the
  high-side dead-time entry):
  - baseline: min `-1.54/-1.82/-1.82/+0.08`, max `126.94/126.61/126.61/128.79`,
    entry `-0.16/-0.47/-0.48/+1.75`; modeled high-channel time
    `16.7295 ns` each (= Ton_cmd - d); mean Vout 0.99996 V.
  - best ZVS: min `-82.89/-83.87/-83.87/-83.66`,
    max `217.15/216.04/216.04/215.58`, entry `-82.78/-83.76/-83.76/-83.58`;
    modeled high-channel time `15.641/15.648/15.648/16.292 ns`;
    mean Vout 1.0000018 V.

## 3. Hard-switch capacitive energy accounting (BOUNDARY.md Section 3.4)

**Verdict: NOT captured.** At a hard-switched turn-on, the first step with
the channel enabled is one full coarse step. That is 62.5 ps (confirmed on
every event), about 6-9 discharge time constants. Backward Euler collapses
the node voltage in that one step. Only the right-endpoint remnant is
metered as `v^2/R`. The rest leaves the orbit as integrator (numerical)
damping and passes through no metered resistor. Nothing is double-counted:
the proxy adds only the measured missing part, `E(h->0) - E(orbit)`, per
event.

Method (`capacitive_accounting_check.py`, `orbit_diagnostics.py`), per
event:

1. Re-integrate a 500 ps post-event window from the orbit's own window-end
   state with A50's unchanged BE step, at 62.5 ... 0.025 ps, metering all
   enabled channels as A55 does.
2. Check that the rung equal to the orbit's own step reproduces the orbit's
   metered window energy. It did, for all 35 events.
3. Take h->0 by Richardson on 0.05/0.025 ps.
4. Subtract a conduction baseline fitted after 250 ps (fit RMS <= 2e-3 W).
5. Measure `C_meas = Q_excess/Vres` from the switching branch.

Across all orbits, the 62.5 ps meter captures 18-31% of each high-side
discharge. The three low-side events (nominal L, 1.075 ns; Vres ~1 V) are
tiny (~0.01 uJ). Their captured fraction (~0-3%) is ill-conditioned because
the conduction cross-term is comparable to the excess. Their missed energy
is still measured directly.

Regulated baseline, 62.5 ps orbit:

| phase | Vres (V) | C_meas (pF) | structural Coss sum (pF) | tau (ps) | 0.5*C_meas*Vres^2 (uJ) | h->0 excess (uJ) | captured at 62.5 ps | at 31.25 ps | at 15.625 ps | missed per event at 62.5 ps (uJ) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 11.965 | 13005.5 | 13020 | 10.1 | 0.9310 | 0.9292 | 25.1% | 40.0% | 57.0% | 0.6962 |
| 2 | 12.101 | 12979.0 | 13020 | 10.1 | 0.9503 | 0.9603 | 30.6% | 45.7% | 61.4% | 0.6662 |
| 3 | 12.101 | 12983.6 | 13020 | 10.1 | 0.9506 | 0.9604 | 30.7% | 45.8% | 61.5% | 0.6658 |
| 4 | 12.481 | 9289.8 | 9300 | 7.2 | 0.7235 | 0.7309 | 22.5% | 35.8% | 51.7% | 0.5666 |

- The measured discharge energy equals 0.5*C*Vres^2 to within 1%. Phases 2-3
  are ~1% above because part of the loop runs through the previous phase's
  enabled low side. C_meas matches the structural Coss sum (2*CH+CL, or
  CH+CL on phase 4) to 0.1%. A51's `measure_node_capacitance_f` reads lower
  (11.9/10.9/10.6/8.2 nF) with finite Ron, because its 0.5 ps probe is
  shorter than the loop tau. It is reported, not used.
- Two step sizes, two routes, same answer. The local 31.25 ps rung from the
  62.5 ps orbit's state captures 40.0/45.7/45.8/35.8%. The independently
  solved 31.25 ps orbit captures exactly the same.
- Orbit totals for the baseline (62.5 / 31.25 / 15.625 ps): captured 4.93 /
  7.56 / 10.44 W, missed 12.97 / 10.35 / 7.46 W. Physical total ~17.9 W at
  every step.
- Independent check: the exact BE energy identity
  `sum h(P_src - P_diss) = dW + sum 0.5*dz^T E dz` closes to about 1e-6 W.
  Integrator-removed energy inside the post-event windows is 13.00 / 10.36 /
  7.47 W. That matches the missed energy (12.97 / 10.35 / 7.46 W).
- The A55 grid's unregulated nominal point (192 W) was missing 12.65 W. Its
  14.905 W should read 27.558 W under this accounting. The A55 grid tables
  did not include A55 BOUNDARY Section 4's "residual capacitive turn-on
  loss" term, and the meter recovers only part of it.

This directly affects the verdict: without it, the hard-switched baseline is
undercounted by 12.97 W, 41% of its proxy.

## 4. Equal-power comparison (only points that reached 250 W; all nine did)

Ranked by partial-loss proxy (W): 0.627406/2.15 **28.206**;
0.627406/4.3 28.207; 0.621524/2.15 28.546; 0.621524/4.3 28.548;
0.627406/1.075 31.205; **baseline 31.382**; 0.621524/1.075 31.413;
nominal/1.075 31.569; nominal/4.3 31.698.

Every all-eight-ZVS point is 2.83-3.18 W below the baseline. Every point that
hard-switches its high sides lies within 0.32 W of the baseline, whatever
its L. Source-resistor and inductor-ESR loss (0.37-0.39 W) are outside the
proxy, as in A55.

Reverse-conduction exposure is exported, not priced. Values are the mean
surrogate current-time inside commanded dead windows:

- baseline: 2.64 A
- ZVS 2.15 ns: 6.77 A (0.6274 nH), 6.89 A (0.6215 nH)
- ZVS 4.3 ns: 17.7-17.9 A

The illustrative break-even constant reverse drops are 0.90 V / 0.80 V at
2.15 ns and 0.32 V / 0.29 V at 4.3 ns. The symmetric-dead-time scheduler is
the reason. At +217 A the low-side swing finishes ~0.7 ns into a 2.15 ns
window. An adaptive or asymmetric dead time would shrink this exposure, but
that lies outside this boundary.

## 5. Step refinement (BOUNDARY.md Section 3.5, plus one further halving)

Each refinement is re-seeded from the coarser regulated z* and re-regulated.
In every case the first trial at the coarse Ton_cmd was already within
tolerance.

| point | step | Ton_cmd (ns) | P (W) | H / L ZVS | A55 meter (W) | proxy (W) | P_in - P_load (W) |
|---|---|---:|---:|---|---:|---:|---:|
| baseline | 62.5 / 5 ps | 18.87947 | 249.982 | FFFF / TTTT | 18.408 | 31.382 | 32.784 |
| baseline | 31.25 / 2.5 ps | 18.87947 | 250.042 | FFFF / TTTT | 21.034 | 31.379 | 32.263 |
| baseline | 15.625 / 1.25 ps | 18.87947 | 250.072 | FFFF / TTTT | 23.913 | 31.377 | 32.003 |
| best ZVS | 62.5 / 5 ps | 17.69187 | 250.001 | TTTT / TTTT | 28.206 | 28.206 | 30.907 |
| best ZVS | 31.25 / 2.5 ps | 17.69187 | 250.045 | TTTT / TTTT | 28.191 | 28.191 | 29.734 |
| best ZVS | 15.625 / 1.25 ps | 17.69187 | 250.068 | TTTT / TTTT | 28.184 | 28.184 | 29.147 |

- ZVS verdicts and Ton_cmd are stable.
- The corrected proxy is stable: spread 0.005 W (baseline) and 0.022 W
  (ZVS). The raw A55 meter is not stable on the hard-switched baseline
  (5.5 W spread).
- `P_in - P_load` converges first-order: successive differences 0.521/0.261
  and 1.173/0.587 W. Richardson h->0 gives 31.742 vs 28.560 W, Δ = 3.18 W.
  Subtracting the other resistive loss (0.37/0.38 W) leaves 31.376/28.176 W,
  matching the finest-step proxies to 0.01 W.
- The ZVS high-side admission margin (0.100/0.101/0.101 ns before window
  end) does not move with the step.

## 6. Safety (+/-250 A project screen, not device SOA)

| scope | max abs phase current |
|---|---:|
| accepted orbits, regulated states (all nine) | 218.65 A (0.621524 nH) |
| Newton Jacobian/line-search probes, the regulated trials | 218.65 A |
| any probe, any outer trial (incl. overshoot to 252.9 W) | 224.31 A |
| any accepted orbit, any outer trial | 219.82 A |
| probes in the step-refinement runs | 217.20 A |

No probe and no accepted orbit tripped the screen. The ZVS points use 87% of
the screen at 250 W. The baseline uses 52%.

## 7. What this cannot decide

- No total, system or hardware loss. Gate drive, realistic third-quadrant
  conduction, magnetic, thermal and package loss are absent. The first two
  vary with the candidates and are large enough to reverse the ranking (see
  Section 0).
- Not the native P24 controller. This is the A51 fixed-window scheduler with
  an openly regulated Ton_cmd (a `PROJECT_DECISION`), not a
  negative-current-threshold control law.
- Not a regulated optimum. The regulated all-ZVS boundary appears to sit
  above 0.6274 nH at 250 W, because that row gained ZVS under regulation. A
  regulated L search might lower the ZVS-side proxy further. It was not run.
- No SPICE confirmation. Not a P24/P25 reproduction.

## 8. Files and reproduction

From this directory; every script refuses to overwrite its outputs:

```
python3 test_regulated_boundary.py -v
python3 run_regulated_candidate.py <label>        # 9 labels: {new_passing,old_critical,nominal}_dt_x{1,0.5,2}
python3 run_regulated_candidate.py nominal_dt_x1 --coarse 31.25e-12 --sub 2.5e-12 --suffix step2p5ps --seed-json runs/nominal_dt_x1.json
python3 run_regulated_candidate.py nominal_dt_x1 --coarse 15.625e-12 --sub 1.25e-12 --suffix step1p25ps --seed-json runs/nominal_dt_x1_step2p5ps.json
python3 run_regulated_candidate.py old_critical_dt_x1 --coarse 31.25e-12 --sub 2.5e-12 --suffix step2p5ps --seed-json runs/old_critical_dt_x1.json
python3 run_regulated_candidate.py old_critical_dt_x1 --coarse 15.625e-12 --sub 1.25e-12 --suffix step1p25ps --seed-json runs/old_critical_dt_x1_step2p5ps.json
python3 capacitive_accounting_check.py
python3 build_results.py
```

Runs were executed as independent processes with `OMP_NUM_THREADS=1`. The
nine coarse regulations take ~5-15 min each, and the accounting check about
4.5 min. No A37-A55 file, `src/scb_ivr/`, `results/` or
`paper_locked/02_ectc2024_main/` was modified.
