# A58 - asymmetric fixed dead time: can tuned (non-adaptive) timing keep the rated-load ZVS advantage? (RESULTS)

Track A, `SENSITIVITY_ONLY`. Boundary: `BOUNDARY.md` (commit `4527e1f`),
unmodified except for the one declared baseline extension (Section 3).
Python solver only; no SPICE. Records: `runs/*.json` (every point, all
regulation trials, z*, full boundary, accounting), `results.json` (built by
`build_a58_results.py`), `logs/`.

## 0. Verdict

**Yes, in this model. With two tuned fixed dead times, the large-ripple
design stays 2.70 W below the equally tuned hard-switched baseline at 250 W,
under the datasheet reverse characteristic.** This recovers 85% of A56's
ideal-adaptive advantage (3.18 W). Under A57's single symmetric dead time,
the same design was 7.06 W worse.

| (all at 250 W, EPC2067, Fig. 8 25 C) | d_rise / d_fall | Ton_cmd | P_A (adaptive) | **P_B (fixed dead time)** |
|---|---|---:|---:|---:|
| baseline 1.4667 nH, tuned | 2.15 / 1.1 ns | 18.356 ns (+10.1%) | 31.456 W | **31.811 W** |
| large-ripple 0.6274 nH, tuned | 1.9 / 0.6 ns | 17.041 ns (+2.2%) | 28.486 W | **29.109 W** |
| difference | | | -2.97 W | **-2.70 W** |

- The ranking does not depend on the reverse model: -2.70 W at 125 C and
  -2.95 W at the 1.2 V floor, where the ZVS optimum moves to 2.0/0.7 ns.
  With A57's turn-on recharge estimate included: -2.51 W.
- It is step-converged. At 62.5 / 31.25 / 15.625 ps, the ZVS point gives
  29.109 / 29.095 / 29.087 W and the baseline gives 31.811 / 31.808 /
  31.806 W. `Ton_cmd` and every verdict are identical across the three steps.
- It is independently confirmed. Richardson-extrapolated `P_in - P_load`,
  minus the other resistive loss, gives 28.455 W vs `P_A` 28.463 W (ZVS) and
  31.449 W vs 31.451 W (baseline). The capacitive accounting of the new
  partial-hard events therefore matches a meter-free energy balance to
  0.01 W.
- All 67 grid points regulated to 250 W. None failed. The maximum orbit
  current is 217.3 A and the maximum Newton probe is 225.1 A, both inside
  the +/-250 A screen.

**The tuned optimum is near-ZVS, not all-eight ZVS.** At 1.9/0.6 ns, three
high-side edges turn on at 0.74-0.76 V residual and three low-side edges at
1.42-1.73 V (the baseline's high side switches at 12 V). Only phase 4
reaches zero on both edges. Turning on slightly early costs 0.26 W of
residual capacitive energy but removes most of the reverse conduction:
A57's 17.0 W falls to 0.64 W.

## 1. What changed and why it matters

The single symmetric window of A51/A56 had to cover the slow high-side
transition (~2.05 ns). That wasted ~1.45 ns of reverse conduction on the
fast +215 A low-side transition (~0.69 ns). Splitting the window removes
that waste. `d_fall` is the lever that matters: the ZVS design's `P_B`
falls from 44.47 W to 29.42 W along `d_fall` alone. `d_rise` is worth only
~0.3 W.

## 2. Grids (P_B, Fig. 8 25 C, W; 62.5 ps)

Large-ripple design, `L = 0.627406 nH`:

| d_rise \ d_fall | 2.15 | 1.2 | 0.9 | 0.8 | 0.7 | 0.6 | 0.5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2.15 | 44.47 | 34.65 | 31.50 | 30.49 | 29.49 | 29.42 | 29.95 |
| 2.0 | 44.22 | 34.36 | 31.21 | 30.20 | 29.20 | 29.13 | 29.65 |
| 1.9 | 44.18 | 34.34 | 31.19 | 30.18 | 29.18 | **29.11** | 29.63 |
| 1.8 | 44.21 | 34.37 | 31.23 | 30.21 | 29.21 | 29.14 | 29.66 |
| 1.6 | 44.45 | 34.60 | 31.46 | 30.44 | 29.44 | 29.37 | 29.89 |

Baseline, `L = 1.4667 nH`. The `d_rise = 2.5` row is the declared one-step
extension: the pre-extension optimum sat on the `d_rise = 2.15` grid edge.
The extension is worse, so the optimum is interior.

| d_rise \ d_fall | 2.15 | 1.6 | 1.4 | 1.3 | 1.2 | 1.1 | 1.0 | 0.9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2.5 (ext.) | 37.43 | 34.24 | 33.07 | 32.50 | 31.93 | 31.83 | 31.94 | 32.24 |
| 2.15 | 37.41 | 34.22 | 33.05 | 32.48 | 31.92 | **31.81** | 31.93 | 32.23 |
| 1.0 | 37.48 | 34.28 | 33.13 | 32.54 | 31.98 | 31.88 | 32.00 | 32.30 |
| 0.5 | 37.56 | 34.39 | 33.22 | 32.64 | 32.08 | 31.98 | 32.10 | 32.40 |

Both optima are interior on both axes. The adaptive `P_A` grids are in
`results.json`; they are nearly flat until `d_fall` falls below the
natural transition.

## 3. The timing that makes it work

Natural transition times at 250 W, taken from the symmetric anchors:

| edge | phases 1-3 | phase 4 |
|---|---:|---:|
| ZVS design, low side (d_fall) | 0.69-0.70 ns | 0.50 ns |
| ZVS design, high side (d_rise) | 2.04-2.05 ns | 1.40 ns |
| baseline, low side (d_fall) | 1.18-1.20 ns | 0.85 ns |
| baseline, high side | hard (12 V) | hard |

Each design's best `d_fall` sits just below its phases 1-3 low-side
transition. The ZVS design's best `d_rise` also sits just below its
high-side transition; the baseline's high side is hard-switched either way. One common
setting cannot match phase 4, whose transitions are shorter. At the ZVS
optimum, phase 4 still conducts in reverse for 0.50 ns (high) and 0.10 ns
(low). Per-phase dead times would recover part of this, but that is
outside this boundary.

**Timing tolerance.** Suppose both designs hold their best `d_rise` and miss
their best `d_fall` by the same delta. The ZVS advantage is then -2.29 W at
-0.1 ns, -2.70 W at 0, -2.74 W at +0.1 ns, -2.30 W at +0.2 ns, -1.86 W at
+0.3 ns, -1.40 W at +0.4 ns and -0.93 W at +0.5 ns. It vanishes near +0.7
ns late by linear extrapolation. If only the ZVS design misses and the
baseline stays at its optimum, the ZVS design stays ahead up to ~+0.35 ns
late. These transition times are for 250 W only. They move with load
current, so a fixed setting tuned here is not tuned at other loads (not
tested).

## 4. Checks

- `test_a58_schedule.py`, 7 tests, all pass:
  - with `d_rise = d_fall = 2.15 ns` the Newton map is bit-identical to A56's;
  - every holder of the four schedule functions is found by object identity
    (6 bindings in 3 modules) and swapped;
  - modes in every namespace match the analytic asymmetric schedule;
  - interval and verdict windows have the declared lengths on the solve path
    and the metering path;
  - overwriting the scalar `dead_time_s` leaves the map bit-identical, so no
    path reads it.
- Anchors: both symmetric points reproduce A56's `P_A` (28.206 / 31.382 W,
  missed C 12.974 W, `P_in - P_load` 32.784 W) and A57's `P_B`
  (44.472 / 37.411 W) to the digits reported there.
- Step ladder and source-side balance: Section 0.

## 5. Stated approximations and limits

- First-order reverse pricing, as in A57 (no clamp-resolved orbit). At the
  tuned optimum the priced reverse loss is only 0.64 W (ZVS) and 0.37 W
  (baseline), so this approximation now carries little weight.
- Linear Co(tr) capacitances, as in A56. The near-ZVS residual voltages
  (0.7-1.7 V) sit where the real EPC2067 Coss is largest, so nonlinear Coss
  would change the residual energies (not tested).
- Common dead times across phases, rated load only, ideal zero-jitter
  timing. Magnetic, gate-drive, thermal and package loss are absent. The
  large-ripple design carries 217 A peak vs 129 A, which makes magnetic
  loss unfavorable to it. Negative current remains ~39% of peak versus P24's
  1-2%, so this is not the paper's operating mode.
- Not a native P24 controller, not a hardware efficiency and not a paper
  reproduction.

## 6. Consequence for the A53-A57 chain

- A56 (adaptive limit): -3.18 W. A57 (one symmetric fixed dead time):
  +7.06 W. **A58 (two tuned fixed dead times): -2.70 W.** Rated-load
  large-ripple operation pays in this model when the falling-edge dead time
  stays within the tested -0.1 ns to about +0.35 ns of its optimum, which
  sits just below the natural low-side transition. Neither an adaptive
  controller nor exact ZVS is required.
- The open terms that could still reverse it are now non-electrical or
  device-nonlinear: magnetic loss at 1.69x peak current, and the
  Co(er)/Co(tr) question for the near-ZVS residuals.

## 7. Reproduction

From this directory; runs are never overwritten (existing points are
reused as continuation seeds):

```
python3 test_a58_schedule.py -v
python3 run_a58.py --design zvs --seed-json ../A56_equal_power_regulated_loss_comparison/runs/old_critical_dt_x1.json --path 2.15:2.15
python3 run_a58.py --design baseline --seed-json ../A56_equal_power_regulated_loss_comparison/runs/nominal_dt_x1.json --path 2.15:2.15
# phase 1 (d_rise at d_fall = 2.15), then one process per d_rise line:
python3 run_a58.py --design zvs --seed-json runs/zvs_r2.150_f2.150.json --path 2.15:2.15,2.0:2.15,1.9:2.15,1.8:2.15,1.6:2.15
python3 run_a58.py --design zvs --seed-json runs/zvs_r<R>_f2.150.json --path <R>:2.15,<R>:1.2,<R>:0.9,<R>:0.8,<R>:0.7,<R>:0.6,<R>:0.5
python3 run_a58.py --design baseline --seed-json runs/baseline_r<R>_f2.150.json --path <R>:2.15,<R>:1.6,<R>:1.4,<R>:1.3,<R>:1.2,<R>:1.1,<R>:1.0,<R>:0.9
# step ladder:
python3 run_a58.py --design zvs --seed-json runs/zvs_r1.900_f0.600.json --path 1.9:0.6 --coarse 31.25e-12 --sub 2.5e-12 --suffix _step2p5ps
python3 build_a58_results.py
```

Runs were independent processes with `OMP_NUM_THREADS=1`, up to 8 in
parallel. A point takes 1-5 min. No A37-A57 file, `src/scb_ivr/`,
`results/` or `paper_locked/` was modified.
