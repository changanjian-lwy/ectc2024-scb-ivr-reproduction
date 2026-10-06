# A154 - the turn-off side for loops above 150 pH: voltage and its loss price (RESULTS)
Boundary: b92af53. Records: release records-a154 (5 runs). Outputs: a154_summary.json (a154_analyze.py), a154_predictions.json.

## 0. Verdict
- **2/4 as registered (2, 3 pass; 1 misses one row by 0.2 V on the safe side; 4 fails on 3 rows, explained below).**
- **The turn-off rule holds: x_off = L * di/dt_off <= ~10 V keeps every switch <= 40 V up to 300 pH.** The 40 V side
  was right on 5 / 5 rows: 200 pH x 48 A/ns 36.5 V, 250 x 40 38.3 V, 300 x 32 37.7 V, 300 x 24 35.9 V; the control
  300 x 48 (x_off 14.4 V) 48.4 V (predicted 47.4).
- **Its price is the result: a slow turn-off costs channel loss.** Edge power in the steady window 10.1 / 14.2 / 22.6 /
  31.1 W per 250 W module at 200 / 48, 250 / 40, 300 / 32, 300 / 24 (pH / A/ns), against ~2.7 W at 72 A/ns (A145),
  so +7 to +28 W (3-11 %) before the damper loss. The harness predicted 12.7-38.2 W; the records read 15-22 % lower,
  as in A145. **A loop above ~200 pH costs several percent by drive alone, so the package spec must bound the loop.**
- **Criterion 4's misses are not new defects:**
  - f200_off48 and f300_off24: one "spike" each, the second peak of phase 1's post-step period swing (167 -> 148 ->
    138 -> 170 A; 164 -> 138 -> 140 -> 161 A), at 1002.09 / 1002.16 us, 0.09 / 0.16 us after the oracle's K4 window
    (ramp + 1 us). The slow turn-on (8-12 A/ns) delays it; in f300_off32 the same swing peak (160 A at 1001.86 us)
    falls inside and is K4. Post-step peaks 167-172 A, below the frozen design's ~177 A.
  - f300_off48 (the control): start-up peak 190 A (<= 200 A, registered <= 180 A). D68's start-up ton under-compensates
    above 150 pH: Vo before the handover 1.007 / 0.989 / 0.993 / 1.000 / 0.984 V against 1.010-1.015 V at 75-125 pH
    (A153), start-up peaks 154-190 A. D68's law has no L term (A155).
- Vo stayed inside 1 % through the line step on every row (7-9 mV).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | max V_DS within +-1.5 V of the prediction, 5 rows | FAIL on f300_off24: 35.9 against 37.6 V (-1.7 V, the safe side); others -1.1..+1.0 V |
| 2 | 40 V side as predicted, 5 rows | PASS |
| 3 | steady edge power within +-30 % of the harness | PASS (-15..-22 %) |
| 4 | COMPLETED, post-step <= 190 A, 0 NEW, start-up <= 180 A | FAIL: f200_off48 / f300_off24 one spike each (K4 timing, above); f300_off48 start-up 190 A |

## 2. Limits
- One row (+4.8 V / 1 us) per point, Q 7, 25 °C; the damper loss is not in the records (harness: +0.2-2 W).
- Turn-on 8-12 A/ns sits at A151's "too slow" edge; here Vo stayed inside 1 %, but load steps were not run.
- The 40 V rule uses EPC2067's continuous rating; with a 48 V transient allowance the control row would also pass.
