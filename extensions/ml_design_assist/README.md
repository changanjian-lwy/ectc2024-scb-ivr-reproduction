# ml_design_assist - machine learning that assists the physics models

**An extension, not the reproduction.** Machine learning, deep learning
and reinforcement learning, used where they help. Asked for on
2026-10-03.

## Rules

1. **The physics stays the authority.**
   - D57-D63 and the co-simulation decide.
   - A learned model is a fast or uncertainty-aware stand-in for them,
     checked against them.
2. **numpy and scipy only.**
   - No new dependencies, and CI stays light.
   - Every step (forward and backward pass, Adam, the Gaussian process,
     the policy gradient) is written out to be read.
3. **Every experiment registers its targets before training,** as the
   main line does (BOUNDARY → runs → RESULTS).
4. **Reinforcement learning can exploit model error.**
   - D63's known blind spot is the timed 60 kHz design on fast line
     steps.
   - A learned policy counts only once it is distilled into a rule the
     RTL can implement and checked in the co-simulation.

## Experiments

Numbers are shared with the main line; A118 and A119 are reserved there.

| # | method | what | status |
|---|---|---|---|
| [A120](experiments/A120_d63_surrogate_mlp/RESULTS.md) | deep learning: a multilayer perceptron | a surrogate of D63 (design + disturbance → peak, Vo extreme, phase 1's crossing, recovery), for fast design-space queries | **done:** all targets met (test peak MAE 2.0 A, 11 000× faster, co-simulation error 8.7 against D63's 9.2 A); the search finds the floor rule with Cs ≲ 8 µF feasible once the bus slew is ≥ 5 µs |
| [A121](experiments/A121_gp_residual_active/RESULTS.md) | Gaussian process | the residual co-simulation − D63 with its uncertainty; choosing the next co-simulation runs (active learning) | **done:** all criteria met; registered before A118 ran, it predicted A118 with MAE 9.7 A (D63 10.5) and 92% coverage. With 37 points, active learning reduces to space-filling |
| [A122](experiments/A122_rl_turn_off_policy/RESULTS.md) | reinforcement learning (policy gradient) | phase 1's turn-off decided per period in the D63 environment, against the hand rules (comparator, timed, floor) | **done:** REINFORCE rediscovers the floor (return −30.5 = always-floor; timed −54.5, comparator −152.8) |
| [A125](experiments/A125_conformal_registration/RESULTS.md) | conformal prediction (split, signed, Mondrian, adaptive) | distribution-free bands around D63's registered predictions, tested in run order on 43 registered rows | **done:** peak coverage 74% (S) / 82% (signed) at nominal 80%; the hand ±10% was a 76% band; finds D63's second weak domain (−8 V / 10 µs at 1 MHz, +18-22%). Bands are registered from the next experiment on |
| [A126](experiments/A126_ppo_line_feedforward/RESULTS.md) | reinforcement learning (PPO) | line-step feed-forward learned in the D63 environment | **invalid:** the policies gamed the reward (steady state shifted) |
| [A127](experiments/A127_ppo_anchored_feedforward/RESULTS.md) | PPO, anchored pure feed-forward (asymmetric critic) | the same task with the steady state anchored; distilled to a 6-parameter falling-step rule | **done:** 3/3 pass steady and long checks |
| [A128](experiments/A128_cosim_vin_feedforward/RESULTS.md) | co-simulation of the distilled rule (RTL `scb_vff.v`, cfg "vff") | 2.5 MHz, the A124 rows | **done:** every row <= 200 A (worst 188 A); cost: -8 V/10 us peak 168.5 -> 188.2 A, Vo -28 -> +38 mV |
| [A129](experiments/A129_cosim_vff_slope_gate/RESULTS.md) | slope gate on the falling term (cfg vff "gth") + the 2.5 MHz standard matrix | 2.5 MHz, the A124 rows, matrix m/j/±25 A | **done:** −8 V/10 us back to 170.9 A / 28.6 mV, −4.8 V/1 us 173.6 A, worst row 181.5 A; matrix passes in both arms; adopted as the line-step closure for steps ≤ 4.8 V at ≥ 1 us; −8 V/5 us 208 A (gate closed): 8 V falls need ≥ 10 us |
| [A130](experiments/A130_cosim_slope_boundary/RESULTS.md) | bus-slew boundary of vff + gth 100 | 2.5 MHz, −8 V 6/7.5 us, +4.8 V 2/3 us, +8 V 10 us, two step phases | **done:** all <= 200 A; spec: <= 4.8 V >= 1 us, −8 V >= 6 us (192.2 A), +8 V >= 10 us (198.3 A, marginal) |
| [A138](experiments/A138_gp_boundary_map/RESULTS.md) | Gaussian-process level-set active learning (D63 prior, residual GP, straddle) | the adopted design's 200 A line-step boundary over L / Cs x 0.7-1.3, 4.8-8 V, 1-20 us; 400 cosim runs | **bands failed:** the rising GP's noise collapsed (0.005 A on 34 points) and one shared straddle sent 302/310 runs to falling steps; verification 20/20 |
| [A139](experiments/A139_gp_boundary_noise_floor/RESULTS.md) | A138 with the noise floor measured (step moved through a period) and the budget split per direction | the same map, fresh test set, 254 runs | **done, 3/3:** cover90 1.00 / 0.85, classification 0.90 / 0.90 (D63 0.85 / 0.55), verification 20/20; finds the peak non-monotone in slew (falling worst at 2-4 us, rising at low L worst when slow) |
| [A146](experiments/A146_cnn_loop_identification/RESULTS.md) | deep learning: 1D CNN (new `ml_cnn`), simulation-based inference, split conformal; vs damped-sine fit, simulator least squares, Cramer-Rao bound | the commutation loop (L, Q, di/dt, Coss spread) from one double-pulse V_DS capture with an unknown probe, noise, jitter and current error | **done, 3/5:** L 2.2 / Q 4.0 / di/dt 5.9 %, coverage 0.90; sine fit 7.9 / 25 / 42 %; the simulator fit (1 %) fails on fast edges, the CNN start rescues 4 of 6 -> procedure CNN then fit; misses = measurement requirements (probe >= 0.7 GHz and > 1 / t_f, noise <= 0.4 V, I0 within 2 %) |
| [A147](experiments/A147_cnn_anomaly_detector/RESULTS.md) | deep learning: 1D convolutional autoencoder (unsupervised, clean runs only) vs z-score and PCA, against the A142 oracles | 1522 cosim records of the 2.5 MHz family (2.33 M periods): does an independent detector find what the hand oracles miss? | **done, 2/4:** on known classes the CNN adds nothing (AUROC 1.000 vs 0.999, z-score fewer false alarms); the data-driven flags point at an unchecked defect: ZVS loss (valley above the floor) after rising line steps, in the frozen design too (+12..+15 A for ~13 us, turn-on V_DS 17-19 V) = the root cause of A144/A145's line-step overshoot -> A148 |
| [A148](experiments/A148_rl_zvs_line_step/RESULTS.md) | reinforcement learning (PPO, anchored) vs a derived volt-second law (RTL cfg vff "vs_g"); D63 + cosim | phase 1's low-side timing after line and load steps, to keep ZVS (A147's finding) | **FAIL 3/7, not adopted:** the law fixes load steps (turn-on V_DS 11.5-12.2 -> 6.9-7.2 V) but not the rising step (the common period stretches, Vo back 42 us, 50 pH switch 41.8 -> 41.2 V); RL neither found nor beat the law, 8 of 9 policies fail the steady check (features downstream of the action close a loop) |
| [A149](experiments/A149_bo_rising_step_overshoot/RESULTS.md) | physics block in D63 (SH_k overshoot from the turn-on V_DS) + law-family grid; GP-BO registered, not run (stop rule) | the rising-step switch overshoot at 50 / 100 pH | **FAIL as registered:** post hoc the rail term alone holds 50 pH at 38.4-38.8 V, but Vo needs 42 us and +4.8 V / 5 us oscillates (325 / 223 A, A143's dt_pred); charge balance: a held phase-1 valley stops the ladder, so every ZVS-holding law costs ~42 us |
| [A150](experiments/A150_gpbo_vo_priced_package/RESULTS.md) | constrained Bayesian optimisation in cosim (GP per output, D63 prior mean, cEI x P(feasible), batches of 4) | (gr, gt) of A148's law: 50 pH switch <= 40 V, Vo as the price | **FAIL, counted as no:** the BO found the band its 5 rows allow (gr 0.675-0.725, gt 0.175-0.35, 39.85 V), but neighbouring slews and L x 1.3 oscillate (203-275 A) and Vo back is 31-52 us; the package goes to hardware (A151 / A152). Lesson: measure a family constraint on its worst member |

## Code

- `src/scb_ivr/extensions/ml_nn.py`: the MLP; tested in
  `tests/extensions/test_ml_nn.py` against finite differences.
- `src/scb_ivr/extensions/ml_cnn.py`: the 1-D CNN (A146); tested in
  `tests/extensions/test_ml_cnn.py`.
- `src/scb_ivr/extensions/ml_d63_data.py`: D63 datasets.
- `src/scb_ivr/extensions/ml_gp.py`: the Gaussian process; tested in
  `tests/extensions/test_ml_gp.py` against brute-force leave-one-out.
- `src/scb_ivr/extensions/ml_rl.py`: the D63 environment, the softmax
  policy, REINFORCE.
- `src/scb_ivr/extensions/ml_conformal.py`: conformal bands (split,
  signed, Mondrian, adaptive); tested in
  `tests/extensions/test_ml_conformal.py` against the finite-sample
  guarantee.
- `src/scb_ivr/extensions/ml_ppo.py`: Gaussian policy and PPO.
- `src/scb_ivr/extensions/ml_rl_ff.py`: the line-step environment
  (sensors rtl | vin | rails) and its fixed laws.
- `src/scb_ivr/cosim/rtl/scb_vff.v`: the Vin feed-forward (opt-in, off =
  bit-identical).

## What the three found together

The 1 MHz turn-off question (T13 in `reports/TRADEOFF_SCORECARD.md`) was
answered three ways:
- **A120:** the surrogate's search of 100 000 designs put the floor rule
  with Cs ≲ 8 µF in the feasible region.
- **A122:** reinforcement learning, which knows nothing of that reasoning,
  converged to the same rule.
- **A121:** the GP gave calibrated error bars before the co-simulation.

**A118's co-simulation then confirmed the design:** the floor with Cs
6 µF meets the load steps and the ±4.8 V steps over ≥ 5 µs.

**The models proposed; the co-simulation decided.**

## What the package block found (A147-A150, then A151-A152)

- **A147:** the detector's unexplained flags located the line-step
  overshoot's cause: phase 1 loses ZVS after a rising step, and its hard
  turn-on rings SH2.
- **A148-A150:** control keeps ZVS on load steps, but on rising steps only
  at a Vo cost of ~42 us and with new oscillations; charge balance says why.
- **A151-A152:** the fix is the drive: a slow hard turn-on with a fast
  turn-off, plus a start-up Ton compensation (50 pH, 36 / 72 A/ns, 36.5 ns).

**The learned tools found the problem and priced the control route; the
physics chose the fix.**
