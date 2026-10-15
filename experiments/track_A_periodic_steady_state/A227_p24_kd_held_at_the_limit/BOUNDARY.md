# A227 - the derivative term held at the lower Ton limit (BOUNDARY)
Method: RTL (scb_ctrl cfg_kd_hold, bridge cfg "kd_hold"; absent = bit-identical) + cosim. Track A, after A224 /
A226. Written and committed before the runs, with the code.
Decision it changes: whether A223's gate and A224's kd 355 join the final configuration, with the derivative term
held while the loop sits at its lower Ton limit (items 9 and the skipping rows of A221).
Cheaper check done first: A224's / A221's records. Budget: 7 runs, with A225's 14 about 2.5 h at 10 jobs.

## 1. What and why
- A224 (records A224_p24_damped_loop/cosim/): kd 355 passed e1-e4 on all its rows (re-applications 152.5-163.4 A)
  but e5 missed twice: N0 no load -23.1 A against A221's -21.2 - 1 A, and N0 10 % s3t, true valleys -16.8..-11.6 A
  against the band -20..-12 A. A226 showed the first is my reference: the final configuration without kd gives
  -22.8 A (A221 had the old N0 trim). The second has no reference with the new trim.
- In the N0 10 % records over the last 60 us Ton leaves 4.0 ns at 25 samples in both A221 (up to 4.41 ns) and A224
  (up to 4.91 ns): the derivative term lifts Ton while the module skips. Skipping has its own hysteresis (A216); the
  damping is for large steps, which take the PI output off the limit within a sample.
- Change: with kd_hold, d_term = 0 at a sample whose PI output (ton_acc + p_term after the sample) is at or below
  the lower Ton limit. One unit test.
- Rows: kd 355 + hold on A224's three skipping rows and the three re-applications that start from skipping
  (w0_N0, w5_N0, w5_N75); and N0 10 % on the final configuration as it is (z_N0_10_d0), the missing reference.
- Not tested: as A224.

## 2. Criteria
- j1: unit tests 108 of 108; cosim_regression --quick and --full bit for bit.
- h1 (skipping rows, held arm): s1, s2, z1r (A221); s3t on N0 10 % and N75 10 %; N0 no load's true valleys no more
  than 1 A below A226's d0 (-22.8 A).
- h2 (re-applications, held arm): A224's e1 (<= 200 A whole run, no overlap or shoot-through, V_DS <= 40 V, Vo
  within 1 % over the last 20 us) and the post-step peak within 5 A of A224's d355 record of the row.
- z_N0_10_d0 is reported: whether the final configuration itself meets s3t at N0 10 % with the new trim.

## 3. Predictions (not criteria)
- Held N0 10 %: true valleys -16.8..-12.5 A (s3t passes); N75 10 % and no load as A224's within 0.5 A.
- Re-applications within 2 A of A224's (the PI output leaves the limit at the first sample after the step).
- z_N0_10_d0: -16.8..-12.5 A, s3t passing (A221 -16.8..-13.5 A with the old trim).

## 4. Decision rule
- j1, h1, h2 pass: rel_gate 25 and kd 355 (dead band 2, hold) join the final configuration; item 9 closes for the
  rows run (A223-A227), and A225's rows are stated for the final configuration.
- h1 misses on N0 10 % and z_N0_10_d0 misses the same way: the miss belongs to the final configuration with the
  new trim (A222), not to the candidate; the candidate is adopted and the miss is reported under the skipping line.
- Otherwise: not adopted; the records say what the hold changes.
