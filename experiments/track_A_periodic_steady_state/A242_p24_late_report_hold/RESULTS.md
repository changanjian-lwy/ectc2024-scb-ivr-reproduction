# A242 - hold the turn-on delay on a late report without reversal (item 10) (RESULTS)
Boundary: 27a5a09 (code 7f64828). Records: release records-a242 (47 records, logs), from 27a5a09 (10) and 6dff09c (37;
nothing under src/ changed between them), cosim_sources_modified False, all COMPLETED. Analysis a242_analyze.py ->
a242_summary.json; figure a242_figure.py -> a242_late_hold.png. Plant V7, final configuration; arm l =
late_hold_a 0.0.

## 0. Verdict
- **Not adopted (g1 / g2 at 1 MHz excepted by the rule; g5, g6 miss on 9 of 28 stage 2 rows).**
- **Item 10 is fixed at 10-200 kHz, at a small cost in Vo** (figure, upper row).
  - Every 10-200 kHz row is <= 159.7 A (A240 up to 210.3 A); N75 100 / 200 kHz 151.3 / 148.9 A.
  - N0's overshoot is 1.0512-1.0513 V for <= 0.92 us (A240 1.0498 V; A241 1.0538 V for 1.55 us).
  - Every dip within 5 mV of A240's; the 10 kHz late fires go (N0 496 -> 12, S75 30 kHz 1440 -> 3).
  - 1 MHz stays open: N75 289.0 A (A240 237.5), S75 204.4 A (221.9). This is the ladder, and it is sensitive.
- **Single re-applications drop:** cw5_N75 171.1 -> 149.7 A, cw5_N0 161.5 -> 151.5 A, w5_N0 159.8 -> 148.0 A, w5_N75
  159.6 -> 149.1 A. Four modules (m4 rows), the load rows and the skipping rows hold.
- **But item 3 gets worse:** f_N75_k2 173.7 against 153.7 A (K3 + NEW, none in the reference), f_N75_k4 +9.4 A,
  f_N75_k0 +2.3 A. The trace (f_N75_k2, phase 3; record `cosim/run_l_f_N75_k2.json`):
  - after the falling step the low-side turn-off current stays at +7..+11 A, so every report is early with m_pos;
  - dt_pred climbs 0.28 ns per period (24.7 -> 28.1 ns) to the restart, and when the valley returns (-19, -22 A) it
    is about 8 ns too long: the spike;
  - in the reference the same no-reversal periods also gave "late" reports (the ring) that offset the climb (15.3-15.9
    ns). Holding only the late ones leaves the climb unopposed.
- **Small misses:**
  - Item 2's rows: +2.1 / +2.5 A and one more NEW on a_S75_d20. The trajectories part at the handover (133.9 / 144.4
    us), where the hold first acts on phases 2-4 at +13..+24 A, and the step meets a different state.
  - NEW counts on re-applications +3 / +4 (u_N0, w5_N0, w20_N0), with lower peaks.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| g0 | unit 121 / 121, regression quick + full, o_cw5_N75 bit for bit | pass |
| g1, g2 | stage 1: A240's q1, q4 | miss only at 1 MHz (N75, S75), excepted by the rule |
| g3, g4 | stage 1: A240's q2 and q5; dips within 5 mV | pass (18 / 18) |
| g5 | stage 2: limits | miss 2 / 28: a_S75h_d2, a_S75h_d20 (item 2: > reference + 2 A by 0.1 / 0.5 A) |
| g6 | stage 2: peak, NEW, Vo against the reference | **miss 9 / 28**: f_N75_k0 / k2 / k4, a_S75h_d2, a_S75h_d20, a_S75_d20, u_N0, w5_N0, w20_N0 |
| g7 | skipping rows | pass |

## 2. Predictions
- Held: 10-200 kHz <= 185 A (159.7); the shortest delay >= 4 ns on N0 / N75 (S75 2.9-3.3 ns, missed there); Vo within
  +2 mV of A240 (+1.6 mV); the 10 kHz late fires mostly gone; skipping rows within 0.2 A.
- Missed: falling and item 2 rows within +-2 A without new K3 / NEW (item 3's climb ran unopposed); 1 MHz 215-245 A
  (N75 289.0 A).

## 3. What follows
- No-reversal periods give both early and late reports, and neither measures a swing. A243 ignores both (A236's
  early hold and this late hold together, cfg only).
