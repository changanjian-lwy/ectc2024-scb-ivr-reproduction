# A179 - the interlock release time at the slow corner, with step-position scatter (RESULTS)
Boundary: 0b2280a (analysis c36f4c5, stage 2 495dad9). Records: release records-a179 (25 run_*.json, run logs).
Analysis: a179_analyze.py -> a179_summary.json. All runs from committed code, plant V5, slow corner (ss).

## 0. Verdict
- **FAIL as registered.** Criterion 3: 1.4 ns fails on R1 (-8 V / 10 us) and R2 (load step); stage 2 ran R2 at
  1.0 ns, which also fails on R2. R1 passes at 0.8 and 1.0 ns; four modules pass at 1.4 ns.
- **The shortened window holds (criteria 1 and 2, 22 of 22 checks).** Every 0.5 / 1.4 ns run equals A173 / A177
  section by section up to its step (1063 sections single, all modules for four), and every old-window run lies
  inside the new positions' range. Settled ss rows can step at 500 us: single runs 61-72 min against A173's
  92-117 min, four modules 4.1 h at 10 jobs.
- **R1 sets the number: release <= 1.0 ns.** Post-step late fires over three positions (old window in brackets):
  0.5 ns 21 / 12 / 15 (9), 0.8 ns 21 / 9 / 10, 1.0 ns 12 / 32 / 22, 1.4 ns 12 / **51** / 15 (**47**). At 1.4 ns two
  of four positions reach ~50 against <= 21 at 0.5 ns: A177's -8 V miss is a real effect of the delay, at some step
  positions. Limit 1.5 x 21 + 5 = 36.5.
- **R2's miss is the spike count, and it does not trend.** All of R2's post-step NEW events are one-period
  spikes 10-18 A above their neighbours, 12.6-34.1 us after the step; no post-step late fires at any delay. NEW over
  three positions: 0.5 ns 19 / 16 / 19, 1.0 ns 13 / 21 / **24**, 1.4 ns **27** / 9 / 7 (means 18 / 19 / 14). Peaks 182.8-184.5 A
  at every delay. The registered tolerance (+2 on the 0.5 ns worst) is narrower than the scatter at >= 1.0 ns.
- **Four modules at 1.4 ns pass.** NEW 17 / 15 (0.5 ns: 22 / 5), late after the step 487 / 417 (425 / 439), peaks
  182.3 / 183.2 A (180.0 / 181.5). A177's four-module miss (NEW 13 vs 8) was step-position scatter.
- No delay changed a peak (R1 169.0-170.9 A, R2 182.8-184.5, four modules 180.0-183.2) or V_DS (<= 32.9 V);
  0 shoot-throughs; all COMPLETED.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | sections before the step equal the old-window run (16 runs) | PASS 16 / 16 |
| 2 | old-window run inside the new range + tolerances (6 row / delay pairs) | PASS 6 / 6 |
| 3 | R1 at 0.8 / 1.0 / 1.4 ns | PASS / PASS / **FAIL** (late after the step 51 vs 36.5) |
| 3 | R2 at 1.0 / 1.4 ns | **FAIL** (NEW 24 vs 21) / **FAIL** (NEW 27 vs 21) |
| 3 | four modules at 1.4 ns | PASS |

Pre-step late fires (start-up settling, identical on every row and position at a given delay): 72 / 79 / 77 / 83 at
0.5 / 0.8 / 1.0 / 1.4 ns. Predictions: criteria 1-2 hold - right; R1 at 0.5 ns >= 30 at some position - wrong (12-21);
1.4 ns passes R2 - wrong, passes four modules - right, fails R1 so 1.0 ns - right; pre-step 0.8 / 1.0 within 72-83 -
right (79, 77).

## 2. Decision (BOUNDARY Section 4)
- The spec reads "release <= 1.0 ns at the slow corner" for the -8 V row's timing. The per-board comparator reference
  (~1.4 ns, A173's estimate) does not meet it at every step position.
- R2 at 1.0 ns failed too, which the rule did not cover. Not run further: its spike count scatters 7-27 at >= 1.0 ns
  without a trend, so no single release time can be read from it at a +2 tolerance. Named open; peaks unchanged.
- Four modules do not set the bound.

## 3. Limits
- Three step positions per row and delay; R1's 1.4 ns effect rests on 2 of 4 positions (51, 47).
- The release time is modelled as a fixed delay after the complement stops; a comparator's offset and noise are not.
- The 500 us step was checked on these ss rows only; ff is not settled there (0.6 mV ADC limit cycle at 400-500 us),
  other corners need the same check first.
