# A254 - the peak current limit at a level set from A253's measured overshoot (RESULTS)
Boundary: c0ceee1 (option 0915877 + fixes 00fca32 / f4657c3). Plant V7; 33 single-module runs and 2 four-module runs.
Records: cosim/run_l_*.json, 35 runs from 8c4fa3a (cosim_sources_modified False; release records-a254). The first
launch was stopped at 21:10 with no run finished (the laptop's power); the whole queue was rerun at 21:50.
Analysis: a254_analyze.py -> a254_summary.json. Its row classifier was fixed after the runs: f_N0_k0 / f_N0_k4 had been
taken for position rows; the criteria are unchanged. Figure: a254_figure.py -> a254_peak_limit.png.

## 0. Verdict
- **p1 and p2 pass; p3 misses on three rows, and on two of them the limit collapses the ladder.** By the rule, each
  row's cost is named below and the user decides.
- **p1, wiring:** all 17 rows without a fire equal their references bit for bit, including the two identity rows that
  cross the level in every full-load period. A253's step-split fault is gone.
- **p2, 1 MHz (item 10):**
  - N75: 193.2 A against 244.6 A, 91 fires, Vo minimum 981.7 mV (the same). Figure (a).
  - S75h: 182.7 A against 211.1 A, 37 fires; Vo minimum 980.1 against 976.4 mV; late fires 146 against 223. Figure (b).
- **Elsewhere on 2.2 nH the limit costs nothing measured:**
  - Every S75h row fires 5 times in the start-up's handover: 174.6 against 178.9 A. The p4 / p5 rows pass (Vo within
    1 mV; u_S75h_100 end deviation 0.142 against 0.136 V).
  - The item-2 rows (S75h 125 C re-application): a_S75h_d20 197.1 A (207.8) passes. a_S75h_d2 is 200.8 A (211.2),
    0.8 A over: p3 misses there.
- **The cost: a 125 % load on N0 collapses the ladder (limit 125 A on 2.933 nH).** Figure (c) / (d).
  - k_N0 (+62.5 A at 500 us): the limit fires from 514.5 us, then in almost every period (549 fires).
    - Rails 1-4 go from 12 V each to 3.8 / 26.6 / 3.6 / 14.0 V.
    - Vo falls to 756.9 mV and is 820 mV at the run's end.
    - The peak is 241.5 A (181.2 without the limit), still rising at 620 us. V_DS 38.9 V (28.1 V).
  - m4_s_p250, four modules (+250 A at 400 us): the same collapse. 1843 fires, Vo 758.6 mV, 234.7 A (181.3).
  - This is the risk the boundary named (Abdelhamid et al., TPEL 2020): a peak comparator that sets the on-time
    unbalances a flying-capacitor ladder. Here it acts in every period.
  - Phase peaks under a 125 % load are about 173 A. On 2.933 nH the current rises only about 37-52 A in the 11 ns path,
    so 125 A + that rise falls under the overload's own peaks.
- **Not tested, and the same risk:** a 125 % load on the 2.2 nH boards. Their full-load peaks are 137-142 A. At 110 A
  plus 49-69 A, an overload's peaks (about 170-178 A) would also reach the limit in every period.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| p0 | tests 721, regression quick + full | pass (tmp/logs/a253_fix2_*.log) |
| p1 | identity rows; every no-fire row equal to its reference | pass: 17 / 17 rows without a fire are equal |
| p2 | 1 MHz rows: q1 + q2 | pass: 193.2 / 182.7 A |
| p3 | stage-2 rows (A253's o3) | **miss**: a_S75h_d2 200.8 A; k_N0 241.5 A, Vo -243 mV; m4_s_p250 234.7 A, Vo -241 mV |
| p4 | stage-1 and position rows no worse | pass (11 rows) |
| p5 | start-ups no worse | pass (u_S75_100 equal; u_S75h_100 5 fires, 165.0 against 169.4 A) |

## 2. Predictions
- Held: p2 (N75 193.2 A, predicted 190-198); fires in every S75h handover (5, predicted 20-70); the four-module ramp row
  m4_l_m80_10us does not fire; Vo within 1 mV outside 1 MHz.
- Missed:
  - "the N0 rows fire rarely or never": k_N0 fired 549 times;
  - "the four-module rows do not fire": m4_s_p250 fired 1843 times;
  - the item-2 rows under 200 A: a_S75h_d2 is 200.8 A.
- The registered risk (truncated pulses short the series capacitors of charge) happened, as a full collapse.

## 3. Limits
- The overshoot on 2.933 nH was scaled by L, not measured. The 125 % load was run on N0 only.
- A limit that acts in every period needs an overload response that keeps the ladder. None was designed or tested
  here, and how the controllers in A253's sources respond to repeated limit events was not checked.
