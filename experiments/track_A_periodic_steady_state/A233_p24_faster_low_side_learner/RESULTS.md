# A233 - a faster low-side learner on phase 1 (RESULTS)
Boundary: f9ae1de. Records: release records-a233 (24 cosim records, log). Analysis: a233_analyze.py -> a233_summary.json.
Runs from f9ae1de (10) and 2501cbe (14; docs only), cosim_sources_modified False. The final configuration (A229 + A231)
with phase 1's lo_smax 128 (s128) and 255 (s255) against its records at 64; plant V7, one module, 25 C unless named.

## 0. Verdict
- **Neither arm is adopted; lo_smax stays 64.** Both miss m1, m2 and m4; s255 also m3.
- **A faster learner raises the rising-step peaks instead of lowering them** (post-step peak, 64 -> 128 -> 255):
  - item 2, S75 125 C, step 2 / 10 / 20 us after the entry: 211.2 / 210.3 / 207.8 -> 226.7 / 213.2 / 209.2 -> 232.1 /
    217.9 / 210.6 A; S75 25 C at 20 us 190.3 -> 196.5 -> 199.5 A;
  - the binding row (S75 125 C +4.8 V / 1 us at 500.3 us) 192.9 -> 198.2 -> 201.2 A, Vo -8.8 -> -13.7 -> -16.9 mV;
  - N0 +4.8 V / 2 us 179.3 -> 186.7 -> 191.4 A.
  The registered premise (the 2 ns-per-decision limit makes the early-step peak) is wrong in sign: catching phase 1's
  valley sooner after a rising rail costs more than it saves, as A148 (a held phase-1 valley stretches the period)
  and A224's D63 study (holding the valley doubles the dip) found from other sides. The slow learner protects the
  rising step.
- **Load side**: +62.5 A unchanged (181.3 -> 181.5 / 182.0 A, -12.8 mV); the re-applications lose most late fires
  (68 / 152 / 110 -> 42 / 33 / 51 -> 0 / 0 / 0) but w20_N0 / w5_N75 peak 11-16 A higher, and at 255 their dips deepen
  5 mV; -8 V / 10 us within 0.7 A; N0 10 % skipping unchanged (-16.2..-13.4 / -13.5 A).
- Every run completes with no overlap or shoot-through, V_DS <= 32.7 V. Item 2 keeps its 40 us hold-off.

## 1. Criteria
| # | s128 | s255 |
|---|---|---|
| m1 item 2 <= 200 A | **miss** (226.7 / 213.2 / 209.2; 196.5 A) | **miss** (232.1 / 217.9 / 210.6; 199.5 A) |
| m2 binding row <= 192.9 + 0.5 A | **miss** (198.2) | **miss** (201.2) |
| m3 k_N0 / w rows | pass | **miss** (w20_N0 -33.4, w5_N75 -28.5 mV against -28.4 / -23.5 + 2) |
| m4 line rows | **miss** (l_N0_p48 186.7 A) | **miss** (191.4 A) |
| m5 N0 10 % skipping | pass | pass |

## 2. Predictions
- Held: z_N0_10 within band; -8 V / 10 us within 1 A.
- Missed: every rising-step prediction (registered lower, measured 1.4-20.9 A higher); k_N0's dip deeper by 1-3 mV
  (unchanged).

## 3. Limits
- One module, the rows above; two values of lo_smax. Why a faster phase-1 learner raises the rising-step peak (period
  stretch, phases 2-4) is read from earlier work, not traced in these records.
