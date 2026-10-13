# A209 - the frozen RTL as a circuit: front end, size and critical path before layout (BOUNDARY)
Method: RTL (analysis only, by synthesis). Yosys 0.49 (the yowasp build, in a git-ignored venv) with ABC, mapped to
two open cell libraries fetched into tmp/ (not in the repository): SkyWater sky130 hd, typical, 1.8 V, 25 C, and
Nangate 45 nm, typical. No file of the repository's RTL changes. Track A, main line. Written and committed before
the synthesis results were read. Looked at beforehand: that yosys 0.49 and 0.70 stop in their Verilog front end on
scb_ctrl.v as it stands (an internal assert, traced to one port connection, Section 1), and one timing-only run.
Decision it changes: item 8 of the controller's open list ("not shown to be a circuit"): whether the controller as
written fits its 4 ns clock in a mature node, which paths would have to be registered or made sequential (that adds
latency to the loop or to the edge timing), and so what any RTL redesign has to respect.
Cheaper check done first: none exists; the last synthesis was A100's (43 924 generic cells, before scb_vff, the
floors and A141-A184). Budget: about 10 synthesis runs, minutes each.

## 1. What and why
- The cosim clocks the controller at 4 ns and places edges on a 31.25 ps grid (T_clk / 2^7). Whether the logic
  between two registers settles in 4 ns has never been checked; cell counts stop at A100.
- Front end: `.lo_add(IS_FIRST ? lo_add : {TW{1'b0}})` in scb_ctrl.v (A148) mixes a signed wire with an unsigned
  constant in one port expression. Icarus accepts it; yosys asserts. The synthesized copy has the constant written
  as `$signed({TW{1'b0}})`: the same TW bits on the port. The repository's file is not touched (frozen).
- Runs, parameters as in the cosim (N 4, TW 32, FB 7, CW 8): scb_ctrl flattened (the whole one-module controller);
  as their own tops scb_phase (FIRST 1 and 0), scb_vff and scb_dep; scb_multi (four modules) for size only.
  Each: `synth -flatten; check -assert; stat`, then `dfflibmap; abc -liberty -D 4000; stat -liberty` per library.
- Read from ABC's timing print: the longest register-to-register (or port) delay and its start and end points.
  Typical corner, no wires, no clock tree, no hold fixing: a lower bound on the real delay.
- What it cannot say: the 31.25 ps edge placement (a delay line or DLL, analog), the comparators, the TDCs, the
  ADC. Those stay model assumptions. A path whose inputs change once per switching period may be given several
  clocks in a real design; each long path is therefore named with what drives it.
- Basis: sky130 as the open stand-in for a 130-180 nm BCD-class node (LSCB's chip, Tong et al. VLSI 2026, is
  180 nm BCD; P24 does not name its controller's process); Nangate 45 nm as a faster reference.

## 2. Criteria
 c1 scb_ctrl and scb_multi pass `synth; check -assert` with 0 problems (on the copy with the one rewritten port).
 c2 the whole one-module controller's longest path <= 4.0 ns in sky130.
 c3 the same in Nangate 45 nm.
 c4 scb_phase alone (the per-clock edge logic) <= 4.0 ns in sky130.

## 3. Predictions (not criteria)
- c1 holds. Size: 55 000-80 000 generic cells for scb_ctrl (A100: 43 924), about 4 times that for scb_multi.
- c2 fails: 10-40 ns, the path through the loop's multipliers and scb_vff's arithmetic into a phase's edge time.
- c3 fails or is marginal: 2.5-10 ns. c4 fails: 4-10 ns in sky130 (32-bit add and compare chains); 1-3 ns at 45 nm.
- The longest paths start at registers that change once per period (the ADC sample, the Ton accumulator).

## 4. Decision rule
- The coverage file's item on implementability gets the numbers: what fits 4 ns in which library, which paths do
  not and what drives them, and the list of RTL changes a synthesizable version needs (the port expression; where
  registers or sequential arithmetic would go, with the latency each adds).
- No RTL is changed in A209. The changes go to the user with the other controller items.

## 5. Addendum, written before any delay was read (2026-10-14)
- The yowasp build of yosys discards ABC's own output (its temporary stdouterr.txt is empty, and the script yosys
  0.49 writes for `-D` has no timing print), so "ABC's timing print" of Section 1 does not exist here. Replaced by
  a small timing estimate of our own on the mapped netlist (a209_sta.py): library tables for delay and transition
  at the driving transition and the load (sum of driven pin capacitances, no wire), the worse of rise and fall on
  every arc, flip-flop clock-to-Q at the start, no setup time at the end, typical corner.
- Its plausibility is checked on a registered 32-bit adder synthesized the same way (row add32), not against a
  sign-off tool: none is installed. The figures are estimates from below (no wires, no clock tree).
- yosys's standard output stops when ABC starts under this build; the logs are taken from yosys's own log file.
- Criteria and predictions unchanged. Seen so far: scb_phase maps to about 77 000 um^2 in sky130 (no delay).
