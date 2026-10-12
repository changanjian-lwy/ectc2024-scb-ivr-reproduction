# A199 - A146's CNN in PyTorch: port and cross-check against the numpy network (RESULTS)
Boundary: 071273d. Records: a199_checks.json (a199_checks.py), runs/*.json (a199_train.py; four runs, all from
071273d with no modified file), a199_summary.json (a199_analyze.py). Environment: torch 2.14.1, numpy 2.5.4,
Python 3.12, Apple M5. The three float64 CPU runs ran in parallel at 2 threads each, the float32 MPS run beside them.

## 0. Verdict
- **6 of 6 criteria pass.** The numpy network and the PyTorch network are the same function, with the same
  gradients and the same optimiser, to rounding.
- **Exact checks (float64, the same weights and inputs).**
  - A146's stored numbers are reproduced with difference 0 (16 numbers), so the rebuilt dataset is A146's.
  - Outputs on the 4000 test captures agree within 5.3e-15.
  - Autograd agrees with the hand-written backward within 7.6e-15 relative on all 12 parameter tensors.
  - After 20 Adam steps the parameters agree within 6.7e-08; the clip acted on all 20 steps at both settings.
- **Retraining (PyTorch's own random numbers, A146's data and settings).**
  - Three float64 seeds: test median |err| L 2.0-2.2 %, Q_act 3.3-4.2 %, di/dt 5.5-6.2 %, k 0.0117-0.0119, against
    A146's 2.2 / 4.0 / 5.9 % / 0.0119. Three-seed mean over A146: 0.96 / 0.93 / 0.98 / 1.00. Covers 0.891-0.916.
  - float32 on MPS, seed 0: 2.2 / 3.4 / 5.9 % / 0.0120, covers 0.899-0.913.
- **New on A146: its numbers carry a seed spread.** Across the three seeds the median error moves by 11 % (L),
  23 % (Q_act), 12 % (di/dt) and 2 % (k) of its mean. A146 quoted one seed; its Q_act 4.0 % is at the upper end of
  3.3-4.2 %. A146's criteria 1-3 hold on every seed here with wide margin. Its criteria 4 and 5 were not rerun;
  criterion 4 failed there by one capture on Q_act, which a seed could move either way.
- **Speed.** One training step alone: numpy 36 ms, PyTorch float64 CPU 10 ms (4 threads), float32 MPS 3 ms,
  float32 CPU 59 ms (slower than float64; not traced). Whole runs: MPS 287 s for 87 epochs against A146's 1326 s
  for 76; the three parallel CPU runs took 997-1297 s (13.5-14.5 s per epoch while sharing the machine).
- **Decision (BOUNDARY Section 4).** ml_cnn's forward, backward and training loop are confirmed by an independent
  implementation; later deep-learning work in the extensions may use PyTorch; A146's numbers stand.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | C0: stored numbers within 1e-9 relative | PASS: 0 (q90, medians, 90th percentiles, covers, scaler) |
| 2 | C1: forward within 1e-9 | PASS: 5.3e-15 over 4000 x 4 outputs |
| 3 | C2: gradients within 1e-9 relative | PASS: 7.6e-15 at the trained weights, 3.6e-16 at the initial weights |
| 4 | C3: 20 Adam steps, parameters within 1e-6, losses within 1e-6 relative | PASS: 6.7e-08 / 1.2e-08 and 7.7e-09 / 6.4e-09 at max_norm 5 / 0.1; clipped on 20 / 20 steps |
| 5 | C4: each seed <= 1.25 x A146, mean >= A146 / 1.25, covers in 0.875-0.925 | PASS: worst seed 1.00 / 1.05 / 1.05 / 1.01; mean 0.96 / 0.93 / 0.98 / 1.00; covers 0.891-0.916 |
| 6 | C5: float32 MPS <= 1.25 x A146, covers in 0.875-0.925 | PASS: 1.00 / 0.84 / 1.00 / 1.01; covers 0.899-0.913 |

| run | epochs (best) | best validation loss | median \|err\| L / Q_act / di/dt / k | covers | time |
|---|---|---|---|---|---|
| A146, numpy, seed 0 | 76 | not stored (below 0.1034) | 0.0220 / 0.0397 / 0.0589 / 0.0119 | 0.909 / 0.898 / 0.911 / 0.897 | 1326 s |
| s0_f64_cpu | 96 (80) | 0.1024 | 0.0220 / 0.0364 / 0.0570 / 0.0119 | 0.901 / 0.898 / 0.904 / 0.913 | 1297 s |
| s1_f64_cpu | 69 (53) | 0.1039 | 0.0196 / 0.0416 / 0.0621 / 0.0117 | 0.912 / 0.899 / 0.910 / 0.915 | 997 s |
| s2_f64_cpu | 93 (77) | 0.0992 | 0.0217 / 0.0331 / 0.0549 / 0.0118 | 0.900 / 0.890 / 0.909 / 0.905 | 1278 s |
| s0_f32_mps | 87 (71) | 0.1051 | 0.0220 / 0.0335 / 0.0589 / 0.0120 | 0.899 / 0.903 / 0.913 / 0.906 | 287 s |

Each saved model, reloaded into a freshly built network, repeats its test predictions exactly (difference 0).

Predictions:
- C0-C2 at 1e-12 or below, C3 around 1e-8: held (<= 7.6e-15; 1.2e-08 and 6.7e-08).
- Stop between 50 and 110 epochs: held (69-96).
- Seed spread under 10 %: wrong for three of four (11 / 23 / 12 / 2 %).
- A CPU float64 run 2-3x faster than 1326 s: wrong as run (997-1297 s, three in parallel, 69-96 epochs). A step
  alone is 3.6x faster.

## 2. Limits
- **C5 is not a fourth independent seed.** It has seed 0's initial weights and batch order (build_model draws in
  float32 and then converts) and differs from s0_f64_cpu in precision and device only.
- **Bit-for-bit agreement at the initial weights.** There the weight gradients differ by exactly 0, at the trained
  weights by ~1e-15. Not traced; it is what one expects if both libraries reach the same matrix product when the
  biases are zero. The same comparison code gives non-zero differences at the trained weights and in C3, so it is
  not comparing a result with itself.
- **Scope.** Only A146's layer kinds are ported and checked; A147's autoencoder (tanh, up, unflatten) is not.
  numpy's own seed spread was not run; the PyTorch seeds stand in for it because C3 shows the two train alike step
  by step. Timings are from one machine with the other runs sharing it.
