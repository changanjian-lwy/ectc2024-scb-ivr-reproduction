# A158 - where the loop-damping boundary lies (RESULTS)
Boundary: cea976e. Records: release records-a158 (5 runs). Outputs: a158_summary.json (a158_analyze.py), a158_predictions.json.

## 0. Verdict
- **0/2 as registered, but both misses are one oracle-timing artefact; with it set aside, the Q-only rule (H1) is right on
  all 5 rows: the damping boundary lies between ring Q 30 and Q 100 at both 50 and 100 pH.**
- **Q 100 and Q 300 lose the valley tracking at both inductances:** q100_s50 2437 late fires, q100_s100 6148, q300_s50
  7151 (42.8 V, 198 A). Undamped did the same in A157.
- **Q 15 and Q 30 at 100 pH hold the controller:** 0 late fires, V_DS 36.7 / 36.9 V (Q 7: 36.4), post-step 169-173 A.
  Each has one NEW "spike": phase 1's post-step period swing (168 -> 152 -> 137 -> 171 A; 166 -> 149 -> 136 -> 165 A)
  peaks at 1002.05 us, 0.05 us after the oracle's K4 window (ramp + 1 us) - the slow-turn-on timing case of A154,
  not a damping effect (no late fire, no voltage or peak change).
- **H2 (the harness's 20 ns ring residual <= 4 V) is wrong on 3 / 5:** 300 pH at Q 7 holds with 7.5 V left (A154), 50 pH
  at Q 100 fails with 3.0 V. What breaks the tracking is Q itself (the ring still running a few periods later, when the
  comparators act), not the residual amplitude at a fixed time.
- **Spec: ring Q <= 30 (tested at 50 and 100 pH; Q 7 tested to 300 pH); Q >= 100 fails.**

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | H1's hold / fail call right on 5 rows | FAIL on q15_s100, q30_s100: one K4-timing spike each (above); right on the other 3 |
| 2 | q30_s100 holds | FAIL by the same spike; 0 late fires, 36.9 V |

## 2. Limits
- The oracle's K4 window (line ramp + 1 us) is narrower than the post-step swing with a slow turn-on (+1.05-1.16 us in
  A154 / A158); widening it would reclassify earlier records and is left as a registered change for later.
- Q 30-100 not resolved; one row (+4.8 V / 1 us) per point.
