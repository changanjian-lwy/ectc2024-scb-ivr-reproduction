# A148 - phase 1's low-side timing through line and load steps: volt-second law against RL (RESULTS)
Boundary: 8110ed0. Code 416a3ad (RTL, D63 floor_keeps_dlo, cfgs); post hoc 6cf8c49 / 78bad48; oracle + analysis e0ec98f.
Records: release records-a148 (26 runs). Outputs: a148_von_check, a148_grid, a148_eval, a148_distill, a148_posthoc_ff,
a148_summary (.json).

## 0. Verdict
- **FAIL as registered (3, 4 pass; 5, 6, 7 fail): phase 1's low-side timing cannot remove the rising-step hard
  turn-on; the package spec stays step-bound. Not adopted.**
- Why (SCB): rail 1 takes the whole step. To keep its valley, phase 1 needs ~22 % more volt-seconds, so its low-side
  time must grow. With one common period that stretches all four phases (504 -> ~600 ns). The voltage loop lags: Vo
  -20..-25 mV, back within 1 % after 42 us instead of 8. Peaks rise (L x 1.3: 201.2 A). At g 1.0 the hard turn-ons
  move to phases 3-4. Even with ZVS, SH2's blocking voltage (rails 1 + 2) rises ~5 V with the step itself.
- Cosim at g 0.75 (the registered candidate), +4.8 V / 1 us:
  - phase-1 turn-on V_DS 19.0 -> 16.8 V without a loop, 15.4 V at 50 pH;
  - largest switch V_DS 41.8 -> 41.2 V (50 pH) and 51.0 -> 46.5 V (100 pH), against 37.3 / 44.4 V at start-up.
- **Load steps work.** s_p62: every phase 11.5-12.2 -> 6.9-7.2 V. Hard turn-ons 136 -> 34 (L x 0.7 / 1.3: 119 / 196
  -> 32 / 30). With loop + edges 36.1 -> 32.5 V (50 pH), 38.7 -> 32.2 V (100 pH). Cost: +2 late fires at L x 0.7,
  Vo back +4..6 us.
- **Falling steps do not bind the package** (first measured). -4.8 V / 1 us reaches 36.9 V (50 pH) and 42.6 V
  (100 pH), below start-up, although phases 2-4 still hard-turn on at 14-15 V.
- **RL neither found the law nor beat it.**
  - The 6 registered policies and 3 post hoc feed-forward policies cost 120-271, against the law's 108 / 179.
  - 8 of 9 fail the steady check, sitting at +200..300 ns in steady state: phase 1 on the floor every period. The
    ninth (post hoc s0) passes it but fails the long-horizon check. That is the comparator regime that oscillates in A142's cosim, which D63 does not model.
  - Cause: every feature downstream of the action (valley report, hard bit, even the loop's Ton) closes a loop. The
    anchor zeroes the action only where the features are zero, not in closed loop.
  - Distilled rules: R^2 < 0; correlation with the law <= 0.04.

## 1. Model work
- D63 V_DS block (von_table, D57's free node to t_tr): phase 1 p90 0.01 V (hard turn-ons 0.42 V) over 193 k cosim
  turn-ons; phases 2-4 read 0.46 V low.
- **Found mid-run: D63's floor mode rewrote dlo with the floor's interval; scb_phase keeps it** (floor_keeps_dlo).
  - With the fix D63 matches the cosim on falling steps: phase 1 2.9-3.9 V (cosim 3.1-4.1 V); phases 2-4 13.7-15.1 V
    (13.6-15.3 V).
  - The grid's B0 was rerun with it (163.5 -> 131.0). Laws and RL always kept dlo.
- D63 against the cosim at g 0.75: phase-1 V_DS 14.0 / 12.5 V against 16.8 / 13.7 V (1 / 5 us); s_p62 7.3 / 7.2 V.
  The law's gain margin: D63 diverges at g 1.25; the cosim breaks at g 1.0 on the 5 us row (233.7 A, 22 late fires).
- a142_oracles has a zero-voltage class "zvs" (turn-on V_DS > 6 V in mode P, with the previous low-off current). It
  is reported apart from the events. Frozen design: 134-138 per step row, 0 on n0.

## 2. Criteria
| # | criterion | result |
|---|---|---|
| 1 | RTL candidate | vs g 0.75: cost 108.0 against the frozen 131.0; the distilled rules fail both checks |
| 2 | RL converges / beats | neither. R^2(vs) -5.9 / -5.3, correlation -0.13 / 0.01. Cost 120.5-133.1 vs 108.0 (w_vo 1) and 221.4-271.1 vs 179.2 (w_vo 4). Steady check failed |
| 3 | identity | PASS: option off = A143 in every field; tb 88 tests; every run from committed code |
| 4 | steady (n0) | PASS: Vo -0.08 vs 0.02 mV, peak 144.0 = 144.0 A, phase-1 V_DS 3.93 = 3.93 V |
| 5 | V_DS <= 12 V / 7 V | FAIL: l_p48_1us 16.8 V, l_p48_5us 13.7 V; s_p62 7.2 V |
| 6 | no regression | FAIL: l_p48_1us back 41.6 vs 7.6 us, 2 late fires (0 before); L x 1.3 201.2 A; L x 0.7 late 7 vs 2 (s_p62 4 vs 2) |
| 7 | loop + edges | FAIL: post-step 41.2 / 46.5 V > start-up 37.3 / 44.4 V; 50 pH whole run 41.2 V > 40 V |

Predictions:
- g 0.75 best: right. RL close to the law: wrong (worse, and not the law).
- Cosim: l_p48_1us 10-12 V wrong (16.8 V); peak 190-198 A right (190.9 A); s_p62 4-6 V close (7.2 V); 50 pH
  35-38 V wrong (41.2 V); falling 45-55 V at 100 pH wrong (42.6 V).
- Post hoc g 1.0: phase 1 11.3 V, but phases 3-4 12.9 / 15.2 V. The 5 us row reaches 233.7 A with 22 late fires.
  Switch V_DS 39.3 V (50 pH), 47.4 V (100 pH). s_p62 4.6-5.3 V.

## 3. Decision and limits
- Frozen controller unchanged. Below 100 pH, start-up and the rising line step bind V_DS; a 5 us rise is as bad as
  1 us (17.4 V), so a slew spec does not help.
- Open knobs (A149 candidates):
  - the Ton term alone (vs_kt, the load-step fix without the line-step stretch);
  - phase 1's Ton during the transient (fewer volt-seconds, slower ladder recovery);
  - phases 2-4 (slots or Ton).
- Limits:
  - single module, one design;
  - the cost weights are ours, with a tight-Vo scenario;
  - D63 lacks the comparator regime the RL policies exploited.
