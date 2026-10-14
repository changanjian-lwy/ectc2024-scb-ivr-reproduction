# A224 - a damped voltage loop for large load steps (BOUNDARY)
Method: RTL (scb_ctrl cfg_kd / cfg_kd_db, bridge cfg "kd_ns_per_v" / "kd_db"; kd absent = bit-identical) + cosim;
D63 (new block Design.kd_ns / kd_db, default 0) as the cheaper check. Track A, controller item 9, after A223.
Written and committed before the runs, with the code.
Decision it changes: whether the final configuration takes A223's gated cap together with a derivative term, so
that load re-applications from light load to full load stay <= 200 A (item 9).
Cheaper check done first: a224_predict.py (D63) -> a224_predictions.json; A223's records.
Budget: stage 1 13 runs (about 1.5 h at 10 jobs), stage 2 7 runs (about 2 h).

## 1. What and why
- A223 (plant V7, records `A223_p24_cap_on_rising_vin/cosim/run_w*_g25.json`): with phase 1 no longer held, three
  re-applications still exceed 200 A - N0 +237.5 A from 5 % 214.4 A, N0 +200 A from 20 % 218.0 A, N75 +237.5 A
  from 5 % 219.2 A - also without the gate (214.0-248.3 A). In run_w20_N0_g25 Vo rings for > 25 us with a period of
  about 3 us (0.959-1.030 V) while the loop's Ton swings 9-36 ns; per period the valleys of all four phases move with
  Ton (phase 1 -15.7 -> +62.8 -> -18 -> +90.6 A), the peaks come at the ring's current maxima.
- Mechanism (my reading of the records and D63, not from a source): phase 1's low-side edge is timed and learned
  (dlo steps up to lo_smax 64 LSB = 2 ns per period), so a Ton that rises ~3 ns per period moves the valley by
  ~10 A per period: the current integrates Ton's excess. The P term around that integrator and Co forms an undamped
  pair: 4 phases x 11 V x 1 ns / 2.93 nH per 0.22 us period = 68 A/us per ns, x kp 355 ns/V / Co 4.67 mF ->
  omega^2 = 5.2e12 s^-2, a 2.8 us period (records: about 3 us; D63 at L0: 3 us, damped within ~15 us). D63 also
  showed that holding the valley (a volt-second feed-forward into dlo, or a ceiling on the timed edge) doubles the
  load-step dip (+62.5 A: -10 -> -18 mV; +200 A: -26 -> -57 mV): the drift is what makes the loop fast.
- Change: damping instead - a derivative term on the Vo sample's change, d_term = -kd x (code - previous code),
  held to the next sample like the P term, zero while |the change| < 2 codes (1 mV), so the ADC's +-1-code limit
  cycle (C09) does not reach Ton. Basis: derivative action of a digital PID on a sampled converter loop (standard
  practice, e.g. Erickson and Maksimovic, Fundamentals of Power Electronics, 3rd ed., 2020, digital control of a
  voltage-mode PWM buck); no source for a dead-banded derivative on a valley-timed SCB - ours. kd from D63:
  355 ns/V (= kp) damps the ring (17-22 -> 4 mV peak to peak at +200 / +237.5 A) and leaves A124's rows within
  1 A; 530 adds 4 A to +62.5 A; without the dead band D63's steady state breaks (valleys -17.6..+15.6 A).
- Stage 1 (decides kd): w5_N0, w20_N0, w5_N75, k_N0, k_S75h, l_N0_p48 at kd 355 and 530 (all with rel_gate 25).
  Stage 2: w0_N0, w30_S75h, u_N0, l_N0_m80 and A221's skipping rows (N0 10 %, N75 10 %, N0 no load; A222's trims)
  at the chosen kd. The reference d0 for every pair row is A223's g25 record (A224's code without kd is A223's,
  checked by i_u_N0_g25).
- Not tested: four modules, other temperatures and step positions, the cold start-ups, L corners.

## 2. Criteria (on the chosen kd; stage 1 scores both)
- j1: unit tests 107 of 107 (new: voltage_loop_derivative); cosim_regression --quick and --full bit for bit;
  i_u_N0_g25 equals A223's run_u_N0_g25.json bit for bit (sections, edge lists, peaks).
- e1 (w rows): whole-run peak <= 200 A, no overlap or shoot-through, V_DS <= 40 V, Vo within 1 % over the last 20 us.
- e2 (u_N0, k_N0): post-event peak <= d0's + 1 A, |Vo extreme| <= |d0's| + 1 mV.
- e3 (line rows l_N0_p48, l_N0_m80, k_S75h): post-event peak <= d0's + 1 A and <= 200 A, |Vo extreme| <= |d0's| + 1 mV.
- e4 (every pair row): start-up and handover peaks <= d0's + 2 A, Vo's maximum before 300 us <= 1.05 V.
- e5 (skipping rows): A221's s1, s2, z1r; s3t on N0 10 % and N75 10 %; N0 no load's true valleys no more than 1 A
  below A221's -21.2 A.

## 3. Predictions (not criteria)
- D63 (k355 / k530): w rows' rings 4 / 4 mV pp (k0 17-22), Vo back within 1 % in 9 / 6-7 us (k0 20-21); p62
  177 / 181 A; rising line rows within 1 A at k355.
- Cosim: k355 brings the three w rows to 185-205 A (the cosim's ring is larger than D63's: phases 2-4 swing more);
  k530 to 175-195 A but +2-5 A on k_N0. Line rows within 1 A at k355. Start-up / handover within 1 A (the handover's
  Vo moves < 1 mV per period). Skipping rows: s1 / s2 hold, true valleys within 2 A of A221's.

## 4. Decision rule
- Stage 1: kd = 355 if it passes e1 on the three w rows and e2 / e3 / e4 on its three other rows; else 530 if it
  does; else neither, stage 2 is not run, and the ring is traced further (A225).
- Stage 2 at the chosen kd: j1 and e1-e5 pass -> rel_gate 25 and kd join the final configuration; item 9 closes for
  the rows run. A miss is reported with its record, and the final configuration stays as it is.

## 5. Stage 2 additions (written after stage 1, before stage 2's runs)
- Stage 1 (a224_summary.json): kd 355 passes e1-e4 on its six rows (w rows 152.6 / 163.4 / 158.1 A); kd 530 passes
  e1 but its S75 125 C start-up reaches 276.6 A at the handover (A223's g25 180.0 A; record
  cosim/run_k_S75h_d530.json): the derivative term pushes Ton to 52 ns while Vo falls from the 1.045 V request,
  Vo undershoots to 0.993 V and the valleys are lost (289.7 A at +38 us). By Section 4 kd = 355.
- Because a kd 1.5 x the chosen one breaks the hottest handover, two start-ups to 200 us are added:
  h_S75_25_d355 (A222's S75 25 C start-up, reference A222's run_s_S75_25_r2.json; criterion e4) and h_S75h_d440
  (S75 125 C at kd 440 = 1.24 x 355; information - the margin, not in the decision).
- Seen in stage 1, reported, not a criterion: kd 355 raises the late fires in the 40 us after the S75 125 C handover
  from 12 to 74 and after the re-applications (e.g. N0 from 20 %: 104 -> 166).
- Prediction: h_S75_25_d355 within 2 A of A222's handover (154.0 A on V5; V7 151.3 A); h_S75h_d440 between 180 and
  230 A at the handover (no basis to place the cliff between 355 and 530).
