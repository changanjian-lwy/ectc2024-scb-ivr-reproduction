# A241 - a fall limit on the slotted phases' turn-on delay (item 10) (RESULTS)
Boundary: 52b67d9 (code e56bc76). Records: release records-a241 (34 records, logs), all from 52b67d9,
cosim_sources_modified False. Analysis a241_analyze.py -> a241_summary.json; figure a241_figure.py ->
a241_fall_limit.png. Plant V7, final configuration; arm f = dt_fall_ns 0.282843 (one dt_step per report).
**Stage 2 was stopped after 15 of 28 rows** (2026-10-23 23:49). With 5 misses the decision was fixed, and further rows
could only add misses. The 13 rows not run: f_S75_k0, r_F0_lm80, r_N13_lm48, k_S75h, u_N0, w5_N0, w20_N0, w5_N75,
w30_S75h, z_N0_10_t0, z_N75_10_t0, m4_l_m80_10us, m4_s_p250.

## 0. Verdict
- **Not adopted (g1, g2, g4 and g5, g6 miss).**
- **The repetition is fixed at 10-200 kHz on every board** (figure, upper left). N75 100 / 200 kHz 210.3 / 203.3 ->
  152.7 / 149.4 A; N0 60 / 100 kHz 196.5 / 195.7 -> 161.1 / 148.3 A; every 10-200 kHz row <= 161.1 A.
  - The slotted phases' shortest delay stays at 13.8-16.7 ns on N0 / N75 (A240 1.0-4.8 ns on the failing rows).
  - The late fires go: N0 10 kHz 496 -> 11, N75 325 -> 7, S75 30 kHz 1440 -> 56. They were phases 2-4's, as A240's
    correction now says.
  - Single re-applications: cw5_N75 171.1 -> 150.1 A, cw5_N0 161.5 -> 152.5 A.
- **1 MHz is worse:** N75 237.5 -> 258.9 A, S75 221.9 -> 241.9 A. The delay no longer collapses (>= 12.6 ns on N75),
  but phase 4's valley swings -123 -> +99 A and its rail reaches 16.28 V (A240 15.38 V). This is the ladder pushed
  by a load whose period is about two switching periods, not the delay.
- **Vo swings more.** After a release the delay no longer follows the fast swing of deep valleys, so the node sits at
  the rail longer and more charge reaches Co.
  - The overshoot is 4-6 mV higher: N0 1.0524-1.0538 V, above 1.05 V for 1.1-1.55 us (A240 never).
  - The loop's Ton is lower when the load returns (S75 100 kHz, 310 us: 255 against 555 LSB at Vo 1.0188 against
    1.0079 V), so S75's dips at 60 / 100 kHz are 5.3 / 5.0 mV deeper (0.9638 / 0.9689 V; g4 misses).
- **Stage 2: the limit makes the delay ratchet up** wherever the valley stays positive. Early reports add a step and
  a late one can take back only a step.
  - f_N75_k0: phase 3 reaches the 28.3 ns restart every 1.75 us (520.5-530.0 us), with a 19-24 A spike after each:
    6 K3 + 6 NEW, 166.1 against 156.2 A.
  - Item 2: a_S75h_d2's phase 1 sits at about 23 ns (reference 7-9 ns), 216.3 / 218.5 A against 211.2 / 207.8 A.
  - f_N75_k2: +4.9 A.
  - Item 3's own row f_N75_k4 loses its K3 and NEW (162.8 -> 159.0 A).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| g0 | unit 119 / 119, regression quick + full, o_cw5_N75 bit for bit | pass |
| g1 | stage 1: A240's q1 (whole run <= 200 A, ...) | **miss 2 / 18**: N75 and S75 at 1 MHz |
| g2 | stage 1: A240's q4 (single re-application + 10 A) | **miss 2 / 18**: the same rows |
| g3 | stage 1: A240's q2 and q5 | pass (18 / 18) |
| g4 | stage 1: Vo min >= A240's - 5 mV | **miss 2 / 18**: S75 60 / 100 kHz (-5.3 / -5.0 mV) |
| g5 | stage 2: limits | **miss 2 / 15**: a_S75h_d2, a_S75h_d20 (item 2: > reference + 2 A) |
| g6 | stage 2: peak, NEW, Vo against the reference | **miss 5 / 15**: f_N75_k0, f_N75_k2, a_S75h_d2, a_S75h_d20, cw5_N75 (NEW 8 against 7; peak -21 A) |
| g7 | skipping rows | not run |

## 2. Predictions
- Held: the shortest delays >= 6 ns on N0 / N75; N75 100 / 200 kHz <= 180 A; N0 60 / 100 kHz <= 175 A; N0's 30-60 kHz
  dips within 5 mV; re-applications lower; item 3's rows at risk.
- Missed: the 10 kHz late fires were expected unchanged (they went, because they were the delay's); 1 MHz was
  expected at 185-225 A (it is 241.9-258.9 A); Vo was expected within +-5 mV of A240 everywhere.

## 3. What follows
- **The records show what collapses the delay.** On A240's and A237's re-application rows, 54 % of the falls over
  0.5 ns (63 % of the total fall) come from reports whose low-side turn-off current had not reversed. Those reports
  carry the edge's ring, not a swing. A242 holds dt_pred on such late reports and leaves early reports as they are.
- 1 MHz is a separate mechanism (the ladder) and stays open.

## 4. Limits
- One fall limit (one step) was tested. Stage 2 is incomplete (13 rows not run), including four modules and the
  skipping rows.
