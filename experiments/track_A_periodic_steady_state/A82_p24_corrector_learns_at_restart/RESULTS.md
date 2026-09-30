# A82 - test D43's prediction: a corrector that also learns at restart edges (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`, with the
predictions written before the runs. Records:
- `run_*.json`;
- `a82_summary.json`;
- `gate_pairs.json`.

**Model: the physical model** (A79's simulator plus `learn_at_restart`),
testing a prediction of the mathematical model (D43) at matched settings.

## 0. Verdict: every D43 prediction holds in the physical model

| run | target | ki (ns/V) | learn at restart | D43 prediction | physical result | phase-4 delay (physical / D43) | phase-4 turn-off current (physical / D43) | phase-4 Vds at turn-on (physical / D43) | criterion 2 |
|---|---:|---:|---|---|---|---:|---:|---:|---|
| 0 | 5% | 1.0 | off | gate (= A79 r2) | bit-identical; restart state | 20.13 ns / 20 | -0.63 / -0.68 A | 11.97 / 11.98 V | fail |
| 1 | 5% | 1.0 | on | soft | **soft** | 7.37 / 7.22 ns | -5.10 / -5.17 A | 9.24 / 9.20 V | **pass** (dither 0.93 A) |
| 2 | 4% | 0.25 | on | soft | **soft** | 7.86 / 7.70 ns | -3.76 / -3.82 A | 9.70 / 9.66 V | **pass** (0.60 A) |
| 3 | 3% | 0.25 | on | soft | **soft** | 8.62 / 8.58 ns | -2.26 / -2.34 A | 10.16 / 10.11 V | **pass** (0.79 A) |
| 4 | 2.5% | 0.25 | on | soft (edge) | soft on average; **not periodic** | 11.27 / 9.52 ns | -1.16 [-3.58, +0.77] / -1.36 A | 10.39 (max 10.9) / 10.34 V | fail (dither 3.39 A) |
| 5 | 2% | 0.25 | on | restart | **restart**; `dt_pred` runs to its 34.8 ns cap | - | +6.82 / +6.78 A | 10.68 V | fail |
| 6 | 3% | 0.25 | off | restart (lock-up) | **restart** | 20.14 / 20 ns | +2.18 / +2.03 A | 10.97 / 10.99 V | fail |

**D43 column notes.** The D43 values are its regulated, valley-consistent
orbits (D43 Section 8.2). Run 0 is compared with D43's A79 r2 cross-check
orbit. Run 4's D43 values come from the 30 ns-restart branch.

Every run regulates Vo to 1.0000 V, with peak Vds 25.2-25.4 V.

1. **The phase-4 "bistability" of A79 was a corrector lock-up.** With the
   corrector also sampling at restart turn-ons:
   - the 5% case that had settled in the restart state (A79 run 2, ki
     1.0) settles soft;
   - so do 4% and 3%, where the controller without the fix settles in the
     restart state (run 6; A78).
2. **Quantitative agreement between the two independent models.** Phase-4
   delays agree within 0.16 ns, turn-off currents within 0.2 A, turn-on
   voltages within 0.05 V (runs 1-3, 5, 6).
3. **P24's stated 1-2% is confirmed insufficient in both models.** At 2%,
   phase 4's current at its turn-off is +6.8 A, its valley lies after the
   restart, and the corrector cannot reach it. Phase 4 is hard-switched
   every cycle.
4. **The corrected lower bound is 3%.** 2.5% is the edge: soft on average,
   but not periodic. 3%-5% (and 7.5%, A79) pass criterion 2 in full. This
   replaces A78's "4-5%" threshold.

## 1. Checks

**Regression gate.** Run 0 (option off) replays A79 run 2 over its full
length bit-identically: 1748 sections, difference 0.0, equal end state.

## 2. Consequences for earlier results

- **A78.** Its verdict "P24's 1-2% is not enough" stands. Its threshold
  "between 4% and 5%" belonged to the corrector that learns only at
  predictive edges. With the fixed corrector it is 2.5-3%.
- **A79.** Its "phase 4 is bistable at 5%" describes that corrector. With
  the fix, 5% is soft for both loop gains tested (A79 runs 1 and 3 and
  A82 run 1).
- **A80/A81 (Verilog).** The RTL's correction accepts every measurement
  pulse. The bridge sends measurements only after predictive turn-ons, so
  the same lock-up is possible there. That is the next RTL change.

## 3. Limits

- **The circuit.** The idealised P24 module of A79.
- **The fix.** One correction rule; its step (0.2 ns) is a
  `PROJECT_DECISION`.
- **Scope.** The 2.5% edge case was run once.

## 5a. Reproduction

```
zsh run_a82.sh
python3 a82_analyze.py
```
