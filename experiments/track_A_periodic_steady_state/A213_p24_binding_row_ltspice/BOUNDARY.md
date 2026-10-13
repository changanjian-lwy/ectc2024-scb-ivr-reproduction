# A213 - the binding row against LTspice: the slow 0.75 L0 board at 125 C, +4.8 V / 1 us (BOUNDARY)
Method: mixed. Tool change (scripts/p24_replay.py: the gate-capacitance spread in the replay netlist), one cosim run
(frozen RTL, cfg only: snapshots), LTspice replays with EPC's model (netlists outside the repository).
Track A, package layer. Written and committed before the cosim run and the replays. Looked at beforehand: that the
seven scaled parameters are each defined once and used only by the vendor model's four gate capacitors.
Decision it changes: whether "the binding row holds 200 A with a 2.4 A margin" (A206: 197.57 A, S75 at 125 C, k 5)
may be said beyond the plant. A206 compared the plant with LTspice at nominal devices and 25 C only.
Cheaper check done first: none. Budget: one cosim run of 524.5 us (about 90 min), 8 replays of minutes.

## 1. What and why
- Cosim: A206's B_S75_hot_p5 cfg with snapshots in [481.0, 484.0] and [499.9, 523.6] us and the gate-edge log; end
  524.5 us. Snapshots are read-only.
- Replays as A205 / A206 (LTspice from the plant's state with the plant's gate commands, two periods, "match":
  the phase resistance makes up the difference between the plant's switch resistance and the vendor model's
  typical device): three settled (P, the first three snapshots), two at the step (T), three at the plant's
  largest peak (K: the snapshot at the peak and the two before).
- The corner in LTspice: `.temp 125` (the vendor model's own temperature dependence), its threshold parameter
  + 1.0 (as the plant's dk2; already in the tool), and new here its gate capacitances x 1.29: the seven amplitude
  parameters of q_gs and q_gd multiplied in the .param lines (p24_replay.scale_params), which is what the plant's
  load_device(cg_scale) does to the same parameters. Drive 3.6 / 0.36 ohm, low sides 0.36 ohm on.
- Not checked on its own: the scaled device against a measurement or a second model; D79's single-edge comparisons
  were at nominal. The plant's reverse fit is the typical 25 C device at this corner too (A206's limit).
- Basis: the vendor's model as run in LTspice. No published measurement of a slow, hot EPC2067 was looked up.

## 2. Criteria
 i1 the cosim record's sections equal A206's B_S75_hot_p5 record bit for bit up to this run's end.
 c1-c4 on each replay, A205's limits: peaks within 2.0 A; one period later currents within 1.5 A, capacitor
    voltages within 20 mV, Vo within 0.5 mV; every switch's largest V_DS within 1.5 V; hard turn-ons within
    0.3 ns and 1.0 V.
 c5 on each of the three peak replays: LTspice's largest peak <= the plant's largest peak + 2.4 A.

## 3. Predictions (not criteria)
- i1 holds. c3 passes on all eight. c1 passes on the settled and step replays and misses on a peak replay.
- c2: the peak replays miss by 1.5-4 A with LTspice the lower one, as on N75 (A206). Settled: as likely as not
  (the slow board's two-cycle orbit hangs on gate delays). c4 misses on several (0.3-1 ns on a slow gate).
- c5 passes: LTspice's largest peak lies 0-4 A below the plant's 197.6 A.

## 4. Decision rule
- c5 passes: the margin may be stated with "LTspice within x A at this corner, two periods at fixed commands".
- c5 fails: the binding row does not hold in LTspice at fixed commands; the margin statement is withdrawn, and the
  cause is traced in one diagnostic round before anything else.
- c1-c4 misses are reported as V6's error at this corner. No plant change in A213.
