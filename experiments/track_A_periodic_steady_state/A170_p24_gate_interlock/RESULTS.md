# A170 - a driver interlock for the high-side lead, gate form (RESULTS)
Boundary: 6e69065 (interlock 8d83e29). Records: release records-a170 (run_*.json, run log).
Analysis: a170_analyze.py -> a170_summary.json (a168_analyze's criteria; A169's run of the same row alongside).

## 0. Verdict
- **FAIL as registered, 2 of 8 rows (ff, hot).** The gate form removes every shoot-through: all eight runs complete,
  including A168 Q60 / Q75 and A169's L x 0.7 and slow-corner rows. Timing pays for it wherever the high-side command
  meets a low side that is still turning off.
  - nom +4.8 V / 1 us: post-step 187.6 A (A169 182.5), 7 late fires, Vo 12.6 mV and 45.5 us back.
  - L x 0.7: post-step 214.3 A, 64 late fires, Vo 14.8 mV and 63 us back. With t_il 1.0 ns: 207.6 A, 108 late fires.
  - slow corner: 4906 late fires, 721 NEW events (post-step 188.9 A).
  - Q60 / Q75 L x 0.7: post-step 213.5 / 197.0 A, 168 / 205 late fires.
- Mechanism (nom, 60 us after the step):
  - The command-to-channel delay of predictive turn-ons has median 2.9 ns in both A169 and A170. Its 90th percentile
    is 9.4 ns in A170 against 4.3 ns in A169, and its maximum 14.9 against 6.1 ns.
  - Holding the gate at 0 V until the low side stops serialises the low side's turn-off (<= 2.9 + 1.8 ns) and the
    high side's whole gate delay. Without the interlock, these overlap and the channel still starts after the low
    side stops (A169 nom: 0 shoot-throughs).
- Steady state is unchanged: delay median 2.83 ns before the step in both runs. The holds there are low-side
  turn-ons waiting <= 0.6-0.7 ns for a high side's turn-off tail.
- Per A170's decision rule the gate form is not enough. A171 tests the threshold form, which holds only a channel
  about to start against a conducting complement.

## 1. Criteria (misses)
| run | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| S50 ff / hot | 38.4 / 32.6 V | ok | ok | ok |
| S50 nom | 33.7 V | ok | post 187.6, late 7 | 12.6 mV, 45.5 us |
| S50 L07 | 33.9 V | Vo 1.010 V | post 214.3, late 64, NEW 4 | 14.8 mV, 63.3 us |
| S50 ss | 32.3 V | ok | post 188.9, late 4906, NEW 721 | ok |
| S50t1 L07 | 35.0 V | Vo 1.010 V | post 207.6, late 108, NEW 6 | 15.4 mV, 48.1 us |
| Q60 L07 | 35.8 V | Vo 1.006 V, hand 202.0 | post 213.5, late 168, NEW 6 | 14.9 mV, 52.2 us |
| Q75 L07 | 33.2 V | Vo 1.011 V, start 212.9 | late 205, NEW 9 | -19.7 mV, 51.5 us |

## 2. Limits
- The L x 0.7 boards' Vo(143.5 us) is 1.006-1.011 V because the interlock also holds turn-ons in the open-loop
  start-up. A per-board trim on the real board would absorb this; the trims were not redone.
- The interlock is ideal: it senses the complement's channel current, then adds a fixed t_il.
