# A137 - restart the feed-forward's low-passes at mode P's entry (RESULTS)
Boundary: e79d2d0. Records: cosim/run_*.json (18), identity rerun in tmp/identity_a137/; a137_summary.json.

## 0. Verdict
- **Adopted by the user's decision (2026-10-04), against registered criterion 2** (fails at L x 0.7, where the counts
  are mode S's, see below). Adopted setting: A129's g125 + vff {rel_q8 320, rel_lp 1, seed 1}. The handover trace at
  L x 0.7 that the rule asked for is not done.
- At L0 and L x 1.3 the restart removes A136's handover regression and beats the original design: L0 m3n late fires
  11 (A136 107, A129's g125 5), m1n 1, start-up peaks 163-182 A (A136 191.5, g125 184); L x 1.3 m3n 0 (A136 173),
  m1n 0 (53), start-up 152-188 A (A136 200-206).
- At L x 0.7 nothing improves: m3n 54 (A136 50), m1n 38 (A136 16), start-up 202-217 A (unchanged). These are the
  absolute cap's numbers too (A134 fl070: m3n 54, m1n 31, start-up 216 A): mode S runs the fixed 35.5 ns Ton, whose
  ripple at L x 0.7 is 1 / 0.7 of L0's, so this handover is mode S's, not the cap's. Criterion 2 asked every row to
  beat A136's, which was too strict where A136 had no regression (post hoc reading; the same kind of slip as A134's
  threshold).
- Operating mode unchanged: post-step peaks within 3.6 A of A136's, no lock at any L.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | identity (A136 q100_m3n rerun), unit tests | pass; 78/78 |
| 2 | handover: m3n / m1n late <= 100 and below A136's; start-up <= A136's, <= 200 A at L0 | **fail** at L x 0.7 only (m3n 54 vs 50, m1n 38 vs 16); L0 and L x 1.3 pass with margin |
| 3 | post-step peaks within 7 A of A136's, no lock | pass (-3.6 to +1.9 A) |
Predictions: m3n near g125's 5 at L0 - 11; far below A136's elsewhere - yes at L x 1.3, no at L x 0.7; start-up
near 184 A at L0 - 163 A.

## 2. Limits
- The mode-S explanation at L x 0.7 is by the formula and the matching A134 counts, not by a handover trace.
- Six rows per L; the matrix's other rows and the four-module design (C08 ran A136's version) are not rerun.
