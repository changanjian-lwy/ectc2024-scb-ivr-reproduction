# A246 - a report with positive current lifts a delay far below the other phases' (item 10) (RESULTS)
Boundary: 6386b51 (code eaff266); c1 cfgs 32434d8 (no change under src/). Records: release records-a246 (54 runs and
logs, plus the two pilot rounds of BOUNDARY Section 1), all cosim_sources_modified False, all COMPLETED. Analysis
a246_analyze.py -> a246_summary.json; figure a246_figure.py -> a246_held_report_floor.png. Plant V7, one module (stage 2
also four modules); arm w = A244's record (final configuration), arm h = final configuration + rev_n 16 + hold_floor_ns 3.0.

## 0. Verdict
- **Adopted by user decision on 2026-10-25, after these results** (hold_floor_ns 3.0 in the final configuration, one
  and four modules). Item 10 closes at 10-200 kHz; 1 MHz stays the ladder's limit (A244).
- **Not adopted as registered: g8 misses on 2 rows (the detector), and g9 on S75h at 100 kHz fails c1 (Vo's minimum
  1.3 mV below arm w's worst).** Put to the user with the evidence below.
- **The lock is gone (g10 pass; figure, top row).** N0 at 100 kHz: 190.5 -> 150.9 A (records A244
  `cosim/run_w_p_N0_100k.json`, `cosim/run_h_p_N0_100k.json`). From 500 us A244's phase 4 sits at 7.5-9 ns and every
  re-application reaches 178-190 A. Arm h's phase 4 still drops in light halves (to 10-12 ns) but is lifted at the next
  positive report; from 500 us it stays at 15-16 ns and every re-application at 134-151 A. Train moved by k T / 6,
  k 0 / 2 / 4: arm h 150.9 / 156.4 / 156.3 A, arm w 190.5 / 156.4 / 190.5 A (the lock forms at two of three positions;
  at k 2 it does not, and both arms are equal; in panels (c) and (f) equal points hide the open marker).
- **The option does only what it is meant to (post hoc, a246_analyze.divergence).** 36 of 46 rows equal A244's record
  bit for bit. On each of the other 10, the first change is a phase-4 turn-on made later, to a delay equal to the other
  phases' smallest minus 3 ns (|delay - floor| <= 0.001 ns).
- **g8's miss is the detector.** It counts only lifts to >= 8 ns (registered against ambiguous pairing at 1 MHz). On S75h
  at 60 / 200 kHz the floor lifts phase 4 at shorter delays: 4.56 -> 4.81 ns at 320.19 us (phase 3 at 7.81 ns), 3.94 ->
  4.44 ns at 330.92 us (phase 3 at 7.44 ns). Peaks equal, Vo's minimum -0.7 / 0.0 mV.
- **The cost: S75h at 100 kHz dips 1.5-2.1 mV deeper wherever the floor acts** (k 0 0.9713 against 0.9728 V, k 2
  0.9715 against 0.9736 V, k 4 no act, equal 0.9726 V; peaks 153.9 / 161.1 / 170.5 against 155.8 / 161.1 / 170.5 A).
  Mechanism (k 0, step at 330 us): A244's phase 4 enters the step with a collapsed delay of 4-7 ns against the
  others' 9.5-10 ns. It turns on early and gives extra volt-seconds, which helps this step (0.9746 V at 332.6 us).
  Arm h has lifted it to 9.3-9.7 ns, so the step gets no extra (0.9713 V). The help is the imbalance that makes N0's lock.
- **Elsewhere:** peaks equal or lower on every row (N0 60 kHz 159.8 -> 158.5 A, N75 1 MHz 246.1 -> 244.6 A, excepted);
  Vo's minimum within -0.7..+3.5 mV of A244 on the other rows. The matrix's lowest stays 0.9418 V (N0 60 kHz, equal).
  Stage 2: k_N0 and m4_s_p250 (four modules) act 2 / 11 times, post-event peaks within 0.04 A, Vo extremes equal.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| g0 | unit 137 / 137, regression quick + full | pass |
| g1, g2 | stage 1: A240's q1, q4 | pass on 16 / 18; N75 / S75 at 1 MHz miss, excepted by the rule (244.6 / 211.1 A) |
| g3, g4 | stage 1: A240's q2 and q5; dips within 5 mV of A240 | pass (18 / 18) |
| g5, g7 | stage 2: limits; skipping rows | pass |
| g6 | stage 2: peak, NEW, Vo against the reference | miss 3 / 28: f_N75_k2, a_S75_d20, m4_l_m80_10us - equal to A244's records bit for bit (A244's own misses, c1 passed there) |
| g8 | rows where the floor never acts equal A244 | **miss 2 / 46**: p_S75h_60k, p_S75h_200k - the floor acted below 8 ns, the detector missed it |
| g9 | no row worse than A244's record | **miss 1 / 46**: p_S75h_100k (Vo's minimum -1.5 mV) |
| c1 | g9's row at k 0 / 2 / 4, worst against worst | **miss**: Vo 0.9713 against 0.9726 V (-1.3 mV); peaks 170.5 / 170.5 A |
| g10 | N0 100 kHz at k 0 / 2 / 4 within 171.5 A | pass (150.9 / 156.4 / 156.3 A) |

## 2. Predictions
- Held: N0 at 100 kHz 145-160 A at all three positions; N0 60 kHz and S75h 60-200 kHz within 2 A of A244; N75 1 MHz
  240-250 A; the floor acts on 5-15 rows (10: pulse rows, four modules at +250 A, k_N0).
- Missed: the risk was named on re-application and falling-line rows (both equal A244); the cost came on S75h 100 kHz's
  dips, not foreseen.

## 3. Limits
- Not tested: bands other than 3 / 4 ns; start-ups into a light load (A245's rows; A244's rows all start at full load,
  and the floor can act from phase 1's 32nd turn-on in mode P); four modules under the accelerator load. 1 MHz stays the ladder's limit (A244).
- The detector registered for g8 misses lifts below 8 ns; the post hoc divergence check covers every changed row instead.
