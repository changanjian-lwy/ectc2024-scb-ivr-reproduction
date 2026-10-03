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

## Code

- `src/scb_ivr/extensions/ml_nn.py`: the MLP; tested in
  `tests/extensions/test_ml_nn.py` against finite differences.
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
