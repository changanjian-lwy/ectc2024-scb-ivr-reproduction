# A208 - the loop's lower Ton limit as its own value: how far down one module regulates (BOUNDARY)
Method: mixed. Bridge change (cosim/bridge.py: cfg "ton_min_ns"; absent = as before, bit for bit), mathematical
model (D63, a208_predict.py) for the prediction, cosim with the frozen RTL on plant V6 for the result. No RTL change:
cfg_ton_min is an existing input of scb_ctrl.
Track A, main line. Started on the user's decision of 2026-10-14 ("do A208 first"). Written and committed before the
runs. Looked at beforehand: D63 with the limit moved (Section 3), the identity checks (Section 2, done before this
commit because they gate the code), and the Ton register of 18 existing V6 records (Section 1).
Decision it changes: the value of the lower limit in the final configuration, and with it one module's minimum load
(A207: about 70 %); then whether a light-load mode or module shedding is still needed.
Cheaper check done first: D63 (it has no gate model, so it bounds the loop, not the gate).
Budget: 6 runs of 450 us on V6 (3 run-equivalents), about 45 min at 6 jobs.

## 1. What and why
- A207: the bridge sets cfg_ton_min to half of cfg ton_ns (22.24 ns in the final configuration). The register
  reaches it at about 174 A; below that load Vo runs away. The limit was never a designed value.
- The change: cfg "ton_min_ns" sets cfg_ton_min directly. cfg_ton_max stays at 2 ton_ns.
- What is not known is where a short on-time stops working. The gate command is the register plus the 8 ns lead; a
  high side turns on through 3.0 ohm and off through 0.3 ohm; the period shrinks with Ton (about 12 on-times), so
  at 10 % of the load the model runs at 6.6 MHz. Only the cosim's gate model can show the limit.
- Rows: A207's rows (final configuration, plant V6, board N0, 25 C, one module; part of 250 A released at 300 us,
  end 450 us) with ton_min_ns = 2.0 ns, low enough to be out of the loop's way down to about 10 %: 60, 50, 40, 30,
  20, 10 % of the load left.
- Existing rows: in the 18 V6 records of A206 / A207 that regulate (12 binding rows, 5 start-ups, A207's 75 %) the
  register never reaches its lower limit in mode P (lowest 20.4-31.8 ns against 17.8-22.7 ns). A lower limit
  therefore leaves them bit for bit; none is rerun.
- Not tested: other boards and temperatures (each board has its own ton_ns: N75 35.58, S75 45.35 ns), slow load
  changes, a start-up into a light load, four modules, the upper limit.

## 2. Criteria
 i1 scripts/cosim_regression.py --quick passes 4 / 4 with the changed bridge.
 i2 A207's 14 us smoke record (sections, edge log, snapshots, gate records) bit for bit with the key absent and
    with the key at the default's value (22.24 ns).
Every row:
 r1 COMPLETED, 0 shoot-throughs, 0 overlaps, 0 forced edges, whole-run peak <= 200 A, V_DS <= 40 V.
 r2 Vo within 1 V +- 10 mV over the last 20 us.
 r3 Vo within 1 V +- 50 mV at all times after the release.
 r4 over the last 20 us every low-side turn-off current within [-20, -12] A (target -15.6 A; A206's full-load run
    and A207's 75 % row: -17.4..-14.0 A) and no late fire.
A row works with r1, r2 and r4. r3 is reported apart: it belongs to the size of an instantaneous release.

## 3. Predictions (not criteria)
- i1, i2 hold (checked before this commit: 4 / 4; 69 sections and 1032 edges identical in both variants).
- D63 with the limit at 2.0 ns of register (its on-time = register + 5.8 ns, from A207): every row regulates. Register
  19.1 / 15.6 / 12.2 / 8.8 / 5.4 / 2.0 ns at 60 / 50 / 40 / 30 / 20 / 10 %; 2.86 / 3.22 / 3.69 / 4.32 / 5.22 /
  6.61 MHz; peak 93 / 80 / 68 / 55 / 42 / 29 A. Vo's overshoot at the release 27 / 34 / 40 / 46 / 52 / 58 mV, so r3
  misses at 20 and 10 %.
- Mine, for the gate D63 does not have: 60, 50, 40 and 30 % work. 20 % as likely as not. 10 % does not work (the
  register at or near the limit; a 10 ns command through 3.0 ohm no longer gives a proportional on-time).
  r1 passes on every row.
- Loss books (scaled from A207's 75 % row: conduction with the rms current, edges with the frequency): 7.5-9 W at
  50 %, 5.5-7 W at 30 %, 5-7 W at 10 %; Pout / (Pout + loss) >= 92 % down to 30 %, 78-84 % at 10 %.

## 4. Decision rule
- i1 or i2 fails: fixed first; no number is used.
- The lowest row that works is one module's floor with the limit out of the way. Proposed value of ton_min_ns: the
  smallest register of that row's last 20 us, rounded down to 0.5 ns. It replaces half of ton_ns in the
  specification, with the minimum load restated; the 18 existing records stand as they are.
- A row that fails r1: reported first, with its record; the proposed limit then lies above that row's register, and
  one more run shows the proposed value on that row (stage 2).
- The four-module ranges, all on or with modules shed, are composed from the rows that work (not a run).
- What stays open afterwards (a light-load mode, shedding) is named with its price; neither is part of A208.

## 5. Addendum, written before the second stage (2026-10-14)
Sections 1-4 stand. Written after the six rows (3a2d2c2) and before the two runs below.
- First stage: 60, 50, 40, 30 and 20 % work (r1, r2, r4); 20 % misses r3 (1.0526 V at the release); 10 % does not
  work: the register sits at the 2.0 ns limit, the module delivers 38 A, Vo ends at 1.0525 V and late fires keep
  coming (59 / 0 / 118 / 43 in the last 20 us). No row fails r1.
- By the rule the proposed value is 4.0 ns (20 %'s smallest register over its last 20 us is 4.22 ns). That value was
  not itself run: at 20 % the register is below 4.0 ns in 67 sections up to 46 us after the release, so the row is
  not bit for bit with it; and what the module does below its floor with a 4.0 ns limit is not known (at 2.0 ns it
  switches roughly).
- Second stage, two runs with ton_min_ns = 4.0: v20 (20 % left) and v10 (10 % left).
  Criteria: v20 works (r1, r2, r4). v10: r1, and over its last 20 us every low-side turn-off current within
  [-20, -12] A with no late fire (r4), while r2 is expected to miss.
  Predictions: v20 works, Vo at the release 1.053-1.060 V (r3 misses as before), register 4.2-4.7 ns at the end.
  v10: the register at 4.0 ns throughout, 46-49 A delivered, Vo ends at 1.085-1.10 V, r4 passes.
- Rule: v20 works: 4.0 ns is the proposed value and one module's tested minimum load is 20 %. v20 does not work: the
  value goes up to 30 %'s smallest end register rounded down (8.0 ns) and the tested minimum is 30 %, without a
  further run. v10 misses r4: reported as the module's behaviour below its floor, with the record.
