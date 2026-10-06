# A157 - the drive spec under weaker loop damping (RESULTS)
Boundary: 95c93bf. Records: release records-a157 (5 runs). Outputs: a157_summary.json (a157_analyze.py), a157_predictions.json.

## 0. Verdict
- **The loop needs damping; ring Q 15 and 30 are enough, an undamped loop fails in steady state whatever the drive.**
  By the registered rule the package spec adds **"loop ring Q <= 30"** (Q between 30 and undamped not measured).
- **Q 15 / 30 at S50 (50 pH, 36 / 72 A/ns):** V_DS 37.3 / 37.2 V (predicted 37.2 / 37.4; Q 7: 37.1), start-up 151-153 A,
  post-step 168-170 A, 0 late fires, 0 NEW, Vo inside 1 %. The harness's small Q offsets hold.
- **Undamped (S50, S100, 125 pH x 24 A/ns):** the valley tracking is lost from start-up on: 8600-8960 late fires spread
  over all four phases, V_DS 58-62 V at start-up and 62-65 V in steady state (whole run 64.8-69.4 V), 11-56 NEW events,
  post-step 196-206 A. A144 saw the same with instantaneous edges; the slow turn-on removes the hard-turn-on excitation
  but not the loop's own ring after every switching event, which the valley comparators then read.
- The harness predicted single-event peaks (38.7 / 37.2 / 44.6 V undamped); it cannot see the controller's breakdown.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | V_DS within +-1.5 V of the prediction | FAIL on the three undamped rows (64.8-69.4 V); Q 15 / 30 within 0.2 V |
| 2 | V_DS <= 40 V on q15 / q30 / q0 at S50 and q0 at S100 | FAIL on q0_s50, q0_s100; PASS at Q 15 / 30 |
| 3 | controller (A152's judge) on all 5 | FAIL on the three undamped rows; PASS at Q 15 / 30 |

## 2. Limits
- Q 15 and 30 on one point only (S50, l_p48_1us); the boundary between Q 30 and undamped is not located.
- The damper is an ideal parallel resistor across each loop inductance; a real package damps through copper and core
  losses whose Q is unknown (a question for Mihai).
