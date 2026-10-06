# A148 - phase 1's low-side timing through line and load steps: volt-second law against RL (BOUNDARY)
Method: mixed - D63 turn-on V_DS block (math, D57) + physics law and PPO in D63 (ML) + RTL option + cosim.
Extension ml_design_assist. Written and committed before the grid, the training and every cosim run. Looked at
beforehand: A143 K4 and A145 records (Section 1), D63 with the frozen design and the volt-second law on 5-8 rows
(used to set the cost weights), the V_DS block check (a148_von_check.json).
Decision it changes: whether the step-induced hard turn-on (A147) can be removed by control, so that the package
loop spec (A145) is set by start-up and steady V_DS only. Cheaper check first: D63 + V_DS block; only its winner
goes to RTL. Budget: D63 part ~1 h CPU; cosim 20 runs, ~2 h at 10 jobs.

## 1. What and why
- Cosim (A143 K4, L0), largest turn-on V_DS in the 60 us after the step (steady 3.9 V), three mechanisms:
  1. +4.8 V / 1-5 us: phase 1 17-19 V. Rail 1 takes the whole step (Cs holds it); under A136's cap phase 1's
     volt-seconds rise ~22 %; dlo learns <= 2 ns per period (smax 64) against ~90 ns needed; valley +12..+18 A, ~25 periods.
  2. s_p62: every phase 11.5-12.2 V (Ton rises, dlo lags; phases 2-4 follow phase 1's period).
  3. -4.8 V / 1-5 us, -8 V / 10 us: phases 2-4 13.6-15.3 V, low-off current up to +92 A. The floor cuts phase 1 at
     -20 A, its period falls 505 -> 350 ns, and the slotted phases 2-4 lose low-side time. In D63 without the floor
     phase 1 crosses to -68..-77 A (A115's runaway region) and phases 3-4 still lose ZVS: not a phase-1 timing problem
     (-> A149, knobs on phases 2-4). Here: no-regression rows.
- A145: after +4.8 V / 1 us the 8 switches reach 41.8-56.6 V against 37.3-45.7 V at start-up (the step binds from
  50 pH); s_p62 36-42 V; falling steps were never run with a loop.
- Knob: phase 1's timed edge t_lon + dlo + lo_add; lo_add is not learned, and a floor turn-off does not overwrite dlo.
  Physics: volt-second balance (V_rail1 - Vo) Ton1 = Vo dlo, so lo_add = g ((rail - Vo) Ton1 - (rss - Vo) tlp) / Vo
  with scb_vff's own estimates (zero in steady state up to Ton's dither). D63, g 1: phase 1 10.9 V (from 18.7),
  s_p62 4.6 V on every phase (from 11.5), but the period stretches 504 -> 600-637 ns, Vo -16 mV, peak 199 A. While
  rail 1 is high the target valley still leaves 8.6 V at 17 V (the floor 7.6 V; D57): ~8 V is this knob's limit.
- Why RL: the knob trades phase 1's V_DS against the period stretch (Vo dip, loop Ton, peaks, phases 2-4 depth) over
  tens of periods; the law balances phase 1 alone. PPO (A127's anchored residual policy, asymmetric critic) optimises
  the trajectory against a priced cost. Rejected: the gain / slew grid alone (it is the baseline RL must beat); MPC
  (needs an online model, not RTL); a network in RTL (a policy counts only after distillation).
- Cross-check asked: does RL converge to the volt-second law, or find a better trade-off with the same signals?
- D63 additions (defaults off, the 9 old tests unchanged + 3 new): von_table (D57's free node from the low-side
  turn-off to t_tr, against (i_off, rail)); checked before registration on 193 k cosim turn-ons: phase 1 median
  0.00 V, p90 0.01 V (hard turn-ons p90 0.42 V); phases 2-4 read 0.46 V low. lo_add as above.

## 2. Cost, training, evaluation (D63)
- Cost per period: (max_k V_DS,k - 6)+ / 2 + ((max peak - 192)+ / 4)^2 + w_vo ((|Vo - 1| - 0.01)+ / 0.005)^2
  + 0.1 sum_k (i_tgt - 10 - valley_k)+ / 20. w_vo 1 (inside 1 % free: the frozen s_m62 already reaches 17 mV) and a
  tight-Vo scenario w_vo 4.
- Physics grid: B0, smax 255, rail-only, vs with g {0.5, 0.75, 1, 1.25} x slew {none, 20, 40 ns per period}; best =
  lowest mean cost on the eval set, per w_vo.
- PPO: lo_add = 100 ns x a, a in [-2, 3]; actor observation (transient, zeroed by the anchor): rail excess, Vin slope,
  Ton vs its low-pass, last valley report, last phase-1 V_DS hard bit (A132's comparator); context rss. 3 seeds x 2
  weightings, 600 iterations x 32 episodes x 200 periods; draws: line +-1..6.4 V over 1..10 us (70 %), load +-20..62.5 A.
- Eval set: A124's 7 rows + 40 draws (seed 999); L x 0.7 / 1.3 on the rows; steady identity and 1000-period checks.
- Distillation: least squares of the best seed's offset on {vs}, {rail, ton}, {+report}, {all} (no intercept); the
  smallest set within R^2 0.05 of {all}.

## 3. Criteria
D63 (choose what goes to RTL; w_vo 1):
1. RTL candidate = lowest eval cost of {best law, distilled rule} that passes both checks; within 5 % -> the law.
2. Reported: RL converges to the law if R^2(vs) >= 0.8 with g in [0.5, 1.5]; beats it if its cost is >= 10 % lower
   and it passes both checks.
Cosim (the candidate as a cfg-gated RTL option, default off):
3. Identity: option off bit-identical (tb tests; one A143 K4 run equal in every record field but provenance / wall).
4. Steady (n0, option on): Vo mean within 0.5 mV, peak within 1 A, phase-1 V_DS mean within 0.3 V of A143.
5. L0: phase-1 turn-on V_DS max (60 us after the step) <= 12 V on l_p48_1us and l_p48_5us (A143 19.0 / 17.4);
   every phase <= 7 V on s_p62 (11.5-12.2).
6. No regression (8 rows at L0; l_p48_1us and s_p62 at L x 0.7 / 1.3): peak <= 200 A, late fires <= A143's, Vo back
   within 1 % no later than A143 + 20 us, falling rows' max V_DS <= A143 + 1 V.
7. Loop + edges (A145 e72; 50 and 100 pH): l_p48_1us post-step max V_DS <= the run's start-up max; at 50 pH the whole
   run <= 40 V (A145 41.8 V). l_m48_1us with the option off and on: measured, no criterion.

## 4. Predictions
- D63: best law g 0.75 without slew limit; RL correlates >= 0.8 with the vs law and lands within 10 % of its cost
  (no new mechanism) - 60 %.
- Cosim: l_p48_1us phase-1 V_DS 10-12 V, peak 190-198 A; s_p62 4-6 V; 50 pH l_p48_1us 35-38 V; l_m48_1us 45-55 V at
  100 pH (unmeasured so far).

## 5. Decision rule
- 3-7 pass: the step no longer binds the package spec at the tested L; adoption is the user's call (the controller
  is frozen); falling steps -> A149.
- 5 passes, 6 fails on peak: not adopted; the peak / V_DS trade-off is the result.
- 5 fails: phase-1 timing cannot remove the step's hard turn-on; the spec stays step-bound.
