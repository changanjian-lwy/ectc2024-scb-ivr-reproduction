# A152 - A151's drive spec with a start-up Ton compensation: robustness matrix (RESULTS)
Boundary: 61224f2. Records: release records-a152 (31 runs). Outputs: a152_summary.json (a152_analyze.py).

## 0. Verdict
- **S50 passes every criterion on all 13 rows and on four modules.** S50 = 50 pH, turn-on 36 A/ns, start-up ton 36.5 ns.
  - Max V_DS 37.6 V (L x 1.3 l_p48_1us); falling rows 33.0 V.
  - Start-up peak <= 198 A (L x 0.7, whose ideal reference is 200 A); 155 A at L0.
  - Post-step peaks <= 180.0 A, every row at or below its ideal reference; 0 NEW events, late fires 0-2.
  - Four modules: 37.1 V, start-up 155 A, post-step 172.2 A, late 0.
- **S100 is 4/5 as registered.** S100 = 100 pH, 18 A/ns, ton 37.5 ns. Criterion 3 misses on one row: -8 V / 10 us has 6 late
  fires (phases 2 / 3; ideal 2, S50 0).
  - No consequence found on that row: post-step V_DS 31.0 V, peak 158.1 A (ideal 174.0 A), 0 oracle events. Its ZVS-lost
    turn-ons after the falling ramp are A148's known mechanism (250, ideal 205, S50 226).
  - Every other row passes: V_DS <= 37.1 V, start-up <= 198 A, post-step <= 184.7 A. Four modules 36.5 V, 155 / 176.8 A, late 1.
- **The start-up Ton compensation fixes A151's handover and changes nothing else.**
  - L0 vs A151: start-up peak 224 -> 155 A at S100, 154 -> 155 A at S50.
  - V_DS, post-step peaks and Vo back stay within 0.1 V / 1 A / 0.1 us of A151.
  - Four modules: 230 A at ton 35.5 (250 us smoke run) -> 155 A.
  - Calibrated at L0, it still holds at the L corners: L x 1.3 reaches Vo 0.969 V at the handover (153 A, ideal 145 A);
    L x 0.7 1.118 V (198 A, ideal 200 A).
- **300 pH fails at every turn-on rate: the turn-off sets it.**
  - The steady window is 48.7 / 48.8 / 48.9 V at 72 / 18 / 9 A/ns; whole run 63.3 / 59.9 / 57.8 V.
  - Steady window vs loop: 28.2 / 27.7 / 31.1 / 48.8 V at 50 / 100 / 150 / 300 pH. The 72 A/ns turn-off ring rises steeply
    above 150 pH, and a slower turn-on cannot touch it.
  - Above ~150 pH the turn-off di/dt has to drop as well, which costs loss (already 1 % at ~70 pH, A145).
- **Package spec from A152:**
  - Loop <= 50 pH (loss allows ~70 pH for 1 %).
  - Turn-on drive <= 36 A/ns, separate from the turn-off; turn-off 72 A/ns.
  - Start-up ton_ns = 35.5 + 36 A / turn-on di/dt (36.5 ns).
  - 100 pH at 18 A/ns with 37.5 ns works, with the late-fire note. 300 pH needs a slower turn-off.

## 1. Criteria
| # | criterion | S50 | S100 |
|---|---|---|---|
| 1 | V_DS <= 40 V, 13 rows | PASS, 37.6 V | PASS, 37.1 V |
| 2 | start-up peak <= max(200 A, ref + 5) | PASS, 198 A (L x 0.7) | PASS, 198 A (L x 0.7) |
| 3 | post-step peak, 0 NEW, late <= ref + 2 | PASS (<= 180.0 A, late <= 2) | FAIL: l_m80_10us late 6 (ref 2) |
| 4 | Vo extreme / back | PASS | PASS |
| 5 | four modules, criteria 1-3 | PASS: 37.1 V, 155 / 172.2 A | PASS: 36.5 V, 155 / 176.8 A |
| 6 | 300 pH <= 40 V at 18 or 9 A/ns | FAIL: 59.9 / 57.8 V (steady 48.8 / 48.9 V) | |

Predictions:
- Right:
  - C1 <= 38 V; falling rows <= 34 V.
  - C2 at L x 0.7 195-205 A (198 A).
  - C5 pass; C6 fails at 40 V.
- Wrong:
  - S100's late fires were not predicted.
  - 300 pH at 18 / 9 A/ns was predicted at about 41 V. It was 57.8-59.9 V: the extrapolation from <= 150 pH missed the
    rise of the turn-off ring.

Vo notes:
- The slew rows show no oscillation: post-step peaks 171.7-174.5 A (A150's edge law gave 203-275 A on the same ramps).
- S50 L x 1.3 l_p48_1us stays 42.1 us outside 1 % at 10.3 mV. Criterion 4 does not count back-time below 11 mV. The ideal
  design's slow ramps do the same: 39.6-43.1 us at 11.0-13.7 mV.

## 2. Limits
- The start-up Ton was calibrated at L0 / 100 pH and L0 / 50 pH on 160 us runs. 39.5 ns at 9 A/ns follows the rule and was
  not calibrated. Not tested: Cs corners, L corners combined with other loops.
- Late fires are a count with no timestamps. Their consequence was checked through V_DS, peaks and the oracles only.
- The plant's edge is a linear current ramp with no gate model (A151). 300 pH uses Q 7 damping (2.01 Ohm).
