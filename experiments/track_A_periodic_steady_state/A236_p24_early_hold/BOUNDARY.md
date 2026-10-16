# A236 - hold the turn-on delay when the valley did not reverse (BOUNDARY)
Method: RTL + cosim (cfg-gated option; code and cfgs committed before the runs).
Track A. Looked at beforehand: A235's run_r_N13_lm48.json (stage 2, its one c1 miss) and A232's run_f_N75_k4_b.json, period
by period; the oracle and turn-on records of A225 / A228 / A229 / A232-A235.
Decision it changes: whether item 3 (a K3 restart and a NEW spike after a -4.8 V / 1 us step, N75 and now N13) closes in
the final configuration, and with it whether A235's L x 1.3 column moves to V7 without that footnote.
Cheaper check done first: the records (below). D63 has no dt_pred block (A143), so no cheaper model. Budget: 26 runs,
about 2.5 h at 10 jobs (two four-module runs set the wall time).

## 1. What and why
- Mechanism (records; plant V7, final configuration): the step lands on rail 1 (N13: 12.39 -> 7.85 V) and the rails
  take ~80 us to share it again. Meanwhile the slotted phase with the highest rail (N13 phase 4: 11.5 V against 10.5 V
  final; N75 phase 3) carries more current, and at its slot its low side turns off at +1..+5 A: the current has not
  reversed, so the node cannot swing and every turn-on is hard (V_DS 10-12 V). Each such turn-on still reports
  "early" (the node was still falling), and the corrector adds dt_step (0.28 ns) to dt_pred, every period for 25-30 us:
  dt_pred 17.6 -> 28.3 ns (N13; recorded edges 8 ns earlier, the driver lead). Past cfg_rs_high (28.28 ns) the restart
  fires (K3); when the valley is negative again dt_pred is ~8 ns too long, the high side's body diode conducts first and
  that period's peak is 12-18 A above its neighbours (NEW: N13 157.6 A at 535.3 us, N75 153.1 A at 521.3 us).
- The pattern (early with the low-off current > 0) is on every falling step (N0 too: 68-75 turn-ons per run, no restart
  because the valley returns sooner), on the re-applications (all phases) and on item 2's rows (phase 1).
- Option (A236): cfg "early_hold_a" -> m_pos per valley report = the current at the actual low-side turn-off above this
  value (a comparator sampled at that edge); scb_phase cfg_early_hold: an early report with m_pos leaves dt_pred (an
  early report without it still steps; late / flat reports unchanged). Off: bit-identical (unit 111 / 111, regression
  quick and full bit for bit, before this boundary). Arm h: early_hold_a 0.0.
- Basis: Chiang & Chen, TPEL 2009 split the turn-on by whether zero voltage can be reached (a valley path otherwise);
  single-phase silicon buck IC, 5 -> 3.3 V, ~3.6 MHz. Zhang et al., TPEL 2023: zero voltage needs the reverse current
  to discharge the node; GS66516T 650 V GaN, double-pulse and 305 kHz TCM. Lange et al., ECCE Europe 2025: body-diode
  conduction marks a dead time that is too long; load-resonant converter, measured. No source holds an adaptive
  turn-on delay on the current's sign: that rule is ours. P24 names no per-phase current comparator at the low-side
  turn-off (the design already assumes one per phase for A220's zero-current end of a pause).
- Rows: each against its reference record (cfg + early_hold_a 0, all else equal). Falling: A232 f_N0_k0 / k4, f_N75_k0 /
  k2 / k4, f_S75_k0; A235 r_N13_lm48, r_F0_lm48, r_F0_lm80; A228 l_N0_m80; A234 m4_l_m80_10us (four modules). Rising:
  A228 l_N0_p48; item 2 (inside the 40 us hold-off): A225 a_S75h_d2 / d20, a_S75_d20 (they ran without kd_band, inert
  there, A233). Load: A229 k_N0, k_S75h (binding row), A234 m4_s_p250. Re-applications: A229 w5_N0, w20_N0, w5_N75,
  w30_S75h, u_N0. Skipping: A229 z_N0_10_t0, z_N75_10_t0. Identity: o_f_N75_k4 = A232's cfg, option off.
- Not tested: other temperatures and boards for the load rows, other step positions, other thresholds than 0 A.

## 2. Criteria
- e0: unit 111 / 111, regression quick and full PASS, run_o_f_N75_k4 = A232's run_f_N75_k4_b (sections, edge lists,
  late fires, overlaps, peaks) bit for bit.
- e1 (falling rows): no K3 and no NEW oracle event after the step.
- e2 (every event row): completes, whole-run gate-level peak <= 200 A (item 2's rows: <= reference + 2 A), V_DS <=
  40 V, no overlap or shoot-through, Vo within 1 % over the last 20 us; four modules also rail 1 <= 13.5 V (A234 f3).
- e3 (every event row): post-event peak <= reference + 2 A (re-applications, measured from the second step: + 10 A,
  A229's spread between arms that differ only near the limit); NEW events after the event <= the reference's; |Vo
  extreme| <= |reference| + 1 mV (not on re-applications).
- e4 (skipping rows): A229's run test (q1) and the true valleys' min / max within +-1 A of the reference.

## 3. Predictions (not criteria)
- e1 passes on all 11 falling rows; the held reports per falling row 40-80 (phases 2-4); the post-step peaks within
  +-2 A (their maxima come in the step's first microseconds, before the hold acts).
- Turn-on V_DS during the positive-valley interval 1-3 V higher (no partial swing); maximum after the step within +1 V.
- Item 2, load, rising rows within +-3 A (few held reports, phase 1); re-applications within +-10 A; skipping rows within
  0.2 A of the reference.

## 4. Decision rule
- e0-e4 pass: early_hold_a 0 joins the final configuration (one and four modules); item 3 closes on V7 for the tested
  boards; A235's N13 c1 miss is item 3's and the L x 1.3 column moves to V7 with A236's option.
- e1 passes, e3 or e4 misses: the miss is traced before any adoption. e1 misses: item 3 stays open; trace.
