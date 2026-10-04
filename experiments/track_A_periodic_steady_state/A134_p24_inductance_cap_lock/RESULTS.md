# A134 - L tolerance and the L+ ladder lock: the feed-forward's phase-1 cap (RESULTS)
Boundary: c699cee. Records: cosim/run_*.json (96); a134_summary.json; diagnosis traces a134_trace_fl12_s_p62.json,
a134_trace_g125_s_p62.json (`a134_analyze.py trace`); D63: a134_predictions.json.

## 0. Verdict
- **A132/A133's "ladder limit cycle" is a lock made by scb_vff's phase-1 Ton cap** (A128: k / rail, k = L0 x 180 A,
  rail estimated as Vin/4 - Vo). Trace of fl12_s_p62 (L x 1.2, +62.5 A at 800 us): phase 1 stops at 48.0 ns =
  844 800 / 550 codes while the loop drives phases 2-4 to its 71 ns clamp; rail 1 12.4 -> 16.5 V, rails 2-4 10.5 V,
  period 605 -> 861 ns, slotted valleys -30 to -48 A, Vo 0.91 V, phase 1 208 A. High-side diode conduction (0-1.6 ns
  per period) and late fires (16, phase 4) do not start it. At L0 the same row settles at 46.2 ns, 1.8 ns under the cap.
- D63 with the RTL-exact cap reproduces it (A133's D63 had no cap): lock on s_p62 from L x 1.05, on every row at
  L x 1.3; none with k = 0 (z) or k x L/L0 (c). **Cosim: z and c are balanced on n0 and s_p62 at L x 1.1 / 1.2 / 1.3**
  (Vo 1.000 V, rails within 0.2 V of L0), where f locks (A133 fl12_s_p62, fl13_n0).
- **L tolerance of the adopted design (f, steps at 800 us):** functional at L x 0.7-1.0 (no lock, no runaway, Vo
  back, matrix 8/8 at every L x 0.7-1.1 with the start-up peak split off). L x 1.05, s_p62: Vo regulated but phase 1
  pinned at the cap (48.0 vs 50.2 ns), rail 1 13.2 V, slotted valleys -22.7 A, turn-on V_DS ~0 V (ladder deviation
  2.5 %); L x 1.1, s_p62: locked (rails 16.3 / 10.7 V, Vo not back in 1 %, 225 A). Within 200 A only at L0: the rising
  rows reach 205.6 / 214.3 / 205.9 A at L x 0.7 / 0.85 / 0.9 (the cap, fixed at L0, is loose there: 180 A x L0/L).
  So the adopted cap gives the design no usable L tolerance on the 200 A spec (about -5 % / +4 %).
- Prices of the two mechanism arms on the rising rows: z (no cap) 211-219 A at L x 1.1 / 1.2 (back in <= 6 us);
  c (calibrated) 174-189 A at L x 1.1 / 1.2, but slower (L x 1.2, +4.8 V / 5 us: back in 42.9 us).
- **Timing flaw (A133 and here):** phase 1 learns for lo_learn = 1024 comparator periods after the handover, so it goes
  timed at 662 us at L0, 712 / 762 us at L x 1.1 / 1.2 and 812-818 us at L x 1.3. The 800 us step hits L x 1.3 in the
  comparator phase (valley held at -15.6 A, period 653 -> 878 ns, slotted valleys -135 A): z 272 A, c 285 A (129 late
  fires) on the rising rows there, and A133's fl13 rows, are of that phase, not of the operating mode. A135 steps at 1000 us.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | z / c never lock at L x 1.1-1.3 (n0, s_p62) | **fail as registered**, on the threshold: s_p62 at 1.04 / 1.12 / 1.22 % ladder deviation (> 1 %) with Vo 1.000 V and rails within 0.2 V of L0, whose own s_p62 is 0.93 %; n0 0.67-0.80 %. Post hoc (+0.5 points over L0's row): pass. References locked: fl12_s_p62 9.8 % (Vo 0.917 V), fl13_n0 4.6 % |
| 2 | f's s_p62 locks at L x 1.1 | pass: 9.25 %, rails 16.3 / 10.7 / 10.7 / 10.4 V, Vo not back within 1 % |
| 3 | tolerance of f | functional L x 0.7-1.0; spec (<= 200 A) only L0 (see Verdict); start-up peaks 216 A at L x 0.7 / 0.85, 208 A at 0.9, 227 A at 1.1 (reported only) |
| 4 | z / c rising-row peaks | z 212 / 219 A (L x 1.1), 211 / 219 A (1.2); c 174 / 189 A, 176 / 187 A; L x 1.3 (learning phase): z 272 / 272 A, c 285 / 200 A |
Predictions (D63): f locks s_p62 from L x 1.05 (cosim: cap-bound at 1.05, locked at 1.1); f worst peak at L x 0.85 / 0.9
211 / 202 A (cosim 214 / 206); z 209-215 A (cosim 211-219); c 182-195 A (cosim 174-189 at L x 1.1 / 1.2): all inside
the bands except L x 1.3, which D63 runs in the timed mode.

## 2. Limits
- The 1 % lock threshold (A106's ladder rule) was set without checking L0: s_p62 sits at 0.94 % there and at
  1.04-1.22 % at L x 1.1-1.3 without any lock (the lock is ~10 %, Vo -90 mV); the post-hoc rule (+0.5 points over the
  same row at L0) is marked as such.
- L x 1.3's step rows (z, c) are in phase 1's learning phase (above); L x 1.2's step comes 38 us after it goes timed.
- One module, equal L in every phase; Cs, Coss and the four-module design untested.
