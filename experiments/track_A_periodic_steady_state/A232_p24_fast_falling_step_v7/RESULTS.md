# A232 - the fast falling step on plant V7: does item 3 survive the adopted controller? (RESULTS)
Boundary: 6e12ef8. Records: release records-a232 (14 cosim records, log). Analysis: a232_analyze.py -> a232_summary.json.
Runs from 665000d (10) and f9ae1de (4; docs and cfgs only), cosim_sources_modified False. -4.8 V / 1 us at 500 us +
k T / 6, plant V7, one module, 25 C; arms d0 (the final configuration before A229) and b (the adopted one, A229).

## 0. Verdict
- **z2 passes, z1 misses: item 3 stays open, much smaller than on V6.** Every run completes within the limits: post-step
  peaks 153.7-165.5 A, V_DS <= 29.8 V, Vo -9.4 / +3.7 mV after the step and back within 1 %.
- **N0 and S75 show no restart and no NEW spike** at any position in either arm (V6, A212: 3 K3 restarts and 3 NEW
  events on N0 at one position). The oracle's known classes remain (K4 1-2, K1 1-2 on N0).
- **N75 keeps one restart and one spike at one or two of three positions, in both arms**: phase 3 restarts (K3) 20.7-21.0
  us after the step and its next peak is 17.5-19.8 A above its neighbours (NEW; 151.5 / 153.1 A) - k4 in d0 and b, k0 in
  d0 (records cosim/run_f_N75_k4_b.json, run_f_N75_k0_d0.json). Being in both arms, it is the phases 2-4 slot logic's
  (A148's valley loss), not the damped loop's.
- The damped loop changes the post-step peaks by -8.0..+2.5 A (N75 k0: 164.2 -> 156.2 A, its d0 peak being the spike).

## 1. Criteria (arm b)
| row | post-step peak | oracle events after the step (b; d0) | z1 / z2 |
|---|---|---|---|
| N0 k0 / k2 / k4 | 164.0 / 160.9 / 164.2 A | K4 2; K4 1 + K1 2; none (d0: none; K4 1; none) | pass / pass |
| N75 k0 / k2 / k4 | 156.2 / 153.7 / 162.8 A | none; none; **K3 1 + NEW 1** (d0: K3 1 + NEW 1; none; K1 1 + K3 1 + NEW 1) | k4 **miss** / pass |
| S75 k0 | 160.3 A | none (d0 none) | pass / pass |

## 2. Predictions
- Held: peaks 170-180 A (lower: 153.7-165.5); b within 2 A of d0 except where d0's peak is the spike; events
  unchanged by the controller (N75 k4 identical in class and timing).
- Missed: K3 restarts on N0 at 1-2 of 3 positions (none on V7).

## 3. Limits
- One module, 25 C, nominal / slow boards at L0 / 0.75 L0; three positions per board (one for S75). Why phase 3 restarts
  ~21 us after the step on N75 is not traced.
