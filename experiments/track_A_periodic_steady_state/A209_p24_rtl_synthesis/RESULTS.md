# A209 - the frozen RTL as a circuit: front end, size and critical path before layout (RESULTS)
Boundary: 1f42b6c, addenda da46641 and 51e78dc (both before any delay was read). Analysis: a209_synth.py +
a209_sta.py -> a209_summary.json (logs in tmp/a209/logs, not in the repository). Yosys 0.49 (yowasp build) with
ABC's plain mapping (`abc -fast -liberty`), SkyWater sky130 hd typical 1.8 V 25 C and Nangate 45 nm typical; timing
by our own estimate on the mapped netlist (library tables, no wires, no clock tree, worse of rise and fall).
Parameters as in the cosim (N 4, TW 32, FB 7, CW 8). The repository's RTL is unchanged.

## 0. Verdict
- **As written, the RTL does not pass a synthesis front end**, and has not been synthesized since A100. Yosys
  (0.49 and 0.70) stops on `.lo_add(IS_FIRST ? lo_add : {TW{1'b0}})` in scb_ctrl.v (A148): a signed wire and an
  unsigned constant in one port expression. Icarus accepts it. With the constant written `$signed({TW{1'b0}})`
  (the same bits) every module synthesizes with 0 problems (c1 holds on that copy).
- **Size: 125 821 generic cells for one module's controller, 2.9 times A100's 43 924.** scb_vff alone is 68 579
  (55 %); a phase is 16 054 (first) or 12 001. Mapped: 0.77 mm2 in sky130, 0.15 mm2 at 45 nm, 2182 flip-flops.
  Four modules (scb_multi): 219 653 cells.
- **The longest path is 12 times the 4 ns clock in sky130 and 2.6 times at 45 nm** (47.0 / 10.5 ns, 145-155 cells):
  from the loop's accumulator ton_acc through the Ton sum, scb_vff's arithmetic and into phase 1's edge logic
  (late_fires, state, gl_ev, t_lo). scb_vff alone is 32.3 / 6.9 ns (its multipliers into lo_add, A148).
  c2 and c3 fail.
- **The per-clock edge logic of one phase is 10 ns in sky130 and 2.4 ns at 45 nm** (scb_phase alone, 30-39 cells:
  32-bit time arithmetic from `now`, t_on, dlo into t_lo, state and the gate events). c4 fails by 2.5 times; at
  45 nm it fits with a factor of 1.6. For scale, a registered 32-bit adder mapped the same way is 3.3 / 0.63 ns.
- **What it means.** In a 45 nm-class logic process the controller could meet its clock after one change: the
  loop-to-feed-forward-to-phase path has to be registered (its source changes once per switching period, so a
  stage of registers costs one clock of latency per period). In a 130-180 nm-class process, the class of LSCB's
  BCD chip, the phase logic itself is 2.5 times too slow: it needs pipelining, a narrower time word, or a slower
  clock with a finer delay line. These are estimates good to a factor (Section 3), enough for this ordering.
- The 31.25 ps edge placement, the comparators, the TDCs and the ADC are outside synthesis and stay assumptions.

## 1. Criteria and numbers
| | generic cells | sky130: area, longest path | Nangate 45: area, longest path | path |
|---|---|---|---|---|
| scb_ctrl (one module) | 125 821 | 0.775 mm2, **47.0 ns** | 0.153 mm2, **10.5 ns** | ton_acc -> phase 1 late_fires |
| scb_phase, first | 16 054 | 0.102 mm2, **10.2 ns** | 0.020 mm2, 2.44 ns | ton_q -> dlo; now -> t_lon |
| scb_phase, others | 12 001 | 0.079 mm2, **10.0 ns** | 0.016 mm2, 2.40 ns | mode_p -> late_fires, t_on |
| scb_vff | 68 579 | 0.443 mm2, 32.3 ns | 0.086 mm2, 6.9 ns | m[0] -> lo_add; lp20 -> dnum 24.7 ns |
| scb_dep | 653 | 0.006 mm2, 7.3 ns | - | highs -> dep |
| scb_multi (four modules) | 219 653 | - | - | - |
| 32-bit registered adder | 332 | 3.34 ns | 0.63 ns | plausibility row |
- c1 pass (0 problems on every top, on the copy with the one rewritten port). c2 fail (47.0 ns against 4.0).
  c3 fail (10.5 ns). c4 fail (10.2 / 10.0 ns).
- In scb_ctrl the eight longest end points all start at ton_acc and end in phase 1 (46.0-47.0 ns in sky130).
- scb_multi is not four times scb_ctrl; why was not analysed.

## 2. Predictions
- Held: c1; c2, c3 and c4 fail; the longest paths start at registers that change once per period; the phase logic
  fits at 45 nm (2.4 ns against 1-3 predicted).
- Missed: the size (55-80 thousand predicted, 125.8 thousand: I did not expect scb_vff to be the larger half);
  the delays sit at or just above the top of my ranges (47 against 10-40 ns, 10.5 against 2.5-10, 10.2 against
  4-10); scb_multi's size.

## 3. Limits
- The timing figures are estimates: ABC's plain mapping (a timing-driven flow would shorten the long paths), no
  wires, no clock tree, no setup time (all of which lengthen them), typical corner, one transition model for rise
  and fall. The ABC delay-targeted script did not finish under this build, and ABC's own report is not available;
  our estimate was checked for plausibility on an adder, not against a sign-off tool.
- sky130 stands in for a 130-180 nm BCD-class node; no BCD library is public. P24 names no controller process.
- Which paths a real design would allow several clocks is read from what drives them, not from constraints.

## 4. What follows
- The list of RTL changes a buildable version needs, for the user's decision with the other controller items:
  (1) the port expression (one token); (2) registers on ton_ph and lo_add at scb_vff's output; (3) for a
  130-180 nm node, the phase logic's timing: pipeline, a narrower time word than 32 bits, or a slower clock.
  None is made here.
