# A59 - nonlinear EPC2067 Coss(V) in the four-phase periodic solver, with A58's dead-time tuning redone (RESULTS)

Track A, `SENSITIVITY_ONLY`. Boundary: `BOUNDARY.md` (commit `5f1de2c`),
unmodified. Python solver only; no SPICE. Records: `runs/*.json`,
`results.json` (`build_a59_results.py`, A58's summarizer pointed here),
`logs/`, the digitized curves `epc2067_coss_qoss_eoss_digitized.csv` and
`epc2067_coss_digitization.json`.

## 0. Verdict

**With the datasheet's nonlinear Coss(V), the tuned large-ripple design's
advantage grows from A58's 2.70 W to 4.58 W at 250 W.** The real curve makes
the baseline's 12 V hard turn-on more expensive and leaves the near-ZVS
design almost unchanged.

| (250 W, fixed dead times, Fig. 8 25 C, Ron 1.55 mOhm/device) | d_rise / d_fall | Ton_cmd | P_A | **P_B** |
|---|---|---:|---:|---:|
| baseline 1.4667 nH, tuned | 2.15 / 1.15 ns | 18.357 ns (+10.1%) | 33.073 W | **33.255 W** |
| large-ripple 0.627406 nH, tuned | 1.95 / 0.65 ns | 17.104 ns (+2.6%) | 28.358 W | **28.671 W** |
| difference | | | -4.72 W | **-4.58 W** |

- Other reverse models give -4.58 W at 125 C and -4.67 W at the 1.2 V floor.
  With A57's turn-on recharge estimate the difference is -4.39 W.
- Step-converged: at 62.5 / 31.25 / 15.625 ps the large-ripple point gives
  28.671 / 28.656 / 28.649 W and the baseline 33.255 / 33.252 / 33.250 W.
  `Ton_cmd` and every verdict are identical.
- Independently confirmed without branch metering. Richardson-extrapolated
  `P_in - P_load` minus other resistive loss is 28.326 W vs `P_A` 28.335 W
  (large-ripple) and 33.066 W vs 33.068 W (baseline). A closed periodic orbit
  needs no stored-energy term, so this holds for nonlinear capacitors.
- All 52 grid points regulated (no failures). Maximum orbit current is
  217.3 A and maximum Newton probe 225.3 A, both inside the 250 A screen.
  Every Newton step converged in at most 3-4 iterations.
- Both optima are interior. The baseline's `d_rise` optimum was on the
  2.15 ns grid edge; the declared extension to 2.5 ns is worse
  (33.29 W at `d_fall` 1.15), so it is interior.

## 1. What the real Coss(V) changes

EPC2067 Coss falls steeply between 10 and 17 V, right where these switches
block (~12 V). Over 0-12 V it is 18.8% larger (charge-equivalent) than the
constant `Co(tr)` A50-A58 used.

| symmetric 2.15/2.15 ns anchors | linear (A58) | nonlinear (A59) |
|---|---|---|
| large-ripple: all eight ZVS | yes | **yes** |
| large-ripple high-side transition, phases 1-3 / 4 | 2.04-2.05 / 1.40 ns | 2.11-2.12 / 1.69 ns |
| large-ripple low-side transition, phases 1-3 / 4 | 0.69-0.70 / 0.50 ns | 0.72-0.73 / 0.60 ns |
| baseline low-side transition, phases 1-3 / 4 | 1.18-1.20 / 0.85 ns | 1.23-1.25 / 1.02 ns |
| baseline `P_A` (adaptive limit) | 31.382 W | **33.003 W** |
| large-ripple `P_A` | 28.206 W | 28.185 W |

Loss breakdown at the tuned optima (W):

| | channel | capacitive (hard/partial) | reverse (Fig. 8) | P_B |
|---|---:|---:|---:|---:|
| baseline, A58 linear | 18.41 | 13.04 | 0.37 | 31.81 |
| baseline, A59 nonlinear | 18.94 | **14.14** | 0.19 | 33.26 |
| large-ripple, A58 linear | 28.22 | 0.26 | 0.64 | 29.11 |
| large-ripple, A59 nonlinear | 28.17 | 0.19 | 0.32 | 28.67 |

The baseline's increase checks against the datasheet directly. On a 12 V
hard turn-on, each low-side device's Coss is charged from the supply and
dissipates `Qoss(12 V) * 12 V - Eoss(12 V)`. With Fig. 6 values that is
26.9 nC * 12 V - 0.152 uJ = 0.171 uJ per device. The linear model gives
`1/2 * 1860 pF * (12 V)^2` = 0.134 uJ, 28% less.

## 2. Grids (P_B, Fig. 8 25 C, W; 62.5 ps)

Declared relative to the nonlinear anchors' transition times (BOUNDARY
Section 3). For the large-ripple design, `t_f` = 0.75 ns and `t_r` = 2.10 ns.
For the baseline, `t_f` = 1.25 ns.

| large-ripple d_rise \ d_fall | 2.15 | 1.15 | 0.95 | 0.85 | 0.75 | 0.65 | 0.55 | 0.45 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2.25 | 43.82 | 33.51 | 31.40 | 30.38 | 29.35 | 29.07 | 29.56 | 30.86 |
| 2.15 (anchor) | 43.60 | - | - | - | - | - | - | - |
| 2.1 | 43.49 | 33.15 | 31.04 | 30.02 | 28.98 | 28.70 | 29.20 | 30.50 |
| 1.95 | 43.45 | 33.11 | 31.01 | 29.98 | 28.95 | **28.67** | 29.17 | 30.46 |
| 1.8 | 43.54 | 33.20 | 31.10 | 30.08 | 29.04 | 28.76 | 29.26 | 30.55 |

| baseline d_rise \ d_fall | 2.15 | 1.65 | 1.45 | 1.35 | 1.25 | 1.15 | 1.05 | 0.95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2.5 (ext.) | - | - | - | - | 33.38 | 33.29 | 33.36 | - |
| 2.15 | 38.56 | 35.66 | 34.49 | 33.92 | 33.36 | **33.25** | 33.35 | 33.73 |
| 1.0 | 38.63 | 35.72 | 34.56 | 33.98 | 33.42 | 33.32 | 33.41 | 33.80 |

The optimum is near-ZVS, as in A58. At 1.95/0.65 ns, three high-side edges
turn on at 0.87-0.92 V and three low-side edges at 0.99-1.22 V. Phase 4
reaches zero on both edges, with residual reverse conduction of 0.26 ns
(high) and 0.06 ns (low).

**Timing tolerance** (same `d_fall` error delta on both designs): the
advantage is -4.18 W at -0.1 ns, -4.58 at 0, -4.40 at +0.1, -3.93 at
+0.2, -3.48 at +0.3, -3.01 at +0.4 and -2.55 W at +0.5 ns. It is wider
than in A58.

## 3. Checks

- `test_a59.py`, 6 tests, all pass:
  - the Coss model matches the printed typical values (Q(20 V), Co(tr),
    Co(er), Coss(20 V)), and q is C's antiderivative with an even/odd
    extension;
  - with a linear charge model the new stepper reproduces the linear
    solver to relative 5.8e-12. The first-draft threshold was 1e-12,
    relaxed to 1e-10 before any run, for the reason recorded in
    `BOUNDARY.md`;
  - the nonlinear Newton step converges in at most 3 iterations and
    changes the orbit;
  - the `_candidate_step` swap covers both holders and is restored;
  - the boundary survives the `asdict` comparison used by A55/A56 metering.
- A60's 1.55 mOhm anchors and A62's 250 W anchors reproduce these tuned
  points bit-for-bit.

## 4. Found while reading the datasheet (reported, not edited)

`src/scb_ivr/device_library.py` and
`paper_locked/04_component_models/EPC2067_typical_params.lib` label three
EPC2067 values "typical" that are the datasheet's MAX column:

- `RDS(on)`: 1.55 mOhm is the max; typical is 1.3 mOhm.
- `Coss(20 V)`: 1607 pF is the max; typical is 1071 pF.
- `Qoss(20 V)`: 56 nC is the max; typical is 37 nC.

`Coss`/`Qoss` feed no computation; every path uses `Co(tr)` = 1860 pF,
which is typical and correct. `RDS(on)` = 1.55 mOhm is used by every
A55-A59 run. Per Fig. 9 it equals the typical device at Tj ~ 60 C. A60
makes this explicit.

## 5. Limits

Same as A58, except that Coss is now nonlinear:

- first-order reverse pricing;
- common dead times across phases;
- rated load only (see A62);
- Ron fixed at 1.55 mOhm (see A60);
- no inductor loss (see A61), gate drive, or thermal model;
- negative current ~39% of peak, which is not P24's operating mode;
- no SPICE (see A64).

## 6. Reproduction

```
python3 digitize_epc2067_coss.py <epc2067_datasheet.pdf>     # refuses to overwrite
python3 test_a59.py -v
python3 run_a59.py --design zvs --seed-json ../A58_asymmetric_fixed_deadtime_tuning/runs/zvs_r2.150_f2.150.json --path 2.15:2.15
python3 run_a59.py --design baseline --seed-json ../A58_asymmetric_fixed_deadtime_tuning/runs/baseline_r2.150_f2.150.json --path 2.15:2.15
python3 run_a59.py --design zvs --seed-json runs/zvs_r2.150_f2.150.json --path 2.15:2.15,<R>:2.15,<R>:1.15,<R>:0.95,<R>:0.85,<R>:0.75,<R>:0.65,<R>:0.55,<R>:0.45
python3 run_a59.py --design baseline --seed-json runs/baseline_r2.150_f2.150.json --path 2.15:2.15,<R>:2.15,<R>:1.65,<R>:1.45,<R>:1.35,<R>:1.25,<R>:1.15,<R>:1.05,<R>:0.95
python3 run_a59.py --design baseline --seed-json runs/baseline_r2.150_f1.150.json --path 2.5:1.15,2.5:1.25,2.5:1.05
python3 run_a59.py --design zvs --seed-json runs/zvs_r1.950_f0.650.json --path 1.95:0.65 --coarse 31.25e-12 --sub 2.5e-12 --suffix _step2p5ps
python3 build_a59_results.py
```

No A37-A58 file, `src/scb_ivr/`, `results/` or `paper_locked/` was modified.
