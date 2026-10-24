# A243 - leave the turn-on delay on every report without reversal (items 10 and 3) (RESULTS)
Boundary: 80647e9 (code 7f64828), control 06d71ff. Records: release records-a243 (46 + 28 records, logs), from 80647e9,
ed12815 and 06d71ff (nothing under src/ changed since 7f64828), cosim_sources_modified False, all COMPLETED. Analysis
a243_analyze.py -> a243_summary.json, a243_control.py -> a243_control.json; figure a243_figure.py ->
a243_hold_without_reversal.png. Plant V7, final configuration; arm b = early_hold_a 0.0 and late_hold_a 0.0.

## 0. Verdict
- **Not adopted (the control's c1 misses on 4 of 8 rows: a_S75h_d20, u_N0, w5_N0, w20_N0).**
- **Items 10 and 3 are fixed where the hold acts** (figure, upper row and lower middle):
  - Every 10-200 kHz row <= 159.6 A (A240 up to 210.3 A); N75 100 / 200 kHz 152.0 / 149.8 A, N0 60 / 100 kHz 158.2 /
    148.4 A. N0's overshoot 1.0510-1.0513 V for <= 0.92 us (A240 1.0498 V); the 10 kHz late fires go (N0 496 -> 11,
    S75 30 kHz 1440 -> 6). 1 MHz stays open: N75 254.3 A (A240 237.5), S75 212.4 A (221.9).
  - Item 3's events go: f_N75_k4 162.8 -> 153.1 A and r_N13_lm48 163.6 -> 156.7 A, neither with a K3 or NEW;
    f_N75_k2 153.6 A (A242 173.7).
  - Re-applications 10-22 A lower (cw5_N75 171.1 -> 149.3 A). Four modules: -8 V / 10 us 167.9 against 166.9 A, Vo
    +20.5 against +22.8 mV (A236's 3 mV cost is gone). Skipping rows pass.
- **The misses come from the start-up, not from the steps.** On every one of the 46 rows the holds before the
  disturbance act only 0.07-2.58 us after mode P's entry (3 per module on N0 / N75, 6-8 on S75 / N13), and the run
  parts from its reference there.
  - a_S75h_d20 (S75 125 C, +4.8 V / 1 us 20 us after the handover, inside item 2's 40 us hold-off): the holds leave
    C1 0.2-0.5 V lower for 20 us. Rail 1 is 12.29 against 11.97 V 1 us before the step and peaks at 16.78 against
    16.52 V, so phase 1's peak is higher at every position: 213.4 / 205.8 / 212.3 against 207.8 / 203.8 / 207.1 A
    (record `cosim/run_b_a_S75h_d20.json`).
  - u_N0 / w5_N0 / w20_N0: NEW at most 16 / 16 / 10 against 13 / 13 / 9. They are the reference's own kinds: order hits
    and 10-25 A spikes at <= 95 A in the 5 us after the release, and phase 1 order hits while skipping at no load.
    At k 4, u_N0 has no hold after the release and still 14 against 8, so the count follows the state carried from
    the handover (record `cosim/run_cb_u_N0_k4.json`).
- **Step-position scatter (c1 passes):** f_N75 (A232's positions: 159.5 / 153.6 / 153.1 against 156.2 / 153.7 /
  162.8 A), r_F0_lm48, r_F0_lm80, a_S75_d20.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| g0 | no change under src/ since 7f64828; A242's g0 | pass |
| g1, g2 | stage 1: A240's q1, q4 | miss only at 1 MHz (N75, S75), excepted by the rule |
| g3, g4 | stage 1: A240's q2 and q5; dips within 5 mV | pass (18 / 18) |
| g5 | stage 2: limits | miss 1 / 28: a_S75h_d20 (item 2: 213.4 > 207.8 + 2 A) |
| g6 | stage 2: peak, NEW, Vo against the reference | miss 8 / 28: f_N75_k0, r_F0_lm48, r_F0_lm80 (+2.1..+3.3 A), a_S75h_d20, a_S75_d20 (NEW 2 / 1), u_N0, w5_N0, w20_N0 (NEW +3 / +3 / +4) |
| g7 | skipping rows | pass |
| c1 | control: worst of k 0 / 2 / 4 against the reference's worst | pass 4 / 8; miss a_S75h_d20 (213.4 > 207.8 + 2 A), u_N0, w5_N0, w20_N0 (NEW) |

## 2. Predictions
- Held: stage 1 as A242 (<= 165 A: 159.6 A; Vo +1.6 mV; 1 MHz open); no K3 / NEW on the falling rows; re-applications
  lower; NEW up to +4 on them; the four-module row inside g6 (A236's Vo cost predicted, absent).
- Missed: f_N75_k0 within +-2 A (+3.3 A, scatter by the control); item 2 by up to 3 A (+5.6 A); skipping rows within
  0.2 A (z_N0 0.8 A, inside g7's 1 A).

## 3. What follows
- The holds do their work after a disturbance. At the handover they only move the ladder, and the step 20 us later
  meets it. A244 enables both holds only after a number of phase-1 periods in mode P, so every row matches its
  reference until its disturbance.
