# A215 - a controller a synthesis tool can build: the port expression and the Ton path as a multi-cycle path (RESULTS)
Boundary: 5c6aacd. Records: release records-a215 (21 cosim records, logs). Analysis: a215_analyze.py ->
a215_summary.json; synthesis a215_synth.py -> a215_synth.json (A209's flow: yosys 0.49, `abc -fast -liberty`, sky130
hd typical and Nangate 45 nm typical, our own timing estimate a209_sta.py). Runs from 5c6aacd,
cosim_sources_modified False on all 21. Final configuration on plant V6 (low sides 0.3 ohm x the board's factor,
A206's trims, ton_min_ns 4.0 ns), one module; references are the source records (A212, A206, A208, A210).

## 0. Verdict
- **c1, c2, c4, c5, c6 pass; c3 fails. The final configuration takes ton_lat 16** (68 ns from the sampling instant
  to the phases' registers). Tested bound: 17 clocks.
- **M = 16: all nine rows pass their source experiment's criteria.** Post-step peaks move by -6.3 .. +1.1 A against
  the references (binding row now S75 25 C k 4, 196.95 A; was 197.57 A on S75 125 C), Vo before 300 us is
  unchanged to 0.1 mV, and the handover peak on N0 falls from 161.98 to 148.89 A (not traced).
- **M = 32 fails on four rows, for two reasons.** (a) Both 30 % rows run away (N0: Vo 0.85-0.89 V at the end with the
  loop at its upper Ton clamp 88.97 ns; N75: Vo 1.151 V with the loop at its 4.00 ns limit): a flaw in my register
  logic. The divider's completion, 32 clocks after a sample, counts as a source event and restarts the count, so
  for M >= 31 the registers load only if the period is longer than 32 + M clocks (256 ns at M = 32). The 30 % rows
  run at 181-232 ns (records cosim/run_m16_m30.json, run_m16_r_N75_25_30.json, 400-450 us), so the phases never
  see the loop again. For M <= 30 the first load comes M + 1 clocks after the sample, before that event.
  (b) Two binding rows cross 200 A: N75 25 C 202.40 A (phase 3), S75 125 C 203.21 A (phase 2); these run at about
  500 ns, above 256 ns; the cause was not traced.
- **Synthesis: no Ton arithmetic reaches a phase register within a clock in the M = 16 build.** Longest path into a
  phase register 13.53 ns sky130 (1.33 x scb_phase alone) and 3.08 ns at 45 nm (under the 4 ns clock); into the new
  registers 23.0 / 4.80 ns (16 clocks allowed). Without the registers (M = 0) the arithmetic reaches 37 phase
  registers and the longest path is 30.6 / 6.45 ns (ton_acc -> phase 1's t_lon).
- **What still exceeds the 4 ns clock at 45 nm**: ton_acc -> scb_vff's divider numerator dnum, 5.14 ns (sky130
  25.1 ns), through the relative cap's product. dnum loads at vin_valid, which comes in the same clock as Vo's sample,
  so in operation ton_acc is a period old there: a multi-cycle path that needs a stated constraint or a register.
  Read from the RTL, not checked by a tool. In sky130 the phase logic itself (13.5 ns) needs a clock of about 16 ns.
- **Slower clocks regulate.** 8 ns clock (fb 8, ton_lat 8): +62.5 A 181.94 A, +4.8 V / 2 us 183.60 A, 0 late fires.
  16 ns clock (fb 9, ton_lat 4; the same 31.25 ps LSB from a 9-bit fine delay): +62.5 A 181.45 A, Vo -15.3 mV, 0 late
  fires. One row: a slower clock with a finer delay line is a candidate for a 130-180 nm node, not yet an answer.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| c1 | unit tests, regression quick / full with the option absent | pass (95 of 95; 4 / 4 bit for bit) |
| c2 | nine rows at M = 16 pass their source criteria | **pass** (9 / 9) |
| c3 | the same at M = 32 | **fail** (m32_m30, m32_r_N75_25_30, m32_B_N75_25 202.40 A, m32_B_S75_hot 203.21 A) |
| c4 | 0 front-end problems, files unmodified | pass (scb_ctrl 126 304 cells, phases 16 046 / 11 996, scb_vff 68 581, scb_multi 220 484) |
| c5 | no arithmetic -> phase register path; <= 15.3 / 3.66 ns; 45 nm < 4 ns | pass (0 paths; 13.53 / 3.08 ns) |
| c6 | into the new registers <= 64 ns | pass (23.03 / 4.80 ns) |

| row (M = 16 / M = 32 / reference) | post-step peak | handover peak | Vo after the stimulus | late fires (end) |
|---|---|---|---|---|
| N0 +4.8 V / 2 us | 182.01 / 181.97 / 184.10 A | 148.9 / 150.0 / 162.0 A | -8.5 +9.3 / -4.9 +7.9 / -6.6 +8.0 mV | 0 |
| N0 -4.8 V / 1 us | 168.68 / 171.39 / 171.68 A | as above | -8.2 +1.0 / -10.5 +5.3 / -9.1 +2.9 mV | 0 |
| N0 -8 V / 10 us | 164.96 / 165.39 / 169.53 A | as above | -25.5 +25.2 / -27.2 +19.1 / -26.5 +21.4 mV | 1 / 0 / 0 |
| N0 +62.5 A | 181.91 / 181.55 / 181.54 A | as above | -15.4 / -15.9 / -15.0 mV | 0 |
| N75 25 C k 4 | 189.93 / **202.40** / 196.24 A | 149.4 / 149.1 / 150.5 A | -9.3 +11.7 / -13.0 +13.2 / -8.8 +8.5 mV | 0 |
| S75 25 C k 4 | 196.95 / 193.79 / 195.81 A | 155.3 / 150.4 / 154.5 A | -14.1 +9.5 / -13.9 +9.2 / -11.7 +9.9 mV | 71 / 94 / 51 |
| S75 125 C k 5 | 195.17 / **203.21** / 197.57 A | 181.1 / 180.9 / 182.1 A | -13.2 +9.5 / -17.2 +10.3 / -12.9 +10.3 mV | 2 / 6 / 10 |
| N0 30 % (A208 m30) | Vo 0.9997-0.9999 / **0.851-0.888** / 0.9997-0.9998 V | | | 0 |
| N75 30 % (A210) | Vo 1.0002 / **1.151** / 0.9998-1.0001 V | | | 0 |
- Vo before 300 us (start-up): 1.0336 / 1.0323 / 1.0351 / 1.0476 V on the four start-ups, as in the references.
- S75 25 C has more late fires at M = 16 (71 against 51, phases 3-4); A206's c6 has no late-fire limit.

## 2. Predictions
- Held: all nine rows at M = 16; Vo before 300 us; c4; 8 ns clock regulates within 5 A; longest path into a phase
  register 13.5 ns (10-14) and 3.08 ns (2.4-3.4).
- Missed: peaks moved down more than predicted (-6.3 .. +1.1 against -1 .. +2 A; binding 196.95 against
  198.1-199.1 A); Vo after a step moved by up to 3.8 mV (under 2 predicted); M = 32's 30 % rows (runaway, not a
  1-3 mV band: I did not see the starvation); the 16 ns clock (predicted to fail, passes); late fires at 8 ns
  (none); cell count 84 442 (55-80 thousand); paths into the new registers 23.0 / 4.80 ns (25-40 / 5-9) and
  without them 30.6 / 6.45 ns (35-47 / 8-10.5).

## 3. Limits
- One module, the nine rows of the boundary; no ADC model of its own (M stands for conversion + arithmetic).
- Timing estimates as in A209 (no wires, no clock tree, typical corner); the multi-cycle character of ton_acc ->
  dnum is read from the RTL. The register-loading flaw is not fixed here: the bridge will refuse ton_lat > 30.
- Basis: registering a value that changes once per switching period is ordinary multi-cycle timing practice; no
  source of the project's literature treats this controller's timing.
