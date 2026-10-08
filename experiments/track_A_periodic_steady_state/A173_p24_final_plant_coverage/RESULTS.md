# A173 - the final gate-level plant on the rest of the matrix, four-module cases and realisable interlock delays (RESULTS)
Boundary: f4c1f3c (L x 1.3 cfg 6c78f28). Records: release records-a173 (run_*.json, run logs). Analysis:
a173_analyze.py -> a173_summary.json. All runs from committed code.

## 0. Verdict
- **13 of 17 rows pass; 4 miss, none on peak current or voltage.** Every row: physical peaks <= 200 A, V_DS <= 34.1 V,
  0 shoot-throughs, 0 overlaps, COMPLETED.
- **Misses (open on the final plant):**
  - ff -8 V / 10 us: one phase-2 restart (K3) 14.5 us after the ramp ends, then a 153 A spike (NEW). It is A148's
    falling-step valley loss on phases 2-4, the same in A164 (V2), where that period's valley stayed at +0.6 A
    and here reached +19.5 A. Vo 31.1 mV and back 24.9 us, each 0.6 over the limit.
  - ss -8 V / 10 us and ss slew4: the post-ramp Vo dip is 3-5 mV deeper than V2's, with the same shape (-25.2 vs
    -22.3 mV; -13.5 vs -8.6 mV, outside 1 % for 7.6 us). The cause is the low sides' turn-off delay plus holds,
    which cost on-time while the loop recovers.
  - Four modules at the slow corner: 8 NEW events, all 10-16 A spikes (145-171 A). Four of them are phase 1 on
    every module 1.02-1.12 us after the ramp: A160's K4-window artefact. Three are ladder spikes, as in V2's slow
    corner (A164 / A167: NEW 4-14). One is a duplicate turn-on 0.1 ns apart (module 2, phase 1, 174.6 us),
    unclassified. Peaks: start 193.0 A, post 181.4 A; 803 late fires (reported only).
- **Interlock delay:** at the slow corner t_il 8.3 ns (a fixed 1.0 V reference) passes: 178.5 A, 244 late fires
  (0.5 ns: 194), holds up to 10.6 ns. So no per-board reference is needed on this row. 1.4 ns passes. L x 0.7 at
  2.0 ns gives the 0.5 ns result exactly (its 2 holds do not touch the peak).
- **Inductor spread on four modules (C14's w5):** 196.5 A (C14, ideal switches: 194.4 A). The ±5 % matching spec
  holds under the gate plant, with a 3.5 A margin.
- Rows where the interlock never acted (0 holds): nom / hot / L x 1.3 / L x 0.7 s_p62, ff s_p62, four modules nom and
  w5. Steady edge power per module: nom 2.45, ff 2.26, hot 2.86, ss 4.52-4.57, L x 0.7 4.18, L x 1.3 1.59 W.

## 1. Criteria (references: A167 else A164, same row; absolute rows per BOUNDARY)
| row | 1 V_DS | 2 start / hand / Vo | 3 post / late / NEW | 4 Vo | holds | result |
|---|---|---|---|---|---|---|
| nom s_p62 / l_m80_10us / slew4 | 29.4-32.4 V | 162.1 / 149.7 / 1.032 | 181.4 / 166.7 / 182.5 A, 0, 0 | as ref ±0.3 mV | 0 | PASS |
| nom L x 1.3 l_p48_1us (ton 40.916) | 34.1 V | 146.5 / 137.2 / 1.035 | 188.7 A (185.4), 0, 0 | 7.9 mV | 0 | PASS |
| nom L x 0.7 s_p62 (absolute) | 30.4 V | 200.2 / 190.2 (<= 205.5) / 1.041 | 182.2 A, 2 (<= 8), 0 | back | 0 | PASS |
| ff s_p62 / hot s_p62 | 33.2 / 28.5 V | 161.6-161.8 / 146.4-150.3 | 181.2 / 181.4 A, 0, 0 | ±0.1 mV | 0 | PASS |
| ff l_m80_10us | 33.2 V | as ff | 181.5 A (176.9), 0, **NEW 1** | **31.1 mV (<= 30.5), back 24.9 us (<= 24.3)** | 6 | miss 3, 4 |
| ss s_p62 | 30.0 V | 188.8 / 188.8 / 1.029 | 184.3 A (183.3), 72 (102), NEW within 1.5 ref + 5 | -16.6 (-16.6) | 23 | PASS |
| ss l_m80_10us | 30.0 V | as ss | 169.4 A, 81 (<= 102.5) | **-25.2 mV (<= 24.3)** | 23 | miss 4 |
| ss slew4 | 31.4 V | as ss | 180.2 A, 190 (224) | **-13.5 mV (<= 10.6), back 17.3 us (<= 2)** | 79 | miss 4 |
| m4 nom s_p62 (absolute) | 29.4 V | 162.1 / 149.7 / 1.032 | 181.6 A, 0 (<= 5), 0 | n/a | 0 | PASS |
| m4 w5 l_p48_1us (absolute) | 33.9 V | 169.1 / 161.9 / 1.026 | 196.5 A, 0 (<= 18.5), 0 | n/a | 0 | PASS |
| m4 ss l_p48_1us (absolute) | 31.2 V | 193.0 / 193.0 / 1.029 | 181.4 A, 803 (reported), **NEW 8** | n/a | 71 | miss 3 |
| ss l_p48_1us t_il 1.4 / 8.3 ns | 30.9 / 30.6 V | 188.8 / 188.8 | 179.8 / 178.5 A (181.7), 210 / 244 (260) | -10.0 / -9.7 | 79 / 91 | PASS / PASS |
| L x 0.7 l_p48_1us t_il 2.0 ns | 32.4 V | 200.2 / 190.2 | 199.7 A (195.3), 2 | -8.6 | 2 | PASS |

Predictions: right on the nominal / hot rows, L x 0.7 s_p62 (start-up identical to A172), m4 nom / w5 / ss post-step,
t_il 1.4 and 2.0. Wrong: t_il 8.3 was predicted to fail; ss l_m80 late fires rose (81 against 65); L x 1.3 +3.3 A
(predicted ±3); ff l_m80 held 6 times (predicted 0).

## 2. Limits
- One step position per row. A129's 2-7 A step-position noise applies to every peak, and the two marginal rows
  (L x 0.7 +4.8 V at 199.7 A, ff -8 V's single spike) are rerun at four more positions in A174.
- The fixed-reference delay was tested on the slow corner's +4.8 V / 1 us only. A174 runs it on the other rows
  where the interlock acted.
- Four modules: devices identical across modules (one corner per board); the slow corner with an inductor spread
  was not run.
