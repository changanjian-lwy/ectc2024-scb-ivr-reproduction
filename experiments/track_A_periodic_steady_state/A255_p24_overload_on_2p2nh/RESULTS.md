# A255 - a 125 % load step on the 2.2 nH boards, with and without the peak limit (RESULTS)
Boundary: 5a2dcaf. Plant V7, single module. Records: cosim/run_{h,l}_o125_*.json, 4 runs from 5a2dcaf
(cosim_sources_modified False; release records-a255). Analysis: a255_analyze.py -> a255_summary.json.

## 0. Verdict
- **c1 passes: the final configuration takes a 125 % load on the 2.2 nH boards.** The step is +62.5 A at 500 us.
  - N75: 182.0 A, Vo minimum 990.0 mV, ladder deviation 0.35 V, V_DS 27.9 V.
  - S75h: 185.6 A, 988.5 mV, 0.35 V, V_DS 30.9 V.
  - Vo is within 0.2 mV of 1 V in the last 20 us. This closes the gap: k_N0 was the only 125 % row before.
- **c2 fails on both boards: with the 110 A limit the ladder collapses, as on N0 (A254).**

  | board | fires | peak | Vo minimum | ladder deviation | rails at 620 us |
  |---|---|---|---|---|---|
  | N75 | 939 | 246.9 A | 731.3 mV | 12.6 V | 3.7 / 24.6 / 3.6 / 16.1 V |
  | S75h | 998 | 212.0 A | 636.7 mV | 14.3 V | 3.2 / 25.4 / 3.2 / 16.2 V |

  - N75: first fire at 508.6 us; the ladder is more than 1 V off from 556.0 us.
  - S75h: its 5 handover fires come at 135.4 us; the ladder is more than 1 V off from 548.6 us.
  - The pattern is N0's: rails 1 and 3 fall to about 3.5 V, and rail 2 rises to about 25 V.
- **By the rule, the overload response is needed on every board.** A256 tests it on k_N0, m4_s_p250 and these two rows.
  Between the first fire and the collapse there are about 40-50 us (N75): a response that acts within a few periods
  comes well before it.

## 1. Criteria
| # | criterion | N75 | S75h |
|---|---|---|---|
| c1 | final configuration: peak <= 200 A, ladder <= 1 V and Vo within 1 % at the end, V_DS <= 40 V | pass | pass |
| c2 | with the limit: ladder <= 1 V, Vo minimum >= arm h - 2 mV, peak <= max(arm h, 200 A) | **fail** | **fail** |

## 2. Predictions
- Held: c1 at 182.0 / 185.6 A (predicted 175-190 A); c2 fails on both boards.

## 3. Limits
- One overload (+25 %), 120 us after the step, single module, two boards (S75 at 25 C not run).
