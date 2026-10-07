# A161 - 150 pH with a faster turn-on (x_on 3.0 V), on A152's robustness matrix (RESULTS)
Boundary: 89f21c0. Records: release records-a161 (14 runs). Outputs: a161_summary.json (a161_analyze.py), a161_predictions.json.

## 0. Verdict
- **4/5 as registered (1, 2, 4, 5 pass; 3 fails on late fires only), so by the registered rule the recommended loop
  bound is 150 pH with a 20 A/ns turn-on (x_on 3.0 V), at a voltage margin of 0.6 V.**
- **Voltage:** every row <= 39.4 V (L x 1.3 l_p48_1us; predicted 39.6), four modules 39.0 V; the A156-offset prediction
  held within -0.5..+1.0 V.
- **Regulation recovers** at 20 A/ns (criterion 4 passes; A159's 12 A/ns missed it): the load-step dip and the slow-ramp
  recovery are back within the ideal reference's margins. Start-up 145-154 A (L x 0.7 194 A).
- **No NEW event at all:** with the faster turn-on the post-step swing peak falls back inside the oracle's K4 window.
- **Late fires on -8 V / 10 us: 28** (12 A/ns at 150 pH: 33; 0 / 6 / 16 at 50 / 100 / 125 pH). They follow the loop, not
  x_on, and had no consequence in any run.
- **The turn-on has a window:** voltage wants di/dt_on <= 3.0 V / L (A156 / A161 on the matrix); regulation wants
  di/dt_on >= ~18-20 A/ns (A159: 12 A/ns misses; 18 / 20 / 24 A/ns pass). The window closes at
  L = 3.0 V / 20 A/ns = 150 pH: that is the loop bound. A156's "adopted x_on <= 1.8 V" attributed the late fires to
  x_on; A159 / A161 show they come with L.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | V_DS <= 40 V, 13 rows | PASS (<= 39.4 V) |
| 2 | start-up <= max(200, ref + 5) A | PASS (145-194 A) |
| 3 | post-step, 0 NEW, late <= ref + 2 | FAIL: l_m80_10us late 28 (only miss; 0 NEW) |
| 4 | Vo extreme / back | PASS |
| 5 | four modules, criteria 1-3 | PASS (39.0 V, 154 / 174 A, late 0, 0 NEW) |

## 2. Limits
- 0.6 V of voltage margin at the worst corner; Cs corners, temperature and a gate model not covered.
- The late fires' mechanism (phase 4's slot after a falling ramp, growing with L) is still not traced.
