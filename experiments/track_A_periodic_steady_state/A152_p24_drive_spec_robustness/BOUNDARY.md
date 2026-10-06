# A152 - A151's drive spec with a start-up Ton compensation: robustness matrix (BOUNDARY)
Method: mixed (cosim matrix; start-up Ton calibrated on 160 us cosim runs beforehand)
Track A, package layer. Written and committed before the runs. Looked at beforehand: A151's records, 9 calibration runs to 160 us.
Decision it changes: which loop / turn-on / start-up Ton goes into the package spec for Mihai (S50, S100 or neither; up to 300 pH?).
Cheaper check done first: 160 us runs (mode S + handover only) to set ton_ns; single-edge harness at 300 pH.  Budget: 31 runs, ~3 h at 10 jobs.

## 1. What and why
- **Found before registering: A151's 18 A/ns misses the 200 A limit at the start-up handover.** A151 checked post-step peaks only.
  Its whole-run peaks are 205 / 224 / 240 A at 50 / 100 / 150 pH (18 A/ns), 276 / 288 A (9 A/ns), 154-163 A (36 A/ns),
  and 141-147 A at 72 A/ns (A145). Mechanism (records): mode S runs open loop at ton_ns 35.5. Its turn-ons are hard
  (V_DS 10-15 V), and a slow turn-on loses on-time. So Vo at 143.5 us is 0.958 V (18 A/ns, 100 pH) instead of 1.016 V
  (72 A/ns). At the handover the voltage loop's proportional term adds kp x 42 mV = 15 ns: Ton 51 ns, phases 2-4 at 209 / 218 / 224 A.
- **Fix, cfg only: raise mode S's Ton by about 36 A / turn-on di/dt.** Calibration, 160 us runs: at 100 pH / 18 A/ns,
  ton_ns 35.5 / 36.5 / 37.5 / 38.5 gives Vo(143.5 us) 0.958 / 0.985 / 1.014 / 1.043 and handover peaks 224 / 174 / 148 / 141 A;
  start-up V_DS 33.2 -> 33.1 V. At 50 pH / 36 A/ns, 35.5 / 36.5 gives 0.998 / 1.024 and 154 / 142 A. Chosen: 37.5 ns at 18 A/ns, 36.5
  at 36 A/ns, 39.5 at 9 A/ns (rule, not calibrated). Side effect: ton_ns also sets the integrator's start value and the vff seed,
  and the Ton clamps 0.5x / 2x ton_ns (17.75 / 71 ns -> 18.75 / 75 ns at 37.5).
- **Spec points.** S50 = 50 pH (rp 0.8224), 36 A/ns, ton 36.5. S100 = 100 pH (rp 1.163), 18 A/ns, ton 37.5. Turn-off 72 A/ns, loop Q 7.
- **Rows per point (13):** L0 l_p48_1us and s_p62 (A151's rows with the new Ton), l_m48_1us, l_m80_10us, L x 0.7 and x 1.3 on
  l_p48_1us and s_p62, and +4.8 V ramps of 2 / 3 / 4 / 5 / 10 us (A150 broke on these). Every run starts at t = 0; step at 1000 us.
- **Extra:** 300 pH (published embedded loops reach 230-320 pH) l_p48_1us at 72 (no fix) / 18 / 9 A/ns. Four modules l_p48_1us at S50
  and S100 (first four-module runs since A148; gen_multi fixed: it read "signed" as a port name, scb_multi.v did not compile;
  regenerated wrapper = A143 g5 record bit for bit over 250 us).
- **References:** the same row of the frozen design on the ideal plant (A143 g4_*_k4 / g5_l_p48_1us_k4, A150 c00_slew*), which
  differs only in loop / edge / vds_win / ton_ns. Not tested: L x Cs corners, other loads, gate-drive realisation.

## 2. Criteria (per spec point, all 13 rows; ref = the row's ideal-plant reference)
1. V_DS: whole-run max over all 8 switches <= 40.0 V.
2. Start-up: highest high-side turn-off current for t < 300 us <= max(200 A, ref + 5 A). (Ideal L x 0.7 already has 200 A.)
3. After the step: peak <= min(ref + 5, 200) A; 0 NEW oracle events (a142_oracles); whole-run late fires <= ref + 2.
4. Vo after the step: |extreme| <= |ref extreme| + 4 mV, and back-within-1 % <= ref + 2 us + P, where P is the L0 package price
   A151 measured on that step type (load step: 3.8 us at S100, 3.2 us at S50; line step: 0). The back-time part counts only when
   |extreme| > 11 mV (1 % + 2 ADC LSB): below that a 1 % band crossing is an artefact (ideal +4.8 V/4 us: 11.0 mV, back 39.6 us).
5. Four modules, each point: criteria 1-3 on l_p48_1us (ref A143 g5_l_p48_1us_k4).
6. 300 pH: some turn-on rate in {18, 9} keeps l_p48_1us <= 40.0 V and passes criteria 2-3.

## 3. Predictions (not criteria)
- C1: S50 <= 38 V, S100 <= 38 V on every row (L0 37.1 / 36.4 in A151); falling rows <= 34 V; L corners within +-2 V of L0.
- C2: L0 / L x 1.3 <= 160 A; L x 0.7 about 195-205 A (ideal 200 A). C3: peaks within +-5 A of ref; closest rows L x 1.3
  l_p48_1us (ref 191.4 A) and L x 0.7 l_p48_1us (184.7 A). C4: pass. C5: pass (handover 230 A at ton 35.5 -> about 150 A).
- C6 fails at 40 V: 300 pH 72 A/ns about 62 V, 18 A/ns about 41 V, 9 A/ns about 40.5 V (steady 72 A/ns turn-off ring grows
  with L: steady window 28.2 / 27.7 / 31.1 V at 50 / 100 / 150 pH); <= 48 V at 18 and 9. Harness, hard turn-on event only: 36.8 / 31.7 V.

## 4. Decision rule
- A point passing 1-4 (and 5) -> its loop / turn-on / ton_ns is the package spec; A151's 18 A/ns claim is corrected to "with ton 37.5".
- S100 fails, S50 passes -> spec is <= 50 pH (also the loss bound, ~70 pH for 1 %); 100 pH listed with the failing rows.
- C2 fails at a corner -> the open-loop start-up needs L-dependent Ton (next experiment), not a new driver.
- C3 / C4 fail on one row class -> stated as a limit of the spec (e.g. ramp time), not fixed here. C6 -> the loop ceiling for voltage.
