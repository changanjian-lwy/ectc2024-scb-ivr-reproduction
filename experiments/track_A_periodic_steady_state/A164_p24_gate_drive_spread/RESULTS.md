# A164 - the gate drive over the datasheet spread: 3.0 ohm +-20 %, high-side turn-on lead, per-board start-up trim (RESULTS)
Boundary: 1ac40b5 (ce50718 + stage-2 cfgs). Records: release records-a164 (18 runs; cosim_cal, cosim_cal_r35,
cosim_pre). Outputs: a164_summary.json (a164_analyze.py), trims.json, a164_pre.json.

## 0. Verdict
- **FAIL as registered: 10 of 17 rows pass, four modules pass.**
  - Every nominal, hot and fast-corner row holds its peaks and voltages.
  - L x 0.7 fails on start-up, and ff -8 V / 10 us misses Vo by 0.6 mV.
  - The slow corner fails on timing faults that have no peak or voltage consequence.
- **The trim works.** One start-up per board puts Vo(143.5 us) at 1.035-1.038 V on every board. The first guesses were
  within 0.014 V; the trims run from 34.8 ns (L x 0.7) to 48.3 ns (slow corner).
- **Peaks and voltages hold at every corner:**
  - V_DS <= 34.1 V nominal, 38.5 V at the fast corner (predicted 38.6), 32.6 V hot, 31.6 V slow;
  - physical post-step peaks <= 192 A;
  - command-time post-step peaks within the A152 reference + 5 A on every row.
- **Four modules (nominal):** 33.7 V, start-up 162.9 A, post-step 182.6 A physical / 172.0 A command-time, 0 late
  fires. A163 had 38 late fires at module 4's phase-4 limit. Edge power 2.9 W per module.
- **The lead is needed even at nominal with 3.0 ohm.** Without it, +4.8 V / 1 us gives 48 late fires after the step.
  With 8 ns there are none, and the steady phase-4 dt_pred is 14.5-15.2 ns instead of 6.5-7.2 ns.
- **Misses:**
  - **L x 0.7, start-up 218.6 A.**
    - Mode S peaks at 202.5 A physical, against 215.6 A in A163 and 205.6 A for A152's ramps: the frozen design's
      open-loop start at L x 0.7, eased by the trim.
    - The 218.6 A comes 2.4 us into mode P, on phase 1. The lead moves only the predictive turn-on, so every mode-P
      pulse is 8 ns wider than mode S's. That is an on-time step at the handover. At L0 the same step adds 10 A
      (140.7 -> 150.6 A, A164 pre).
    - Fix tested in A165: move the whole pulse.
  - **Slow corner (4 rows), criterion 3.** 65 late fires in the handover (150-200 us), none in steady state, ~160
    more after the rising line steps, where hard turn-ons take up to 16.6 ns (limit ~13.5 ns with the lead).
    NEW spikes (1-14 per row) follow the steps: one-period peaks 10-13 A above their neighbours, <= 176 A. The handover
    peak is 199.5 A.
  - **ff -8 V / 10 us, criterion 4:** Vo +28.5 mV against 27.9 mV allowed. At nominal the same row gives -20.9 mV.
- **Edge power per module** (600-950 us, high sides gate-driven, low sides on A152's ramps):
  | board | nominal | ff | hot | slow | L x 0.7 | L x 1.3 |
  |---|---|---|---|---|---|---|
  | W | 2.5 | 2.3 | 3.0 | 4.7 | 4.4 | 1.6 |
  The loss budget's ideal-edge terms leave out 1.0-1.9 W of this. At the slow corner the budget's hard-turn-on term
  already exceeds it.
- **The +-30 % pre runs (a164_pre.json, cosim_cal_r35)** are the reason for +-20 %. At 3.5 ohm x 1.3 the slow corner
  has turn-on delays of 9-20 ns and transitions up to 32 ns. Its handover reaches 216-228 A with an 8-9.5 ns lead, and
  209 A even with the valley seed at its learned value.

## 1. Criteria
| rows | 1 V_DS | 2 start / Vo | 3 post / late / NEW | 4 Vo | misses |
|---|---|---|---|---|---|
| nom (6) | 6/6 | 5/6 | 6/6 | 6/6 | L07 218.6 A |
| ff (3) | 3/3 | 3/3 | 3/3 | 2/3 | l_m80 +28.5 mV (27.9 allowed) |
| ss (4) | 4/4 | 4/4 | 0/4 | 4/4 | late 65-226, NEW 1-14 |
| hot (2) | 2/2 | 2/2 | 2/2 | 2/2 | |
| no-lead controls (2) | 2/2 | 2/2 | 1/2 | 2/2 | l_p48 late 48 |
| four modules | 33.7 V | 162.9 A | 182.6 / 172.0 A, late 0 (A163: 38) | - | |

## 2. Limits
- Low sides keep A152's ramps. The plant's devices are identical within a board. The lead is applied in the bridge,
  so it is bounded by t_drv (10 ns).
- The slow corner stacks threshold max, Q_G max and the driver's +20 %.
- Hot is 125 C on the devices only (no electrothermal loop).
