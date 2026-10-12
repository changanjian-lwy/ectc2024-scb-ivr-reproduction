# A204 - the ten networks' disagreement as a guard and as an interval scale (RESULTS)
Boundary: 6adebc2. Run from 6adebc2. Record: a204_summary.json (a204_spread.py), from A201's runs/pred_s*.npz.
Parameters in the order L / Q_act / di/dt / k.

## 0. Verdict
- **2 of 4 criteria pass: the spread is calibrated inside the training conditions and does not see outside them.**
  The guard and the scaled interval are not adopted.
- **Inside the training conditions (test set).** The scaled intervals cover 0.903 / 0.898 / 0.915 / 0.913, as the
  fixed ones do, at 0.96 / 0.91 / 0.80 / 0.99 of their median width. The guard flags 4.7 %. The spread ranks the
  error with a rank correlation of 0.21 / 0.33 / 0.52 / 0.15: useful for di/dt, weak for k.
- **Noise 0.8 V.** The spread grows only 1.3-1.5 x; 35 % of the captures are flagged (50 % needed). Scaled cover
  0.78 / 0.67 / 0.89 / 0.81 against 0.70 / 0.60 / 0.85 / 0.72 fixed: better, Q_act still short.
- **Probe 0.5 GHz.** Spread 1.1-1.3 x; 10 % flagged. di/dt's cover is 0.54 scaled against 0.58 fixed.
- **I0 read 5 % high.** 6 % flagged, the same as inside the training conditions; k's cover 0.12 scaled against 0.08
  fixed. As registered: the capture and the sensed current are each in range, so the input cannot reveal the error.
- **Why.** Ten networks trained on the same captures share their bias. A wrong measurement condition shifts all
  ten predictions together, so the mean is wrong while the spread stays small. Disagreement measures the training's
  randomness, not the distance from the training conditions.
- **Decision (BOUNDARY Section 4).** A146's requirements on noise, probe bandwidth and current-sense accuracy stay
  external requirements. The ensemble keeps A201's fixed intervals, and no interval is claimed outside the training
  conditions. A201's caution stands without a remedy from the records; training on wider conditions was not run.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | scaled intervals, test cover within 0.87-0.93 | PASS: 0.903 / 0.898 / 0.915 / 0.913 |
| 2 | guard flags 3-7 % of the test captures | PASS: 4.7 % |
| 3 | guard flags >= 50 % in the noise 0.8 V and probe 0.5 GHz rows | FAIL: 35 % and 10 % |
| 4 | scaled cover >= 0.75 on every parameter in those rows | FAIL: Q_act 0.67 (noise); di/dt 0.54, k 0.69 (probe) |

| row | flagged | spread / calibration median | cover, fixed | cover, scaled | cover, fixed, unflagged only |
|---|---|---|---|---|---|
| test | 4.7 % | - | 0.90 / 0.90 / 0.91 / 0.91 | 0.90 / 0.90 / 0.92 / 0.91 | - |
| noise 0.8 V | 35 % | 1.3 / 1.5 / 1.4 / 1.4 | 0.70 / 0.60 / 0.85 / 0.72 | 0.78 / 0.67 / 0.89 / 0.81 | 0.81 / 0.73 / 0.88 / 0.80 |
| probe 0.5 GHz | 10 % | 1.2 / 1.2 / 1.1 / 1.3 | 0.75 / 0.76 / 0.58 / 0.62 | 0.76 / 0.77 / 0.54 / 0.69 | 0.77 / 0.80 / 0.56 / 0.64 |
| jitter 150 ps | 10 % | 1.1 / 1.0 / 1.2 / 1.1 | 0.78 / 0.88 / 0.78 / 0.82 | 0.80 / 0.88 / 0.80 / 0.83 | 0.80 / 0.90 / 0.79 / 0.83 |
| I0 read 5 % high | 6 % | 1.0 / 1.0 / 1.0 / 1.1 | 0.33 / 0.90 / 0.92 / 0.08 | 0.32 / 0.90 / 0.91 / 0.12 | 0.32 / 0.92 / 0.92 / 0.07 |

Predictions:
- Test set (cover 0.89-0.91, 4-6 % flagged, width 0.8-1.0 x, rank correlation 0.2-0.4): held except two covers at
  0.913 and 0.915 and the rank correlation's range (0.15 to 0.52).
- Noise 0.8 V (spread 1.5-2.5 x, 40-80 % flagged, scaled cover 0.75-0.85): too optimistic on all three (1.3-1.5 x,
  35 %, Q_act at 0.67).
- Probe 0.5 GHz (30-70 % flagged; di/dt below 0.75): the flag share was wrong (10 %); di/dt held (0.54).
- I0 read 5 % high (about 5 % flagged, k below 0.3) and jitter (5-20 % flagged): held (6 %, 0.12; 10 %).

## 2. Limits
- **One guard.** The largest relative spread over the four parameters, one threshold. Input-space guards (the
  waveform's noise level or rise time measured directly) were not tried and would be the natural next thing: both
  failing rows change the capture in a way one can measure without a network.
- **Ten networks from one training set.** Networks trained on different data draws might disagree more; not tested.
- **Simulated rows.** Each row moves one condition to one value; no real capture.
