# A163 - the package drive as gate resistances, with gate-driven edges in the plant (RESULTS)
Boundary: 57a180f. Records: release records-a163 (29 runs + 15 start-up diagnostics). Outputs: a163_summary.json
(a163_analyze.py), a163_startup_diag.json (a163_startup_diag.py, post hoc, cosim_diag/).

## 0. Verdict
- **FAIL as registered (A, B and D all miss).** D (75 pH, 3.5 / 0.3 ohm) holds V_DS (<= 36.4 V) but has 7-24 late fires
  on three line-step rows (mechanism 2 below). The resistor drive (50 pH, 2.5 / 0.3 ohm) is not the package spec yet.
  The decision rule's "B fails" branch applies: A164 takes the datasheet-consistent spread, a margin on r_on, a high-side
  turn-on lead and a per-board start-up trim.
- **Nominal devices behave as predicted:**
  - V_DS <= 36.4 V on every row (A152 ramps 37.6 V). Edge power 2.4 W per module at L0 (A152 ramps 3.9 W).
  - The deferred valley measurement works: the command lands 2.4 ns before the valley, the channel starts at the valley
    (error 0.11 ns, V_DS 3.5 V). Measured at the command instead (C), the turn-on lands a gate delay late: +0.5 W.
  - Whole-run physical peaks are within -1.9..+1.8 A of A152's physical peaks on the L0 / L x 1.3 rows. The registered
    criterion 3 compares physical peaks with A152's command-time peaks, so 9 rows miss by definition (+5..+9 A). Command
    against command, A163 is 2.3-5.9 A lower (L x 0.7 3.0 / 7.2 A).
- **Three mechanisms break the spread (B), each with its own fix:**
  1. *Start-up on-time.* Mode S's on-time is open loop, so every corner shifts Vo(143.5 us) at the registered ton:
     | corner | -0.3 V | nom | +0.5 V | +1.0 V | +1.5 V | C_ISS x 1.5 | driver x 0.7 |
     |---|---|---|---|---|---|---|---|
     | Vo (V) | 1.043 | 1.012 | 0.958 | 0.903 | 0.833 | 0.980 | 1.037 |
     | handover peak (A) | 148 | 157 | 239 | 376 | 368 | 190 | 148 |
     - The handover has a cliff below Vo ~0.99 V. Above it the peak stays <= 157 A, all the way to 1.17 V.
     - Slope 0.025-0.0265 V/ns. A fixed ton high enough for +1.0 V puts a nominal board at 1.11 V. Fix: trim each
       board's start-up ton (A164).
  2. *Valley timing.* The RTL schedules a predictive turn-on no earlier than one 4 ns clock after the low side's
     turn-off command (dt_pred >= 0, decided in the next window). The valley comes 9.5 ns after that command on phase 4
     and 11.1 ns on phases 1-3. So the gate delay (command to channel start) must stay below ~5.5 ns on phase 4 and
     ~7 ns on phases 1-3.
     - Measured on phase 4: nominal 2.4 ns; +1.0 V 6.0 ns (late fires begin); +1.5 V 7.2 ns, which gave 1407 late fires
       on phase 4 and spikes to 172 A in steady state.
     - The four-module run's 38 late fires are this limit at nominal: module 4's phase 4 drops to a 3.1 ns gap
       (5th percentile).
     - Fix: a lead on predictive high-side turn-ons (A164).
  3. *Driver -30 %* (1.75 ohm): 40.6 V on +4.8 V / 1 us. That is 1.6 V above the single-edge harness. Fix: r_on margin.
- **Two of the registered corners are outside the datasheet.** This was my error in D79.
  - EPC's typical curve already has V_GS(TH) 1.51 V at 18 mA. Shifting it +1.5 V gives 2.99 V and R_DS(on) 1.81 mOhm,
    beyond the 2.5 V / 1.55 mOhm maxima. +1.0 V meets both (2.49 V, 1.53 mOhm).
  - C_ISS x 1.5 matches C_ISS max, but scales Q_G to 25.8 nC, beyond the 22.3 nC max. x 1.29 is consistent.
  - The B verdict above stands as registered; A164 uses the consistent corners (tests/test_p24_gate_model.py).
- **The ramp results were judged at command time.** A145-A162 counted the current when the turn-off was commanded. The
  physical peak comes 5-8 A later. A152's L x 0.7 start-up was 197.9 A at command time and 205.6 A physical.
  - Here L x 0.7 reaches 215.6 A, in mode S at 137 us. The ton calibrated at L0 over-delivers at L x 0.7 (Vo 1.147 V).
  - The per-board trim addresses this too.
- **Efficiency:** the loss budget's ideal-edge switching terms (0.9 + 0.3 W) miss 1.3 W per module of gate-driven edge
  power at L0 (~0.5 % at 250 W). Low sides still use A152's ramps.

## 1. Criteria
| part | rows | 1 V_DS | 2 start | 3 post / late / NEW | 4 Vo | misses |
|---|---|---|---|---|---|---|
| A S50 | 13 + m4 | 14/14 | 12/14 | 5/14 | 14/14 | L07 x2 215.6 A; peaks definitional (9 rows); slew4 late 5; m4 late 38 |
| B spread | 8 | 5/8 | 6/8 | 0/8 | 8/8 | vthmax 46.6 V / 368 A / 1678 late; cissmax late 179 / 44 + 3 NEW; r07 40.6 V |
| C cmd | 2 | diagnostic | | | | s_p62 back 9.0 us (ref 6.8), l_p48 1 NEW |
| D S75 | 5 | 5/5 | 5/5 | 1/5 | 5/5 | late 7 / 12 / 24 (l_p48, l_m80, slew2: phases 2-4 after the line steps, gate delay up to 6.8 ns at 3.5 ohm); peaks definitional |

## 2. Limits
- The low sides keep A152's ramps. The plant's 20 devices are identical, and the driver is an ideal 5 V source behind a
  resistor.
- Late fires are whole-run totals. Their timing was inferred from command-to-turn-off gaps (A164 logs them per section).
- The start-up diagnostics run to 190 us only. Their late-fire counts include up to 45 us of mode P after the handover.
