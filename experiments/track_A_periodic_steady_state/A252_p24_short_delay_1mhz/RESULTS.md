# A252 - a short held delay on the 1 MHz train (an oracle for item 10's open part) (RESULTS)
Boundary: 45df558. Plant V7, single module. Records: cosim/run_{s4,n5,n9}_*.json, 3 runs from 45df558
(cosim_sources_modified False; release records-a252). Analysis: a252_analyze.py -> a252_summary.json. Reference: the
final configuration's records (A246 run_h_p_N75_1000k / run_h_p_S75h_1000k).

## 0. Verdict
- **k1 misses in all three arms**, so by the rule item 10's 1 MHz part goes to a cycle-by-cycle current limit (A253).
  - s4 (S75h at 4.41 / 4.34 / 4.16 ns): 206.5 A against 211.1 A.
  - n5 (N75 at 5 ns): 207.6 A against 244.6 A. n9 (N75 at 9 ns): 214.1 A.
  - q2 (V_DS, time above) passes in all three; q1 (<= 200 A) misses.
- **The delay matters more than predicted on N75:** 5 ns takes 37 A off (prediction: 230-250 A, "not a delay
  question"). Vo's minimum is better too: 990.7 against 981.7 mV (n5), 986.7 against 976.4 mV (s4).
  - The peaks stay on phase 4 after the train's releases. They start from positive valleys (+26 to +68 A) with on-times
    of 31-47 ns (highoffs; the gate record's i_max is about 12 A higher).
  - The learner's own peaks on N75 are higher: 232 A from +35 A with a 38.4 ns on-time.
- **What a short delay costs in steady state (200-300 us, before the train):** phases 2-4 turn on hard at the rail.
  The median V_DS at turn-on is 12.5-12.7 V (n5) and 11.7-12.0 V (s4), against 4.4-5.4 V with the learner. Late fires:
  n9 phase 2 350 against 105.
  - A held short delay is therefore not a design. A delay that drops only during trains would need its own detector and
    still misses 200 A here.

## 1. Criteria
| # | criterion | s4 (S75h) | n5 (N75) | n9 (N75) |
|---|---|---|---|---|
| k1 | A240's q1 and q2 (peak <= 200 A, V_DS, time above) | **miss**: 206.5 A | **miss**: 207.6 A | **miss**: 214.1 A |

## 2. Predictions
- Held: s4 within 5 A of 211.1 A (206.5 A); k1 misses everywhere.
- Missed: n5 / n9 at 230-250 A (207.6 / 214.1 A). T37's reading that N75's 1 MHz is a ladder matter, not a delay one,
  is too strong: the delay moves the peak by 37 A, though not under 200 A.

## 3. Limits
- Two delays on N75, one on S75h, one train (A240's 1 MHz, 250 <-> 25 A). The steady-state cost is shown as V_DS at
  turn-on only; its switching loss was not computed.
- If A253's limit costs too much (its o3 / o4), a short delay during trains plus the limit is the next candidate.
