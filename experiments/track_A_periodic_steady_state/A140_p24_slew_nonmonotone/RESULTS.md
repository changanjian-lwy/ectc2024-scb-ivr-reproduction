# A140 - why the post-step peak is not monotone in line-step slew (RESULTS)
Boundary: f68b5f7. Records: `cosim/run_*.json` (36, committed in cc67b67); reused A137
`run_s070_l_p48_{1,5}us` and A138 `vf05`, A139 `vf04`, `ur01` (GitHub release records-a138-a139). `a140_predictions.json`, `a140_summary.json` (`a140_analyze.py`),
D63 scans `a140_d63_s{1,2,3}.json` (`a140_d63.py`). Conditions: adopted single-module design (C10 template), Cs x 1.0,
line step at 1000 us (+0.125 / 0.25 / 0.375 us for the position repeats), peak = max high-side turn-off current after it.

## 0. Verdict
1. **The falling bump is the slope gate (confirmed on -4.8 V, nominal L).** Gate open at 1 / 2 us: 173.5 / 162.2 A;
   gate shut from 2.5 us: 191.6 / 187.3 / 179.7 / 172.2 A at 2.5 / 3 / 4 / 5.1 us. Peaks are phase 4, smooth (within
   0.3-6 A of the neighbouring periods), set by phase 4's turn-on current: 33-47 A with the gate open, 57-68 A shut.
   D63 placed the edge correctly (between 2.0 and 2.5 us).
2. **gth 50 is not a fix.** -4.8 V becomes flat (173.5-175.6 A), but -6.4 V rises to 207.6-214.1 A at 2.4-5.7 us
   (B: 203.1 / 179.4 / 205.4 A at 2.4 / 3.1 / 4.0 us) and -8 V / 10 us at L x 1.3 goes 179.3 -> 198.1 A. On -6.4 V the
   peak grows the earlier the gate opens (opened 2.31 us after the step: 179.4 A; 1.47 us: 203.1 A; 0.58-1.07 us:
   ~214 A; never: 205.4 A): the falling term is not monotone in its own onset, so no single gth suits every |dv|.
   D63 missed this (predicted 179-186 A for G on -6.4 V).
3. **Most of the rising "slower is worse" is a controller event, not a slew trend.** In 9 of 9 B rising runs at
   >= 10 us the peak period follows a duplicate phase-1 turn-on: two low-side turn-offs ~5-6 ns apart, then two
   high-side turn-ons ~5-6 ns apart; the Ton timer restarts at the second, so the on-time grows ~6 ns (28.7 -> 34.9 ns,
   x 6.3 A/ns = +38 A). Duplicates: none in the 100 us before any step, all on phase 1, 5-23 per L x 0.7 rising run
   with or without vff, 0-3 per falling run. Same signature as the l_p48_5us spike (C06 / C09 / C10) and A139's
   +14 A heavy tail.
4. **Without those periods the rising curve is mild:** L x 0.7, +4.8 V: 185.2 / 188.6 / 194.1 / 185.6-191.1 (four
   positions) / 179.3 A at 1 / 5 / 10 / 20 / 40 us (with them 213.4 A at 10 us, 192.1-208.9 A at 20 us). vff off:
   209.1 / 198.7 A at 5 / 20 us, so the cap lowers every slew, by less on slower ramps; D63's "plant-driven rise" is
   not what cosim shows. +8 V at L x 0.7 is a real window: 230.8 A at 20 us (210.1 without the duplicate period),
   203.7 A at 50 us (180.2).
5. **Decision (Section 4):** criterion 4 fails -> gth stays 100; the falling spec is written as windows (Section 2).
   Next: the duplicate turn-on (A141, RTL) - it changes the rising spec, removes up to +35 A here and the heavy tail.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | G rising run = A139 ur01 bit for bit | PASS (3342 sections) |
| 2 | falling worst run gate-shut, >= 10 A over the fastest open run | FAIL as registered: -4.8 V passes (+18.1 A); -6.4 V's fastest open run is itself 203.1 A (+2.2 A); post hoc shut 4.0 us 205.4 vs open 3.1 us 179.4 A |
| 3 | G rise with slower slew <= 3 A | PASS (2.1 A on -4.8 V, 0.3 A on -6.4 V - at 208-214 A) |
| 4 | G slow falls <= 190 A, envelope <= B | FAIL: L x 1.3 -8 V 198.1 / 192.4 A at 10 / 12.1 us; -6.4 V 214.1 vs 205.4 A |
| 5 | rise from the plant (O and B +5 A) | FAIL: O 20 us 198.7 < 5 us 209.1 A; B median 202.6 >= 193.6 A comes from Verdict 3 |

## 2. Spec at nominal L / Cs (replaces A130's minimum-slew wording; A139's 95 % table covers the L / Cs corners)
- Falling, |dv| <= 4.8 V: allowed <= 2 us (gate opens; 162-174 A) and >= 5.1 us (A139 certified); 2.3-5 us is a
  forbidden window (180-192 A, no 95 % margin). The window moves to slower slews with L (D63: ~3 us at L x 1.1) and
  to faster ones at L x 0.7 (183.1 A shut at 2.4 us), so the fast band needs a corner check before use.
- Falling, 6.4-8 V: no fast band (203-214 A at 2.4-4 us); >= A139's minimum (6.7-11.6 us by corner).
- Rising at L x 0.7: +4.8 V 10-20 us forbidden while the duplicate turn-on exists (> 200 A in 3 of 5 runs); +8 V
  forbidden up to >= 50 us (A138: > 200 A at every slew 1.2-18.9 us; 230.8 A at 20 us, 203.7 A at 50 us).

## 3. Limits
- The duplicate turn-on is read from event logs (3 runs in full, a detector on 41); its RTL cause is not located.
- Spec edges are from 3-6 runs per line (+-0.5 us); corner edges from D63, whose falling error is +7.8 +- 19.6 A
  and which has no duplicate turn-on and missed the open-gate -6.4 V peaks by ~30 A.
