# A139 - A138's boundary map with the noise floor measured and the budget split per direction (BOUNDARY)
Extension ml_design_assist. Written and committed before any A139 run, after A138's RESULTS (157a33f), whose
criterion 2 failed. Looked at beforehand: A138's state (406 points), a dry run of this loop with fake cosim.
Decision it changes: as A138's - the adopted design's bus-slew spec under L x 0.7-1.3 / Cs x 0.7-1.3 - now with bands
that can be trusted, or the conclusion that this GP cannot give them.
Cheaper check done first: A138's data (rising residual sd 5.7 A with weak input ties: scatter, not structure).
Budget: <= 260 single-module runs (~4.5 min per 10 at 10 jobs; ~2 h). Raw records local (.gitignore), as A138.

## 1. What and why
- A138 failed for two reasons it identified (RESULTS 0): the rising GP's fitted noise collapsed to 0.005 A on 34 points,
  and one straddle over both directions then gave falling steps 302 of 310 runs.
- Fix 1, noise measured: four points near the boundary - rising (L, Cs, dv, slew) (1.0, 1.0, +8, 3.0 us) and
  (0.7, 0.7, +6.4, 1.0 us), falling (1.0, 1.0, -8, 6.7 us) and (1.3, 1.0, -6.4, 8.8 us) - each run with the step at six
  positions 85 ns apart (one switching period); the pooled sd per direction is the GP's noise lower bound
  (ml_gp.GP noise_min; default 0 leaves every earlier fit bit-identical, unit tests pass).
- Fix 2, budget per direction: each batch 6 rising + 4 falling, each by its own straddle (kriging believer).
- Training data: all A138 points (incl. its test and verification runs) + the scatter runs + new active points.
  Fresh held-out test: 20 uniform points per direction (seed 139), never trained on.
- Then A138's spec table, 20 verification cells at their slews, and up to 10 cells without a safe slew run at 20 us.
- Design, inputs, prior grid, response, table definition: A138's, unchanged.

## 2. Criteria
1. Validity: every run completes, timed before its step, sources unmodified.
2. Fresh test (20 per direction, final GP): 90 % intervals cover >= 80 %; classification >= 90 % and >= D63's.
3. Verification: >= 18 of 20 cells <= 200 A at their table slew, none above 205 A.
Reported: the measured scatter; the test numbers of the GP trained on A138 + scatter runs only; the 20 us runs of
cells without a safe slew (how many exceed 200 A).

## 3. Predictions
- Scatter sd 2-7 A (A129's 2-7 A for moving a step by under a period), rising and falling alike.
- With the floor the rising GP's coverage >= 0.8 and its MAE near D63's (~4-5 A): the rising residual is scatter.
- Falling: classification >= 0.9, coverage 0.8-0.9.
- The table keeps A138's shape: falling tighter than A130 at L x 0.7 and L x 1.3 / Cs >= 1.0; rising +8 V without a safe
  slew at L x 0.7; most cells without a safe slew exceed 200 A at 20 us.

## 4. Decision rule
- 1-3 pass: the table is the adopted design's bus-slew spec under L / Cs tolerance; cells tighter than A130's are
  named in CURRENT_STATUS / scorecard T18; A138 is superseded.
- 2 fails again: the GP route is closed for this map; the spec is stated only from verified cosim cells (A138 + A139).
- 3 fails: failed cells tightened to the next slower verified slew or left open.
