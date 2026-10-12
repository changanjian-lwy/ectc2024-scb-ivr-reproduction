# A200 - every remaining hand-written gradient against autograd (RESULTS)
Boundary: db607bc. Run from db607bc. Record: a200_audit.json (a200_audit.py). torch 2.14.1, numpy 2.5.4, float64, CPU.

## 0. Verdict
- **7 of 7 criteria pass.** Every hand-written gradient in ml_design_assist agrees with autograd to rounding, and
  A150's Gaussian-process fits had converged.
- **MLP (ml_nn).** A120's network with sample weights: 2.3e-15 at its stored weights, 7.0e-16 at the initial ones;
  sigmoid with cross-entropy 3.8e-16. `MLP.fit`'s 20 Adam steps with L2 end within 1.1e-16 of
  torch.optim.Adam with weight_decay on the weights only.
- **The CNN layers A199 left out.** A147's autoencoder (up): outputs within 2.4e-15, gradients within 1.1e-15 at
  its stored weights. A network with tanh, flatten, dense, unflatten and up: 2.2e-16 and 4.6e-16.
- **PPO (ml_ppo.update, taken from the function).** Actor (W, b, log_std) 2.0e-15 for the plain policy and 2.4e-15
  for the anchored one; critic 1.4e-15; 22 % of the batch on the clipped side.
- **REINFORCE (ml_rl.train).** 5.7e-14 over 118 steps of 16 synthetic episodes. This module had no test before.
- **GP (ml_gp).** The likelihood's value agrees within 3.5e-13; autograd's gradient is within 2.2e-07 of central
  differences. Refitting A150's four outputs with the exact gradient lowers the negative log marginal likelihood
  by at most 5.3e-11 and moves the latent mean on A150's grid by at most 9.8e-06 predictive sd. The three models
  A150 stored without the D63 prior (PK1, PK5, OBJ) are reproduced exactly.
- **Decision (BOUNDARY Section 4).** The hand-written gradient code is confirmed by an independent
  implementation. The negative RL results (A126-A127, A148) and the numbers of A120 and A147 are not artefacts of
  a gradient error. A150's GP fits stand.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | MLP gradients <= 1e-9 | PASS: 2.3e-15 / 7.0e-16 / 3.8e-16 |
| 2 | MLP.fit, 20 Adam steps with L2, parameters within 1e-9 | PASS: 1.1e-16 |
| 3 | remaining CNN layers, outputs and gradients within 1e-9 | PASS: worst 2.4e-15 |
| 4 | PPO actor and critic <= 1e-9, plain and anchored, >= 10 % on each side of the clip | PASS: worst 2.4e-15; 22 % clipped |
| 5 | REINFORCE <= 1e-9 | PASS: 5.7e-14 |
| 6 | GP likelihood: value within 1e-9, autograd within 1e-5 of central differences | PASS: 3.5e-13, 2.2e-07 |
| 7 | GP convergence: drop <= 1e-4, grid shift <= 0.01 sd, control within 1e-6 | PASS: 5.3e-11, 9.8e-06 sd, control 0 |

Predictions:
- Criteria 1-5 at 1e-12 or below and criterion 2 around 1e-13: held (worst 5.7e-14; criterion 2 at 1.1e-16).
- The finite-difference GP fits are converged (drops below 1e-6): held. PK1's first length scale sits on its upper
  bound (3.0), as A150 stored it.
- The anchored policy's output-bias gradient is exactly zero in both: this was visible before registration (the
  smoke run raised a 0 / 0 warning there), so it was not a blind prediction.

## 2. Limits
- **Gradients of given losses only.** The environments, rollouts, generalised advantage estimation and returns
  are not checked here; neither are the GP's prediction and leave-one-out formulas (unit-tested against brute force).
- **One batch per case.** Random batches, one seed each; PPO at one clip setting (0.2) and one entropy weight.
- **A150's GPs on the D63 residual** (V50's stored model) are not rebuilt; V50 is checked here without the prior.
