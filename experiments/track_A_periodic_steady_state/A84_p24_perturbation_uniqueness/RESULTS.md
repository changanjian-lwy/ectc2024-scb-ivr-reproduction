# A84 - perturbation test: is the soft state the only one? (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`. Records:
- `run_k*.json`;
- `a84_summary.json`;
- `gate_pairs.json`.

**Model: the physical model** (A82's simulator plus a controller-state
kick). Recovery involves the corrector and loop dynamics, which D43's fixed-
point map does not simulate.

## 0. Verdict

**With the corrector that also learns at restart turn-ons, the restart
state is not an attractor.** A kick of phase 4's `dt_pred` to 20.2 ns
produces exactly one restart turn-on; from the next cycle phase 4 is
predictive and soft again. This holds at 5% and at 3%.

**With the old corrector, the same kick moves an established soft state
into the restart state for good.** At 5%, run k2 was soft before the kick,
with no phase-4 restart since the start-up. After the kick, every one of
the ~600 remaining cycles is a restart. It ends in exactly A79 run 2's
state:
- -0.63 A at phase 4's turn-off;
- turn-on at 11.97 V.

So the old controller has two attractors, and a single disturbance switches
between them. That is the bistability of A79 and D43. With the fix there is
one.

| run | target | learn at restart | kick at | phase-4 restarts before / after the kick | phase 4, last 50 cycles | criterion 2 |
|---|---:|---|---:|---|---|---|
| k0 (gate) | 3% | on | none | 153 (start-up) / - | predictive, 10.16 V | pass |
| k1 | 5% | on | 250.02 us | 0 / **1** (at 250.19 us) | predictive, 9.21 V | fail (dither 1.05 A; otherwise soft once per cycle, no restart) |
| k2 | 5% | off | 250.02 us | 0 / **596** (to the end) | restart, 11.97 V | fail |
| k3 | 3% | on | 250.03 us | 153 (start-up) / **1** | predictive, 10.15 V | pass |
| k4 | 3% | off | 250.13 us | 1230 in total: locked from the start-up; the kick was redundant (as anticipated in BOUNDARY) | restart, 10.97 V | fail |

**Common results.** Every run ends at Vo 1.0000 V, with peak Vds
25.2-25.4 V.

**Start-up at 3% with the fix (k0, k3).** It passes through 153 phase-4
restarts during the transient, then learns its way out. This is the zero-
start path of A82 run 3.

## 1. Checks

**Regression gate.** k0 (no kick) replays A82 run 3 over its full length
bit-identically: 1791 sections, difference 0.0.

## 2. Limits

- **One kind of perturbation.** The kick hits the corrector state. Load
  and line steps, and plant-state kicks, are not tested.
- **One kick per run**, from one steady state per target.
- **The circuit.** The idealised P24 module of A79.

## 5a. Reproduction

```
zsh run_a84.sh
python3 a84_analyze.py
```
