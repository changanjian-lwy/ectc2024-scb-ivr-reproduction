# A150 - constrained GP-BO of the phase-1 edge law (gr, gt): 50 pH switch <= 40 V, Vo as the price (RESULTS)
Boundary: 9524dea (addendum 67d7c5e, before confirmation). Records: release records-a150 (125 runs). Outputs:
a150_bo.json (BO state: per-batch models, forecasts made before each run), a150_summary.json.

## 0. Verdict
- **FAIL as registered (criterion 3), so counted as no.** No (gr, gt) in A148's law holds the 50 pH / 72 A/ns switch
  <= 40 V without breaking the 200 A limit elsewhere, even with the Vo spec relaxed. The package stays hardware-bound.
- **The BO did find the band its five rows allow.** 16 cosim points (4 batches x 4, 5 runs each) give gr 0.675-0.725,
  gt 0.175-0.35; P(feasible) > 0.5 on 2.2 % of [0, 1.25]^2. At the candidate (0.675, 0.25), three step positions give
  V50 39.85-39.87 V and peaks <= 197.3 A.
- **The law excites A143's dt_pred oscillation on rows the search did not watch.**
  - +4.8 V at 2 / 3 / 4 us: 224.1 / 275.1 / 203.1 A (frozen 177.2 / 176.1 / 176.8 A).
  - l_p48_5us at L x 1.3: 241.7 A.
  - 5-18 NEW oracle events on each of these rows.
  - The post hoc largest-margin point (0.725, 0.35) fails the same rows, and also -4.8 V / 1 us (211.8 A), so the
    failure does not hinge on the tie-break.
- **What it would have cost** (candidate vs frozen, L x 1 / 0.7 / 1.3):
  - Vo back within 1 %: 40.9 / 30.7 / 52.2 us (frozen 7.6 / 14.9 / 8.7).
  - Vo dip: -28 / -20 / -38 mV (frozen -12 / -10 / -13).
  - Post-step peaks: +10 / +12 / +3 A.
  - V_DS: 41.8 -> 39.85 V.
  - At L x 1.3 this already exceeds A149's scenario (~45 us / +-3.5 %).
- **There is no cheap middle point.** Already at gr 0.45, where V_DS is still 41.0 V, Vo back reaches 39-48 us. The 1 %
  band is a step, as A149's charge balance predicts.
- **ML lesson.** The optimiser settled on the edge of the one oscillation row it was given, and the oscillation moved to
  neighbouring slews and to L x 1.3. When a constraint stands for a family of rows (slews x L), it must be measured on the
  family's worst member. Otherwise the optimum lands on an unmeasured failure (compare A126's reward gaming).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | pre-run forecasts within +-2 sd >= 70 % | PASS 36/48 (V50 14/16, PK1 11/16, PK5 11/16); batch 1 PK1 over-confident, z -1.3..-8 (D63 corner prior) |
| 2 | feasible point | PASS: (0.675, 0.25) 39.85 V / PK1 196.4 / PK5 189.3 A; (0.725, 0.35); (0.7, 0.175) |
| 3 | confirmation | FAIL: step positions pass; slews 2 / 3 / 4 us 224.1 / 275.1 / 203.1 A and l_p48_5us L x 1.3 241.7 A, NEW 5-18 |
| 4 | steady state | PASS: Vo +0.02 mV, phase-1 V_on 3.93 V, peak 143.97 A, identical to frozen |

## 2. Cross-checks
- **Trade-off line** (per unit gain, at the candidate):
  - gr: dV50 -8.2 V, dPK5 +59 A. It pulls V_DS down and provokes the 5 us row.
  - gt: dV50 +3.1 V, dPK5 -56 A. It calms the 5 us row and pushes V_DS up.
  - The band is where the two just balance, as predicted.
- **A143 signature.** All failing confirmation rows and all 7 oscillating 5 us rows have phase 2-4 low-offs >= 0 A
  (lo234_pos 1-103). Calm rows show 0, except three boundary points with 1-2 (an early warning). As predicted.
- **D63 as prior mean.** It wins LOO for V50 (0.31 vs 0.44 V) but loses for PK1 (60 vs 13.5 A): D63's corners are
  6-8 A high at gr < 0.5, and it misses blow-ups. Half right. D63 did call the divergence at (0, 1.25): cosim 260 A, 46 NEW.
- **SH-block proxy bias:** -0.37..+1.41 V over 21 points (predicted 0..+1.5 V). Measuring V50 directly was needed.
- **Predictions:**
  - C2: passed (I gave it 40 %).
  - Location: wrong. Predicted gr 0.35-0.6; it is 0.675-0.725.
  - V50: right. Predicted 39.5-40.0 V; 39.46-39.85 V.
  - PK1: right. Predicted 195-200 A; 196.4-197.7 A.
  - Vo back: wrong. Predicted 15-45 us; worst-L 52.2 us.
  - C3: failed (I gave it 40 %), but on unwatched rows, not on step-position noise.

## 3. Limits
- One law family, single module. L corners loop-free. Slews and corners checked only in confirmation.
- A BO over the slew family would need about 3x the runs per point. Not worth it: even with the oscillation fixed (an RTL
  dt_pred fall limit, A143's open candidate), the L x 1.3 Vo price exceeds the scenario that motivated this study.
