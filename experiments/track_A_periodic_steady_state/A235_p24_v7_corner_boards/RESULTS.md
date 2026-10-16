# A235 - the final configuration on plant V7 for F0, S0 and N13 (RESULTS)
Boundary: 1debe0a. Stage 1 -> 2: fe39f70 (a235_trims.json). Records: release records-a235 (17 cosim records, logs).
Analysis: a235_analyze.py (1 -> a235_trims.json, 2 / default -> a235_summary.json). Runs from 1debe0a (3), fe39f70 (10)
and 60e4d3f (4; D84 docs only), cosim_sources_modified False. Plant V7, the final configuration (A229 / A231) per corner,
one module, 25 C unless named; events at 500 us.

## 0. Verdict
- **c2 passes, c1 passes on 13 of 14 runs.** The ff (F0) and ss-at-L0 (S0) columns move to V7 with the final
  controller for every registered row; the L x 1.3 (N13) column for +4.8 V / 1 us, +62.5 A and -8 V / 10 us. Its
  -4.8 V / 1 us row is traced below (decision rule) and stays item 3's.
- Trims by the registered rule: stage 1 Vo(143.5 us) F0 1.0391 / S0 1.0377 / N13 1.0352 V -> -2 / -2 / 0 steps ->
  stage 2 1.0360 / 1.0345 / 1.0352 V (target 1.035 +- 0.002). Mode-S on-time from V5: F0 -0.2825, S0 +0.3275, N13 -0.22 ns.
- Peaks (gate level, whole run) 159.5-187.9 A at 25 C; V_DS <= 37.6 V (F0 +4.8 V); Vo <= 1.0371 V before 300 us and
  within 1 % at the end of every run (0.9997-1.0031 V). S0 at 125 C: start-up 127.9 A, handover 172.0 A, Vo max 1.0474 V, +4.8 V / 1 us
  184.7 A.
- **The miss, r_N13_lm48 (-4.8 V / 1 us): two NEW and one K3 after the step, peak 163.6 A, Vo -7.7 mV, back within 1 %.**
  - 502.0 us: phase 3's high-off 146.0 A, 11.9 A above both neighbours, 2 ns after the K4 window (ramp end + 1 us). It
    is the step's own first periods (phase 3's valleys +17..+34 A, period 662 -> 455 ns), not a separate mechanism.
  - 534.7 us restart (K3) and 535.3 us spike 157.6 A (gate level 163.6 A, the run's peak): item 3. The step lands on
    rail 1 (12.39 -> 7.85 V) and the rails take ~80 us to share it; phase 4 (highest rail) turns its low side off at
    +1..+5 A for ~30 us, every hard turn-on reports early and dt_pred climbs 0.28 ns per period, 17.6 -> 28.3 ns, past
    cfg_rs_high; the restored valley then meets a delay ~8 ns too long and the high side's body diode conducts first.
    Figure: A236_p24_early_hold/a236_item3.png (from cosim/run_r_N13_lm48.json). Same mechanism as A232's N75 phase 3.
    A236 tests holding dt_pred on an early report whose low-side current had not reversed.

## 1. Criteria
| run | post-event peak | Vo after event | oracle after event | c1 / c2 |
|---|---|---|---|---|
| F0 +4.8 V / -4.8 V / +62.5 A / -8 V | 187.3 / 164.5 / 180.9 / 159.5 A | +7.1 / -4.7 / -12.6 / +26.2 mV | K4 1 / - / - / - | pass / pass |
| S0 +4.8 V / -4.8 V / +62.5 A / -8 V | 183.8 / 167.9 / 182.7 / 163.7 A | +10.1 / -11.0 / -14.4 / -25.7 mV | K4 1 + K1 1 / - / - / - | pass / pass |
| N13 +4.8 V / -4.8 V / +62.5 A / -8 V | 187.9 / 163.6 / 180.4 / 164.5 A | +9.1 / -7.7 / -16.3 / -28.2 mV | K4 1 / **NEW 2 + K3 1** + K4 1 / - / - | **-4.8 V miss** / pass |
| S0 125 C start-up / +4.8 V | - / 184.7 A | - / +10.3 mV | - / K4 1 | pass / (not judged) |

## 2. Predictions
- Held: stage 1 within 1.035 +- 0.006 V (+4.1 / +2.7 / +0.2 mV); +4.8 V / 1 us S0 178-185 (183.8), N13 186-192 (187.9),
  S0 125 C 180-190 A (184.7); other rows <= 185 A (<= 182.7 A).
- Missed: F0 +4.8 V / 1 us 180-186 A (187.3 A).

## 3. Limits
- One module; F0 / N13 at 25 C only, S0 at 25 and 125 C; one step position per row; four modules not on these boards.
