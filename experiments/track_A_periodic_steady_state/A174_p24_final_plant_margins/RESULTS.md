# A174 - the final plant's marginal rows at other step positions, and a fixed-reference interlock (RESULTS)
Boundary: 39ed6bf. Records: release records-a174 (run_*.json, run log). Analysis: a174_analyze.py ->
a174_summary.json. All runs from committed code.

## 0. Verdict
- **L x 0.7 exceeds 200 A at one of five step phases.** After +4.8 V / 1 us the post-step peak is 199.7 (A172),
  199.9, 199.8, 199.5 and 201.5 A (step at +0, 1, 2, 3, 4 T/5). At the 201.5 A phase Vo stays outside 1 % for
  37.9 us (11.0 mV). Decision rule: the spec states that the L x 0.7 board exceeds 200 A at some step phases, by up
  to 1.5 A here. L x 0.7 is at the edge of the tested margin, not inside it. The spread over phases is 2.0 A,
  inside A129's 2-7 A.
- **ff -8 V / 10 us: the spike is phase-dependent, the Vo excess is not.** NEW at 2 of 5 phases (the original and
  +1 T/5), so 1 of the 4 new ones: not systematic by the registered rule (>= 2). Vo 30.6-31.8 mV at every phase
  (limit 30.5) and post-step 181.5-183.0 A (V2 176.9). A176 places that offset in the gate-driven low sides.
  A175 / A176 show the restarts behind the spike are systematic on falling steps.
- **A fixed 1.0 V interlock reference does not meet the criteria at the slow corner.** At t_il 8.3 ns, against
  the 0.5 ns runs, peaks change by <= 0.7 A and V_DS does not rise. But:
  - late fires: +90 % on the −8 V ramp, +57 % on slew4, +44 % on the load step, and ×2.0 on four modules
    (1608 against 803);
  - NEW spikes: +4 on the load step, 82 against 8 on four modules;
  - four-module Vo: −13.7 mV against −9.9, outside 1 % for 9.9 us.
  Decision rule: the slow corner needs the per-board reference form (V_th − 0.2 V, ~1.4 ns; A173 passes it on
  +4.8 V / 1 us). ff at its fixed-reference value (1.0 ns) passes, the same as 0.5 ns.

## 1. Criteria
| row | criterion | result |
|---|---|---|
| sh1-sh4 L x 0.7 +4.8 V / 1 us | 1 (A168) | sh1-sh3 PASS (199.5-199.9 A); sh4 miss: post 201.5 A, Vo 11.0 mV / back 37.9 us |
| L x 0.7, 5 phases | 2: all <= 200 A | **no** (201.5 A at +4 T/5) |
| sh1-sh4 ff -8 V / 10 us | 1 (A168) | miss on all four: Vo 30.6-31.8 mV (<= 30.5); post 182.1 / 183.0 A at sh2 / sh4 (<= 181.9); NEW 1 at sh1 |
| ff, 5 phases | 3: NEW at >= 2 of 4 new | **no** (1 of 4) |
| fr ff l_m80_10us (1.0 ns) | 4 | PASS |
| fr ss l_m80_10us (8.3 ns) | 4 | miss: late 154 vs 81 |
| fr ss s_p62 (8.3 ns) | 4 | miss: NEW 21 vs 17 (late 104 vs 72 within) |
| fr ss slew4 (8.3 ns) | 4 | miss: late 299 vs 190; Vo -9.9 vs -13.5 mV (smaller, but outside ±2 mV) |
| fr m4 ss l_p48_1us (8.3 ns) | 4 | miss: late 1608 vs 803, NEW 82 vs 8, Vo -13.7 vs -9.9 mV |

Predictions: L x 0.7 195-203 A with one of four above 200 A - right. ff spike at 0-1 of 4 new phases - right; ff Vo
28-32 mV - right. Fixed reference within criterion 4 everywhere - wrong; four-module late 850-1000 - wrong (1608).

## 2. Limits
- Five phases per row. The L x 0.7 maximum over all phases may exceed 201.5 A.
- The 8.3 / 1.4 ns delays are estimated from the gate model (comparator 0.5 ns + gate fall / recharge), not from a
  driver circuit. Comparator offset and noise, which could release early, are not modelled.
- The per-board form was run on one row only (A173, ss +4.8 V / 1 us).
