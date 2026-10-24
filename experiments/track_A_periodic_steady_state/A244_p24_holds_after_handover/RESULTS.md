# A244 - the holds act only after the handover (items 10 and 3) (RESULTS)
Boundary: 59b9356 (code), control 0e83537. Records: release records-a244 (47 + 6 records, logs), all from 59b9356 or
later commits with no change under src/, cosim_sources_modified False, all COMPLETED. Analysis a244_analyze.py ->
a244_summary.json, a244_control.py -> a244_control.json; figure a244_figure.py -> a244_holds_after_handover.png.
Plant V7, final configuration; arm w = early_hold_a and late_hold_a 0.0, hold_wait 32.

## 0. Verdict
- **Adopted by user decision on 2026-10-24, after these results** (early_hold_a 0, late_hold_a 0, hold_wait 32; one
  module and four modules). Item 3 closes; item 10 stays open for the lock below and for 1 MHz.
- **Not adopted as registered: g2 misses on N0 at 100 kHz** (190.5 A against the board's single re-application +
  10 A = 171.5 A). This row is a second part of item 10, which the holds do not fix (below). The current final
  configuration misses it too: A240 195.7 A.
- **The wait does what it is for (g0, g8 pass).** All 47 runs equal their references before the disturbance. o_cw5_N75
  equals A243's record bit for bit. A243's handover costs are gone:
  - item 2 rows 211.2 / 207.8 A, as the reference;
  - release rows' NEW counts as the reference (13 / 13 / 6);
  - N0's Vo maximum 1.0490-1.0498 V (A240 1.0490-1.0498; A243 1.0513).
- **Item 10, 10-200 kHz:** every row <= 190.5 A (A240 up to 210.3 A).
  - N75 at 100 / 200 kHz: 152.1 / 149.5 A (A240 210.3 / 203.3 A).
  - N0 at 60 kHz: 159.8 A (A240 196.5 A).
  - 10 kHz late fires: N0 496 -> 15, S75 at 30 kHz 1440 -> 3.
  - Dips within 1.2 mV of A240's.
  - 1 MHz stays the ladder's: N75 246.1 A (A240 237.5), S75 211.1 A (221.9).
- **Item 3:** f_N75_k4 162.8 -> 153.4 A and r_N13_lm48 163.6 -> 162.4 A, without a K3. Re-applications are 3-22 A
  lower (cw5_N75 171.1 -> 149.1 A).
- **What the holds leave: the lock after a reversed collapse** (figure, upper right; records `cosim/run_w_p_N0_100k.json`,
  A240 `cosim/run_p_N0_100k.json`).
  - A release valley that did reverse (-61 A) is a valid report. At about 490 us one such report lowers phase 4's
    delay from 15 to 8 ns.
  - At the next full-load half the phase turns on with positive current, so every report is held. The delay stays at
    7-8 ns and the phase takes more current each period: peaks 178-190 A at every re-application.
  - A240 does the same from about 340 us: 5-8 ns, 185-196 A, never recovering. A243 never collapsed on this row
    (15 ns, 148.4 A).
- **Stage 2's three misses are step-position scatter (c1 passes on all):**
  - f_N75, positions k 0 / 2 / 4: 158.2 / 158.9 / 153.4 against 156.2 / 153.7 / 162.8 A.
  - a_S75_d20: NEW at most 4 against 6; peaks 191.9 against 191.9 A.
  - m4_l_m80_10us (four modules, -8 V / 10 us; one period at +7.0 us on module 4's phase 4): 169.5 / 168.7 / 168.7
    against 166.9 / 169.2 / 168.5 A; |Vo| at most 20.1 against 24.2 mV.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| g0 | unit 123 / 123, regression quick + full, o_cw5_N75 bit for bit | pass |
| g8 | every run equals its reference before the disturbance | pass (47 / 47) |
| g1 | stage 1: A240's q1 | miss only at 1 MHz (N75, S75), excepted by the rule |
| g2 | stage 1: A240's q4 (single re-application + 10 A) | **miss on N0 100 kHz (190.5 A)**; 1 MHz excepted |
| g3, g4 | stage 1: A240's q2 and q5; dips within 5 mV | pass (18 / 18) |
| g5 | stage 2: limits | pass (28 / 28) |
| g6 | stage 2: peak, NEW, Vo against the reference | miss 3 / 28: f_N75_k2 (+5.2 A), a_S75_d20 (NEW 3 / 1), m4_l_m80_10us (+2.6 A) |
| g7 | skipping rows | pass |
| c1 | control on g6's misses | pass (3 / 3) |

## 2. Predictions
- Held: g8 on every run, o row bit for bit; 10-200 kHz on N75 / S75; falling rows without K3; re-applications lower;
  item 2 within 2 A (equal).
- Missed: every 10-200 kHz row <= 165 A (N0 100 kHz 190.5 A, the lock above); N0's overshoot <= 1.0515 V (held:
  1.0498 V); release rows' NEW within +-2 (held: equal).

## 3. What follows
- A report without reversal carries no valley, but the holds keep a delay that a reversed valley has collapsed. A next
  step would return such a delay towards the phase's settled value (learned from reversed reports) instead of holding
  it. The settled values differ by board (S75 at 125 C 9.6-10.5 ns, N0 15.8-17.4 ns, N13 17.6-18.8 ns) and S75's and
  N13's are not settled 13 us after the handover, so the reference would have to be learned.
