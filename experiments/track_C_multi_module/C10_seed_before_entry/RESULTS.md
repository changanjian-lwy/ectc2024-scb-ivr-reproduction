# C10 - seed every module's low-pass with the Ton before mode P (RESULTS)
Boundary: 8e20d1e (trace cfgs c9b6b13). Records: cosim/run_*.json (18 four-module rows, 18 single-module rows,
c06al10_s_m62, c10al6_s_m62); c10_summary.json.

## 0. Verdict
- **Adopted by the user's decision (2026-10-05), against one registered item:** the four-module final design is
  C06 + vff {rel_q8 320, rel_lp 1, seed 2}, and the single module's adopted setting takes seed 2 (identical records).
  The lock is gone; every criterion passes except no-new-failure (one late fire on s_m62), which the trace shows is
  not only the step offset, so the decision rule alone did not adopt it.
- Seed 2 (tlp restarts from the Ton the clock before en rises = cfg_ton 1136) puts every slave on the master's footing:
  slave rail 1 12.27-12.36 V on all 18 rows, never above 13.3 V (C09 13.8-15.4 V for 19-30 us; C06 12.8-13.2 V);
  master <= 12.56 V. Rows without a step peak 163.3-180.1 A (C09 192.5-203.5; C06 163.3-184.3).
- Single module: 18/18 records equal A137's bit for bit (L x 0.7 / 1.0 / 1.3): the master's loop has not moved Ton
  by the first Vin sample, so seed 1 already took 1136 there.
- Compared with C06: post-step peaks -2.2..+4.2 A (l_m48_1us 187.5 vs 183.3 A; whole-run max 188.7 A, so the
  four-module "<= 185 A" becomes <= 189 A). Late fires 125 in total (C06 96, C09 666); the extra ones are handover
  fires on m1n 25 (19) and m3n 90 (68); m1n / m3n handover peaks 172-180 A (C06 163-184), master Ton up to 1461
  (C06 1330, C09 1649): the relative cap starts at 1.25 x 1136 and is looser than C06's absolute cap. After 242 us
  the peaks are C06's (144.0-144.6 A).
- s_m62: one late fire (slave 3, phase 4, after the -250 A step; C06 0). Trace: C06 at C10's offset (499 ns) 0,
  C10 at C06's offset (403 ns) 0; post-step peak 144.0 A in all four runs; slave 3's phase 3 -> 4 turn-on spacing
  within 0.34 ns of C06's at the same offset over the first 20 periods (3.3 ns over the 400 us after the step);
  every other s_m62 criterion passes. So it needs both C10's design and this offset; its effect on
  the recorded edges is below what the records resolve. C10 also loses three of C06's own misses (late fires on
  l_m48_1us and l_m80_10us, step_10pct on l_p48_5us / l_m80_10us, back_2us on l_m48_1us).
- l_p48_5us (C09's open item): the one-period spike recurs, smaller, elsewhere: slave 3 phase 1, +30.85 us, 179.3 A
  (C09 slave 1, +32.17 us, 184.6 A; C06 at C09's offset: master, +35.30 us, 176.1 A). In all three it follows two
  low-side turn-offs ~6 ns apart; a property of the design, not of the seed. Not traced further.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| S | single-module records = A137's | pass, 18/18 |
| G1 | slave rail 1 <= 13.5 V, <= 5 us above 13.3 V (n0, m1n, m3n) | pass (12.29-12.36 V, 0 us) |
| G2 | whole-run peak <= max(185, C06 + 3) A | pass (163.4, 180.0, 180.1 A) |
| G3 | late fires <= 1.5 x C06 + 6 | pass (0, 25, 90) |
| 1 | hard limits / no new failure | hard pass; **no new failure: fail** on s_m62 (late fires 1 vs the A129 reference's 0); m3n sd_band = the ADC limit cycle (Ton 1203-1214, Vo -0.260 / +0.260 mV) |
| 2 | late fires <= 1.5 x C06 + 6 | pass, 18/18 |
| 3 | post-step peak within 7 A of C06 | pass (-2.2..+4.2 A), no contingency needed |
| 4 | G1 on 18 rows, G2 on 9 rows without a step | pass |
Predictions: identity 18/18 - right; slaves like the master, rail 1 <= 13.2 V - right (12.36 V); whole-run peaks
163-185 A - right (163.3-180.1 A); late fires at or below C06 - wrong on m1n / m3n (25 / 90 vs 19 / 68);
post-step peaks within the 2-7 A floor - right; l_p48_5us 175-180 A - right (179.3 A).

## 2. Limits
- The late fire is a counter (scb_phase counts any edge of the phase computed after its time); the records do not
  time it, so which edge it was and by how much is not known.
- Four-module L corners were not run with seed 2 (C08 ran L x 1.2 with A136's cap without the restart).
- The deviations from the hand-off's gate thresholds (13.0 V, 185 A) were set in the BOUNDARY from C06's own values.
