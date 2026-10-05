# A141 - the floor's late report: A140's duplicate phase-1 turn-on (BOUNDARY)
Track A (main line; the fix also covers track C's slave floor). Code committed in 5106106 (cfg `floor_late`, tb 85
tests); this file is committed before the runs. Looked at beforehand: A140's and C10's event logs (below).
Decision it changes: whether floor_late joins the adopted design (single and four modules), and the rising-step spec
at L x 0.7 (+4.8 V 10-20 us is forbidden only because of the duplicate).  Cheaper check done first: the event logs
of all 36 A140 records + C10 / A137 records, and the tb (the defect reproduced at unit level).  Budget: 20 cosim runs,
~20 min wall at --jobs 10.

## 1. What and why
- **Cause (RTL, not the bridge).** Every duplicate in A140 (140 of 140) is two edge pairs: an off-LSB-grid one from
  the floor (A118's front end armed at i_target + trim - 2 A) and an on-grid one from the RTL's timed turn-off. The
  floor always fires in the window *before* the one where the RTL commits its timed edge; its TDC report reaches the
  RTL two windows later (synchroniser), when phase 1 is already in UP, and scb_phase took the report only in LOW. The
  front end's turn-on reaches the power stage first (the RTL's later turn-on finds V_DS = 0), but Ton counts from the
  RTL's own turn-on: +0-6 ns on, +20-38 A. "RTL first" pairs (6 of 136) are harmless. The bridge models A81's
  hardware partition faithfully (async latch + delay line; a 2-FF report latency cannot be removed), so the defect is
  the RTL's arbitration. C10's slaves (C06 slot floor) show the same signature (module 3's 179.3 A on l_p48_5us).
- **Fix (cfg floor_late 1).** A floor report in UP earlier than t_lo is the turn-off (t_lo = a_tlo, t_on = a_tlo +
  dt_pred, HIGH, the pending clocked turn-on dropped); in HIGH, an earlier floor turn-on moves t_on. Off = unchanged.
- **Rows (arm F = adopted design + floor_late 1; `make_cfgs.py`):** R: A140's ten L x 0.7 rising rows (+4.8 V at 1, 5,
  10, 20 (4 step positions), 40 us; +8 V at 20, 50 us); D: falling A124 rows at L0 (-4.8 V/1 us, -8 V/10 us);
  A: C10's single-module rising rows s100 / s130 l_p48_1us / 5us; C: C10's four-module l_p48_1us / 5us.
  Identity: I0 = A140 cfg B_L070_p4.8_s10.0 verbatim on the new code; I1 = C10 s100_n0 + floor_late 1.
- Not tested: L x 0.7 falling rows, the other A124 load rows (no floor-first event on any record: n0, m1n, m3n,
  s_p62 at L x 0.7 / 1 / 1.3, C10 n0 / s_* - I1 checks the option is inert there).

## 2. Criteria
1. Identity: I0's sections (vo, ton_lsb) and turn-on times equal A140 run_B_L070_p4.8_s10.0's; I1's equal C10
   run_s100_n0's (bit for bit).
2. Mechanism: 0 floor-first duplicate turn-ons (off-grid then on-grid, same phase, < 20 ns; `make_cfgs.floor_first`)
   in every F run, every module, over the whole recorded window.
3. Peaks: every F run's post-step peak <= its reference's nodup + 2 A (nodup = reference peak with the periods ending
   < 60 ns after a floor-first duplicate taken out; reference = A140 / A137 / A138 / A139 / C10 record of the row).

## 3. Predictions (not criteria; `a141_predictions.json`)
- F peaks = reference nodup: L x 0.7 +4.8 V 185.2 / 188.6 / 194.1 / 191.1, 188.4, 188.1, 185.6 / 179.3 A at
  1 / 5 / 10 / 20 (q0-q3) / 40 us; +8 V 210.1 / 180.2 A at 20 / 50 us; D 173.5 / 168.5 A; A s100 179.2 / 176.6,
  s130 186.6 / 175.2 A (s130 1 us: a hard turn-on 0.76 us after the step, not a duplicate - unchanged); C 180.6 /
  176.6 A. Rows without a duplicate before the peak replay up to the first late report.
- The HIGH path is not used: dt_pred ~9.3 ns > two windows, so every late report arrives in UP.
- I1 bit for bit (no late report in s100_n0's record).

## 4. Decision rule
- 1-3 pass: floor_late 1 joins the adopted design (single and four modules); the L x 0.7 rising spec is rewritten from
  the F peaks (+4.8 V allowed at every slew whose runs are all <= 200 A); A139's +14 A tail and C06/C09/C10's
  l_p48_5us spike are closed as this defect. Then CURRENT_STATUS, scorecard, scb-map.
- 1 fails: code defect - fix before any reading of 2-3.
- 2 fails: inspect each remaining event (HIGH path, another source); not adopted until explained.
- 3 fails: per-row explanation; not adopted as is.
