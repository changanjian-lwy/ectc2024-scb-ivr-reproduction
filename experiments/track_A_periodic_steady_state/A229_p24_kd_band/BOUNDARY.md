# A229 - the derivative term held within a band above the lower Ton limit (BOUNDARY)
Method: RTL + cosim (scb_ctrl cfg_kd_band, bridge cfg "kd_band_ns"; runs from this commit).
Track A. Written and committed before the runs. Looked at beforehand: A228's records (the Ton register in its last
20 us windows, the times of the re-application peaks in A223 / A224).
Decision it changes: whether A224's damped loop enters the final configuration with the term held while skipping -
that closes item 9 (re-applications from light load: final configuration 214-248 A; arm h 152.5-159.9 A) - or the
line stops with item 9 open.
Cheaper check done first: A228's records. The Ton register over the last 20 us of N75 10 % (t1) peaks at 4.38 / 4.72
/ 4.53 ns in d0 / k / h (limit 4.0 ns); Vo stays within 0.9992-1.0082 V there, so the PI output inside a burst is at
most 4.0 + 355 ns/V x 0.8 mV = 4.3 ns. Without a derivative term the re-application peaks come 13.5-17.7 us after the
step, and the first 5 us stay <= 180 A (A223 g25). Budget: 20 runs, about 3-4 h at 10 jobs.

## 1. What and why
- A228: the derivative term (kd 355, with or without A227's hold at the limit) moves the 10 % skipping rows' upper
  valley end by 1.4-2.8 A against d0, whose four runs agree within 0.6 A. Inside a burst Vo moves by 2 codes or more
  per sample, the PI output sits just above the limit, and the term kicks Ton there; phase 1's low-side learner
  (<= 2 ns per period) does not follow and the valleys drift - A223's mechanism at small Ton.
- Change: with cfg kd_hold, d_term = 0 while the PI output is at most the limit + kd_band (cfg kd_band_ns, Ton LSB in
  the RTL; absent = A227 bit for bit). Arm b = A228's arm h + kd_band_ns 4.0: the band reaches 8.0 ns, above the
  burst's 4.3 ns with margin; after a re-application the P term alone passes 8 ns within about one or two samples
  (kp 355 ns/V x the first 10-20 mV of dip).
- Rows: part S = A228's three skipping rows at its four release instants (12 runs; d0 = A228's records); part W =
  the six re-applications that start from light load (w0_N0, w5_N0, w20_N0, w5_N75, u_N0, w30_S75h); part I = k_N0 and
  k_S75h (Ton register >= 28.0 ns after the handover in A228's arm h: the band cannot act).
- Not run: l_N0_p48, l_N0_m80, h_S75_25 (arm h's Ton register >= 21.5 ns after the handover: the band cannot act;
  A228 q3 stands for them); other loads, temperatures and boards for skipping; four modules.
- Source: I know of no published controller that holds a derivative term near the lower on-time limit. The hold
  borrows conditional integration (Astrom and Hagglund, Advanced PID Control, ISA 2006, anti-windup: the integrator is
  stopped while the actuator saturates; their setting is process control with an integrating term, not a D term in a
  switching converter). Here it is applied to the D term, with a band above the limit; the band is our own choice.

## 2. Criteria
- j1: unit tests 109 of 109 (new: voltage_loop_derivative_held_within_a_band); cosim_regression --quick and --full
  bit for bit.
- q1 (part S, per row): no more runs fail than d0's (A228's q1 run test).
- q2 (part S, per row, one-sided against d0): mean over the four instants of each run's lowest true valley >= d0's
  mean - 1.0 A, and of each run's highest <= d0's mean + 1.0 A.
- q3 (part W): A224's e1 (w rows: whole-run peak <= 200 A, no overlap or shoot-through, V_DS <= 40 V, Vo within 1 %
  over the last 20 us), e2 (u_N0) and e4 (every row), against A223's g25 records.
- q4 (part I): bit for bit A228's arm h records (sections, edge lists, peaks).

## 3. Predictions (not criteria)
- Part S: arm b's means within 0.5 A of d0's at both ends; the Ton register's maximum over the last 20 us within
  0.1 ns of d0's run at the same instant.
- Part W: re-application peaks within 3 A of arm h (152.5 / 153.1 / 159.0 / 159.9 A; u_N0 58.9 A); w30_S75h bit for
  bit arm h.
- Part I: bit for bit.

## 4. Decision rule
- j1 and q1-q4 pass: the final configuration becomes V7 + A222's trims + vff rel_gate 25 + kd 355 ns/V, dead band 2,
  kd_hold 1, kd_band_ns 4.0; item 9 closes with part W's and A228's numbers; the docs follow.
- Else: the final configuration stays as it is and this line stops (A223-A229). Item 9 stays open, recorded as a
  trade-off between the damped loop and the skipping valley band, unless the miss names a new mechanism.
