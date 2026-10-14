# A220 - a pause that starts at zero current (RESULTS)
Boundary: 4952714 (branch a220-zcd, merged into main with db7efde). Records: release records-a220 (6 cosim records,
logs). Analysis: a220_analyze.py -> a220_summary.json. Runs from 4952714, cosim_sources_modified False. Final
configuration on plant V6, ton_lat 16, skip hi 5 / lo 1 mV, res_ofs_a and zcd_a = 8 ns x Vo / L (2.73 A on N0,
3.64 A on N75 / S75), one module; references: A217's records of the same rows.

## 0. Verdict
- **Not adopted. z1 fails on the three skipping rows, and the valleys are no better than A217's.**
- **The zero-current turn-offs land where they were meant to**: every phase's last low-side turn-off before a pause
  is at -1.05..-1.06 A (N0) and -1.41..-1.42 A (N75), against -11..-16 A in A217 (prediction -1..+1 A: N75 0.4 A
  beyond). Semiconductor loss falls by 12 %: 2.39 / 2.53 W at 10 % (A217 2.73 / 2.87 W).
- **The idle ring hardly shrinks**: 5.07 / 5.71 / 5.15 A at the pauses' ticks (N0 10 %, N75 10 %, no load; A217
  6.19 / 7.12 / 7.08 A; criterion <= 1.5 A). From 0 V and -1.4 A a node should ring with about 1.5 A.
- **Why, as far as traced: V6 has no resistance in an idle phase.** Its circuit R is 0 (since A206 the on-resistance
  sits in the switches, and a switch that is off has none), so nothing damps the ring of an inductor against the
  switches' output capacitance: in the no-load record the ring's rms over 6 us bins stays at 1.91-2.07 A through a
  pause of about 30 us (cosim/run_z_N0_25_0.json, 420-450 us; A217's 2.41-2.48 A). With D64's own copper model
  (skin depth at the ring's 20-25 MHz, plate gap 0.5 mm) an inductor's AC resistance is about 10 mOhm and the ring
  would decay with about 0.5 us, inside a 1.7 us pause. Where the remaining 5 A come from (the phases are coupled
  through the series capacitors and still switch while their neighbours idle) was not traced.
- **The first round after a resume is better, the alternation is not**: first valleys N0 -15.62 / -17.76 / -15.00 /
  -14.96 A, N75 -15.95 / -16.80 / -19.55 / -18.84 A (A217: N0 -15.62 / -11.49 / -9.95 / -14.36, N75 -15.96 / -19.95
  / -24.56 / -20.88). Then the two-period alternation grows anyway (N0 phase 4: -14.96, -8.74, -18.44, -6.40 A).
  True valleys over the last 60 us (turn-offs followed by that phase's turn-on within 100 ns): N0 10 % -21.2..-5.0 A,
  N75 10 % -23.4..-9.3 A, no load -29.6..-14.4 A (A217 -18.8..-5.7, -24.6..-8.5, -27.2..-15.1 A).
- **s3 and s3w as registered count the zero-current turn-offs (about -1 A) as valleys**, so they fail on any row
  that skips; I did not see this when registering. The true valleys above fail the band too.
- The slow board does not skip (A217), so its two rows are A217's bit for bit; the +62.5 A row passes s1-s4.

## 1. Criteria
| row | s1 | s2 | s3 | s4 | s3w | z1 | true valleys, last 60 us (A) | idle ring (A217) | loss (A217) |
|---|---|---|---|---|---|---|---|---|---|
| N0 10 % | pass | pass | **miss** | - | **miss** | **miss** | -21.2 .. -5.0 | 5.07 A (6.19) | 2.39 W (2.73) |
| N0 no load | pass | pass | not measured | - | **miss** | **miss** | -29.6 .. -14.4 | 5.15 A (7.08) | - |
| N75 10 % | pass | pass | **miss** | - | **miss** | **miss** | -23.4 .. -9.3 | 5.71 A (7.12) | 2.53 W (2.87) |
| S75 25 C 10 % | pass | pass | pass | - | pass | not measured | no skip | - | 13.67 W (13.67) |
| S75 125 C 10 % | pass | pass | pass | - | pass | not measured | no skip | - | 12.72 W (12.72) |
| N0 5 %, +62.5 A | pass | pass | pass | pass | pass | not measured | -18.3 .. -14.6 | - | 4.11 W (4.13) |
- j1: unit tests 103 of 103, regression quick and full bit for bit. Peaks <= 181.1 A, V_DS <= 31.2 V.
- "not measured": no pause tick (z1) or no turn-off (s3) in the window; the analysis function scores them false / true.

## 2. Predictions
- Held: the turn-offs near 0 A (N0; N75 at -1.4 A); s1, s2, s4 as in A217; loss lower (by 12 %, predicted 0-10 %).
- Missed: z1 (5.1-5.7 A against 0.3-1.2); the first valleys within 2 A on every phase (N75 phases 3-4 -19.6 / -18.8 A);
  no alternation; s3 on N75; the slow board (it does not skip).

## 3. What follows
- The decision rule's branch for a failing z1 assumed a misplaced turn-off; the turn-offs are in place, and the ring
  persists because the plant has no damping in an idle phase. Before any further change to the pause or the
  resume, the plant needs the inductor's resistance (D64: DC and skin-effect AC), which V6 also lacks in its loss
  books. The valleys found in A216-A220 are stated for an undamped idle ring.
