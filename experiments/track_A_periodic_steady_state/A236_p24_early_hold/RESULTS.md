# A236 - hold the turn-on delay when the valley did not reverse (RESULTS)
Boundary: 050441c, amended 1cdab3a (Section 5: the first commit crashed every run at t = 0; fixed before any record).
Records: release records-a236 (26 cosim records, logs). Analysis: a236_analyze.py -> a236_summary.json; figure
a236_figure.py -> a236_item3.png. Runs from 1cdab3a (10) and 9ab4618 (16; A235 docs only),
cosim_sources_modified False. Plant V7, the final
configuration, each row against its reference record; arm h = + early_hold_a 0.0.

## 0. Verdict
- **Not adopted as registered: e0, e2 and e4 pass; e1 misses on one row, e3 on two.** The final configuration stays;
  item 3 stays open, now traced and confirmed by intervention.
- **The hold removes item 3's own events wherever they occurred.** N75 k4: K3 + NEW -> none, peak 162.8 -> 151.6 A (the
  reference's peak was the spike); N13 -4.8 V: the restart and the 157.6 A spike are gone, dt_pred stays at 18-19 ns
  instead of climbing to 28.3 ns (a236_item3.png). No K3 on any of the 11 falling rows; 9-58 held reports per row.
- **e1's miss is not item 3:** N13's remaining NEW is the step-window swing peak at 502.002 us (146.0 A, 11.9 A above
  its neighbours, 2 ns after the K4 window), identical in both arms; the hold does not act there (no early report).
- **e3's misses are the hold's cost.**
  - Four modules, -8 V / 10 us: the undershoot after the ramp is 3.0 mV deeper (-24.1 against -21.1 mV at 415 us).
    The peak is 2.6 A higher (169.5 against 166.9 A, module 4 phase 4, during the ramp).
  - S75 125 C, +4.8 V / 1 us 2 us after the entry (item 2, inside the 40 us hold-off): the hold acts five times on
    phase 1 (139.6-151.3 us, its positive-valley stretch), and the trajectory departs from the reference at 139.999 us.
    From 162 us the h arm alternates between long and short periods and leaves three spikes 10-12 A above their
    neighbours (154-158 A, phases 3 / 4 / 1 at 165.9-166.1 us). The row's peak is unchanged (211.0 against 211.2 A).
  - Likely reason (not isolated): the ratchet's late turn-ons let the body diode carry extra charge, which partly
    covers a falling line's energy deficit; held, that charge is missing.
- Everything else within the registered tolerances: the other falling rows within -1.5..+1.9 A; load, rising and
  item 2 rows within 0.8 A; re-applications +4.8 A at most (w20_N0); skipping valleys within 0.03 A.
- Identity: run_o_f_N75_k4 = A232's run_f_N75_k4_b bit for bit (sections, edge lists, late fires, overlaps, peaks).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| e0 | tb 111 / 111, regression quick + full PASS (fresh outputs), o row bit for bit | pass |
| e1 | falling rows: no K3, no NEW | 10 / 11; **r_N13_lm48: one NEW (the step-window peak at 502.0 us)** |
| e2 | limits on every event row | pass (peaks <= 193.6 A outside item 2; V_DS, overlaps, Vo at the end) |
| e3 | peak / NEW / Vo against the reference | 21 / 23; **a_S75h_d2 (3 NEW), m4_l_m80_10us (+2.6 A, \|Vo\| +1.3 mV)** |
| e4 | skipping rows | pass |

## 2. Predictions
- Held: post-step peaks within +-2 A except where the reference's peak was the spike; item 2 / load / rising rows within
  3 A; re-applications within 10 A; skipping rows within 0.2 A; turn-on V_DS maximum after the step within +1 V.
- Missed: e1 on all 11 falling rows (N13's step-window peak, outside the hold's reach); held reports 40-80 per row
  (9-58).

## 3. Limits
- One threshold (0 A). The undershoot cost was seen on four modules only; the one-module -8 V rows (l_N0_m80,
  r_F0_lm80) moved 0.2-0.9 mV. 25 C except S75h; one step position per row except N0 / N75.
