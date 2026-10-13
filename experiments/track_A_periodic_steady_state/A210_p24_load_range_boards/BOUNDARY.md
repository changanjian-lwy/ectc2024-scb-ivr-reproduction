# A210 - the minimum load on the other boards: the 4.0 ns lower Ton limit on N75 and S75 at 0 / 25 / 125 C (BOUNDARY)
Method: mixed. Cosim with the frozen RTL (cfg only) on plant V6; a scaling argument for the prediction. No code change.
Track A, main line. Written and committed before the runs. Looked at beforehand: A208's eight rows (board N0) and the
full-load valley currents and Ton registers of A206's stage-2 records on these boards (Section 1).
Decision it changes: the minimum-load line of the specification. A208 gives 20 % with ton_min_ns = 4.0 ns on N0
alone; the specification is carried by the binding boards (0.75 L0, slow devices, 0 / 25 / 125 C).
Cheaper check done first: the scaling below. Budget: 9 runs of 450 us, about 75 min at 9 jobs.

## 1. What and why
- Rows: A206's board cfgs (final configuration on V6, low sides 0.3 ohm x the board's drive factor, A206's trims,
  9.5 ns lead on slow boards) with ton_min_ns = 4.0 ns and part of 250 A released at 300 us, end 450 us:
  N75 25 C at 40, 30, 20 % left; S75 at 25, 0 and 125 C at 30 and 20 %.
- Scaling. The on-time for a load goes with L: 0.75 of N0's (D63 on N0: 18.0 / 14.6 / 11.2 ns at 40 / 30 / 20 %).
  The register is the on-time less the board's offset, read at full load (on-time 0.75 x 38.6 = 28.9 ns):
  N75 register 23.75 ns, offset +5.2 ns; S75 31.3-31.7 ns at 25 C, 31.6-32.0 at 0 C, 30.4 at 125 C, offset
  -1.5..-3.1 ns (the slow gate turns on later than its 9.5 ns lead). So the 4.0 ns limit, a register value, binds
  at very different loads on the two board classes.
- r4's band per board, from its own full-load record widened by 3 A: N75 [-20, -12] A (full load -17.0..-15.3);
  S75 [-22, -8] A at every temperature (full load -18.8..-10.6: the two-cycle orbit of slow boards, A195).
- Not tested: fast devices, L x 1.3, -40 C, four modules, loads between the rows, start-up into a light load.

## 2. Criteria (every row; as A208)
 r1 COMPLETED, 0 shoot-throughs, 0 overlaps, 0 forced edges, whole-run peak <= 200 A, V_DS <= 40 V.
 r2 Vo within 1 V +- 10 mV over the last 20 us.
 r3 Vo within 1 V +- 50 mV at all times after the release (reported apart).
 r4 over the last 20 us every low-side turn-off current inside the board's band and no late fire.
A row works with r1, r2 and r4.

## 3. Predictions (not criteria)
- N75: register 8.3 / 5.8 / 3.2 ns wanted at 40 / 30 / 20 %. 40 and 30 % work. 20 % does not: the register sits at
  4.0 ns, about 57 A are delivered and Vo ends at 1.02-1.04 V, with clean switching (r4 passes).
- S75: register 13-14 ns at 30 % and 10-11.5 ns at 20 %, far from the limit. 30 % works at the three
  temperatures. 20 % runs near 6.9 MHz (period about 145 ns) with a gate that needs about 10 ns to turn on: it
  fails r4 or r2 at one temperature at least.
- r1 passes on every row. r3 misses on the 20 % rows.
- Loss books: N75 4-5 W at 30 %; S75 5-7 W at 30 %.

## 4. Decision rule
- The specification's minimum load is the highest of the boards' lowest working rows, N0's 20 % included, stated
  per board class if they differ.
- A board whose 30 % row does not work is reported, and its floor bracketed by one more row at 40 or 50 % (same cfg).
- An r1 failure is reported first, with its record. Nothing in the controller or its configuration changes in A210.
