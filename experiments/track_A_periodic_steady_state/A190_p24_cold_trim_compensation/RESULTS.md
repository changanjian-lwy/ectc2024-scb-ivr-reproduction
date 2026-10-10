# A190 - a temperature-compensated mode-S trim below 25 C (RESULTS)
Boundary: e41dd44. Records: release records-a190 (11 start-ups to 200 us, log). Analysis: a190_analyze.py ->
a190_summary.json. Code cfe581f, plant V5, t_il 1.0 ns; device model extrapolated below 25 C.

## 0. Verdict
- **PASS as registered: the table holds on every hold-out board.** The start-up spec now covers -40 to 125 C.
  - The correction is ton_s(T) = ton_s(25 C) + DT[corner][T]: slow +0.531 / +1.441 ns, nominal +0.113 / +0.313 ns
    at 0 / -40 C.
  - It was taken from S75 and N0 only. The corner is read from the board's 25 C trim (slow ~35.5 ns, nominal
    ~23.7 ns).
- **Hold-out boards:**
  - Vo(143.5 us) 1.0314-1.0344 V (target 1.035 +- 0.015; predicted +-10 mV, measured within 4 mV);
  - start-up <= 136.7 A, handover <= 166.3 A, handover minima 1.000-1.001 V, V_DS <= 28.9 V.
  - S0 at -40 C: handover 277.9 -> 158.8 A (A189 uncompensated).
- **In-sample:** S75 at 0 C 211.1 -> 153.1 A; N0 at -40 C 193.1 -> 161.9 A, with its minimum 0.976 -> 0.996 V.
- Both A189 causes are removed. The entry Vo is back above the cliff, and it matches the bumpless seed's assumption
  again.

## 1. Criteria
| run | hold-out | Vo(143.5) | c1 start / hand | c3 | c4 entry | c8 |
|---|---|---|---|---|---|---|
| S0 0 / -40 C | yes | 1.0344 / 1.0335 | 123.4 / 166.3; 123.2 / 158.8 | PASS | 1.035 / 1.034 | PASS |
| S80 0 / -40 C | yes | 1.0340 / 1.0329 | 132.6 / 150.4; 132.4 / 151.9 | PASS | 1.035 / 1.034 | PASS |
| N75 0 / -40 C | yes | 1.0314 / 1.0317 | 136.5 / 149.3; 136.7 / 149.3 | PASS | 1.031 / 1.032 | PASS |
| N13 -40 C | yes | 1.0325 | 116.6 / 152.6 | PASS | 1.032 | PASS |
| S75 / N0, 0 and -40 C | no | 1.0314-1.0338 | <= 135.7 / <= 162.7 | PASS | >= 1.031 | PASS |

## 2. Limits
- The device model's temperature factors are linear from 25 C, so below 25 C is an extrapolation. The table is
  only as right as that model.
- Start-ups only (to 200 us). No post-step rows cold; four modules and ff cold with the table not run (ff passed
  uncompensated in A189).
- Two temperatures. Between them the table is interpolated, untested.

## 3. Decision (BOUNDARY Section 4)
The table holds. FINAL_SPEC's start-up row adds it: -40 to 125 C at the tested points.
