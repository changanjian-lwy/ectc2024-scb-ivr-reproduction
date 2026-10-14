# A215 - a controller a synthesis tool can build: the port expression and the Ton path as a multi-cycle path (BOUNDARY)
Method: RTL (two changes) + cosim (21 runs) + synthesis (yosys / ABC, A209's flow and timing estimate).
Track A. Written and committed before the cosim runs and the synthesis. Looked at beforehand: the unit tests (95 of
95) and `cosim_regression.py --quick` and `--full` (4 of 4 each, bit for bit) with the new RTL and the option absent;
a 12 us smoke run of three cfgs (timing only). The user unfroze the RTL on 2026-10-14; this is the first batch.
Decision it changes: whether the final configuration takes the registers (cfg "ton_lat"), with how many clocks, and
which RTL changes remain before the controller meets a clock (A209 Section 4, items 1 and 2).
Cheaper check done first: a delay of 68 / 132 ns at the loop's 100 kHz crossover is 2.4 / 4.8 degrees of phase, so
no stability problem is expected; the open question is the peak rows, which only the cosim answers (D63 gives every
phase the new Ton in the sample's period and has no place for a delay inside a period).
Budget: 21 runs, 13.5 run-equivalents of 900 us, about 3 h at 8 jobs; synthesis about 1 h at 2 jobs.

## 1. What and why
- A209: the RTL stops a synthesis front end (a signed wire and an unsigned constant in one port expression), and
  its longest path, from the loop's accumulator through scb_vff into phase 1's edge logic, is 47.0 ns (sky130) /
  10.5 ns (45 nm) against a 4 ns clock. That path's sources change once per switching period.
- Change 1 (scb_ctrl): the constant is written `$signed({TW{1'b0}})`. The same bits.
- Change 2 (scb_ctrl, scb_vff): input cfg_ton_lat = M. With M != 0 the phases read their Ton (and phase 1's lo_add)
  from registers that load M clocks after the last change of anything the arithmetic reads (the sample, scb_vff's
  updates including the divider's result, the handover, a slave's ext_ton). The arithmetic then has M clocks by
  construction, and a new Ton reaches the phases M + 1 clocks later than today. M = 0: the old controller, bit for
  bit. cfg key "ton_lat" (bridge); scb_multi regenerated; six unit tests added.
- The same M stands for an ADC's conversion time: the bridge gives the code in the clock after the sampling
  instant, so M is the whole distance from that instant to the phases (conversion + arithmetic).
- Rows (final configuration, plant V6, lower Ton limit 4.0 ns), each at M = 16 (68 ns) and M = 32 (132 ns):
  A212's N0 rows +4.8 V / 2 us, -4.8 V / 1 us, -8 V / 10 us, +62.5 A; A206's binding rows S75 125 C k 5 (197.57 A),
  N75 25 C k 4 (196.24 A), S75 25 C k 4 (195.81 A); the 30 % rows of A208 (N0) and A210 (N75). References: the
  source records. Three of them ran with another lower limit (A206's rows: 0.5 ton_ns; A208's m30: 2.0 ns); their
  Ton registers never went below 20.5 / 5.5 ns, above both limits, so the limit did not act in them.
- Information rows, cfg only: an 8 ns clock (fb 8, the same 31.25 ps LSB, ton_lat 8) on +62.5 A and +4.8 V / 2 us,
  and a 16 ns clock (fb 9, ton_lat 4) on +62.5 A: what a slower clock would do for a 130-180 nm node, where A209
  found the phase logic 2.5 times too slow.
- Synthesis: the repository's files as they are (front end); the final configuration's build (scb_ctrl with its
  option inputs tied, a215_synth.py TIES; numeric settings stay inputs) with cfg_ton_lat 16 and with 0.
- Not tested: an ADC model of its own, four modules, other corners; the 31.25 ps edge placement stays an assumption.

## 2. Criteria
1. c1 identity (done before this file, repeated in RESULTS): unit tests all pass; regression quick and full pass.
2. c2: each of the nine rows at M = 16 passes its source experiment's criteria, by that experiment's analysis
   function (A212 c6 + c7; A206 c6; A208 / A210 r1, r2, r3, r4).
3. c3: the same at M = 32.
4. c4: yosys reports 0 problems on scb_ctrl, scb_phase (both kinds), scb_vff and scb_multi, files unmodified.
5. c5: in the final build with M = 16, no path from the Ton arithmetic's registers (ton_acc, p_term, scb_vff's)
   reaches a phase's register within a clock (netlist connections), and the longest path into a phase's register is
   at most 1.5 times scb_phase's own (15.3 ns sky130, 3.66 ns at 45 nm); at 45 nm it is under 4 ns.
6. c6: the longest path into the new registers is at most 16 clocks (64 ns) in both libraries.

## 3. Predictions (not criteria)
- M = 16: all nine rows pass. Phase 1 always ends its pulse on the previous sample's Ton (its turn-off comes 24-33 ns
  after its turn-on, the registers load at 68 ns). Post-step peaks move by -1..+2 A; the binding row lands at
  198.1-199.1 A. Vo's extremes after a step move by under 2 mV. Start-up: phase 1's first pulse in mode P keeps
  mode S's Ton (23.4 instead of 44.5 ns); Vo's maximum before 300 us within 1.5 mV of the reference.
- M = 32: the binding row at 199.0-200.4 A (about even odds of crossing 200 A); the other rows pass; at 30 % load
  (period about 230 ns) two or three phases run on the previous sample's Ton and Vo's band at the end widens by 1-3 mV.
- 8 ns clock: regulates, peaks within 5 A, more late fires than at 4 ns. 16 ns clock: fails (a predictive
  turn-on 11-16 ns after the low-side turn-off cannot be placed in the next 16 ns window without being late).
- Synthesis: c4 passes. Final build: far fewer cells than A209's 125 821 (lo_add's arithmetic, scb_dep and the unused
  options fold away): 55-80 thousand. Longest path into a phase register 10-14 ns sky130, 2.4-3.4 ns at 45 nm; into
  the new registers 25-40 ns sky130, 5-9 ns at 45 nm. Without the registers (final0) 35-47 ns / 8-10.5 ns.

## 4. Decision rule
- c1 fails: stop and fix. c4 fails: fix the reported construct and repeat.
- c2 passes: the final configuration takes ton_lat 16; the later RTL batches run with it and the coverage file names
  the rows run with it (a full regression of the table follows the last batch). c2 fails: try M = 8 and 4 on the
  failing rows; if none passes, the configuration keeps 0 and the zero-latency assumption becomes a stated one.
- c3 passes as well: the specification gets "sampling instant to the phases' registers: up to 33 clocks (132 ns)
  tested". c3 fails: the tested bound is 17 clocks, and the failing row names what limits it.
- c5 / c6 fail: the offending paths are listed for the next RTL step. The 16 ns row decides whether a slower clock
  is a ready answer for a 130-180 nm node or the phase logic has to be restructured there.
