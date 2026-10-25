# A246 - a report with positive current lifts a delay far below the other phases' (item 10) (BOUNDARY)
Method: RTL + cosim (cfg-gated option; code eaff266 and cfgs committed before the runs).
Track A. Looked at beforehand: A244's 47 records and two pilot rounds on five of its rows (records in release
records-a246, from ab9b725 / eaff266, provenance clean).
Decision it changes: whether hold_floor_ns 3.0 joins the final configuration and closes item 10 at 10-200 kHz (the lock
after a reversed collapse, N0 at 100 kHz 190.5 A against the board's single re-application + 10 A = 171.5 A).
Cheaper check done first: A244's records (below); no cheaper model has the dt_pred learner or the gate delay.
Budget: 50 runs in one queue at 10 jobs (four modules and the lock's row first), about 6 h.

## 1. What and why
- **The lock (A244 `cosim/run_w_p_N0_100k.json`):** in a light half after a release, phase 4's valleys reach -40..-70 A,
  its node finishes the swing before the gate turns on, and its reversed reports lower dt_pred 0.3-1.1 ns each, 13.3 ->
  7.7 ns, while phases 2-3 stay at 16-17 ns. In the next full-load half its low-side turn-off current is positive; the
  holds (A236 / A242) and the flat reports (no swing, no dip) leave dt_pred; the phase turns on early with positive
  current every period and climbs to 170-182 A at each re-application.
- **Why a floor:** with positive current the node cannot swing, so the delay buys no soft turn-on; a delay shorter than
  the other phases' only gives this phase more volt-seconds. In A244's records a report with positive current and a
  delay more than 3 ns below both other slotted phases occurs 210 / 538 times on N0 100 kHz / N75 1 MHz, 1-11 times on
  seven rows, never on 37 (margins down to 0.1 ns, so every row is run). Settled delays differ by phase by at most
  1.6 ns (N0 phase 4 15.8 against 17.3-17.4 ns).
- **Option (A246):** scb_ctrl cfg_hold_floor / cfg_floor_band (bridge "hold_floor_ns"): phases 2..N get dt_floor = the
  other phases 2..N's smallest dt_pred minus the band; a report with m_pos that leaves dt_pred (early or late held by
  A236 / A242 while the holds act, or flat) raises dt_pred to it when below. Off: unit 137 / 137, regression quick and
  full PASS. No source for the rule; it is ours.
- **Pilots (N0 100 kHz):** round 1 (ab9b725, held early / late only): band 3 ns 153.2 A, but band 4 ns 192.2 A: the lock
  formed and the full-load half's reports were flat, which round 1 left alone. Round 2 (eaff266, flat too): band 3 ns
  150.9 A, band 4 ns 176.1 A (lifted 8.7 -> 12.9 ns at the first positive report, still 4 ns early: 168 A). With band
  3 ns: N0 60 kHz 158.5 A (A244 159.8), S75h 100 kHz 153.9 A (155.8), N75 1 MHz 244.6 A (246.1).
- **Rows:** arm h = A244's cfg_w_<row> + rev_n 16 (the final configuration since A245; it never acts on these rows) +
  hold_floor_ns 3.0 on A244's 46 rows. Control: N0 100 kHz with the load train moved by 2 / 6 and 4 / 6 of the
  switching period (0.5112 us) in arm h and arm w (no floor).
- **Not tested:** bands other than 3 / 4 ns; start-ups with the floor beyond A244's rows; four modules under the
  accelerator load.

## 2. Criteria (arm h)
- g0: unit 137 / 137; regression quick and full PASS.
- Stage 1 (A240's 18 rows), as A244: g1 A240's q1; g2 A240's q4 (peak after 300 us <= the board's single re-application
  + 10 A); g3 A240's q2 and q5; g4 Vo's minimum after 300 us no more than 5 mV below A240's. 1 MHz rows (N75, S75)
  excepted from g1 / g2 as in A244 (the ladder, not the delay).
- Stage 2 (A236's 25 rows, A237's 3), as A244: g5 limits; g6 peak, NEW, Vo against the reference; g7 skipping rows.
- g8: a row where the floor never acts equals A244's record bit for bit. Detector a246_analyze.floor_acts: a report
  with positive current, 20 us or more after mode P, followed by a longer delay (>= 8 ns) on that phase; it reads none
  of A244's 47 records as an act and finds the first divergence of each pilot.
- g9: no row worse than A244's record: stage 1 peak after 300 us <= +2 A and Vo minimum >= -1 mV; stage 2 post-event
  peak <= +2 A (+10 A on re-application rows), NEW <= A244's, |Vo| <= +1 mV (as g6's tolerances).
- g10: N0 100 kHz at k 0 / 2 / 4 of T / 6: arm h within A240's q4 (171.5 A) at all three.

## 3. Predictions (not criteria)
- N0 100 kHz 145-160 A at all three positions (arm w at k 2 / 4: 175-195 A, the lock forming or not); N0 60 kHz,
  S75h 60-200 kHz within 2 A of A244; N75 1 MHz 240-250 A (excepted).
- The floor acts on 5-15 rows (pulse rows, four modules +250 A, k_N0); the rest equal A244 bit for bit.
- Risk: a re-application row (item 2, WIDE) where lifting a delay costs a few A; a falling-line row (item 3) where the
  floor lifts a phase whose valley stays positive.

## 4. Decision rule
- **g0 or g8 fails:** the option or the detector is wrong. Not adopted; traced.
- **All of g0-g10 pass** (1 MHz excepted): hold_floor_ns 3.0 joins the final configuration (one and four modules).
  Item 10 closes at 10-200 kHz; 1 MHz stays a limit with its mechanism.
- **A g9 miss only:** that row at k 2 / 4 of T / 6 in both arms (A243's c1: arm h's worst over k 0 / 2 / 4 against arm
  w's, +2 A / +10 A on re-applications, NEW at most arm w's most, |Vo| +1 mV). All pass c1: adoption goes to the user
  with the evidence; otherwise not adopted, traced.
- **A miss of g1-g7 or g10:** not adopted; traced.
