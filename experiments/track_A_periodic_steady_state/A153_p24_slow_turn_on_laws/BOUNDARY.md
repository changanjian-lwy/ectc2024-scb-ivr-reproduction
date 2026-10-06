# A153 - D68's slow-turn-on laws tested where no run has been (BOUNDARY)
Method: mixed (math: D68's laws and predictions; RTL cosim cfg only, frozen design)
Track A, package layer. Written and committed before the runs; D68 and its script were written from A145 / A151 / A152's
records only (no A153 run existed).
Decision it changes: whether the package spec can be stated as formulas in (L, turn-on di/dt) for Mihai's actual values
(start-up ton_S(d), L * di/dt_on <= x*), instead of one co-simulation campaign per point.
Cheaper check done first: D68 (single-edge harness, 63 edges, 22 s; the laws fitted on 7 + 12 existing runs).
Budget: 7 runs (3 x 300 us, 4 x 1400 us), ~1 h at 10 jobs.

## 1. What and why
- D68 derives the slow hard turn-on from the node charge (Q0 ~ 162 nC for 2 + 3 EPC2067 at 12 V):
  - start-up: each hard turn-on of mode S loses t_lost ~ (di/dt)^-1/2 of on-time, so
    ton_S(d) = 35.5 + K (d^-1/2 - 72^-1/2), K = 15.6 ns (A/ns)^1/2 (A152's rule 36 A / d is a 1/d fit to it);
  - line-step overshoot: the whole-run max V_DS depends on x = L * di/dt_on only; <= 40 V for x <= x* = 3.2 V
    (to 150 pH; above, the 72 A/ns turn-off ring binds).
- Both were fitted on existing runs. This experiment tests them at new points:
  - u24 / u12 / u06_l100: A151's n0 cfg at 100 pH, turn-on 24 / 12 / 6 A/ns, ton 35.5, 300 us (start-up only);
  - v75_on40 (x 3.0 V), v125_on24 (3.0 V), v125_on32 (4.0 V), v75_on24 (1.8 V): A152's s100_l_p48_1us cfg (frozen
    design, +4.8 V / 1 us at 1000 us, turn-off 72 A/ns, Q 7) with loop L, turn-on d and D68's ton_S(d).
- 75 and 125 pH and 40 / 32 / 24 / 12 / 6 A/ns have not been run before. Not tested: other rows, L / Cs corners,
  four modules, > 150 pH, a gate model.

## 2. Criteria
1. Start-up law: Vo(143.6 us) of u24 / u12 / u06 inside D68's band (K 14.6-16.7) widened by +-0.005 V, on all 3;
   and at u24 and u06 (where the two differ by >= 0.01 V) D68 is closer than A152's 36 A / d rule.
2. Overshoot law: whole-run max V_DS (vds_win, all switches) within +-1.0 V of the x-curve on all 4 v rows.
3. The 40 V side as predicted on all 4 v rows (<= 40 V at x 3.0 / 1.8, > 40 V at x 4.0).
4. Start-up with D68's ton_S: highest high-side turn-off current for t < 300 us <= 165 A and Vo(143.6 us) within
   +-0.015 V of the 72 A/ns value at that L, on all 4 v rows.
5. Controller unchanged on all 4 v rows: COMPLETED, post-step peak <= 190 A, 0 NEW oracle events (a142_oracles).

## 3. Predictions (a153_predictions.json; not criteria)
- Vo(143.6 us): u24 0.9781 [0.9755, 0.9805] (A152 rule 0.9880); u12 0.9406 [0.9355, 0.9455] (rule 0.9455);
  u06 0.8877 [0.8789, 0.8959] (rule 0.8605).
- Max V_DS: v75_on40 39.2 V, v125_on24 39.2 V, v125_on32 42.5 V, v75_on24 36.8 V (bands +-1.0 V).
- ton_S: 36.128 / 36.846 / 36.419 / 36.846 ns; Vo at the handover 1.0167 (75 pH) / 1.0079 (125 pH).
- Post-step peaks 175-185 A (A152: <= 180 A at x 1.8 V).

## 4. Decision rule
- 1-4 pass: D68's two laws become the package spec formula (scorecard T20, Mihai summary Section 3 and question 3,
  learning material).
- 2 or 3 fails: the x-rule stays descriptive; the spec stays at the tested points (A152).
- 1 fails: A152's rule stays (it over-compensates, the safe side) and D68 Section 3 is corrected.
- 5 fails on a row: that row's drive is not adopted whatever its V_DS.
