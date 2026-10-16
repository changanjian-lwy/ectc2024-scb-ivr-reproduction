# A234 - four modules on plant V7 with the final controller (RESULTS)
Boundary: a06e607. Records: release records-a234 (6 cosim records with four modules each, log). Analysis: a234_analyze.py
-> a234_summary.json. Runs from a06e607, cosim_sources_modified False. Four N0 modules (nominal L0, 25 C) on one output,
common Ton and slave floor (C12's arrangement), plant V7, the one-module final configuration without skipping; arms d0
(before A229) and b (final: A229 + A231); events at 400 us (system totals).

## 0. Verdict
- **Passes as registered: f1-f3.** The four-module design of record becomes the one-module final configuration without
  skipping, on plant V7, for these rows (it was C12 + lo_learn 4 on V2-V5). First four-module runs on V6 / V7.
- **Post-event peaks, b (d0)**: +4.8 V / 1 us 169.1 (169.0) A, +250 A 173.3 (173.2) A, -8 V / 10 us 159.2 (162.6) A;
  Vo +7.7 / -12.9 / +22.8 mV (d0 +7.7 / -14.1 / +23.0 mV); back within 1 % at the end of every run.
- **Start-up and handover**: 116.8 A and 140.2 A on every run (mode P entered at 144 us); no module locks (each module's
  phase-1 rail in mode P <= 12.23 V against C10's 13.5 V gate).
- No overlap or shoot-through on any module, V_DS <= 33.1 V, late fires 0-1; the oracle sees only K1 (2, both arms) on
  +4.8 V / 1 us.
- The four modules here are identical boards: inductance or device spread between modules (D66: about +-5 % binds
  200 A with passive sharing; C14) is not in these runs.

## 1. Criteria (arm b)
| row | f1 | f2 (b - d0: peak, |Vo|) | f3 rail 1 |
|---|---|---|---|
| +4.8 V / 1 us | pass (169.1 A, 33.1 V) | +0.1 A, 0.0 mV - pass | 12.23 V - pass |
| +250 A | pass (173.3 A) | +0.1 A, -1.2 mV - pass | 12.23 V - pass |
| -8 V / 10 us | pass (159.2 A) | -3.4 A, -0.2 mV - pass | 12.23 V - pass |

## 2. Predictions
- Held: start-up <= 165 A (116.8), handover <= 185 A (140.2), rail 1 <= 12.9 V.
- Missed: the post-event peaks were 10-15 A lower than registered (169.1 / 173.3 / 159.2 against 180-190 / 180-185 /
  165-175 A); b within 3 A of d0 holds on two rows, -3.4 A on -8 V / 10 us.

## 3. Limits
- Identical modules, 25 C, N0 boards, three events at one position each; no skipping, no load release, no falling
  -4.8 V / 1 us, no spread between modules.
