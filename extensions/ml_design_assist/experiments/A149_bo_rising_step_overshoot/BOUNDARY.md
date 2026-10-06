# A149 - rising-step switch overshoot: D63's SH_k block, a stable law family, D63 grid, then (only with a candidate) GP-BO in cosim (BOUNDARY)
Method: mixed - math (D63 block calibrated on A144/A145 cosim records; D63 grid; charge-balance bound), ML (GP Bayesian
optimisation in cosim, only if the D63 stage finds a candidate), RTL options + cosim for that candidate.
Extension ml_design_assist (ML block 2026-10-06..10). Written and committed before the D63 grid, any RTL and any cosim.
Looked at beforehand: (a) the 0.4 us window peaks of SH2-4 against phase k-1's turn-on V_DS in the A144/A145/A148 loop
records (the block's form); (b) ~30 D63 probe points of the family (sec. 3), with SH from a provisional table.
Decision it changes: can control hold the 50 pH / 72 A/ns design <= 40 V on +4.8 V / 1 us? Yes -> the loop spec is
start-up-bound (37.3 V); no -> the package needs < 50 pH or stronger damping.
Cheaper check first: D63 + block (~10 ms per row) and a charge-balance argument, before any RTL or cosim.
Budget: D63 grid 1350 points x 6 rows (+ robustness rows), < 15 min at 10 jobs. Cosim only with a candidate: <= 38
BO points x 4 loop-free rows (4 min each) + <= 6 loop + edge runs (37 min each), ~3 h wall at 10 jobs.

## 1. What and why
- After +4.8 V / 1 us rail 1 takes the step (B2 = rail 1 + rail 2: 24 -> 28.8 V) and phase 1 hard-turns on (18-19 V);
  SH2 rings to B2 + x(dV) (A144 mechanism B). Frozen design at 50 pH / 72 A/ns: 41.8 V > 40 V.
- **Block (D63, `Design.sh`, rec "sh"):** SH_k = rail_(k-1) + rail_k + f(V_DS,on of phase k-1), k = 2..4, per period,
  from D63's rails and von. f per (L, di/dt): medians of the window excess (SH_k peak - blocking voltage) in 1 V bins of
  turn-on V_DS (>= 3 windows per bin), made non-decreasing, linear between bins, flat outside. Calibration: A144 + A145
  records (frozen controller). Held out: the 10 A148 loop + edge records (laws g 0.75 / 1.0, falling steps). Seen: at
  72 A/ns f has slope ~1 up to 12 V then saturates near 13 V (50 pH), slope ~1.4 (100 pH); instantaneous edges ~1.7
  (A144's 24 + 1.7 dV). SH1 (own turn-off, D65's mechanism A) is <= 24 V in every record and stays out of the block.
- **Family** (exogenous Vin features or low-gain linear terms; zero at constant Vin and load by construction):
  - gr in [0, 1.25]: rail term, lo_add += gr tlp (rail - rss) / Vo (A148's vs_kr = gr x 1310.72);
  - gt in [0, 1.25]: Ton term, lo_add += gt (ton_1 - tlp) rail / Vo (vs_kt);
  - rel_k in [-68, 68]: phase 1's relative cap in a rising transient, rel_eff = clamp(rel - (rel_k max(rail - rss, 0))
    >> 16, 64, 1023) (Q8 codes; -+0.25 at 4.8 V). > 0 = fewer volt-seconds in the transient (the handoff's idea);
  - kv in [0, 1.0]: phases 2-4 Ton x (1 + kv lo_add_prev / T0), T0 = 504 ns: their duty kept while the period stretches.
  Grid: gr 0, .25, .5, .625, .75, .875, 1, 1.125, 1.25; gt 0, .25, .5, .75, 1, 1.25; rel_k -68, -34, 0, 34, 68;
  kv 0, .25, .5, .75, 1 (1350 points). Rows: l_p48_1us, l_p48_5us, s_p62, l_m48_1us at L0; l_p48_1us at L x 0.7 / 1.3.
- **Why GP-BO for the cosim stage, not:** RL (A148: features downstream of the action close a loop; a 4-parameter static
  law needs no policy); a cosim grid (>= 4^4 x 4 rows = 1000 runs); CMA-ES / Nelder-Mead (many evaluations, no noise
  model, cannot start from D63's map); gradients (none, and the peak has 2-7 A step-phase noise, A129). GP-BO fits few
  parameters, expensive noisy evaluations, and takes D63 as the prior mean (GP on cosim - D63).
- What BO does and does not show: it only searches. Cross-checks: D63 against cosim at the BO points (independent
  models), and the optimum against the charge-balance argument below. It validates nothing by itself.
- Charge balance (registered reasoning): rail 1's excess drains only through net charge into C1, q1 - q2 per period
  (phase 1's high-side charge minus phase 2's). With every valley held and volt-seconds balanced at a common period,
  q_k ~ (Vo T / rail_k)(v + (Vo T / 2L)(1 - Vo / rail_k)) falls with rail_k, so q1 < q2: rail 1 recovers only if phase 1's
  valley rises (hard turn-ons) or phases 2-4 carry less (deeper valleys in a stretched period = an output current deficit,
  a Vo dip). Keeping phase-1 V_DS low therefore costs Vo for as long as the ladder takes.
- Not tested: other designs, multi-module, L corners with loop + edges, start-up (A145's 37.3 V kept).

## 2. Criteria
1. Block, held out: from each A148 loop + edge record's own B and turn-on V_DS, the run's max SH2-4 (after 150 us)
   within +-1.0 V on all 10 records.
2. D63 candidate: a grid point with, in D63 (50 pH / 72 A/ns block): max SH <= 40.5 V after the step on l_p48_1us and
   l_p48_5us (D63 ran 0.4 V high on average at 50 pH in the probes); peak <= 200 A on all 6 rows; late fires <= the frozen
   design's on each row; no divergence with (gr, gt, kv) x 1.25 on l_p48_1us / l_p48_5us (D63 diverged at g 1.25 where
   the cosim broke at 1.0); Vo within 5 mV of 1 V from 27.6 us after the step on l_p48_1us (the frozen cosim's 7.6 us +
   20 us; D63's Vo excursions in this regime are 2-3x smaller than the cosim's, so this is a necessary condition only).
3. Cosim (only if 2 passes), best BO point: 50 pH loop + edge l_p48_1us whole-run max V_DS <= 40 V; peak <= 200 A on
   l_p48_1us at L x 0.7 / 1 / 1.3, l_p48_5us and s_p62 at L0; Vo back within 1 % <= 27.6 us (l_p48_1us, L0); late fires
   <= A143's on each row; options off bit-identical with tb tests; every run from committed code.

## 3. Predictions (not criteria)
- Probes seen (D63 SH50 l_p48_1us): frozen 41.7, (gr, gt) 0.75 41.6, 1.0 40.3 V (cosim 41.8 / 41.2 / 39.3); rel_k 68 / 100
  41.9 / 42.4 V with rail 1 17.4-18.4 V and phases 2-4 hard; a phase-2 Ton cut raised SH; kv 1 cut the Vo dip
  (-16 -> -7 mV) but raised the rebound (+12 -> +19 mV), rail 1 and the peak (211 A); (1, 1, -34, 0) 39.1 V, 204 A.
- Criterion 1 passes (provisional table: 41.2 / 39.3 / 46.5 / 47.4 V within ~0.6 V).
- Criterion 2 fails: every point with SH <= 40.5 V has gr >= 0.9 and misses the Vo condition (the stretch-end rebound);
  rel_k > 0 never helps; kv shifts the dip into the rebound.
- If the cosim stage is reached: Vo back >= 35 us at every point with V_DS <= 40 V.
- D63 end-to-end misses the cosim's g 1.0 hard turn-ons on phases 3-4 (12.9 / 15.2 V; D63 <= 6.3 V) - a known gap.

## 4. Decision rule
- 2 fails -> stop at D63, no RTL or cosim: the 50 pH / 2 ns rising step cannot be held <= 40 V by this controller's
  timing; the package spec stays hardware-bound (< 50 pH or more damping). The grid's Pareto front (SH vs Vo) is the
  trade-off record.
- 2 passes -> RTL options for the needed terms (default off, bit-identical, tb tests), GP-BO as in sec. 1 (8 starting
  points from D63's candidates, batches of 5, <= 6 rounds; constrained EI; GPs on cosim - D63 for SH (block on the
  loop-free cosim's B and V_DS), peak and Vo back). 3 passes -> candidate offered to the user (not adopted by default);
  3 fails -> same conclusion as above, with cosim evidence.
