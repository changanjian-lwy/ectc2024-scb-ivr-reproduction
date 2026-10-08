# A174 - the final plant's marginal rows at other step positions, and a fixed-reference interlock (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, threshold-form driver interlock; frozen RTL controller;
cfg only)
Track A, package layer. Written and committed before the runs. Looked at beforehand: A173 (all 17 runs), A172.
- L x 0.7 +4.8 V / 1 us: 199.7 A, 0.3 A under the budget (A172). A129 measured 2-7 A of post-step peak change
  from moving a step by less than one period.
- ff -8 V / 10 us (A173): one phase-2 restart and a 153 A NEW spike 14.5 us after the ramp. This is A148's
  falling-step valley loss, which reached +19.5 A in that period (V2 +0.6 A).
- Fixed 1.0 V interlock reference: t_il 8.3 ns passed at the slow corner on +4.8 V / 1 us (A173). The other rows
  where the interlock acted (holds > 0): ss s_p62 23, ss l_m80_10us 23, ss slew4 79, ff l_m80_10us 6, four
  modules ss 71. Rows without holds do not use t_il.
Decision it changes:
- whether the L x 0.7 board meets 200 A at every step phase or the spec must name it as failing at some;
- whether ff's falling-ramp event is systematic;
- whether the interlock may use a fixed reference (no per-board trim).
Cheaper check done first: none; a step phase is a system property. Budget: 13 runs, --jobs 10, ~4.5 h wall
(four modules ~4.5 h, single ~1.5-2.5 h).

## 1. What and why
- Step position: L x 0.7 l_p48_1us (A172's cfg) and ff l_m80_10us (A173's cfg), step moved by k T / 5, k = 1..4
  (T 364.1 / 510.1 ns, the steady period before the step). With the original these give 5 phases per period.
- Fixed reference: t_il = 8.3 ns (ss), 1.0 ns (ff) on A173's cfgs of ss s_p62, ss l_m80_10us, ss slew4, ff
  l_m80_10us and four modules ss l_p48_1us. The values are from A173's estimate: comparator + gate fall to 1.0 V +
  recharge to the device's own channel start.
- Not tested: step positions on other rows, a fixed reference on four modules' other rows.

## 2. Criteria
1. Step-position rows: A168's criteria (a168_analyze.judge) against the same row's reference (A167 / A164), as in
   A172 / A173.
2. L x 0.7 decision quantity: the post-step peak over the 5 positions (A172 + 4). Pass = every position <= 200 A.
3. ff decision quantity: NEW events over the 5 positions. Systematic = a NEW spike at >= 2 of the 4 new positions.
4. Fixed-reference rows, each against A173's t_il 0.5 run of the same row (the change the delay causes):
   post-step peak within ±3 A; late <= 1.5 x A173 + 5; NEW <= A173 + 2; |Vo extreme| within ±2 mV; V_DS <= 40 V;
   0 shoot-throughs, COMPLETED.

## 3. Predictions (not criteria)
- L x 0.7: post-step 195-203 A over the positions; at least one of the four above 200 A.
- ff: the NEW spike at 0-1 of 4 positions; Vo extreme 28-32 mV.
- Fixed reference: within criterion 4 on all five rows. Late fires +0-30 %; four modules 850-1000.

## 4. Decision rule
- L x 0.7 all <= 200 A: the marginal pass stands, with the measured spread. Any above: the spec states that the
  L x 0.7 board exceeds 200 A at some step phases (by how much), and L x 0.7 is named as beyond the tested
  margin.
- ff spike at >= 2 positions: an open item on the final plant (fast corner, falling ramp). Otherwise it is a
  single-phase event, reported with the spread.
- Criterion 4 on all five: the spec allows a fixed 1.0 V interlock reference (t_il <= 8.3 ns), with no per-board
  reference. Otherwise it names the rows that need the per-board form (<= 1.4 ns).
