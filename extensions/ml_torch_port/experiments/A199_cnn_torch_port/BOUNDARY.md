# A199 - A146's CNN in PyTorch: port and cross-check against the numpy network (BOUNDARY)
Method: ML (deep learning: the same 1D CNN in a second implementation; no new model, no new data)
Extension ml_torch_port. Written and committed before the checks and the training runs. Seen before writing: A146's
stored summary (the reference numbers below) and timing-only smoke runs (600 traces, 3 epochs; no check result and no
loss printed): one training step takes 36 ms in numpy, 10-11 ms in PyTorch float64 on the CPU, 59 ms in float32 on
the CPU and 3 ms in float32 on the Apple GPU backend (MPS).
Decision it changes: whether ml_cnn's hand-written backward passes and training loop are confirmed by an independent
implementation, and whether later deep-learning work in the extensions may be written in PyTorch with A146's numbers
carrying over.
Cheaper check done first: tests/extensions/test_ml_cnn.py (finite-difference gradients of every parameter and of the
input, on small networks; one sine-frequency fit).
Budget: data rebuild and checks a few minutes; training <= 150 epochs x 6-9 s = <= 23 min per float64 run, three in
parallel at 2 threads each, plus one float32 MPS run (<= 4 min): <= 30 min wall, one machine, alone.

## 1. What and why
- **Problem.** ml_cnn (forward, backward, Adam, clipping, early stopping) is written by hand in numpy. It has
  finite-difference unit tests on small networks but no second implementation, and every A146 / A147 number rests on
  it. It is also slow (36 ms per step).
- **Method.** The same layer specs build torch.nn layers (`torch_cnn.py`); autograd replaces the backward methods.
  Two comparisons:
  - exact: the same weights and inputs in float64, then outputs, gradients and parameter updates are compared;
  - statistical: training from PyTorch's own random numbers (ml_cnn's distributions), then A146's test numbers.
- **Data.** A146's dataset, rebuilt by a146_run's own functions with its generator (1460) and its order of calls:
  32 000 training examples, 2000 validation, 2000 calibration, 4000 test.
- **Tested.** conv / relu / pool / flatten / dense, the summed-square loss, Adam, the norm clip and early stopping,
  on A146's network (four conv layers 16-32-32-32, dense 64, 4 outputs; 114 900 parameters).
- **Not tested.** A147's autoencoder layers (tanh, up, unflatten: not ported). A146's baselines and robustness rows
  (unchanged, not rerun). Nothing new about the loop identification itself. A146 ran one seed, so the numpy
  network's own seed-to-seed spread is not known; the 25 % band of criterion 5 is a judgement.

## 2. Criteria
1. **C0, data identity.** With the rebuilt dataset and A146's stored weights, q90, median_err, p90_err and cover90
   equal a146_summary.json's to <= 1e-9 relative (16 numbers). If this fails, criteria 5 and 6 compare different
   data and are void.
2. **C1, forward.** The stored weights copied into the PyTorch model: max |PyTorch - numpy| over the 4000 x 4
   standardised test outputs <= 1e-9.
3. **C2, gradients.** For each of the 12 parameter tensors, max |autograd - backward| / max |backward| <= 1e-9, at
   the trained weights and at the seed-0 initial weights, on the first 64 training examples.
4. **C3, optimiser.** After 20 Adam steps from the same initial weights on the same batches: max |parameter
   difference| <= 1e-6 and every loss within 1e-6 relative, at max_norm 5 (A146's) and at max_norm 0.1 (so that the
   clip acts). Not bit-identical by construction: clip_grad_norm_ divides by norm + 1e-6, ml_nn.Adam by the norm.
5. **C4, retraining in float64 on the CPU, seeds 0, 1, 2.** Per parameter: each seed's test median |err| <= 1.25 x
   A146's (L 0.0220, Q_act 0.0397, di/dt 0.0589, k 0.0119); the three-seed mean >= A146's / 1.25; each 90 % cover
   within 0.875-0.925.
6. **C5, float32 on MPS (PyTorch's usual setting), seed 0.** Median |err| <= 1.25 x A146's and cover within
   0.875-0.925, per parameter.

Margin against the reference record: A146's own covers (0.897-0.911) sit >= 0.014 inside the band, which is about
+-3 sd of the test and calibration sampling (sd ~0.008, binomial estimate with 4000 and 2000 captures).

## 3. Predictions (not criteria)
- C0-C2 differences at 1e-12 or below (float64 rounding); C3 around 1e-8.
- Retraining stops between 50 and 110 epochs (A146: 76); the three seeds' median errors differ by under 10 %.
- A full run is 2-3x faster than A146's 1326 s on the CPU in float64, more on MPS.

## 4. Decision rule
- C0-C3 pass: ml_cnn's forward, backward and optimiser are confirmed by an independent implementation, and the
  port is exact.
- C4 and C5 pass as well: later deep-learning work in the extensions may use PyTorch; A146's numbers stand.
- C1-C3 fail: the per-tensor record says which layer or step differs; that is a defect in ml_cnn or in the port
  and is fixed before anything else rests on either.
- C4 or C5 fail while C1-C3 pass: the two implementations agree step by step, so the difference comes from the
  initial random numbers and the batch order; run numpy seeds 1 and 2 (~22 min each) to measure its spread before
  concluding.
