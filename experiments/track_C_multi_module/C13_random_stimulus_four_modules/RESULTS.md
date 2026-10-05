# C13 - random stimuli on four modules (RESULTS)
Boundary: 0295131. Records: cosim/run_*.json (31 + 3 single-module replays run_s1_*, release records-c13).
Summary: c13_summary.json (registered classifier); post hoc: c13_posthoc.py -> c13_posthoc.json.

## 0. Verdict
- As registered 5/6: criterion 1 fails on one event. The trace (Section 2) shows a rounding tie, with every edge in
  its intended window, so under the decision rule (Section 4) it becomes a known class (K5).
  **The four-module design (C12 + lo_learn 4) is frozen; the multi-module level is closed.**
- Conditions: 30 draws (L 12, B 6, D 6, S 6 from 145 us), four modules, L x 0.7-1.3, Cs x 0.7-1.3, driver +-3.4 ns.
- Passed: overlaps / alternation 0, NEW 0 (K1 6, K2 23 all y08, K3 94 all y18, K4 5), all settle, I0 = A143 bit for
  bit, rail 1 <= 12.53 V (limit 13.5). S rows from 145 us settle (late fires up to 130 in y28 / y29, transient).
- Peaks > 200 A only on falling ramps outside A139's certified table, the same on one module (Section 2).
  LBD peak <= 200 A in 88 % (prediction >= 85 %).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | floor-first 0 | FAIL as registered: y08 (1, a 0.36 LSB tie -> K5) |
| 2 | overlaps / alternation 0 | PASS |
| 3 | NEW 0 | PASS |
| 4 | settle | PASS |
| 5 | I0 identical | PASS |
| 6 | rails | PASS (max 12.53 V) |

## 2. Trace (post hoc)
- y08 module 2 phase 1 at 1012.02 us. The low-off command times (edges minus t_drv and the low-side mismatch) are:
  floor 32384408.648, clocked 32384409.003 LSB. The floor's report round(t_cmd / lsb) = 32384409 = t_lo, so
  `fl_lo` (a_tlo - t_lo < 0) is false and the pending turn-on stays. Both turn-ons follow their low-off by 312 LSB
  (dt_pred), 0.36 LSB (11 ps) apart. The second lands on a gate already on (V_DS 0); that period's peak is 95.5 A
  (neighbours 89.4 / 100.8). One cycle earlier the floor led by 72 LSB and floor_late dropped the pending turn-on.
- 279 records (C12, C13, A142 z, A143) hold 18 duplicates: 17 K1 (clocked first, floor 0.04-26.7 LSB later) and this
  one (floor first by 0.36). With floor_late, a floor-first duplicate is only possible within 0.5 LSB, so it is K1
  in the mirror order. a142_oracles now classes it as K5 (< 0.5 LSB). The effect is a Ton error < 16 ps (< 0.1 A).
- One-module replays of the > 200 A rows (modules / slave_floor removed) peak on phase 4 at the same time:
  y08 (-7.74 V / 1.24 us, L x 0.80) 248.6 vs 259.6 A; y10 (-6.81 V / 1.37 us, L x 0.96) 214.2 vs 218.2 A;
  y02 (-6.72 V / 4.95 us, L x 1.25, Cs x 1.29) 227.8 vs 229.0 A. A139's table needs >= 6.7 / 8.8 / 11.6 us for
  these cells, so all three are outside the spec. Four modules add 1-11 A.

## 3. Limits
- 30 draws: a defect class with a per-run rate < 10 % can be missed (95 %).
- y08's +11 A over one module is at 6.3 V/us, 4.7 x the A130 slope limit; inside the table, four modules stay within
  +-2 A of one (C10-C12).
- y18's 94 K3 restarts (S stratum, positive valleys) were not traced individually.
