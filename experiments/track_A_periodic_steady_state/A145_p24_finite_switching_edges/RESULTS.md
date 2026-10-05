# A145 - finite switching edges in the cosim plant (RESULTS)
Boundary: 29daf38. Records: release records-a145 (22 runs). Summary: a145_summary.json (a145_analyze.py); single
edges: a145_edge.json (a145_edge.py). All runs from committed code (cosim_sources_modified False).

## 0. Verdict
- **Plant:** cfg "edge" (channel current as a right-hand-side source; turn-off ramp from i0 > 0, hard turn-on ramp
  until V_DS <= 0). Edges off = A144 bit for bit (2 full runs, harness, regression); Fast / Kernel / Kernel2 identical
  with edges on; h 10 vs 5 ps: 1 mV.
- **Real edges do not remove the overshoot.** V_DS <= 40 V fails at every (L, didt). Best: 50 pH at 72 A/ns
  (143 A in 2 ns), 37.3 V at start-up and 41.8 V after +4.8 V / 1 us. From 100 pH, mechanism B stays at 44-57 V.
  - Why (harness): a ramp turns the loop's L di/dt into channel V x I. The overshoot falls only 6 / 27 % at 100 pH
    (1 / 2 ns), not the 13 / 47 % that a ring's sinc response predicts.
  - A slow edge can raise the overshoot: at 50 pH, 3 ns, the node clamps while the channel still carries ~25 A.
  - The hard turn-on's V_DS fall is short against the ring of the next phase's loop, except at 50 pH.
- **Steady state <= 40 V up to 150 pH** (SH1 15.3 / 25.7 / 32.9 V at 144 A/ns, 16.1 / 23.4 / 30.1 V at 72 A/ns;
  every switch <= 33.9 V).
- **Controller holds everywhere:** 0 late fires, 0 new duplicates, peaks 1.5-13 A below A144's. Turn-off currents
  are 1.4-2.7 A lower: the channel conducts during the ramp and the voltage loop shortens Ton.
- **Loss: the loop spec loosens from ~30 to ~70 pH.**
  - The loop-dependent loss P_L is 1.4 / 3.8 / 6.4 W (144 A/ns) and 1.7 / 3.8 / 6.3 W (72 A/ns) at 50 / 100 / 150 pH.
    1 % of 250 W is reached at 73 / 69 pH.
  - A144's 0.5 L I^2 per turn-off (7.75 W per 100 pH) was twice the energy the damper actually takes.
- **The edges cost on their own:** without a loop, 1.19 / 2.74 W (1 / 2 ns), turn-off and the valley's partial hard
  turn-on together. D62's I^2 t_f^2 / (24 C) with C 13.5 nF is ~30 % low against the plant's turn-off (C_eff 10 nF).
  2 ns edges cost 1 % of the module.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | identity | PASS: id_q7_l100_l_p48_1us, id_q7_l50_n0 = A144 in every field; harness rows; impls identical; regression --full PASS |
| 2 | V_DS <= 40 V whole run | FAIL at all 6 (L, didt); max n0 / l_p48_1us / s_p62: 144 A/ns 45.4-45.7 / 51.8-56.6 / 45.4-45.7 V; 72 A/ns 37.3-45.0 / 41.8-54.7 / 37.3-45.0 V |
| 3 | controller vs A144 q7 | PASS at all 6 + both no-loop rows (late 0, new 0, on-V mean 3.3-3.7 V, Vo back within 1 %) |
| 4 | loss | edge power (n0) 1.36-1.42 W (144), 3.77-4.43 W (72); L_loss 73 / 69 pH |
| 5 | cost | edge steps 1.3 / 2.4 % PASS; wall time x1.6-2.5 vs A144 FAIL (Python edge steps slow under 10 parallel jobs; smoke +27 / +41 %) |

Predictions:
- Steady SH1 15.5 / 26.3 / 33.7 and 16.7 / 23.3 / 30.3 V: held within 0.8 V.
- Whole l_p48_1us 54 / 57 / 57 and 41 / 54 / 57 V: held within 3 V (measured 51.8 / 56.3 / 56.6 and 41.8 / 51.0 / 54.7).
- n0: within 2.3 V. Controller holds: held.
- Edge power with loop: within 8 %. No loop: 0.8 / 2.5 predicted, 1.19 / 2.74 W measured (the valley turn-on share was underrated).
- P_L 1.8 / 4.3 / 7.1 and 2.1 / 4.1 / 7.2 W: measured 0.4-0.6 W lower, so L_loss is ~70 pH, not ~60.

## 2. Decision (registered rule: none passes 2) and limits
- Edges cannot fix the hard-turn-on overshoot; it becomes a control requirement.
  - Next on that line: limit dV at hard turn-ons in start-up and fast line steps (A148, RL in the ML block), or check
    the EPC2067 transient V_DS rating.
- Loop spec from steady voltage and loss: <= ~70 pH for 1 % (steady voltage allows 150 pH).
- Edge rate: 1 ns (144 A/ns at 143 A) costs 1.2 W, 2 ns 2.7 W (no loop), so a <= 1 ns edge is part of the spec.
- Mihai: real on / off di/dt with P24's driver, loop Q, EPC2067 transient rating (D65 list).
- Limits:
  - The edge is a linear current ramp with one di/dt for turn-on and turn-off. There is no gate model, Miller
    plateau or delay, and the channel cannot go back into the ohmic region (V_DS < 0 in an off ramp: <= 192 steps
    per run).
  - The damper loss comes from the harness (143 A, SL1 in reverse conduction), not measured in the closed loop.
  - One module, L x 1.0, three rows, Q 7.
