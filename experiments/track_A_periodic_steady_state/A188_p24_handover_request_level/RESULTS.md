# A188 - the Vo handover request at 1.045 V, above the 25 C start-up (RESULTS)
Boundary: f792ff3. Records: release records-a188 (5 runs, log). Analysis: a188_analyze.py -> a188_summary.json. Code
cfe581f, plant V5, t_il 1.0 ns.

## 0. Verdict
- **PASS as registered: the start-up spec is adopted.** It is t0 200 ns + per-board mode-S trim (cfg_ton_s) +
  bumpless seed (ton_ns) + handover at Vo >= 1.045 V or 144 us.
- **g0:** the S0 25 C check run never sets the request and equals A185 up to 150 us (731 sections). The 25 C results
  are therefore A185's: every 25 C run of A185 stays <= 1.0358 V before 144 us.
- **Hot (trims and seeds set at 25 C, locked):**

  | board | request / entry | Vin at entry | Vo at entry | handover minimum (t0 400 record) | Vo maximum |
  |---|---|---|---|---|---|
  | S75 | 131.2 / 131.4 us | 46.0 V | 1.047 V | 0.995 V (0.991) | 1.047 V |
  | S0 | 131.6 / 131.8 us | 46.1 V | 1.048 V | 0.996 V (0.991) | 1.047 V |
  | N0 | 140.0 / 140.2 us | 48.0 V | 1.046 V | 0.997 V (0.999) | 1.046 V |
  | F0 | none / 144 us | 48.0 V | 1.037 V | 1.000 V | 1.038 V |

  - Start-up <= 139.0 A, handover <= 184.4 A, S75 post-step 193.8 A, V_DS <= 31.8 V, 0 shoot-throughs.
  - Mode P within 0.55 A of the t0 = 400 hot records.
- **Against the frozen 400 ns start-up**, on the same boards and conditions:
  - start-up peaks <= 145 A (was up to 207.3 A on S75);
  - S75's 25 C handover 151-162 A with minimum 1.000 V (was a 278.4 A runaway at 0.961 V);
  - overshoot <= 48 mV at 25 / 125 C (was 57-71 mV hot);
  - ladders at the handover: max/min <= 1.028 where the handover is at 144 us. The hot slow boards hand over
    mid-ramp (131 us) at 1.096-1.100. Both are well below the 1.61-1.80 of the slow boards at 400 ns.
  - The price is at 25 C on the L0 nominal / ff / four-module boards: their handover minimum is 0.989-0.993 V
    (was 0.998-0.999 V; A185, the 200 -> ~520 ns period jump).

## 1. Criteria
| run | g0 | c1 | c2 | c3 | c4 entry Vo | c5 dev | c6 | c7 |
|---|---|---|---|---|---|---|---|---|
| S0 25 C (150 us) | = | - | - | - | - | - | - | - |
| S75 125 C | - | PASS | PASS 193.8 | PASS | 1.047 | 0.03 | 0.995 (0.991) | 1.047 |
| S0 / N0 125 C | - | PASS | - | PASS | 1.048 / 1.046 | 0.55 / 0.18 | 0.996 / 0.997 | <= 1.047 |
| F0 125 C | - | PASS | - | PASS | 1.037 | none | 1.000 (none) | 1.038 |

## 2. Predictions
- Requests "S0 / S75 at ~131-132 us, Vin ~46 V": right. "N0 at ~142-144 us": 140.0 us. "F0 none": right.
- c7 <= 1.048 V: right (1.047). c6 S0 / S75 >= 0.99, N0 / F0 ~1.000 / 0.999: right (0.995-1.000).

## 3. Limits
- 25 C is A185 (in-sample seeds, +4.8 V / 1 us on S75 / N0 only). Hot runs: one step position (S75).
- Below 25 C not run: a colder board whose mode-S Vo stays under 1.045 V hands over at 144 us at its own Vo (A163's
  cliff below ~0.99 V still applies there).
- Four modules hot not run.

## 4. Decision (BOUNDARY Section 4)
Adopted. FINAL_SPEC's start-up row becomes this spec at 25 and 125 C. The slow corner's inductance limit after the
step at 125 C is a mode-P item (A187).
