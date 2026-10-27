# A257 - the adopted peak limit on the 3.813 nH board (N13, 140 A) (RESULTS)
Boundary: 9d3b1d5. Plant V7, one module, 25 C, N13 (L x 1.3). Records: cosim/run_{h,s}_{o125,lp48}_N13.json, 4 runs
from 9d3b1d5 (cosim_sources_modified False; release records-a257). Analysis: a257_analyze.py -> a257_summary.json.
Figure: a257_figure.py -> a257_limit_on_n13.png.

## 0. Verdict
- **n2 passes on both rows: the 140 A level stands on N13.**
  - o125_N13 (+62.5 A, 125 % load):
    - fires 16 times, from 538.48 us, 38 us after the step, when the loop has pushed the peaks past about 170 A;
    - suspends at 542.35 us (phase 4's count at 6);
    - then runs as the final configuration: 181.0 A against 180.4 A, ladder 0.59 V (same), Vo -16.3 mV (same), NEW 0;
    - hand-back kick 1.2 A.
  - lp48_N13 (+4.8 V / 1 us): no fire. Its 187.9 A pulse crosses 140 A within 11 ns of the controller's turn-off, so
    the limit's turn-off is dropped. The two arms are equal bit for bit.
- **n0 passes:** arm s equals arm h before its first fire on o125_N13, and everywhere on lp48_N13.
- **n1 fails as registered on lp48_N13's ladder clause. The cause is my threshold, not N13.**
  - During the +4.8 V ramp rail 1 takes the step: 16.99 V at 501.3 us, a deviation of 3.79 V. A235's record of the
    same row (V7, before A244-A246) has the same 3.79 V at the same instant. S75h's +4.8 V row has 3.74 V (A246).
  - I registered "<= 1 V after the event" without checking the row's own reference. Token lesson 8 says to check
    first, and I did not.
  - The rest of n1 passes: 187.9 A, V_DS 33.7 V, Vo within 0.05 % over the last 20 us. o125_N13 passes n1 in full
    (180.4 A, 0.59 V, 29.0 V).
- **Found on the way (the final configuration, not the limit): a slower settle after a rising line step on N13.**
  - Hard turn-ons are those with V_DS > 6 V at turn-on.
    - lp48_N13 has 198 after the step: phase 1 48, phase 3 60, phase 4 90, until 600.9 us.
    - A235's record has 41, all on phase 1, ending at 529.0 us.
  - Phases 3-4 turn on at a median of 6.5 / 7.0 V (max 12.1 / 14.2 V; steady state 3.2-4.2 V) from 520 to 600 us.
    Over that time rail 2 dips to -1.12 V at 536.5 us, which takes the ladder deviation back above 1 V from 537 to
    547 us (figure (c)).
  - The -4.8 V and +62.5 A rows on N13 match A235's hard turn-on counts: 184 / 184 and 178 / 176.
  - Peaks, V_DS and Vo are unchanged from A235. The ladder ends at 0.28 V, against A235's 0.36 V.
  - This fits the turn-on-delay learner re-learning more slowly after the rails move (an open candidate since A251).
    Not traced to a rule; no criterion is broken, so it is recorded, not run.
- **Prediction misses:**
  - I estimated a 40 A rise in the 11 ns path on N13, so an effective cap of about 180 A. The cut pulses end at
    169-171 A, so the rise is about 30 A.
  - o125_N13 fired 16 times and suspended; I predicted 0-5 fires and no suspension.

## 1. Criteria
| # | criterion | o125_N13 | lp48_N13 |
|---|---|---|---|
| n0 | arm s = arm h before the first fire | pass | pass (no fire, bit for bit) |
| n1 | final configuration: peak <= 200 A, ladder <= 1 V after the event, Vo within 1 % at the end, V_DS <= 40 V | pass | **fail**: ladder 3.79 V during the ramp (A235 the same); the rest passes |
| n2 | limit vs final configuration (A256's s2 test) | pass | pass |

## 2. Limits
- One module, 25 C. Not run: N13 at 1 MHz (A240's train has no N13 row), four modules on N13, overloads above 125 %.
