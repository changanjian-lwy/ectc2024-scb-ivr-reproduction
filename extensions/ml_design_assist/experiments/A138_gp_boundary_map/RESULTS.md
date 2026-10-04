# A138 - GP level-set active learning of the 200 A line-step boundary under L / Cs tolerance (RESULTS)
Boundary: eaced63. Records: a138_state.json (all 406 points: inputs, D63 prior, cosim response, flags), a138_summary.json,
cosim/cfg_*.json (400 runs; raw records local, BOUNDARY "Records"). Log: 00:55-03:58, 400 runs, 10 jobs.

## 0. Verdict
- **Criterion 2 fails: the GP's bands are not trusted** (decision rule); the 20 verification runs stand alone and all
  pass (<= 198.7 A at their table slews).
- **Why it failed (method, not data):** with 34 rising training points, maximum likelihood drove the rising GP's noise
  to 0.005 A and its slew length scale to 0.12-0.14: it interpolated the step-position scatter (rising residual
  cosim - D63: mean -0.9 A, sd 5.7 A, weakly tied to any input). Test coverage 0.33, MAE 4.6 A (D63 alone 4.0 A).
  The straddle compared both directions on one scale, so the over-confident rising GP lost every contest: active
  learning spent 302 runs on falling steps and 8 on rising ones.
- **Falling steps are where D63 is wrong:** residual mean +7.8 A, sd 19.6 A, -48 to +58 A, correlated with L (+0.61);
  the falling GP (noise 8.4 A) improves on D63 (test MAE 9.0 vs 11.6 A, classification 0.93 vs 0.80; coverage 0.73).
- **Cosim findings that stand without the GP:** at L x 0.70-0.83, rising 7-8 V steps exceed 200 A at every tested slew
  (1.2-18.9 us: 194.6-214.7 A, 4 of 6 above 200 A) - D63's "slower is worse" is not shown, but no slew makes them safe.
  Nominal +8 V at 3.0 us: 198.7 A (A130's spec asks 10 us).
- Table cells tighter than A130's spec (not trusted, criterion 2): falling 4.8 V at L x 0.7 (3.9-5.1 us vs 1 us),
  -8 V at L x 1.3, Cs x 1.0-1.3 (11.6 us vs 6 us). A139 repeats the map with the noise floor measured and the budget
  split per direction.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | validity | pass: 400/400 completed, timed before the step, sources unmodified |
| 2 | test cover90 >= 0.8, accuracy >= 0.9 and >= D63 | **fail**: cover90 rising 0.33, falling 0.73; accuracy 1.00 / 0.93 (D63 0.93 / 0.80) |
| 3 | verification 18/20 <= 200 A, none > 205 A | pass: 20/20, 170.8-198.7 A |
Reported: the initial-design GP had cover90 0.27 / 0.27, accuracy 0.93 / 0.80 - active learning raised falling
accuracy and coverage, not rising. Predictions: rising 4.8 V always safe - not in the GP table (L x 0.7, Cs x 1.3);
+8 V never safe at L x 0.7 - consistent with cosim; nominal +8 V 2.3 us (D63) - cosim 198.7 A at 3.0 us; falling -8 V
2.3-8.8 us - the table asks up to 11.6 us; cosim above D63 on rising rows - no (mean -0.9 A), on falling - yes (+7.8 A).

## 2. Limits
- 15 test points per direction: coverage is resolved to 1/15.
- Coss, load steps, four modules and start-up not covered (BOUNDARY 1).
