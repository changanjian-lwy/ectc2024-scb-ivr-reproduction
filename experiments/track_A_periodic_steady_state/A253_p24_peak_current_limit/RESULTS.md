# A253 - a cycle-by-cycle peak current limit for item 10's 1 MHz train (RESULTS)
Boundary: 8124d0a (option 0915877). Plant V7, single module. Records: cosim/run_o_*.json, 8 runs from 00fca32
(cosim_sources_modified False; release records-a253). 00fca32 fixes a NameError on the option's on-path: the first
launch failed every run at once, the regression has no "ocp" case. Analysis: a253_analyze.py -> a253_summary.json.
References: A246 run_h_ (the final configuration).

## 0. Verdict
- **o1 fails (wiring), traced and fixed after the runs.** Rows where the limit never acted still left their reference
  (p_N75_100k, a_S75h_d20, a_S75_d20, k_S75h). A stale limit turn-off was dropped only after the plant had stepped to
  its time, which split the integrator's step.
  - The currents part at float level from the first crossing (p_N75_100k at 148.94 us, k_S75h at 134.38 us; turn-on
    times still equal). The runs then drift: a_S75h_d20 peak 207.78 A in both, k_S75h within 0.01 A.
  - p_N0_100k (145 A on 2.933 nH) is equal: its current never reaches the level there.
  - The fix drops a stale turn-off before the step (f4657c3), so a run with no fire is the reference bit for bit.
- **o2: S75h 1 MHz passes, N75 1 MHz misses with fires** (the rule's "cap estimate is wrong"):
  - S75h 1 MHz: 199.1 A against 211.1 A, 4 fires; Vo minimum 980.3 against 976.4 mV.
  - N75 1 MHz: 212.1 A against 244.6 A, 13 fires; Vo minimum 980.0 against 981.7 mV (o4 passes).
- **Measured overshoot (the registered cap assumed about 60 / 45 A plus 12 A):**
  - In the 11 ns path (t_ns 1 + t_drv 10), the current rose 49-69 A above the 130 A level on 2.2 nH. That is 4.5-6.3
    A/ns, steeper than the pulse's mean slope (3.8-5.1 A/ns): the slope rises toward the on-time's end.
  - The gate's own turn-off adds 8-14 A (gate record i_max against the current at the command).
  - Level + 82 A at worst, so 130 A caps at about 212 A.
- **o3 misses on the item-2 rows (S75h 125 C re-application):**
  - a_S75h_d2: 209.9 against 211.2 A, 16 fires.
  - a_S75h_d20: 207.8 A, no fire. The controller's own turn-off came within 11 ns of the crossing.
  - Both references were already over 200 A (A225's item 2, open for slow boards).
- **No fixed level fits both sides at 11 ns.** A 200 A cap needs about 110 A on 2.2 nH. But every S75h row reaches
  169.4 A in the start-up's handover, where such a level would act. A re-registered level (A254) must therefore include
  every row the limit can reach.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| o1 | identity rows equal to the reference, no fires | **fail**: p_N75_100k differs (no fire; wiring, fixed); p_N0_100k equal |
| o2 | 1 MHz rows: q1 + q2 | **miss** on N75 (212.1 A, 13 fires); S75h passes (199.1 A) |
| o3 | stage-2 rows: whole <= 200 A, NEW, post-event peak, Vo | **miss** on a_S75h_d2 (209.9 A) and a_S75h_d20 (207.8 A); a_S75_d20 and k_S75h pass |
| o4 | 1 MHz rows: q3, Vo minimum >= reference - 2 mV | pass (N75 -1.7 mV, S75h +3.9 mV) |

## 2. Predictions
- Held: fires on N75 / S75h 1 MHz and a_S75h_d2 (13 / 4 / 16), Vo within 2 mV.
- Missed: peaks 190-200 A (212.1 on N75, 209.9 on a_S75h_d2); a_S75h_d20 had no fire; k_S75h and a_S75_d20 were not
  equal to their references (the wiring).

## 3. Limits
- The latency (t_drv 10 ns) is the controller's own driver path. A comparator inside the power stage might be faster,
  but no source gives that delay, so it was kept.
- The overshoot was measured on 3 rows, all on 2.2 nH. For other inductances it is scaled by L.
