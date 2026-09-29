# A69 - physical-model cross-check of the mathematical model's D41/D42 orbits (RESULTS)

Track A, cross-check. Boundary: `BOUNDARY.md`, plus its Section 5a
amendment made before the long runs. Records:
- `run_*.json`, one per run;
- `ref_*.json`: the mathematical model's section states used as start
  states and references.

## 0. Verdict

**An independently written time-domain simulation of the same circuit and
control reproduces the mathematical model's periodic orbit, its weak
instability without damping, and its stability with P25-scale damping,
each to within a fraction of a percent.** The orbit is a property of the
circuit, not of the event machinery.

| check | physical model (A69) | mathematical model (D41/D42) |
|---|---:|---:|
| period after one cycle, lossless | 1946.408 ns | 1946.412 ns (diff 3.5 ps) |
| section state after one cycle, lossless | currents within 0.09 mA; voltages within 10 uV | - |
| deviation growth per cycle, lossless (cycles 60-120) | 1.0592 | \|lambda\| = 1.0604 |
| deviation growth per cycle, 0.5 mOhm (cycles 60-120) | 1.0388 | \|lambda\| = 1.0432 |
| decay of a 0.2 A kick per cycle, 4.9 mOhm (cycles 20-60) | **0.9289** | **\|lambda\| = 0.9264** |
| period at 4.9 mOhm after 80 cycles | 2172.40 ns | 2172.35 ns |

- **Growth fits.** They use the cycles where the leading mode dominates.
  Over cycles 10-60 the lossless fit is lower (1.014), because the slow
  0.977 pair and the start transient mix in.
- **The 4.9 mOhm run.** It contracts from 0.2 A to a ~1e-3 A floor, which
  is the residual model-to-model offset.

## 1. What this adds to the chain

- **D41's orbit is real and reproduced independently.** Only the start
  state is shared between the two models. The simulator differs in
  integration (fixed-step trapezoid), switches (resistors), reverse
  conduction (diodes) and control (per-step checks).
- **D41's weak instability is real, and small losses remove it.** D42
  predicts the crossing at ~1.7 mOhm per phase and |lambda| = 0.926 at the
  P25-estimated 4.9 mOhm. A69 sees the same contraction rate.
- **A model-accuracy lesson.** A 10 uOhm ON resistance, "negligible" at
  5e-4 of Vo, shifted the period by 0.25 ns: the drop acts over the whole
  ~1.5 us current decay. The offset was found by step halving and ON-R
  scaling (BOUNDARY 5a).

## 2. A controller finding (not a failure of either model)

A run at 4.9 mOhm was started from the *lossless* orbit, which has Vo
1.035 V against the damped steady state's 0.844 V. It deadlocked at about
7.9 us:
- phases 2 and 3 turned their low sides off on their timers;
- their high sides then waited for a zero-voltage condition that never
  came, because the currents at the timed turn-off were not negative
  enough;
- phase 1 kept waiting for its current target.

The single-sensor, fixed-shift control as specified has no timeout or
forced turn-on, so large transients can lock it up. Hardware needs a
fallback, which is relevant to start-up (Track B). Local perturbations
(0.2 A) are absorbed normally.

## 3. Limits

- The idealised circuit matches D41/D42: linear Coss, ideal-diode reverse
  conduction, 0.1 uOhm ON resistance, constant-current load and open loop.
  It is not the GS61008T vendor model.
- The fixed step is 10 ps (5 ps check: identical to 0.1 ps in period).
  Events are landed by interpolated partial steps; diode states update at
  step boundaries.

## 4. Reproduction

```
python3 a69_transient.py lossless 150 10e-12 ref_D41_lossless.json 1e7
python3 a69_transient.py damped 150 10e-12 ref_D42_R0p5mohm.json 1e7
python3 a69_transient.py damped4p9_perturbed 80 10e-12 ref_D42_R4p9mohm.json 1e7 start_D42_R4p9mohm_perturbed.json
python3 a69_transient.py lossless 5 10e-12 ref_D41_lossless.json 1e5   # BOUNDARY 5a smoke (10 uOhm)
```
