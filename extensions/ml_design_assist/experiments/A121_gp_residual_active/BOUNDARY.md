# A121 - a Gaussian process on the residual co-simulation − D63, and active learning (BOUNDARY)

Extension `ml_design_assist`. **Written, and its A118 predictions
registered, before any A118 result was read.** The A118 runs were still
in progress, with no output file.

## 1. What and why

**What:** a Gaussian process (`src/scb_ivr/extensions/ml_gp.py`: ARD
squared-exponential kernel, marginal-likelihood fit, closed-form
leave-one-out) on the residual "co-simulation peak − D63 peak" after a
step.

**Why:**
- D63 is ~10% off.
- The co-simulation costs ~8 minutes per run.
- A model of the residual with its uncertainty says where D63 is
  trustworthy, and which runs would teach the most (active learning).

**Data:**
- the 25 non-runaway 1 MHz transients of A115-A117 (A120's set);
- inputs: pct, ln Cs, fc, ln slew (standardised); comparator, timed
  edge, floor, load (binary); di / 62.5; dv / 4.8.

**A registered prior:** the floor is absent from the training data. Its
length scale is fixed at 1, so a floor row borrows from the timed rows
(it is the timed design on rising steps) with added uncertainty.

## 2. Fitted (training only, before A118)

- **Residual:** mean +0.6 A, D63's MAE 9.2 A.
- **Leave-one-out:** D63 + GP MAE **6.8 A (0.74 of D63's)**; coverage at
  ±1.645 sd **88%**.
- **Hyperparameters:** s 15.8 A, noise 0.6 A.

## 3. Registered prospective predictions: A118's 13 step rows

`a121_predictions_a118.json`. Each row is D63 → D63 + GP ± sd (A).

| row | D63 | D63 + GP |
|---|---|---|
| f6_s_m62 | 140.2 | 141.3 ± 12.6 |
| f6_s_p62 | 172.8 | 173.6 ± 12.6 |
| f6_l_m48_1us | 203.2 | 214.3 ± 13.5 |
| f6_l_p48_1us | 208.4 | 200.8 ± 12.6 |
| f6_l_m48_5us | 173.6 | 176.8 ± 13.9 |
| f6_l_p48_5us | 191.1 | 204.1 ± 14.3 |
| f6_l_m48_20us | 143.0 | 151.3 ± 12.6 |
| f6_l_p48_20us | 168.5 | 184.7 ± 14.2 |
| f15_s_m62 | 140.2 | 141.3 ± 12.6 |
| f15_l_m48_5us | 186.6 | 189.9 ± 14.0 |
| f15_l_p48_5us | 203.7 | 216.8 ± 14.3 |
| t6_s_m62 | 140.2 | 141.6 ± 1.5 |
| t6_l_m48_5us | 185.6 | 190.5 ± 9.7 |

## 4. Criteria

1. **Leave-one-out:** D63 + GP MAE ≤ 0.8 × D63's; coverage ≥ 75%. Both
   are met in Section 2, since they are fitted quantities.
2. **Prospective, on A118's non-runaway step rows:**
   - D63 + GP MAE ≤ D63's MAE (not worse);
   - coverage at ±1.645 sd ≥ 75%;
   - the floor rows' median sd above the training's leave-one-out
     median sd. The GP should know that the floor is new.
3. **Active learning (output, not a criterion):** after A118, refit on
   all and list the 8 next co-simulation runs with the largest predictive
   sd in the floor region (pct 8-12%, Cs 4-10 µF, floor 1-4 A, ±62.5 A,
   ±4.8 V over 1-20 µs).
