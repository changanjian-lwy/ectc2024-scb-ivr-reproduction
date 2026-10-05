# C13 - random stimuli on four modules (RESULTS)
Boundary: 0295131. Records: cosim/run_*.json (31, release records-c13). Summary: c13_summary.json.
## 0. Verdict
- FAIL 5/6 (criterion 1). Four-module design (C12 + lo_learn 4) NOT frozen yet. Conditions: 30 random draws (L 12, B 6, D 6, S 6), 4 modules, template A143.
- One floor-first duplicate: y08 module 2 phase 1 at 1012.03 us, two turn-ons 11 ps apart (and two low-offs 10 ps apart at 1012.022); that period's peak is 95.5 A, normal. y08 = L x 0.80, Cs x 1.04, -7.74 V in 1.24 us (6.2 V/us, outside A139's table).
- Peaks > 200 A only on fast/corner falling ramps: y08 260 A (late 8), y02 229 A (-6.72 V / 4.95 us, L x 1.25, Cs x 1.29), y10 218 A (-6.81 V / 1.37 us, L x 0.96, late 7). LBD peak <= 200 A in 88 % (prediction >= 85 %).
- Passed: overlaps / alternation 0, NEW 0 (K1 6, K2 23 all y08, K3 94 all y18, K4 5), all settle, I0 identical to A143, rails <= 12.53 V (limit 13.5). S rows from 145 us settle; late fires up to 130 (y28 / y29).
## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | floor-first 0 | FAIL: y08 (1) |
| 2-6 | overlap/alt 0, NEW 0, settle, I0, rails | PASS |
## 2. Limits
- Trace of y08's 11 ps duplicate (RTL window) not done: it has no peak consequence; the 260 A peak is the fast-ramp physics (K2 order swaps in the ramp).
- 94 K3 restarts in y18 (S stratum) not examined.
