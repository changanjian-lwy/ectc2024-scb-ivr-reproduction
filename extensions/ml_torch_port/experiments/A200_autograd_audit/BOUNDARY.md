# A200 - every remaining hand-written gradient against autograd (BOUNDARY)
Method: ML (deep learning, reinforcement learning and Gaussian-process code checked by automatic differentiation;
no training, no new model)
Extension ml_torch_port. Written and committed before the audit ran. Seen before writing: A199's results, and a
smoke run that executes every section and prints no number (it stopped at the layers not yet ported).
Decision it changes: whether results that rest on hand-written gradients can be read as results of the method -
above all the negative RL results (A126-A127, A148: the learned policy lost to the hand law), A120's surrogate and
A147's autoencoder - and whether A150's Gaussian-process fits, optimised with finite-difference gradients, had
converged.
Cheaper check done first: the unit tests (tests/extensions/test_ml_nn.py, test_ml_ppo.py, test_ml_gp.py,
test_ml_cnn.py: finite differences on small cases, a brute-force GP). ml_rl has no test.
Budget: seconds, one process.

## 1. What and why
- **Problem.** A199 confirmed ml_cnn's conv / relu / pool / flatten / dense layers and its training loop. Still
  resting on hand-derived gradients alone: the MLP (ml_nn; A120, the PPO actor and critic), the layers of A147's
  autoencoder (up) and the unused tanh / unflatten, the PPO clipped-surrogate gradient including the anchored
  policy (ml_ppo), and the REINFORCE gradient (ml_rl). ml_gp has no analytic gradient: scipy's L-BFGS-B differences
  the likelihood numerically, so its convergence was never checked with an exact gradient.
- **Method.** Each loss is written again in PyTorch from the module's docstring and differentiated by autograd.
  The hand gradients are taken from the functions themselves: `loss_grads` where it exists; for ml_ppo.update a
  recording optimiser that keeps what it is handed; for ml_rl.train one iteration at lr 1 on fixed synthetic
  episodes, where the change of W is the gradient. All in float64.
- **Data.** A120's stored network and dataset (256 rows); A147's stored autoencoder on random inputs; random
  batches for the sigmoid MLP, PPO and REINFORCE; A150's 21 stored points for its four outputs (V50, PK1, PK5,
  OBJ), each fitted without the D63 prior mean.
- **Not tested.** Environments, rollouts, advantage estimation (GAE) and returns: only the gradient of a given
  loss. The GP's predictions and leave-one-out formulas (unit-tested against brute force). ml_conformal (no
  gradient). A150's GPs on the D63 residual (the prior is not rebuilt here).

## 2. Criteria
A gradient difference is max |autograd - hand| / max |hand| per parameter tensor (the absolute difference where the
hand gradient is identically zero).
1. **MLP.** <= 1e-9 on every tensor: A120's network at its stored and at its initial weights with sample weights,
   and a sigmoid / cross-entropy network.
2. **MLP.fit.** After 20 Adam steps with the L2 term, max |parameter difference| <= 1e-9 against
   torch.optim.Adam with weight_decay on the weights only.
3. **Remaining CNN layers.** Outputs within 1e-9 and gradients <= 1e-9: A147's autoencoder at its stored and its
   initial weights, and a network with tanh, flatten, dense, unflatten and up.
4. **PPO.** Actor (W, b, log_std) and critic gradients <= 1e-9, for the plain and the anchored policy, on a batch
   where at least 10 % of the samples are on each side of the clip.
5. **REINFORCE.** <= 1e-9.
6. **GP likelihood.** Value within 1e-9 relative at four hyperparameter points per output; autograd within 1e-5
   relative of central differences (step 1e-5) at the three points away from the optimum.
7. **GP convergence.** For each of A150's four outputs, L-BFGS-B with the exact gradient (from ml_gp's optimum and
   from its eight starts, same bounds) lowers the negative log marginal likelihood by <= 1e-4 and moves the latent
   mean on A150's grid by <= 0.01 predictive sd. Control: where A150 stored a model without the D63 prior, the
   refit here reproduces its (s, n, l) within 1e-6 relative.

## 3. Predictions (not criteria)
- Criteria 1-5 at 1e-12 or below; criterion 2 around 1e-13.
- The anchored policy's output-bias gradient is exactly zero in both implementations.
- GP: the finite-difference fits are converged (drops below 1e-6); a length scale sits on its bound (3.0) for PK1.

## 4. Decision rule
- All pass: the hand-written gradient code of ml_design_assist is confirmed by an independent implementation; the
  negative RL results and the surrogate / autoencoder numbers are not artefacts of a gradient error; A150's GP fits
  stand. The extension README records it.
- A gradient criterion fails: the record names the module and the tensor; every experiment that used it is listed
  as affected and the gradient is fixed before any of them is cited again.
- Criterion 7 fails: A150's models are refitted with the exact gradient and its feasible band is recomputed from
  the stored points (no new co-simulation) before A150 is cited again.
