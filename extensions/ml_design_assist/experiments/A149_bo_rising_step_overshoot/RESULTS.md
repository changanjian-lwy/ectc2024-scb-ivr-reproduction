# A149 - rising-step switch overshoot: D63's SH_k block, a stable law family, D63 grid, post hoc cosim (RESULTS)
Boundary: 6a34924 (post hoc addendum 537fa4a, before any cosim). Code 6a34924, analysis 0aaa82f. Records: release
records-a149 (11 runs). Outputs: a149_sh_table, a149_shblock, a149_grid, a149_summary (.json).

## 0. Verdict
- **FAIL as registered (criteria 1 and 2 fail; 3 not reached), so the stop rule applies: no new RTL, and GP-BO was not run.**
- **Post hoc, control can hold the switch <= 40 V at 50 pH, but only at a cost that rules out adoption.** The rail term
  alone (vs_kt 0) with gr 1.0 / 0.75 gives a whole-run max of 38.4 / 38.8 V (start-up 37.3 V); at 100 pH it is 44.4 V.
  The cost, against the frozen design:
  - Vo back within 1 % after 42.5 / 42.2 us instead of 7.6 us, with a -31 mV dip;
  - +4.8 V / 5 us oscillates: 325 / 223 A, 64 / 5 new oracle events, 230 / 17 late fires;
  - L x 0.7 / 1.3 peaks 199-202 A.
- **Why Vo cannot be had (SCB charge balance, confirmed in D63's trace):**
  - Rail 1's excess drains only through the net charge into C1 (q1 - q2).
  - If phase 1's valley is held, the ladder stops: in D63 rail 1 stays at 16.8 V for 8 us. It then drains only as
    phases 2-4 dig deep valleys (-40..-50 A) in the stretched period, which is an output-current deficit. Vo dips,
    then rebounds when the stretch ends.
  - Every ZVS-holding law measured needs 41.6-42.5 us: A148 g 0.75 / 1.0, A149 gr 0.75 / 1.0.
- **The 5 us oscillation is A143's mechanism.** The deep phase 2-4 valleys make dt_pred fall and the phases swing with
  Cs. D63 has no dt_pred block and predicts 196 A.
- **The handoff's transient-cap idea works against the goal.** Fewer phase-1 volt-seconds starve the ladder: rail 1
  goes to 17.4-18.4 V, phases 2-4 turn on hard, and SH rises.
  The Ton term gt trades V_DS against the 5 us ramp: with gt 0.75, 41.2 V and 187.9 A (A148); with gt 0, 38.8 V and
  223 A.
- **Decision: the package spec stays hardware-bound (< 50 pH or stronger damping).** The control path would need two
  things: (a) a line-step Vo spec of about 45 us / +-3.5 % at +4.8 V / 1 us, which is a spec decision; (b) a fix for
  the 5 us oscillation. Given (a), (b) is a 2-D (gr, gt) cosim search, for which GP-BO is the right tool.

## 1. Model work
- **SH block** (A144 / A145 calibration, 72 A/ns):
  - 50 pH: f = 4.7 / 9.2 / 11.9 / 12.6 V at 4 / 8 / 12 / 16 V. It saturates because the turn-on's V_DS fall (~sqrt(dV))
    is long against the 50 pH ring.
  - 100 pH: f = 4.4 / 10.0 / 15.4 / 19.7 V.
  - Held out: rising rows +0.15..+0.68 V. Falling rows -0.56..-1.21 V: no falling rows in the calibration, and the max
    over many windows exceeds the bin median.
- **D63 against the post hoc cosim (gr 1.0 / 0.75):**
  - SH 40.3 / 40.5 V against 38.4 / 38.8 V, so D63 is 1.7-1.9 V conservative.
  - The block on the loop-free records' own B and V_DS: 39.0 / 40.2 V.
  - Phase-1 V_DS within 1.4 V on the 1 us rows.
  - Peaks: L0 199 / 196 against 196.5 / 193.1 A; L x 1.3 205.7 against 200.8 A; L x 0.7 202 against 202 / 199 A.
  - 5 us row: blind (196 A against 325 / 223 A).
  - Vo excursions in D63 are 2-3x too small (the dip and the stretch-end rebound have the right shape).
- **D63 grid:** 243 of 1350 points have SH <= 40.5 V. All of them have gr >= 0.75, and the L x 1.3 peak saturates at
  205.7 A for every gr >= 0.75. kv halves the dip but raises the rebound, rail 1 and the peak; kv 1.5 diverges.

## 2. Criteria
| # | criterion | result |
|---|---|---|
| 1 | block held out, +-1 V | FAIL: 9 of 10 within; v075_e72_l100_l_m48_1us -1.21 V (a falling row) |
| 2 | D63 candidate | FAIL: all 243 SH-feasible points > 200 A at L x 1.3 / 0.7 (best 205.7 A); 116 also miss the Vo condition |
| 3 | cosim | not reached. Post hoc conditions: V_DS PASS (38.4 / 38.8 V); peaks FAIL (325 / 223 A at 5 us, 202 / 200.8 A at the corners); Vo FAIL (42.5 / 42.2 us); late FAIL |

Predictions:
- Criterion 1 passes: wrong (1.21 V on a falling row).
- Criterion 2 fails: right, but the binding constraint is the corner peak, not Vo.
- gr 1.0 at 50 pH 39-40 V: 38.4 V. At 100 pH 42-44 V: 44.4 V.
- Peaks L0 194-198 A: 196.5 A, right. L x 1.3 199-203 A: 200.8 A, right.
- No break at 5 us: **wrong** (325 A).
- Vo back >= 35 us: right (42.5 us).
- gr 0.75 at 40.5-41.5 V: **wrong** (38.8 V). The Ton term, not the rail term, held A148's V_DS up.

## 3. Limits
- Single module, one design, two post hoc points; the L corners ran without loop and edges.
- The Vo criterion is ours (frozen + 20 us); the load's real line-step tolerance is not known.
- GP-BO, the planned ML part, did not run (stop rule). The post hoc cosim answered the question at lower cost.
