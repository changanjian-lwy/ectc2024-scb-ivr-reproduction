# A220 - a pause that starts at zero current (BOUNDARY)
Method: RTL (scb_phase, scb_ctrl) + bridge (the front ends' zero-current threshold) + cosim.
Track A. Written after A217's three nominal-board records (N0 10 % and no load, N75 10 %), committed before A220's
runs. A217's other three rows were still running; they cannot change the decision below.
Decision it changes: whether skipping (A216 + A217) is adopted, which s3 still blocks after A217.
Cheaper check done first: none that sees the mechanism. The ideal plant's switch capacitances are linear and small
(A217: its valleys were already near the band), and the effect lives in V6's EPC model.
Budget: 6 runs, about 3 run-equivalents of 900 us, about 1.5 h at 4 jobs.

## 1. What and why
- A217 (V6, records z_N75_25_10, z_N0_25_10, z_N0_25_0 in its cosim folder): the offset puts phase 1's first valley
  after a resume at -15.62 / -15.96 A (N0 / N75), but phases 2-4 still miss: N75's first round -19.9 / -24.6 /
  -20.9 A, then a decaying alternation (phase 3: -8.6, -20.1, -13.1 ...); s3 fails on both nominal boards.
- Cause, read from the edge log (N75, resume at 440.191 us): the four low-side intervals have the same length
  (A216's design), each current falls by 18.3-19.3 A, and each first valley differs from phase 1's by the current
  that phase carried at its own low-side turn-on: +2.7 / -0.6 / -5.7 / -2.6 A. Those currents are a ring of the idle
  phases. The pause starts with every low side turned off at its valley (-11..-16 A, a negative current), so each node
  swings to its rail and then rings between the inductor and the switches' output capacitance with about 11 V. In
  the plant the only damping is the inductor's 0.54 mOhm (time constant 2L/R = 8 us): at the ticks of a pause the
  idle currents are still 6.2-7.1 A (A217, last 60 us; 6.4 A after 60 us of pause at no load).
- Change (cfg skip "zcd_a", needs "async"): the pause's last low-side intervals end at zero current. Phase 1, when
  its next round is skipped (skip_q), ends its low side by its front end instead of the timed edge; each of phases
  2-4, when its high side turns off after that decision (zpend), arms its own front end (A133's latches) and is held
  at its report, its slot not taken (half a period after the slot it turns off anyway). The threshold is zcd_a, the
  same latency x slope as A217's offset (2.73 A on N0, 3.64 A on N75 / S75), so the edges land near 0 A. A node then
  starts its pause at 0 V and rings with about Vo instead of about the rail, so the idle currents should fall roughly
  tenfold. The resume (A216, A217) is unchanged. Unit tests: two new ones (103 in all).
- Basis: turning the low side off when the inductor current reaches zero before skipped pulses is the usual light-
  load mode of synchronous bucks: TI LM5160 datasheet (zero-cross detector turns the low side off, DCM at light
  load; single-phase COT buck, 65 V, up to 1 MHz); US 7 245 113 (pulse skipping with a zero-current detector,
  synchronous buck); US 6 815 936 (diode emulation that adjusts the turn-off for the comparator's delay, as zcd_a
  does). None treats a series-capacitor buck, a multiphase pause or GaN at several MHz; that part is ours.
- Rows: A217's six (N0 10 %, N0 no load, N75 10 %, S75 25 C 10 %, S75 125 C 10 %, N0 5 % then +62.5 A), with
  zcd_a; the edge log covers the last 20 us. References: A217's records of the same rows.
- Not addressed: the inductor's real damping (unknown; a damped ring would mostly vanish within a pause), N0's
  ladder share of phases 3-4's valleys, four modules.

## 2. Criteria
1. j1: zcd_a absent, the cosim is the old one: unit tests all pass, regression quick and full.
2. A216's s1, s2, s3 and s4 (+62.5 A row) by a216_analyze.one, unchanged. A row with no low-side turn-off in s3's
   20 us is reported "not measured" for s3.
3. s3w: the same band over the last 60 us (every row has turn-offs there; A217's no-load row 28).
4. z1: the idle phases' largest current at the ticks of a pause, the first tick of each pause left out, last 60 us:
   at most 1.5 A on every row (A217: 6.2-7.1 A).

## 3. Predictions (not criteria)
- z1 passes: 0.3-1.2 A (Vo over the node's impedance, the output capacitance being larger at low V_DS).
- The pause-entry turn-offs at -1..+1 A (A217: -11..-16 A).
- First valleys after a resume within 2 A of -15.6 A on every phase of N0 and N75; no alternation.
- s3 and s3w pass on N75; on N0 phases 3-4 may sit up to 1 A above -12 A (the ladder's share); the no-load row's
  s3w passes. Slow board: s3 passes with its wider band (-22..-8 A).
- s1, s2, s4 as in A217; loss per module 0-10 % lower than A217's (no ring energy, no negative current at entry).

## 4. Decision rule
- s3 and s3w pass on N0 and N75 (or miss by at most 1 A on N0's phases 3-4), z1 passes: skipping is adopted with
  zcd_a and A217's offset (the final configuration gains "skip"); the slow board's result is stated with it.
- z1 passes but s3 / s3w still miss by more than 1 A: the ring was not the only cause; the edge log decides the next
  step (each phase resuming from its own comparator, A217's alternative). z1 fails: the zero-current turn-off is not
  where it is meant to be; fix before anything else.
