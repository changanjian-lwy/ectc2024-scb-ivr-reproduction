# A160 - the oracle's K4 window under slow turn-ons (RESULTS)
Boundary: 199e576. Output: a160_scan.json (a160_scan.py; 660 local records, 580 with a step).

## 0. Verdict
- **FAIL as registered (criterion 3), so K4_US stays 1.0** and the slow-turn-on swing peaks stay documented exceptions.
- **A 2.0 us window would be safe by everything else:** it reclassifies 25 events in 13 runs, all "spike" events at
  ramp + 1.00-1.97 us, none above its run's post-step peak (criterion 2); the ten known swing peaks of A154 / A158 / A159
  all become K4 (criterion 1); every run with a mechanism-traced NEW flag keeps it (A142 z104 35 -> 33, A150 c12_slew3
  18 -> 17, A142's post hoc P / Q / R rows, A157 / A158's Q >= 100 and undamped rows). NEW runs 62 -> 54.
- **Criterion 3 fails on A151 on9_l100_l_p48_1us, and the criterion was wrong there:** its single NEW event is the same
  post-step swing peak (phase 1, 170.6 A, excess 18.8 A, at ramp + 1.0 us), not a traced mechanism. A151's RESULTS
  listed it as part of "9 A/ns is too slow"; that conclusion rests on the load-step Vo (+2.8 us) and the 150 pH line step
  (Vo outside 1 % for 44 us) alone. A151 RESULTS gets a post hoc note.
- Widening K4 is a user decision now (the registered rule kept it).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | the ten known swing peaks become K4 | PASS (8 runs cleared, incl. the four-module run's 4 events) |
| 2 | every other reclassified event a spike <= the run's post-step peak | PASS (15 more, ramp + 1.37-1.97 us) |
| 3 | no mechanism-traced NEW run loses its flag | FAIL: A151 on9_l100_l_p48_1us (1 -> 0), whose event is itself a swing peak |

## 2. Limits
- Only local records of A140-A159, C13, C14 and the ML folder's A14x-A15x; older experiments use other oracles.
