# A142 - random-stimulus test of the adopted single-module RTL (RESULTS)
Boundary: ccb9965 (post hoc cfgs, not registered: e6d9a15, 7ad9e9f, a0cf9bf). Records: a142_inputs.json,
a142_summary.json (`a142_analyze.py`), a142_posthoc.json (`--posthoc`); raw records (141 runs) in GitHub release
records-a142. Log 14:04-15:09 (121 runs, 10 jobs) + 20 post hoc runs.

## 0. Verdict
- **Fail, 4/5 (criterion 3).** One of 120 draws, z104 (S: +7.89 V over 3.95 us at 295 us, L x 1.10, Cs x 0.89),
  oscillates for ~50 us: 351 A, Vo 0.93-1.08 V (34 us outside 2 %), 229 late fires, 27 spikes / 8 order hits; Vo back within
  1 % by +76 us. The 96 L / B / D draws (steps in timed mode) and the other 23 S draws: 0 NEW.
- **Not an arbitration window error, a mode defect.** Every edge is in its intended window. In the mode-P comparator
  phase (from the handover at 144 us to the timed switch at 520-810 us) phase 1's low-off waits for its comparator, so
  phase 1's valley holds at -15.6 A and the period stretches (556 -> 819 ns). The relative cap holds phase 1's Ton at
  33 ns on a 20 V rail; the loop drives phases 2-4 to 57-71 ns. Phases 2-4 lose their valleys (low-offs up to +96 A),
  currents ratchet, Vo swings. The same step at 1000 us (timed): 196 A, period <= 653 ns, the error goes to phase 1's
  valley (+13-18 A) instead.
- **It reaches inside A139's certified envelope** (nominal L / Cs: rising +4.8 V certified from 1.0 us): +4.8 V at
  3 / 4 / 5 / 7 us in the comparator phase gives 196 / 254 / 247 / 195 A (L x 1.3, 4 us: 245 A). +5.6 / +6.4 V at 4 us:
  386 / 388 A. The worst slew is ~4-5 us; +6.4 V at 1 us gives 209 A and at 20 us 195 A. Driver mismatch and L / Cs
  corners are not needed (P4, P5). Without vff the step gives one 377 A peak and 6 us outside 2 % (P1).
- **Decision:** the single-module controller is not frozen. A143 = a comparator-phase fix; C13 (four modules) waits.
  Regression rows: z104, R_dv4.8_s4_L100, R_dv4.8_s5_L100, Q_dv6.4_s4, with P2 as the timed reference.
- **Deviation from the registered rule:** Section 4 split a trace into "arbitration defect -> A143" or "plant
  transient, edges in their windows -> known class, freeze". This is neither: the edges are in their windows, but the
  mode's control law breaks the certified spec. Freezing would ship a 254 A row inside the envelope, so this result
  takes the A143 branch.
- Everything else passed: 0 floor-first duplicates, 0 overlaps / alternation hits, every run settles, and I0 is bit
  identical to A141. Only known classes otherwise.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | floor-first duplicates 0 | pass: 0 in 121 runs |
| 2 | overlaps 0, alternation 0 | pass |
| 3 | NEW hits 0 | **fail**: z104 (27 spikes, 8 order); 0 in the other 119 draws |
| 4 | settles: Vo within 1 %, ladder <= 0.03 | pass: ladder <= 0.019, abs(Vo_end - 1 V) <= 0.02 %, all COMPLETED |
| 5 | I0 = A141 F_s100_l_p48_1us | pass: every list identical, 181.76 A |

Predictions: K1 in 4 runs (3 %, predicted 5-20 %), next peak within 1.4 A (predicted 2 A). K2 0 (z117 none). K3 1 run
(z029, no peak effect). K4 5 runs (z054 / z060 of the six predicted, plus z002 z108 z119). L / B / D peak <= 200 A
in 97 % (predicted >= 85 %); max 245 A z069 (-7.5 V / 3.2 us + load, outside A139). Unexplained spikes in falling
rows: 0 (predicted ~1).

## 2. Limits
- The P / Q / R rows (20) are post hoc one-factor runs, not registered. The slew window and the threshold (+4.0 V at
  4 us: 195 A) each rest on single runs. Noise floor 1-5 A (A139) vs effects of 50-190 A.
- 12 of the 24 S draws stepped in the comparator phase. Only z104 had a rising step with a 2-6 us slew; the other
  four rising ones (1.1-1.3 us or 18 us) are clean. One module only.
- The mechanism is read from the records (period, valleys, Ton per phase), not yet from a model. D63's cmp mode with
  a135's VffRTL cap is the cheap check for A143.

## 3. Post hoc trace (a142_posthoc.json; step at 295 us unless stated; T1 = longest phase-1 period)
| row | change from z104 | peak A | out 2 % us | T1 ns |
|---|---|---|---|---|
| z104 | - | 351 | 34.3 | 819 |
| P2 / P3 | step at 1000 us (timed) / 600 us (comparator) | 196 / 350 | 0 / 34.3 | 653 / 814 |
| P1 | no vff | 377 | 6.0 | 882 |
| P4 / P5 | nominal driver / nominal L, Cs | 361 / 382 | 32.4 / 35.3 | 823 / 799 |
| P6 / P8 / P7 | +4.8 V at 2.4 us / at 1 us / +7.89 V at 10 us | 192 / 192 / 280 | 4.0 / 4.5 / 23.3 | 702 / 703 / 771 |
| Q (nominal) | +6.4 V at 1 / 4 / 10 / 20 us; +5.6 V at 4 us | 209 / 388 / 228 / 195; 386 | 11.6 / 40.6 / 13.6 / 4.7; 36.9 | |
| R (nominal) | +4.8 V at 3 / 4 / 5 / 7 us; +4.0 V at 4 us | 196 / 254 / 247 / 195; 195 | 3.6 / 14.5 / 13.5 / 3.6; 3.6 | |
| R (4.8 V, 4 us) | L x 0.7 / L x 1.3 | 202 / 245 | 0.7 / 20.8 | 472 / 837 |
