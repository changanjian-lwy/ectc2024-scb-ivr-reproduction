# A201 - A146's CNN over ten seeds: the spread, A146's criteria on every seed, and an ensemble (BOUNDARY)
Method: ML (deep learning: A146's 1D CNN retrained in PyTorch, a deep ensemble = the mean of the seeds' predictions,
split-conformal intervals; A146's simulator fits rerun for its criterion 4)
Extension ml_torch_port. Written and committed before the training runs and the fits. Seen before writing: A199's
four retraining runs (three float64 seeds and one float32 run) and A146's stored summary; a timing-only smoke run
(2 epochs on 1200 examples; one simulator fit, 14 s). No ensemble was formed from A199's saved networks.
Decision it changes: how A146's CNN numbers are quoted (one seed, or a range); whether A146's verdicts on its own
criteria are properties of the method or of seed 0; whether the estimator of the "CNN" step should be an ensemble.
Cheaper check done first: A199 (the PyTorch network is the numpy network to rounding; three seeds already spread
by 11 / 23 / 12 / 2 % in L / Q_act / di/dt / k).
Budget: ten runs of <= 150 epochs at ~4 s per epoch on MPS in three processes, 20-35 min; 12 x 40 + 40 simulator
fits at ~25 s each on 8 processes, ~30 min; <= 70 min wall, one machine, alone.

## 1. What and why
- **Problem found in A199.** A146 trained one seed and quoted its test medians as the method's numbers. Three
  PyTorch seeds moved Q_act's median between 3.3 and 4.2 %. A146's criterion 4 failed by one capture (33 of 40 on
  Q_act), which a seed can move either way; its measurement requirements (criterion 5) rest on the same one network.
- **Why it is affordable now.** A run takes ~5 min on MPS against 22 min in numpy.
- **Method.** Seeds 0-9, float32 on MPS, A146's data, network and settings (A199's `torch_cnn.fit`). For every
  seed: A146's criteria 1-5 with A146's thresholds. The ensemble is the mean of the ten seeds' predictions, with
  its own conformal widths from the calibration set. Criterion 4 needs A146's simulator fit on the first 40 test
  captures, started from each estimator's prediction (11 x 40 fits) and once from the centre.
- **Control.** A146's stored numpy network goes through the same code first; it must give A146's stored numbers.
- **Not tested.** New data, new network sizes, fresh measurement draws per epoch, other ensemble forms. The
  seed changes the initial weights and the batch order together (one seed for both). MPS runs are not
  bit-reproducible; the predictions are stored in runs/.

## 2. Criteria
1. **Control.** The stored numpy network through this pipeline reproduces A146's stored criterion-4 numbers (share
   inside the interval, mean evaluations from both starts, median costs), its test medians and its four robustness
   rows (median error and cover) within 1e-6 relative.
2. **A146's criteria 1-3 on every seed.** Medians <= 5 / 10 / 15 % and k <= 0.03; covers within 0.87-0.93; medians
   <= half the sine fit's (7.9 / 25.0 / 41.9 %): all three on 10 of 10 seeds.
3. **Ensemble error.** The ten-network mean's test median |err| is <= 0.90 x the mean of the ten single-seed medians
   for L, Q_act and di/dt, and <= 1.00 x for k; its covers are within 0.87-0.93.
4. **A146's criterion 4 for the ensemble.** The fit started from the ensemble lies inside the ensemble's 90 %
   interval on >= 85 % of the 40 captures for each parameter, needs fewer evaluations than from the centre, and its
   median cost is not higher (<= 1.001 x).
5. **A146's criterion 5 pattern.** On >= 9 of 10 seeds and on the ensemble, the three rows that failed in A146
   fail again (noise 0.8 V, probe 0.5 GHz, I0 error 5 %: some cover < 0.75) and the jitter 150 ps row passes.

## 3. Predictions (not criteria)
- Seed spread over ten seeds (range / mean of the medians): L 10-15 %, Q_act 20-30 %, di/dt 10-20 %, k 2-5 %.
- A146's criterion 4 passes on 3 to 7 of the 10 single seeds.
- The ensemble's medians are 0.80-0.90 x the single-seed mean for L, Q_act and di/dt, and 0.95-1.00 x for k.
- In the I0 5 % row, k's cover stays at 0.2-0.3 on every seed (k is read from the ring amplitude per amp).

## 4. Decision rule
- Whatever the outcome, A146's CNN numbers are quoted from now on as the range over the ten seeds; A146's RESULTS
  and the extension README get a dated note that points here.
- Criterion 3 passes: the "CNN" step of A146's procedure is the ten-network ensemble. Fails: the single network
  stays and the ensemble is not adopted.
- Criterion 4 decides only whether the chosen estimator's interval can be used as the fit's starting box; "CNN,
  then fit" stays either way, because only the fit reaches 1 %.
- Criterion 5 passes: A146's measurement requirements stand as written. Fails: they are rewritten with the rows
  and the ranges found here.
- Criterion 1 fails: the pipeline differs from A146's; nothing else is read until it is fixed.
