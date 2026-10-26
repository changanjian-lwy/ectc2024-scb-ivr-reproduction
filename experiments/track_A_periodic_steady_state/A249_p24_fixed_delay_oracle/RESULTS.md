# A249 - one fixed turn-on delay per board in the closed loop (an oracle test of A247 / A248) (RESULTS)
Boundary: 5529c36 (option b3093a2). Plant V7, single module. Records: cosim/run_[so]_*.json, 18 runs, from committed code
(release records-a249). Analysis: a249_analyze.py -> a249_summary.json. Post hoc trace: a249_trace.py -> a249_trace.json.
Figure: a249_figure.py -> a249_fixed_delay_oracle.png. References: the final configuration's records (A246 run_h_ /
run_ch_; A245 run_r_u_S75h_30).

## 0. Verdict
- **c0 and c1 pass in both arms; c2 misses on p_S75h_100k.** By the rule, before step 3 I name what the learner's
  per-period adaptation bought on that row. It is also named for the start-up row, where the registered risk showed
  although c2 passed.
- **The N0 lock does not need the learner.** With phases 2-4 held at one value, the N0 100 kHz train peaks at 149.5 /
  152.2 / 160.6 A at k 0 / 2 / 4 (arm s; the final configuration 150.9 / 156.4 / 156.3 A; limit 171.5 A).
- **Steady and stage-2 rows hold** (arm s): N0 60 kHz, N75 100 kHz, N75 falling line and S75h re-application are each
  within 2 A (10 A on the re-application) and 1 mV of the final configuration.
  - On S75h a fixed delay removes the hard turn-ons: 0 against 312 (re-application) and 0 against 396 (start-up). The
    largest V_DS at turn-on is 5.5 V there, against 9.2 V.
  - On the N0 rows the hard turn-ons are the same (1325-1343 against 1330-1363). They are valley turn-ons with no window
    (A247), not the learner's doing.
- **What the learner bought: both times through its collapse.** Its phases 2-4 delays fall to 3.6-5.8 ns, the
  behaviour A236-A246 limited, and that acted as an actuator (figure).
  - **S75h train (c2 miss: Vo minimum 968.8 against 971.3 mV).** At the first release (305-310 us) the learner's phases
    3-4 collapse: 5.8 / 3.8 ns against 11.3 / 10.7 ns fixed. Their valleys go to -39 / -43 A against -22 A, and the period
    is 265 against 207 ns.
    - Vo then peaks at 1028.4 mV, not 1037.0, and is at 1006.8 mV, not 1019.5, when the load returns at 310 us. Ton is at
      559 LSB there, not 242.
    - The first dip is 978.2 against 968.8 mV. The learner's own deepest dip comes two pulses later (971.3 mV).
    - From pulse 4 on, the two arms are within 1.2 mV pulse by pulse. The whole 2.5 mV comes from the first release.
  - **S75h 30 A start-up (c2 passes: 0.54 V at the end, still falling).** Both runs enter mode P with phases 2-4
    turning on a clamped node (V_DS -2.2 V) and the ladder off by about 3 V.
    - Fixed: once the driver's lead has ramped in (112 us), the commands are deferred. Phases 2-4 turn on 13.4-14.1 ns
      after t_lo, on a clamped node, with valleys of -48 to -60 A.
    - While Vin ramps to 48 V, rail 1 takes the rise: 17.7 V at 140 us, a deviation of 6.4 V at 137 us.
    - Learner: its phases 2-4 collapse to 3.6-3.8 ns at 110-130 us (V_DS 1.6-3.8 V), and the ladder is within 1 V by
      about 130 us.
    - Peaks (118.5 / 119.0 A), V_DS maxima (27.9 / 28.3 V) and Vo are the same. Late fires: 2 against 167.
  - The timing matches: the deviation falls when the collapse happens. The causal chain is not isolated. My working
    hypothesis: when the node clamps, the turn-on delay changes the phase's charge per period. No source covers the
    delay as a ladder or charge actuator in an SCB (not yet searched).
- **Arm o does worse than arm s:**
  - N0 k4 171.3 A (0.2 A of margin);
  - f_N75_k4 +2.5 A (c2 by 0.5 A);
  - hard turn-ons on N75 1859 against 1398, and 1210 against 320.

  A248's open-loop window centre, mapped to a command at -17 A, does not carry into the closed loop. The learner's own
  settled value does.

## 1. Criteria
| # | criterion | arm s | arm o |
|---|---|---|---|
| c0 | phases 2-4 dt_pred at the end = dt_fix_ns within 1 LSB | pass, 9 / 9 | pass, 9 / 9 |
| c1 | N0 100 kHz k 0 / 2 / 4: peak after 300 us <= 171.5 A | pass: 149.5 / 152.2 / 160.6 A | pass: 147.7 / 153.5 / 171.3 A |
| c2 | other rows no worse than the final configuration | **miss on p_S75h_100k**: Vo minimum 0.9688 against 0.9713 V (tolerance 1 mV) | **miss** on p_S75h_100k (the same) and f_N75_k4 (+2.5 A, tolerance 2 A) |

## 2. Predictions
- Held: c1 in both arms; p_S75h_100k has no collapsed phase.
- Missed:
  - c1 inside 145-160 A: k4 gave 160.6 A (s) and 171.3 A (o).
  - p_S75h_100k's Vo minimum within 1 mV: it is 2.5 mV lower.
  - u_S75h_30 in band at the end: 0.54 / 0.72 V, not <= 0.3 V.
  - Fewer hard turn-ons on N0: there are the same number.
- The registered risk (a 12 V value at the start-up's low rails) showed as a ladder deviation, not as hard turn-ons.

## 3. Limits and next
- Single module, plant V7, three boards. Not run: four modules, start-ups on N0 / N75, items 2 / 3 on other boards.
- The start-up row ends at 300 us, while the fixed arms are still settling. c2 only reads the end.
- A fixed delay keeps steady state and the N0 lock, but it loses the actuator the learner used by accident. Step 3 has
  to give the transients an explicit path: the start-up ladder while Vin ramps, and the first load release.
  - The literature's structure points that way: the learner only in steady state, plus a transient path (Chiang TPEL
    2009; Yousefzadeh and Maksimovic TPEL 2006).
  - First check how SCB / flying-capacitor converters balance their ladder (literature). Then check in the plant harness
    whether a delay that matches the start-up rails (A248's table stops at 10 V) keeps the node from clamping.
