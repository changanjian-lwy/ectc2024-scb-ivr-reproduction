# A147 - a learned anomaly detector against the hand-written oracles (BOUNDARY)
Method: ML (deep learning: 1D convolutional autoencoder on per-period features; baselines: per-channel z-score, PCA;
reference: the A142 oracles and the run-level verdicts)
Extension ml_design_assist. Written and committed before training. Seen before writing: the feature / label counts
(a147_features.py: 1522 records, 2.33 M periods, 718 records with NEW / FF oracle events, 39 with > 100 late fires,
630 above 200 A) and plumbing smokes (20 training records, 2 epochs; detection numbers not read).
Decision it changes: whether this project's verification (A142 oracles + reading each run) can be called complete
for the 2.5 MHz single-module family, or missed defects must be reopened; and whether a learned monitor is worth
keeping as a check on future runs. Cheaper check first: the z-score detector (no model) is one of the arms.
Budget: features 18 s; training <= 60 epochs (~15 min); scoring 1522 records (~5 min); inspection by hand.

## 1. What and why
- Problem: every failure mode so far (A133 floor rails, A134 lock, A140 duplicate turn-on, A142 comparator-phase
  oscillation, A144 ring lock) was found by a person reading runs, and coded into an oracle afterwards. An oracle only
  finds what it was written for.
- Method: features per phase-1 period (32 channels: per phase turn-on count, peak, valley, turn-on V_DS, Ton,
  non-predictive turn-ons; Vo, Vin, ladder deviations, Ton code, period, mode P), windows of 64 periods (~32 us). An
  autoencoder trained on clean records only learns what normal operation looks like, transients included; a window it
  cannot reconstruct is unusual, whatever the reason. Why convolution: oscillations, locks and post-step ringing are
  temporal patterns of in-range values; a per-value threshold cannot see them, a filter over time can.
- Arms: AE (conv 32-16-8, bottleneck 8 x 16 = 128); PCA with 128 components (linear, same bottleneck); zmax (the
  median as the model). Score: max |residual| in sd units over the window (a mean would dilute one duplicate in 2048
  values); AE mean square kept as a secondary score. Threshold: 99th percentile of validation windows.
- Data: clean = no NEW / FF event, late <= 5, peak <= 200 A. Clean records of A139, A142, A143, A145 are held out
  whole for testing (A145: finite edges, a physics change the AE never saw); the other clean records train / validate.
- Not tested: four-module records, other designs (t0 200 / 1000 ns), start-up before mode P.

## 2. Criteria (AE, primary score)
1. False alarms: <= 2 % of the clean test windows.
2. AUROC, oracle-defect windows (NEW / FF event inside) against clean test windows: >= 0.95 and >= the better
   baseline + 0.02.
3. Run level: >= 1 flagged window in >= 90 % of storm, runaway and regulation runs and >= 80 % of defect runs.
4. The 20 highest unexplained flags (no oracle event in the window, run not storm / runaway / regulation; one per
   record) are each classified with evidence: (a) defect the oracles missed, (b) legitimate rare operation,
   (c) detector artefact; (c) <= 10 of 20.

## 3. Predictions (not criteria)
- zmax catches every count anomaly (a duplicate saturates the clip) but not spikes or oscillations inside the clean
  transient range; PCA between. AUROC: AE 0.92, PCA 0.88, zmax 0.85 -> criterion 2 likely fails on the 0.95 bar.
- False alarms 2-3 % (A142's random stimuli reach steps the training runs did not) -> criterion 1 marginal; A145's
  edges (peaks -1.5 A, ~0.2 sd) not flagged.
- Run level: storm and runaway 100 %, regulation ~90 %, defect runs ~75 %.
- Unexplained flags: mostly (b) (large line / load steps, L corners), a few (c), 0-2 (a).

## 4. Decision rule
- Any (a): reopen it as a defect (its own experiment); the verification claim is narrowed until it is closed.
- No (a) and 1-3 pass: the oracles are complete for this family as far as an independent detector can tell; the AE
  becomes an optional check (scripts) for future runs.
- 2 fails but 4 is clean: the AE adds no detection power over the oracles; report it as a negative result (the
  oracles plus zmax suffice) and do not keep it.
