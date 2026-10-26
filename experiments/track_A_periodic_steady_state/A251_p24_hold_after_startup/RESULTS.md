# A251 - the learner through the start-up, then its delay held (RESULTS)
Boundary: 2df53b4 (option 1172a40). Plant V7, single module. Records: cosim/run_z_*.json / run_cz_*.json (15 of 55 arm-z
runs) and cosim/run_h_u*.json (20 start-ups, the final configuration), from committed code (release records-a251):
27 at 2df53b4, 8 start-ups at 8124d0a (adds A253's bridge option, off). u_N75_20 first ran while the bridge was being
edited (cosim_sources_modified True); its rerun at 8124d0a is the record, equal to the first edge for edge.
Analysis: a251_analyze.py -> a251_summary.json. References: A246 run_h_ / run_ch_, A245 run_r_.

## 0. Verdict
- **Not adopted; arm z stopped after the decision rows** (14 matrix rows + u_S75h_30; 36 matrix rows and 19 start-ups
  in arm z not run). z1 passes, z2 misses on 6 rows, z4 misses. The hold buys nothing the final configuration lacks:
  the final configuration already passes z1 (N0 100 kHz 150.9 / 156.4 / 156.3 A at k 0 / 2 / 4, limit 171.5 A).
- **What the hold costs (arm z against the final configuration):**
  - 1 MHz is worse: S75h 224.4 against 211.1 A, N75 246.9 against 244.6 A (both over 200 A in both arms).
  - p_N0_10k: Vo minimum 963.7 against 968.9 mV (-5.2 mV).
  - S75h 100 kHz at k 0 / 2 / 4: peaks after 300 us lower by 2.4 / 6.9 / 9.3 A, but Vo minima lower by 1.1 / 2.5 /
    2.8 mV (tolerance 1 mV).
  - u_S75h_30 (75 A start-up): end deviation 0.183 against 0.114 V (within z2's tolerance).
- **The learner's per-period adaptation helps the fast transients** (A249's finding, confirmed with the hold after the
  start-up). The final configuration stays: A244 cfg_w + rev_n 16 + hold_floor_ns 3.0.
- **Side result, the floor on start-ups (arm h):** the final configuration on A245's 20 start-ups gives records equal to
  A245's run_r_ edge for edge (turn-ons, high-offs, low-offs; 20 / 20). The floor never acts on a start-up, as
  predicted (it needs a held report with m_pos). A245's g1-g3 hold on all 20 (end deviation 0.079-0.899 V, limit 1.0 V;
  peaks 75.1-169.4 A; V_DS <= 30.9 V). The open caveat "floor never run on start-ups" is closed.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| g0 | unit 144 / 144, regression quick + full | pass |
| z1 | N0 100 kHz k 0 / 2 / 4 peak after 300 us <= 171.5 A | pass: 148.8 / 156.4 / 157.7 A |
| z2 | no worse than the final configuration | **miss** on p_N0_10k (Vo -5.2 mV), p_N75_1000k (+2.3 A), p_S75h_1000k (+13.3 A), p_S75h_100k k 0 / 2 / 4 (Vo -1.1 / -2.5 / -2.8 mV); passes on the other 9 run rows |
| z3 | before the hold, turn-ons equal the reference | pass, 15 / 15 (hold at 232-273 us, before the 300 us train) |
| z4 | 1 MHz rows meet q1 + q2 | **miss**: 246.9 / 224.4 A |
| h_ok | the final configuration on the start-ups meets A245's g1-g3 | pass, 20 / 20 |

## 2. Predictions
- Held: z1 (148.8-157.7 A against 149-161 A); z2 misses on p_S75h_100k; arm h passes on every start-up.
- Missed: z4 (S75h 1 MHz rose, not fell); z2 also misses on p_N0_10k and both 1 MHz rows.

## 3. Limits
- 36 matrix rows and 19 start-ups not run in arm z (stopped by the rule; the decision did not need them).
- Only HOLD_N 256. A hold that starts later (after the train's first releases) was not tested; A249 says the cost sits in
  the first release, so a later hold would not change z4.
- 1 MHz item 10 stays open after this line; A252 (a short fixed delay) and A253 (a peak current limit) test it.
