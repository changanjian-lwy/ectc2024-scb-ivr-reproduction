# A150 - constrained GP-BO of the phase-1 edge law (gr, gt): 50 pH package switch <= 40 V, Vo as the price (BOUNDARY)
Method: mixed - ML (GP surrogates + constrained Bayesian optimisation) driving RTL cosim (A148's scb_vff vs_kr / vs_kt, no RTL change)
ml_design_assist extension. Written and committed before any A150 run. Looked at beforehand: the five prior points'
records (frozen design A143/A145, A148 v075/v100, A149 r075/r100) and the D63 A149 grid slice rel_k 0, kv 0.
Decision it changes: whether "relax the line-step Vo spec, hold the 50 pH / 72 A/ns switch by control" is an option with
a price for Mihai (scorecard), or the package stays hardware-bound whatever the Vo spec. User chose it as a scenario study.
Cheaper check done first: D63 grid (A149) - it is blind to the +4.8 V / 5 us oscillation and wrong on Vo recovery
(2.5 vs 42 us at (0.75, 0)), so it serves only as prior mean / smoothness. Budget: <= 4 batches x 4 points x 5 runs
+ 2 fill + 24 confirmation runs <= 106 runs, ~36 min per batch at 10 jobs, <= 3.5 h wall.

## 1. What and why
- Problem: A149 post hoc showed the rail term alone holds 38.4-38.8 V at 50 pH but breaks +4.8 V / 5 us (223-325 A) and
  costs Vo (back 42 us at L0, 52-54 us at L x 1.3; frozen 7.6 / 8.7 us). The Ton term gt calms 5 us but raises V_DS.
  Between the frozen design (0, 0: 41.8 V, Vo 8.7 us) and (0.75, 0) V_DS and Vo trade continuously, so the cheapest
  point that just reaches 40 V may cost far less Vo than a full ZVS hold. Unknown: whether such a point keeps the peaks.
- x = (gr, gt) in [0, 1.25]^2 (D63 grid span); vs_kr / vs_kt = round(g x 1310.72). One evaluation = 5 cosim runs:
  e50 (A145 e72_l50_l_p48_1us, loop 50 pH Q 7 + 72 A/ns) -> V50 whole-run max V_DS; l_p48_1us at L x 1 / 0.7 / 1.3 ->
  PK1 max peak, OBJ = log worst-L Vo error area (mV us, 100 us after the step, about the pre-step mean); l_p48_5us -> PK5.
- Method: one GP per output (ml_gp; length scales 0.2-3, the D63 slice's own scales are 0.2-0.7; noise floors 0.1 V /
  1 A / 0.05). V50 and PK1 use D63 as prior mean when that lowers the leave-one-out RMSE (5 prior points: 0.71 vs 1.20 V,
  0.62 vs 3.75 A). Acquisition EI(OBJ) x P(feasible) (Gardner et al. 2014, cEI; Eriksson & Poloczek 2021, SCBO),
  P(feasible) alone until a feasible point exists; batches of 4 by kriging believer, 0.075 exclusion, 0.025 grid.
  Stop: after >= 2 new batches, max P(feasible) < 0.02 (infeasible) or max cEI < 0.02 (converged); at most 4 batches.
- Why GP-BO: 2-D, ~36 min per batch, noisy (step position 0.2-5 A), constraint boundaries unknown and one of them (the
  5 us oscillation) invisible to D63. Rejected: grid 6 x 6 (36 points, ~9 h); CMA-ES (>= 60 evaluations); RL (A148:
  feedback features, failed the steady check); SH-block proxy as V50 screen (bias +0.07..+1.45 V over the five prior
  points, larger than the margin sought); D63-only optimisation (blind / biased as above).
- Deviations from the A149 handoff plan: (a) V50 is measured (loop + edge) at every point, not proxied; (b) Vo is the
  price, not a 50 us threshold - that value was ours, and L x 1.3 already sits at 52-54 us; (c) the frozen design is a
  fifth prior point and the L0 l_p48_1us peak is in PK1 (as in A149 criterion 3).
- Not tested: other law families (rel_k, kv), 100 pH, four modules, efficiency (the law is zero at constant Vin).

## 2. Criteria
1. BO forecast calibration: of the (new point, V50 / PK1 / PK5) pairs, >= 70 % within the +-2 sd predicted before the run.
2. A feasible point: single runs V50 <= 40.0 V, PK1 <= 200 A, PK5 <= 200 A, 0 NEW oracle events on all 5 runs,
   COMPLETED, cosim sources unmodified.
3. Confirmation of the candidate (lowest OBJ among feasible): steps moved by +0.17 / +0.34 us on the 5 rows -> V50 <=
   40.0 V and peaks <= 200 A; +4.8 V at 2 / 3 / 4 / 7 / 10 us (L0), l_p48_5us at L x 0.7 / 1.3, s_p62 and l_m48_1us
   (L0) -> peaks <= 200 A; every run 0 NEW events and Vo back within 1 % (finite).
4. Steady state unchanged on the candidate's l_p48_1us record (600-1000 us vs the frozen record): Vo mean within 0.5 mV,
   phase-1 turn-on V_DS mean within 0.3 V, max peak within 1 A.
Price (reported, not a criterion): Vo back / extreme at L x 1 / 0.7 / 1.3, IAE vs frozen (274 mV us worst-L), peak
margin used per row vs frozen, late fires. Frozen reference runs on the five slews are part of confirmation.

## 3. Predictions (not criteria)
- Criterion 2 passes: 40 %. If so: gr 0.35-0.6, gt 0-0.4, V50 39.5-40.0 V, PK1 195-200 A, worst-L Vo back 15-45 us,
  IAE 400-700 mV us. Criterion 3 passes given 2: 40 % (peaks at the limit, step-position noise heavy-tailed, A139).
- PK5 > 200 A (oscillation) starts near gr 0.6 at gt 0 and moves to higher gr as gt grows.
- SH-block proxy bias stays in +0.0..+1.5 V and grows with gr. D63 keeps winning LOO for V50 and PK1.
- At the best point dV50/dgr < 0 and dV50/dgt > 0; dPK5/dgt < 0 at gr >= 0.75 (gt calms 5 us, gr lowers V_DS).
- Oscillating 5 us runs show phase 2-4 low-offs >= 0 A within 60 us (A143's lo234_pos > 0); calm ones do not.
- Criterion 1 passes.

## 4. Decision rule
- 2, 3, 4 pass: "50 pH / 2 ns <= 40 V by control" goes to the scorecard and the Mihai summary with its gains and price;
  not adopted (the Vo spec is Mihai's call).
- 2 fails at the stop: no (gr, gt) holds 40 V without breaking the peak limits, whatever the Vo spec -> the package
  stays hardware-bound (< 50 pH or stronger damping); closest point's misses reported. If 1 also fails, the claim covers
  the points run only, not the map.
- 2 passes, 3 fails: feasible only within step-position noise -> counted as no; the near miss's price reported.

## 5. Addendum (after the BO stopped on budget, before any confirmation run)
- BO: 16 new points, feasible (0.675, 0.25), (0.725, 0.35), (0.7, 0.175). The registered candidate (lowest OBJ) is
  (0.675, 0.25), OBJ 6.6299 vs 6.6318 for (0.725, 0.35): a 0.2 % IAE tie under noise, but the margins differ (V50
  0.15 vs 0.34 V; smallest margin in noise units 0.30 vs 0.69, V50 / 0.5 V, peaks / 3 A).
- Post hoc, not part of the verdict: the same confirmation rows on the largest-margin feasible point (0.725, 0.35),
  in the same cosim call (`a150_bo.py --confirm --posthoc`). The verdict stays on the registered candidate; the post
  hoc point only tells whether a pass/fail there hinges on the tie-break.
