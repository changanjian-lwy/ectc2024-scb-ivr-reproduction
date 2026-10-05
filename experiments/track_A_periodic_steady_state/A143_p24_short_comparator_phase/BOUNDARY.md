# A143 - shortened mode-P comparator phase (BOUNDARY)
Method: RTL (cosim of the adopted RTL with one cfg value changed, lo_learn; no RTL edit), after a math check (D63).
Track A. Written and committed before the runs. Looked at beforehand: A142's records R_dv4.8_s4_L100, R_dv4.8_s3_L100,
Q_dv6.4_s4, z104, P1, P2 (per-cycle tables) and a D63 probe (not stored; numbers below).
Decision it changes: whether the single-module controller is frozen with a short comparator phase (and which
lo_learn K), so that C13 can start. Cheaper check done first: D63 cmp vs floor mode with the RTL-exact vff (A140's Vff).
records_last 16000 (amended before any result: 6000 left the handover out of 1200-1400 us records).
Budget: stage 1 64 runs (~25 min, 10 jobs), stage 2 42 single + 4 four-module runs (~35 min).

## 1. What and why
- A142: a rising line step in the comparator phase (144 us handover -> timed switch after lo_learn 1024 phase-1
  turn-offs, 520-810 us) oscillates for 30-50 us (+4.8 V / 4 us nominal 254 A, +6.4 V / 4 us 388 A, z104 351 A); the
  same step in timed mode is 196 A (P2).
- Mechanism read from the records (refines A142 Section 0): phase 1's comparator holds its valley, so its period grows
  with its rail (506 -> 600-650 ns; rail 1 12.3 -> 17 V). Phases 2-4 follow that period (slots T/4 after t_lo1), their
  valleys deepen (-37 ... -100 A). Each deep valley pulls their error-based dt_pred down in one or two reports (half the
  error per report), while an early turn-on raises it by only 0.28 ns per report: dt_pred falls 11 -> 2-4 ns (Q: 0.1 ns)
  and stays there for 30 us. The high side then turns on with the valley's current still flowing (-55 ... -88 A, or hard
  on at +12 ... +29 A with V_DS 10-16 V): the valley carries into the next cycle, phases 2-4 act as an undamped
  integrator with the series capacitors, and the ~4.6 us swing grows (valleys -100 <-> +50 A, Vo 0.967-1.038).
  P2 (timed): the period stays <= 653 ns, phase 2-4 low-offs -57 ... -12 A, no swing.
- D63 (fixed transition time, i.e. no dt_pred collapse) reproduces the first 4 us (period 504 -> 603 ns, rail 1 16.7 V,
  valleys -41 ... -58 A) but no swing: cmp +4.8 / +6.4 / +7.9 V at 4 us 201 / 223 / 244 A vs floor (timed) 179 / 184 /
  ~190 A. Handoff candidate (a), phase 1's on-low time capped at a low-passed reference x (1 + r), helps in D63 only at
  r = 1/16 with shift 5 (+7.9 V 197 A); r >= 3/16 changes nothing. At r -> 0 it is the timed mode, so (a) = (b) with an
  RTL change; (c) (Ton rate limit) does not touch the trigger (phase 1's Ton falls first, 37.8 -> 32.7 ns). Not run.
  A dt_pred fall limit (the amplifier) is a later candidate: D63 puts its comparator-phase peaks at 201-244 A, above
  timed mode, so it cannot replace (b) here.
- Candidate (b): lo_learn K = 4 / 16 / 64 (window ~2 / 8 / 32 us at L x 1.0). A99 chose 1024 for a sign rule moving dlo
  31 ps per cycle; since A100 dlo steps adaptively up to 64 LSB (2 ns) per cycle, and the floor covers the deep side.
- Not tested: dt_pred fall limit, cap (a), multi-module beyond g5's 4 rows (C13 does that).

## 2. Criteria
1. g1 at K: peak <= 200 A on the R rows (A139-certified), <= 210 A on z104 and Q_dv6.4_s4; phase 2-4 low-offs >= 0 A
   within 60 us after the step: 0; Vo outside 2 %: <= 5 us.
2. g3 at K vs the same row at K 1024: whole-run peak <= +7 A (noise floor), peak in [144, 244] us <= +7 A, late fires
   <= +5, max |Vo - 1| in [144, 244] us <= +0.2 points, rail 1 max in that window <= +0.3 V.
3. g1, g3, g4, g5: status COMPLETED, 0 overlaps, 0 floor-first duplicates, 0 NEW hits (A142 oracles and classes),
   |Vo_end - 1| <= 1 %, ladder deviation <= 0.03. (g2 measures the residual window: no pass criterion.)
4. Identity: g3_s100_n0_k1024 = A141 I1_s100_n0 and g4_s100_l_p48_1us_k1024 = A141 F_s100_l_p48_1us: sections,
   ipk, late fires and the last 6000 entries of every event list equal (A143 keeps records_last 16000, the whole run).
5. g4 at K vs K 1024: post-step peak <= +7 A and <= 200 A (a row whose K 1024 run is already above 200 A: <= +7 A only),
   late fires <= +5.
6. g5 at K vs C12's record of the row: peak <= +7 A, late fires <= +5, rail 1 (vin - vcs[0]) of every module in mode
   P before 242 us <= 13.5 V and <= 5 us above 13.3 V (the C-line lock gate), 0 floor-first duplicates.
Choice of K: the smallest of 4, 16, 64 that passes 1-3 in stage 1; stage 2 runs at that K. If stage 2 fails, the next
larger K that passed stage 1 runs stage 2 once.

## 3. Predictions (not criteria)
- g1: every K alike within noise (the steps are in timed mode): R rows 185-200 A, z104 190-200 A (P2 196 A at 1000 us),
  Q_dv6.4_s4 190-205 A; no positive phase 2-4 low-off.
- t_lo_timed: K 4 / 16 / 64 -> ~146 / ~152 / ~176 us at L x 1.0 (~147 / ~154 / ~183 us at L x 1.3).
- g3: K changes the handover by < 7 A; K 4 is the likeliest to differ (dlo from the handover's first periods).
- g2: K 1024 and K 64 oscillate on +4.8 V at 146 / 160 us (>= 230 A); K 4 / 16 end the window during the step
  (+4.8 V <= 210 A, +6.4 V <= 230 A).
- g4, g5: within the noise floor of K 1024 / C12 (steps at 800-1000 us are in timed mode at every K).

## 4. Decision rule
Pass (1-6 at the chosen K): the adopted design takes lo_learn K on one and four modules; the single-module controller
is frozen; the residual is g2's window; C13 starts with K. Fail: report which criterion and keep lo_learn 1024; next is
the dt_pred fall limit or cap (a) as an RTL option.
