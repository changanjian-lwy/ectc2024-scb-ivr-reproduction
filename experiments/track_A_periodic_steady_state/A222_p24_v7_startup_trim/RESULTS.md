# A222 - mode S's trim on plant V7 (RESULTS)
Boundary: 89df633, round 2 02aaf11 (Section 5, before its runs). Records: release records-a222 (5 cosim records,
logs). Analysis: a222_analyze.py -> a222_summary.json. Runs from 89df633 / 02aaf11, cosim_sources_modified False.
Plant V7 (A221's r_core), final configuration otherwise (ton_lat 16, ton_min_ns 4.0), one module; references:
A215's V6 records of the same rows.

## 0. Verdict
- **k1 and t1 pass after round 2. By the decision rule skipping is adopted on nominal boards and the final
  configuration moves to plant V7** with mode S's trims N0 23.4375 ns, N75 23.46875 ns, S75 35.84375 ns (+1 / +2 /
  +3 steps of 31.25 ps against V6's).
- **N0 (k1)**: Vo's maximum before 300 us -0.49 mV from V6, post-step peak 181.30 A (V6 181.91), A212's c6 and c7
  pass.
- **N75 (t1)**: Vo before the handover +0.98 mV, maximum +0.95 mV; start-up / handover peaks 137.1 / 149.3 A (V6
  137.1 / 149.4).
- **S75 needed a second round**: round 1 kept its trim on the premise that its handover is requested by Vo; at 25 C
  it is at 144 us, and Vo came 4.96 mV low (t1 missed; record cosim/run_s_S75_25.json). With +3 steps: -0.01 mV,
  peaks 136.9 / 151.3 A (V6 137.1 / 155.3). The check at 125 C with the same trim: Vo before the handover -0.19 mV,
  maximum 1.0474 V (V6 1.0476 V, limit 1.05), handover 180.0 A (V6 181.1), A206's c6 passes.
- What moves with it: the specification's light-load line (A221's rows, on V7): N0 and N75 at 10 % regulate with every
  valley inside -20..-12 A; N0 with no load regulates (1.0017-1.0049 V) with valleys down to -21.2 A, 1.2 A outside
  the band. The slow board does not skip (A217) and stays at a 30 % minimum.

## 1. Criteria
| row | criterion | V7 against V6 | result |
|---|---|---|---|
| k N0 +62.5 A, N0 trim | k1 | Vo before 300 us -0.49 mV, post-step peak -0.61 A, c6 + c7 | pass |
| N75 25 C start-up, N75 trim | t1 | before the handover +0.98 mV, maximum +0.95 mV, c6 | pass |
| S75 25 C start-up, old trim | t1 | -4.96 / -4.96 mV | **miss** (round 1) |
| S75 25 C start-up, S75 trim | t1 | -0.01 / -0.01 mV, c6 | pass (round 2) |
| S75 125 C start-up, S75 trim | check | -0.19 / -0.20 mV, maximum 1.0474 V, c6 | pass |

## 2. Predictions
- Held: N0 -0.5 mV and the post-step peak within 0.3 A of A221's (181.30 against 181.23); N75 +1.0 mV; round 2's
  S75 25 C (+0.2 predicted, -0.01); start-up and handover peaks within 4 A of V6's (at the edge: S75 25 C's
  handover -4.0 A).
- Missed: S75 25 C in round 1 (my premise about its handover); the hot start-up's maximum (1.0474 V, predicted
  1.0481-1.0490: lower).

## 3. Limits
- The trims are this model's; in a product each board's trim is its own factory measurement (A184, A206), so these
  steps stand for that calibration, not for a design change.
- The cold table (A190) was not rerun on V7; 0 C and -40 C start-ups stay V5 / V6 results.
