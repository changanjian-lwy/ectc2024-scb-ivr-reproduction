# A175 - the final gate-level plant on the rest of A152's matrix at nominal devices (RESULTS)
Boundary: a76a53b. Records: release records-a175 (run_*.json, run log). Analysis: a175_analyze.py ->
a175_summary.json. All runs from committed code.

## 0. Verdict
- **5 of 6 pass.** Every row: physical peaks <= 183.7 A, V_DS <= 33.0 V, 0 shoot-throughs, 0 interlock holds,
  COMPLETED, 0 late fires.
- **Miss: -4.8 V / 1 us, 6 NEW spikes** (10-20 A above the neighbours, 139-165 A, 27-41 us after the step), after 3
  restarts (K3). Post-step peak 172.4 A, Vo -10.2 mV (A163 -10.0). Mechanism: A148's falling-step valley loss on
  phases 2-4. Their valleys go positive after the step (phase 4 up to +34.5 A, phases 2-3 +12-13 A); phase 1
  stays at -20 A. A163 (V2, 2.5 ohm, no lead) has no events on this row. With A173's ff -8 V / 10 us this is the
  second falling step to show it on the final plant, so it is systematic for falling steps, not a single event.
- With A171-A173, the final plant at nominal devices has run all 13 rows of A152's matrix: 12 pass, -4.8 V / 1 us
  misses on oracle events only.
- Against A163 the final plant runs +0.7..+6.1 A higher after the step and +0.2..+3.8 mV in Vo (the 3.0 ohm drive
  and the lead), as calibrated in the boundary.

## 1. Criteria (reference A163 s50, same row)
| row | 1 V_DS | 2 start / hand / Vo | 3 post / late / NEW | 4 Vo extreme (limit) | result |
|---|---|---|---|---|---|
| slew10 | 31.9 V | 162.1 / 149.7 / 1.032 | 183.7 (180.4), 0, 0 | 9.8 (11.6) | PASS |
| slew5 | 32.2 V | as above | 182.3 (178.2), 0, 0 | 8.7 (9.9) | PASS |
| slew3 | 32.6 V | as above | 181.8 (176.9), 0, 0 | 8.6 (10.3) | PASS |
| slew2 | 33.0 V | as above | 182.9 (176.8), 0, 0 | 9.2 (10.6) | PASS |
| l_m48_1us | 29.4 V | as above | 172.4 (166.9), 0, **NEW 6** | -10.2 (15.0) | miss 3 |
| L13 s_p62 | 28.9 V | 146.5 / 137.2 / 1.035 | 179.8 (179.1), 0, 0 | -18.1 (22.5), back within ref + 5 | PASS |

Predictions: post-step A163 + 1-5 A - right on slew10 / 5 / 3 (+3.3 / +4.1 / +4.9), above on slew2 (+6.1) and
l_m48 (+5.5), below on L13 s_p62 (+0.7); Vo A163 + 2-4 mV on the ramps - right (+3.2..+3.8; +0.2 / +0.6 on the
steps); 0 holds and start-up as A173 - right; NEW 0 on -4.8 V - wrong.

## 2. Limits
- Nominal devices only; one step position per row.
- The falling-step mechanism is named, not fixed: the RTL is frozen. Whether the lead or the low sides' gate delay
  turns A148's valley loss into restarts is not separated (A163 has neither; A164's V2 with the lead had no
  -4.8 V / 1 us row).
