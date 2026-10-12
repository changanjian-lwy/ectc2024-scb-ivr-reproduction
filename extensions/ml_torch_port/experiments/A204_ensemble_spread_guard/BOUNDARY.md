# A204 - the ten networks' disagreement as a guard and as an interval scale (BOUNDARY)
Method: ML (deep ensemble: the spread of A201's ten networks; split-conformal intervals, fixed and normalised by the
spread). An analysis of A201's stored predictions; no training and no new simulation.
Extension ml_torch_port. Written and committed before the analysis ran. Seen before writing: A201's results (the
ensemble's cover in the robustness rows: L 0.33 and k 0.08 at I0 +5 %, L 0.71 at 0.8 V noise) and a smoke run that
loads the records and prints their shapes only.
Decision it changes: whether A146's measurement requirements on noise and probe bandwidth can be checked from the
capture itself (a guard built from the networks' disagreement) or must be guaranteed from outside, and which
interval the ensemble reports.
Cheaper check done first: none is cheaper; the records exist.
Budget: seconds.

## 1. What and why
- **Problem found in A201.** Outside the training conditions the ten-network mean is more overconfident than one
  network: its intervals are half as wide and the shift caused by the wrong condition is unchanged.
- **Idea.** Ten networks trained on the same data agree where the data constrain them and may disagree where an
  input is unlike the training captures. Their spread costs nothing extra.
- **Quantities.** s(x): the standard deviation of the ten predictions of a capture, per parameter. Guard: g(x) =
  the largest s / (calibration median of s) over the four parameters; a capture is flagged when g exceeds the
  calibration set's 95th percentile. Scaled interval: mean +- q (s + s0), with s0 the calibration median of s and q
  the split-conformal rank of |mean - y| / (s + s0) on the calibration set.
- **Data.** A201's ten prediction files: calibration set (2000 captures), test set (4000, inside the training
  conditions), and A146's four robustness rows (1000 each: noise 0.8 V, probe 0.5 GHz, jitter 150 ps, I0 read 5 %
  high).
- **Not tested.** Other guards (input-space distances, per-parameter thresholds), other ensemble sizes, retraining
  on wider conditions, real captures.

## 2. Criteria
1. **Scaled intervals inside the training conditions.** Test cover within 0.87-0.93 for each of the four parameters.
2. **False flags.** The guard flags 3-7 % of the test captures.
3. **The guard sees out-of-range captures.** It flags >= 50 % of the captures in the noise 0.8 V row and in the
   probe 0.5 GHz row.
4. **Scaled intervals out of range.** In those two rows the scaled intervals cover >= 0.75 on every parameter.

## 3. Predictions (not criteria)
- Test set: scaled cover 0.89-0.91, 4-6 % flagged, median scaled width 0.8-1.0 x the fixed width; the spread ranks
  the error weakly (rank correlation 0.2-0.4).
- Noise 0.8 V: spread 1.5-2.5 x, 40-80 % flagged, scaled cover 0.75-0.85.
- Probe 0.5 GHz: spread 1.2-2 x, 30-70 % flagged; di/dt's cover stays below 0.75 (the networks agree on a shifted
  value), so criterion 4 fails on this row.
- I0 read 5 % high: about 5 % flagged (3-8 %) and k's cover stays below 0.3. The capture and the sensed current are
  each inside their training ranges, so no property of the input can reveal the error.
- Jitter 150 ps: 5-20 % flagged.

## 4. Decision rule
- Criteria 1 and 2 are preconditions: if either fails, the spread is not calibrated inside the training
  conditions and neither the guard nor the scaled interval is used.
- Criterion 3 passes: the guard is adopted - a capture on which the ten networks disagree beyond the threshold is
  not reported - and A146's noise and probe requirements can be checked from the capture. Fails: they stay
  external requirements.
- Criterion 4 passes: the scaled interval replaces the fixed one for the ensemble. Fails: the fixed interval stays
  and no interval is claimed outside the training conditions.
- The I0 row is in no criterion: whatever it shows, the current-sense accuracy stays an external requirement.
