# A221 - the inductor's core loss in the plant (V7), and a pause that keeps the slots' period (BOUNDARY)
Method: plant (circuit.py: r_core) + RTL (scb_ctrl: one condition) + cosim.
Track A. Written after A220's records and six development runs (not records; scratch worktree, uncommitted code),
committed before A221's runs. Looked at beforehand: (1) V6 with 10 mOhm in series with an idle phase's inductor:
the first valleys after a resume at -15.6..-16.2 A on all four phases (N0, N75 10 %), but the alternation still began
at the third round; (2) its cause in A220's own RTL: phase 1's zero-current turn-off makes the skipped instant
(t_lo + dt_pred) early, so the pause measured a short period and the first two rounds' slots were 38.1 / 76.2 / 114.4 ns
instead of 42.1 / 84.2 / 126.4 ns (N75), jumping at the third (A216 and A217 have the right slots); (3) with that
fixed and the idle damping: N75 10 % true valleys -17.0..-13.3 A over the last 60 us (band -20..-12), N0 10 %
-16.6..-5.2 A; without the damping -21.4..-7.3 / -22.9..-1.1 A; (4) N0's ladder is unbalanced by the release itself
(rail 4 - rail 1 up to 3.7 V at 340 us, 1.56 V at 450 us, also without skipping: A216's 20 % row 2.64 -> 0.43 V),
decaying with about 125 us; N75's is not.
Decision it changes: whether skipping is adopted, and whether the plant gains the core loss (V7).
Cheaper check done first: the development runs above. Budget: 8 runs, about 2.5 h at 8 jobs (the binding row 2.1 h).

## 1. What and why
- V6 has no resistance in an idle phase: its circuit R is 0 and an off switch has none, so an inductor's ring
  against the switches' capacitance never decays (A220: 1.9-2.1 A rms through a 30 us pause), and each phase resumes
  from a different point of it. V6's loss books also have no inductor loss.
- Plant V7 = V6 + a resistor r_core across each inductor: the parallel model of a magnetic core's loss. Basis: D76
  (HBS1 of P24 Table 2, data of Murali et al. as read there: R_acx = 0.301 / 0.886 / 2.557 mOhm/nH at 2 / 4 / 8 MHz,
  a triangular ripple at duty 0.077), small signal (kappa 1). The model's R_ac(f) = (2 pi f L)^2 / r_core is fitted
  at 8 MHz, the measured point nearest the ring: r_core = 2.90 ohm at L0, 2.17 ohm at 0.75 L0. It then books
  0.5-1.0 x D76's small-signal loss between 2 and 8 MHz, and at the ring's 20-25 MHz (Q about 7) 1.7 x more damping
  than D76's f^1.5 extrapolation, which the rc2 rows (twice r_core) bracket. No source gives HBS1 above 8 MHz.
- RTL: with cfg_zcd a pause leaves t_per (the slots' period) as it was (scb_ctrl, one condition; one unit test that
  fails without it). Off (no zcd) bit for bit.
- Rows: N0 10 %, N75 10 %, N0 no load, N0 5 % then +62.5 A with A220's settings + the fix on V7; N0 runs to 750 us
  (the ladder); N0 10 % and N75 10 % again at twice r_core (rc2). V7 against V6: A215's ton_lat 16 rows +62.5 A on N0
  and the binding row S75 125 C k 5 with r_core (references: A215's records).
- Not tested: kappa > 1, the copper's resistance (D72), core loss at other temperatures, four modules, the slow
  board's skipping (it does not skip, A217).

## 2. Criteria
1. j1: r_core and zcd absent: unit tests all pass (104), regression quick and full, the three r_core tests.
2. k1 (two k rows): A215's criteria of the row (A212 c6 + c7 / A206 c6) pass on V7; the post-step peak within 3 A of
   A215's record; Vo's maximum before 300 us within 2 mV.
3. On the three main skipping rows (N0 10 %, N75 10 %, N0 no load) and the +62.5 A row: A216's s1, s2 (and s4).
4. s3t (main rows): the true valleys, low-side turn-offs followed by that phase's turn-on within 100 ns, over the last
   20 us (60 us if none), inside the board's band (-20..-12 A); no late fire.
5. z1r (main rows): every phase's current at its low-side turn-on of a resume in the edge log is within 1.5 A of 0
   (development runs: 0.64-0.67 A damped, 4.8-5.8 A on V6). A220's z1 (the pauses' ticks) is reported, not judged.

## 3. Predictions (not criteria)
- k rows: inductor peaks within -1..+1 A of V6 (the core's current bypasses the inductor, its mean is zero); Vo the
  same within 1 mV; the core books 14-15 W per module on N0 at full load and 17-20 W on S75 125 C.
- z1r passes on every skipping row, also at rc2 (0.5-1.0 A). s3t passes on N75 (-17..-13 A) at both r_core; on N0
  10 % at 750 us the ladder is within 0.3 V and s3t passes; N0 no load misses by up to 3 A (few rounds per burst).
- s1, s2, s4 as in A220; the semiconductor loss at 10 % as in A220 (2.4-2.5 W) plus 0.5-1.5 W of core.

## 4. Decision rule
- j1 fails: stop and fix. k1 fails: V7 changes normal operation beyond the tolerance; skipping is not judged on it.
- k1 and, on the main rows, s1, s2, s3t, z1r (and s4) pass: skipping is adopted for nominal boards (skip, res_ofs_a,
  zcd_a) and the final configuration moves to plant V7 (V6 results stay V6 results, as the coverage file states);
  a miss at rc2 is stated as the damping it needs. A miss only on N0 no load: adopted with the minimum load stated
  where it passes.
- s3t misses by more than 1 A on N75 or N0 10 %: not adopted; the edge log names the next cause.
