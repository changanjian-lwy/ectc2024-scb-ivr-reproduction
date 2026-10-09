# A177 - the per-board interlock reference on the slow-corner rows (RESULTS)
Boundary: 1a4b4d1. Records: release records-a177 (run_*.json, run log). Analysis: a177_analyze.py ->
a177_summary.json. All runs from committed code.

## 0. Verdict
- **1 of 4 pass as registered** (slew4). With A173's +4.8 V / 1 us row, the per-board form (t_il 1.4 ns) meets
  A174's criterion 4 on 2 of the 5 slow-corner rows. Decision rule: the slow corner needs a release faster than
  ~1.4 ns (adaptive dead-time drivers: 0.03-1 ns). Named open.
- The misses are small:
  - −8 V / 10 us: late fires 130 against a limit of 126.5; Vo −27.8 mV against −25.2 ± 2;
  - load step: NEW 20 against a limit of 19;
  - four modules: NEW 13 against a limit of 10.
- The per-board form recovers most of what the fixed 1.0 V reference loses. On four modules: late 792 (0.5 ns: 803;
  fixed 8.3 ns: 1608) and NEW 13 (8; 82).
- **No interlock delay tested (0.5-8.3 ns) changed a peak or a voltage.** Post-step peaks stay within ±0.9 A and
  V_DS does not rise on any row. So the release time is a timing specification, not a safety one.
- **Late fires grow monotonically with the delay** at 0.5 / 1.4 / 8.3 ns:
  - −8 V: 81 / 130 / 154;
  - load step: 72 / 83 / 104;
  - slew4: 190 / 205 / 299;
  - +4.8 V: 194 / 210 / 244;
  - four modules: 803 / 792 / 1608.
  NEW spikes and the Vo extreme do not: −8 V NEW 3 / 0 / 5 and Vo −25.2 / −27.8 / −26.0 mV. Criterion 4's NEW and
  Vo tolerances (+2, ±2 mV) are near the scatter between neighbouring runs.

## 1. Criteria (against A173's t_il 0.5 ns run; A174's 8.3 ns alongside)
| row | post (A) | late | NEW | Vo extreme (mV) | holds / max | result |
|---|---|---|---|---|---|---|
| ss −8 V / 10 us | 170.0 (169.4 / 169.8) | **130** (81 / 154) | 0 (3 / 5) | **−27.8** (−25.2 / −26.0) | 49 / 3.5 ns | miss |
| ss load step | 184.2 (184.3 / 183.7) | 83 (72 / 104) | **20** (17 / 21) | −16.7 (−16.6 / −16.4) | 21 / 3.5 ns | miss |
| ss slew4 | 181.1 (180.2 / 180.9) | 205 (190 / 299) | 4 (10 / 12) | −12.0 (−13.5 / −9.9) | 80 / 3.6 ns | PASS |
| four modules ss +4.8 V / 1 us | 181.2 (181.4 / 181.4) | 792 (803 / 1608) | **13** (8 / 82) | −10.4 (−9.9 / −13.7) | 97 / 3.5 ns | miss |

V_DS 30.0-32.0 V; 0 shoot-throughs; all COMPLETED. Predictions: all pass - wrong (1 of 4); late +0-20 % - right on
three rows (+15 / +8 / −1 %), wrong on −8 V (+60 %); four modules 800-950 - just below (792).

## 2. Limits
- 1.4 ns is A173's estimate for a comparator at V_th − 0.2 V (0.5 ns propagation + gate fall + recharge). A real
  driver's comparator offset and noise are not modelled.
- One step position per row; A174 measured 2-3 A of phase spread on peaks, and the NEW / Vo scatter here is of the
  same nature.
- No release time between 0.5 and 1.4 ns was run, so the threshold of the slow corner's timing is not located.
