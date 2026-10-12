# A201 - A146's CNN over ten seeds: the spread, A146's criteria on every seed, and an ensemble (RESULTS)
Boundary: a10dc5e. Records: runs/s<seed>.json and runs/pred_s<seed>.npz (a201_train.py), a201_fits.json
(a201_fits.py, 480 simulator fits), a201_summary.json (a201_analyze.py). torch 2.14.1, float32 on MPS.
The ten runs finished under three commits (a10dc5e, 6b8e719, 05fce69) because A202 was committed meanwhile; they
differ only in A202's files and torch_mlp.py (`git diff a10dc5e 05fce69` is empty on torch_cnn.py, A199's and
A201's folders).

## 0. Verdict
- **5 of 5 criteria pass.** A146's method holds on every seed; its single-seed numbers were one draw from a wide
  spread; averaging ten networks removes most of that spread.
- **The control is exact.** A146's stored numpy network through this pipeline reproduces A146's stored fit and
  robustness numbers with difference 0. Seed 0 here repeats A199's float32 run to the stored digits.
- **Spread over ten seeds (test medians).** L 1.9-2.8 %, Q_act 3.2-4.4 %, di/dt 5.3-6.8 %, k 0.0113-0.0122; means
  2.2 / 3.6 / 5.8 % / 0.0118. Range over mean 42 / 35 / 27 / 8 %. Covers 0.884-0.914. These ranges replace A146's
  2.2 / 4.0 / 5.9 % / 0.012.
- **A146's criteria by seed.** Criteria 1-3 pass on 10 of 10. Criterion 4, which A146 failed by one capture,
  passes on 7 of 10 (seed 0 misses on L, seeds 1 and 4 on di/dt, each by one or two captures of 40): its verdict
  was a property of the seed. Criterion 5's pattern (noise 0.8 V, probe 0.5 GHz and I0 +5 % fail, jitter 150 ps
  passes) holds on 9 of 10; on seed 2 the jitter row fails too (di/dt cover 0.735).
- **The ten-network mean.** Medians 1.26 / 1.94 / 4.13 % / 0.0102, that is 0.58 / 0.54 / 0.71 / 0.87 of the
  single-seed mean; covers 0.904 / 0.898 / 0.911 / 0.906 with intervals about half as wide (L 3.4 against 6.4 %).
  A146's criterion 4 passes for it: the fit lies inside its interval on 92.5 / 95 / 90 / 92.5 % of 40 captures,
  with 23.9 evaluations against 31.3 from the centre.
- **Why averaging helps this much.** The error against the number of networks K follows a + b / K: predicted
  1.74 / 1.56 / 1.40 % for L at K = 2 / 3 / 5, found 1.74 / 1.56 / 1.39 %. The seed-dependent part b is 74 / 79 /
  55 / 27 % of one network's squared error (L / Q_act / di/dt / k). The limit for many networks is 1.11 / 1.66 /
  3.9 % / 0.0100; ten networks are close to it.
- **Against the simulator fit (1.1 / 0.53 / 1.65 % / 0.0102).** The ensemble equals it on k and nearly on L; it
  stays 3.7x worse on Q_act and 2.5x on di/dt. "CNN, then fit" stands.
- **A new caution.** Outside the training conditions the ensemble is more overconfident than one network: with
  I0 read 5 % high its cover is 0.33 on L and 0.08 on k (single seeds: k 0.17-0.28); at 0.8 V noise 0.71 on L.
  Averaging removes random error, not the shift a wrong measurement condition causes, and its intervals are
  narrower. A146's measurement requirements matter more for the ensemble, not less.
- **Decision (BOUNDARY Section 4).** A146's CNN numbers are quoted as the ranges above. The "CNN" step is the
  ten-network ensemble; its interval may serve as the fit's starting box. A146's measurement requirements stand.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | control within 1e-6 relative | PASS: 0 |
| 2 | A146's criteria 1-3 on 10 of 10 seeds | PASS: 10 / 10 / 10 |
| 3 | ensemble medians <= 0.90 x the seed mean (L, Q_act, di/dt), <= 1.00 x (k); covers 0.87-0.93 | PASS: 0.58 / 0.54 / 0.71 / 0.87; 0.898-0.911 |
| 4 | A146's criterion 4 for the ensemble | PASS: inside 0.925 / 0.950 / 0.900 / 0.925; 23.9 against 31.3 evaluations; cost 16.7789 against 16.7790 |
| 5 | A146's criterion 5 pattern on >= 9 of 10 seeds and on the ensemble | PASS: 9 of 10; ensemble yes |

| seed | epochs | median \|err\| L / Q_act / di/dt / k | fit inside the interval | A146 c4 |
|---|---|---|---|---|
| 0 | 87 | 0.0220 / 0.0335 / 0.0589 / 0.0120 | 0.800 / 0.975 / 0.875 / 0.900 | fail |
| 1 | 79 | 0.0283 / 0.0367 / 0.0553 / 0.0121 | 0.950 / 0.875 / 0.825 / 0.925 | fail |
| 2 | 61 | 0.0237 / 0.0350 / 0.0684 / 0.0114 | 0.875 / 0.875 / 0.900 / 0.950 | pass |
| 3 | 87 | 0.0190 / 0.0415 / 0.0589 / 0.0121 | 0.925 / 0.850 / 0.875 / 0.925 | pass |
| 4 | 66 | 0.0236 / 0.0402 / 0.0611 / 0.0122 | 0.925 / 0.975 / 0.800 / 0.925 | fail |
| 5 | 97 | 0.0200 / 0.0318 / 0.0529 / 0.0117 | 0.925 / 0.950 / 0.900 / 0.925 | pass |
| 6 | 90 | 0.0202 / 0.0324 / 0.0572 / 0.0119 | 0.950 / 0.850 / 0.900 / 0.975 | pass |
| 7 | 92 | 0.0220 / 0.0442 / 0.0555 / 0.0116 | 0.875 / 0.900 / 0.875 / 0.900 | pass |
| 8 | 91 | 0.0208 / 0.0320 / 0.0579 / 0.0114 | 0.900 / 0.925 / 0.875 / 0.925 | pass |
| 9 | 87 | 0.0192 / 0.0319 / 0.0560 / 0.0113 | 0.925 / 0.975 / 0.900 / 0.950 | pass |
| mean of ten | - | 0.0126 / 0.0194 / 0.0413 / 0.0102 | 0.925 / 0.950 / 0.900 / 0.925 | pass |

Error against the number of networks averaged (mean over the subsets, at most 120 per size): 1: 2.19 / 3.59 / 5.82 %;
2: 1.74 / 2.82 / 4.98 %; 3: 1.56 / 2.49 / 4.65 %; 5: 1.39 / 2.15 / 4.39 %; 10: 1.26 / 1.94 / 4.13 %.

Predictions:
- Spread 10-15 / 20-30 / 10-20 / 2-5 %: wrong, larger on all four (42 / 35 / 27 / 8 %).
- A146's criterion 4 passes on 3 to 7 seeds: held (7).
- Ensemble 0.80-0.90 x for L, Q_act, di/dt and 0.95-1.00 x for k: wrong, the gain is larger (0.58 / 0.54 / 0.71 / 0.87).
- k's cover at I0 +5 % stays 0.2-0.3 on every seed: 6 of 10 (the others 0.17-0.19).

## 2. Limits
- **One training set.** The seed changes the initial weights and the batch order together; the data, their
  measurement draws and the calibration set are the same for all. The a + b / K reading uses medians, not means.
- **Cost.** Ten trainings (382 s each on a shared GPU) and ten forward passes per capture (~1 ms) against one;
  480 fits took about 55 min on 8 processes, longer than the 30 min budgeted.
- **Scope.** A146's simulated captures and its measurement model; no hardware. Criterion 4 uses 40 captures, so
  one capture is 2.5 points of its share.
