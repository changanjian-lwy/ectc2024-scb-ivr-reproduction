# A146 - CNN identification of the commutation loop from one V_DS capture (BOUNDARY)
Method: ML (deep learning: 1D CNN, simulation-based inference, split-conformal intervals; baselines: damped-sine fit,
simulator least squares, Cramer-Rao bound)
Extension ml_design_assist. Written and committed before training. Seen before writing: the 24 000 clean traces
(a146_data.py), the CRB at 12 points, two 6-parameter simulator fits, and a 3-epoch smoke run (plumbing only).
Decision it changes: how the loop values A144 / A145 depend on (L, Q, edge di/dt; D65's questions for Mihai) get
fixed - by Mihai's estimate only, or measured from one double-pulse V_DS capture, with which probe / trigger quality.
Cheaper check first: the CRB (the information is there: sd 0.05-2 % with a known measurement chain).
Budget: training <= 45 min (18 s per epoch, <= 150 epochs), 80 simulator fits ~3 min, all on one machine, alone.

## 1. What and why
- Measurement: a double-pulse turn-off of SH1 at a sensed current I0 (low side off, reverse conduction), V_DS of SH1
  from the gate edge, 32 ns; plant = A145's harness (cosim FastPlant with finite edges, nonlinear Coss).
- Unknowns: loop L 25-300 pH, Q 2-30 (Q_act = q sqrt(k) is the target), di/dt 36-576 A/ns (log-uniform), Coss
  spread k 0.85-1.15; I0 60-200 A. Measurement draws (unknown to every estimator): probe 2nd-order low-pass fc 0.7-2
  GHz, noise 0.05-0.4 V, trigger jitter +-50 ps, I0 error +-2 %; 25 GS/s (800 samples).
- Why a CNN: the cues are local patterns in time (the edge's curvature -> di/dt, the ring's period -> L C, its
  amplitude per amp -> sqrt(L / C), its decay -> Q); a convolution finds them wherever the jitter puts them, and one
  network amortises the inference (ms per capture, no initial guess) while marginalising the unknown probe and jitter.
  Why not only a fit: the fit needs the simulator per evaluation (~15 s per capture) and a start; why not only the
  sine fit: nonlinear Coss biases it and it cannot separate L from k or see di/dt.
- Cross-validation: two independent inference routes (amortised CNN, simulator fit with trigger shift and probe
  bandwidth as extra unknowns) on the same captures; the CNN's estimate as the fit's start.
- Data: traces 0-15999 train (two measurement draws each), 16000-17999 val, 18000-19999 conformal calibration,
  20000-23999 test; CNN conv 16-32-32-32 (k 9 / 7 / 5 / 5, ReLU, pool 2) + dense 64; Adam 1e-3, batch 64, patience 15.
- Not tested: real hardware, other loop topologies (split L, Cin ESL), gate-model edges, temperature.

## 2. Criteria (test set unless stated)
1. CNN median |error|: L <= 5 %, Q_act <= 10 %, di/dt <= 15 %, |dk| <= 0.03.
2. Split-conformal 90 % intervals: test coverage in [0.87, 0.93] for all four.
3. CNN median error <= 1/2 of the damped-sine fit's for L, Q_act, di/dt.
4. Simulator fit (centre start, 40 test captures): its estimate inside the CNN's 90 % interval for >= 85 % per
   parameter; from the CNN start: mean evaluations below the centre start's, median cost not higher.
5. Robustness (1000 test captures each, outside the draws: noise 0.8 V, probe 0.5 GHz, jitter 150 ps, I0 error 5 %):
   coverage >= 0.75 for every parameter and row.

## 3. Predictions (not criteria)
- CNN: L 3 %, Q_act 6 %, di/dt 8 %, k 0.02. di/dt split: t_f >= 0.5 ns 5 %, t_f < 0.5 ns (31 % of the test) 20-40 %:
  an edge faster than the probe's response is degenerate with the unknown fc (seen in a fit: 300 A/ns at 0.8 GHz
  fitted as 179 A/ns at 1.31 GHz, residual at the noise level).
- Sine fit (smoke): L 7 %, Q_act 25 %, di/dt 45 %. Simulator fit: L 0.5 %, Q_act 1.5 %, k 0.005, di/dt good for slow
  edges and degenerate for fast ones like the CNN.
- Coverage 0.89-0.91. Robustness: jitter 150 ps and probe 0.5 GHz hurt di/dt most (coverage ~0.7 -> criterion 5 may
  fail there); noise 0.8 V and I0 5 % change little (I0 error enters sqrt(L / C) via the amplitude: L, k shift ~2-3 %).

## 4. Decision rule
- 1-4 pass: the CNN (with conformal intervals) is the measurement tool for L, Q and k, di/dt where t_f > the probe's
  response; the simulator fit refines from the CNN start. The procedure and its probe / trigger requirements go to the
  Mihai summary as the way to settle the loop values on hardware.
- 1 or 3 fails: the network is not the tool; report the simulator fit as the method and the CNN's failure mode.
- 4 fails: the two routes disagree - find which is biased (model check on the disagreeing captures) before any use.
- 5 fails on a row: that row becomes a measurement requirement (probe bandwidth / trigger jitter limit).
