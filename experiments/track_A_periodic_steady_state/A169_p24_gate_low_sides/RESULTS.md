# A169 - the adopted drive with gate-driven low sides (RESULTS)
Boundary: 23e464b (gate bookkeeping fab6366). Records: release records-a169 (run_*.json, run log).
Analysis: a169_analyze.py -> a169_summary.json (a168_analyze's criteria; stopped runs via safe_stats).

## 0. Verdict
- **FAIL as registered, 3 of 5 rows.** Once the low sides' turn-off takes real time, the adopted drive (A167: 8 ns
  lead ramped over 20 us) shoots through. It happens on the two rows whose dt_pred collapses:
  - L x 0.7: SH4 at 152.1 us, phase-4 dt_pred 2.5 ns;
  - slow corner: SH3 at 161.5 us, phases 3-4 dt_pred 0.0 ns, lead ~6.9 ns into its ramp.
- The other three rows pass and match the ideal-low-side references:
  - nom: 33.7 V; post-step 182.5 vs 181.7 A;
  - ff: 38.4 vs 38.5 V; post-step 181.8 vs 180.8 A;
  - hot: 32.6 V; post-step 179.3 vs 179.9 A.
  - Vo(143.5 us) is 1.031-1.032 V, 3-4 mV below the ideal-low-side trim. Edge power is 0.1 W lower.
- Low-side turn-off: delay <= 2.2-2.9 ns, active edge <= 1.2-1.8 ns (device-model estimate 1.3-1.9 ns delay).
  Turn-offs with reverse current open at once.
- Mechanism (as A168 Q60 / Q75): phase-4 valleys -43..-65 A after the L x 0.7 handover (A167 -27..-38 A). The node
  swings within ~2 ns of the low side's turn-off, beyond the high side's reach. The error-based dt_pred then falls
  below the ramped lead, so the high-side command precedes the low side's turn-off.
- The prescribed follow-up (bound the lead by the low side's turn-off) cannot work. A safe lead at dt_pred = 0 must
  satisfy lead <= high-side delay min (ff ~1.5 ns) - low-side turn-off (~2.5 ns) < 0, which is no lead at all (A164:
  48 late fires without it). The structural fix is a driver interlock, registered as A170.

## 1. Criteria
| row | 1 V_DS | 2 start / Vo | 3 post / late / shoot | 4 Vo | verdict |
|---|---|---|---|---|---|
| nom l_p48_1us | 33.7 V | 162.1 A / 1.032 V | 182.5 A, 0 late, 0 | 8.4 mV | PASS |
| ff l_p48_1us | 38.4 V | 161.6 A / 1.032 V | 181.8 A, 0 late, 0 | 7.3 mV | PASS |
| hot l_p48_1us | 32.6 V | 161.8 A / 1.031 V | 179.3 A, 0 late, 0 | 5.8 mV | PASS |
| nom L07_l_p48_1us | - | (196.1 A whole-run) | OVERLAP_STOP 152.1 us | - | miss 3 |
| ss l_p48_1us | - | (188.8 A whole-run) | OVERLAP_STOP 161.2 us | - | miss 3 |

## 2. Limits
- A164's trims were not redone with low-side gates. Vo is still within 4 mV of the trim target.
- The low side's turn-on runs through the same 3.0 ohm. It matters only for the start-up's hard low-side turn-ons
  (delay 1.7-12.3 ns). Reverse conduction before a ZVS turn-on is not modelled as delayed.
- Before fab6366 only command-level low-side conduction was checked. Shoot-throughs against a gate-driven low side's
  turn-off are new in this count.
