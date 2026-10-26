# A248 - which plant blocks make the free swing late and shallow (BOUNDARY)
Method: physical model (the co-simulation's plant, one edge at a time) + math (D57 with blocks); no full co-simulation.
Track A. Written and committed before the harness grid and the analysis. Looked at beforehand: one swing per board
and variant (timing, finite traces, the low side's channel stop at about 2.5 ns), no comparison with D57 or records.
Decision it changes: which free-swing model step 2 (D63's learner block) uses. The options are the plant's own
single-edge table or D57 with named blocks. A247's rule requires this check before step 2.
Cheaper check done first: A247's two-parameter fit (D57 1.5 ns early and 0.92 V low). Budget: about 10 min.

## 1. What and why
- A247 found D57 1.5 ns early and 0.92 V low against the V7 records, and c1 failed on the L x 1.3 board. Its GP
  lowered the residual by 38 % but pointed at the rail. The plant has blocks D57 lacks:
  - the gate model: the low side's channel stops about 2.5 ns after its command (A163-A206);
  - r_core: a resistor across each inductor (core loss, A221): 2.9 Ohm on N0, 2.2 on N75, 3.8 on N13, which draws
    about 4 A at 12 V against the swing;
  - the 50 pH loop with its 0.82 Ohm damping (A144);
  - the 72 / 36 A/ns edges (A145);
  - the Miller follow of idle gates (A206).
- Harness (a248_swing.py, like A206's): FastPlant with the circuit that bridge.make_params builds from each board's
  V7 cfg. Setup: all low sides on, the ladder at rail = Vin / 4, one low side commanded off at i_off, no turn-on,
  40 ns.
  - Boards: N0, N75, S75h (A246), N0 at 125 C (A231), N13 = L x 1.3 (A235).
  - Phases 2 (for 2-3) and 4; rails 10-14 V; i_off -60..-10 A.
  - Variants: full; one block dropped each (gate, miller, r_core, loop, edge); bare (all dropped).
- Not tested: the swing's dependence on the other phases' state beyond the ladder at Vin / 4; rails outside 10-14 V;
  currents outside -60..-10 A.

## 2. Criteria
- h1 (the plant's single edge reproduces the records, no fitted number): the full harness's V_DS at each A247 record's
  (board, phase group, rail, i_off, actual delay) inside the grid.
  - RMSE <= 0.35 V overall;
  - on each board with >= 100 rows: median |e| <= 0.30 V and soft / hard agreement (2 V) >= 95 %.
- h2 (the blocks are the difference): each variant is fitted to D57 as V(t) = V_D57(t - shift) + offset over delays
  0-25 ns on the grid. bare: |shift| <= 0.30 ns and |offset| <= 0.20 V. Each block's share of full's shift and offset
  is reported.
- h3 (D57 can carry them): D57 plus r_core and a swing held at x = 0 until the middle of the low side's current fall
  (from the harness, not fitted). RMSE against the full harness <= 0.30 V over delays 0-25 ns on the grid.

## 3. Predictions (not criteria)
- h1 passes: RMSE 0.20-0.35 V, close to A247's corrected D57 (0.27 V) without its two fitted numbers.
- full against D57: shift 1.3-1.7 ns, offset 0.7-1.1 V.
  - The gate takes most of the shift (> 70 %); r_core most of the offset (> 60 %).
  - loop, edge and Miller each < 0.2 ns and < 0.15 V.
- bare passes h2 (|shift| < 0.2 ns, |offset| < 0.15 V). h3 passes with 0.15-0.30 V.

## 4. Decision rule
- **h1 passes:** step 2 uses the plant's single-edge table per board as its swing model. If h3 also passes, D57 with
  r_core and the gate's start delay is the analytic form, used where the table has no grid (rails, currents).
- **h1 fails:** a single edge does not carry what the records show (other phases, the ladder's motion, history). That
  state is traced before step 2.
- **h2 fails:** the plant's core differs from D57's node (device counts, Coss, reverse conduction). That difference is
  named before D57 is used anywhere again.
