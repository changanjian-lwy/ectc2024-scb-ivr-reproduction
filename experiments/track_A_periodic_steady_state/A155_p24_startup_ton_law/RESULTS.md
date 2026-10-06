# A155 - the start-up ton law with loop and turn-off terms, tested to 300 pH (RESULTS)
Boundary: 86bea7b. Records: release records-a155 (5 runs). Outputs: a155_summary.json (a155_analyze.py), a155_fit.json,
a155_predictions.json.

## 0. Verdict
- **PASS 4/4. The start-up on-time is now one formula from 50 to 300 pH:**
  ton_S = 35.5 ns + [V_T − 1.048 + 0.447 d_on^-1/2 + 0.171 L[nH] − 0.279 d_off^-1/2] / 0.0283, V_T = 1.015 V
  (d in A/ns). In ns: 15.8 (d_on^-1/2) + 6.0 per nH of loop − 9.8 (d_off^-1/2), referred to the ideal plant.
- At four combinations never run (175 pH / 18 / 56 A/ns, 200 / 16 / 50, 250 / 12.8 / 36, 300 / 10 / 30) the handover Vo
  is 1.012 / 1.023 / 1.011 / 1.010 V (target 1.015 +- 0.010) and every start-up peak 151-152 A.
- **The L term is needed:** the control (300 pH with D68's ton, no L / turn-off term) reached 0.9951 V (predicted
  0.9941) and 162 A. A154's 166-190 A start-ups above 150 pH were this missing term.
- Start-up V_DS <= 35.3 V on all five (x_on 3.0-3.2 V, x_off 9-10 V).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | Vo 1.015 +- 0.010 V, 4 law rows | PASS (-0.005..+0.008 V) |
| 2 | start-up peak <= 165 A, 4 law rows | PASS (151-152 A) |
| 3 | c300 Vo within 0.010 V of 0.994 and < 1.005 | PASS (0.9951) |
| 4 | start-up V_DS <= 40 V, all 5 | PASS (<= 35.3 V) |

## 2. Limits
- Start-up only (300 us, n0): the line and load steps at these drives are A154's (similar x) and A153's.
- The fit is empirical in L and d_off (two linear terms); its d_on term is D68's node-charge law. Valid over the fitted
  range: L 50-300 pH, d_on 6-72, d_off 24-72 A/ns, Q 7, 25 °C, nominal L / Cs.
