# C11 - the four-module final design (vff seed 2) at L x 1.2 and 1.3 (RESULTS)
Boundary: 14cb7b0. Records: cosim/run_*.json (4); c11_summary.json.

## 0. Verdict
- **Pass, 5/5: the four-module final design holds L x 1.2 and 1.3, handover included.** Seed 2 removes C08's L x 1.2
  handover: l120_s_p62 rail 1 12.35 V (C08 l12q 17.2-17.3 V for 52 us), whole-run peak 178.8 A (212.8 A), late fires 0
  (54). The operating mode is C08's to the decimal: post-step 177.8 A, ladder 1.12 %, Vo 1.000.
- L x 1.2: m3n 148.3 A, 0 late fires, ladder 0.74 % (L0 0.61 %); l_p48_1us 188.0 A (post-step 186.1 A), 5 late fires,
  ladder 0.60 %.
- L x 1.3: s_p62 rail 1 12.75-12.87 V, 178.6 A, post-step 177.7 A, ladder 1.22 % (limit 1.43 %), 0 late fires.
- The seed (1136) sits below the steady need (~1450 at L x 1.2, ~1600 at 1.3), as on one module (A137 s130); the cap's
  low-pass catches up with no lock. Steps landed in the timed mode (master timed from 761.9 us / 813.1 us).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | rail 1 <= 13.5 V, <= 5 us above 13.3 V (every module) | pass (12.35-12.87 V, 0 us) |
| 2 | whole-run peak <= 200 A | pass (148.3-188.0 A) |
| 3 | no lock (A134's rule vs C10's row at L0) | pass (ladder 0.60-1.22 %, Vo 0.9998-1.0001) |
| 4 | l120_s_p62 post-step within 7 A of C08's l12q | pass (177.8 vs 177.8 A) |
| 5 | late fires <= 100, no overlap | pass (0-5) |
Predictions: rail 1 <= 13.0 V - right; whole-run 160-190 A - right but m3n lower (148.3 A); late fires below C08's 54
- right (0-5); ladder ~1.1 % / up to 1.3 % - right; post-step 175-182 A - right; l_p48_1us 180-195 A - right.

## 2. Limits
- Four rows, not C06's 18; L x 0.7-0.9 not run (mode S's fixed-Ton handover, the next line of work).
- Every module's L moved together; module-to-module L spread is C07's (floor on, L +5 %).
