# C06 - Slave slot floor for the four-module final design (RESULTS)
Boundary: ac7f444 (code 7b6dad7). Records: cosim/run_*.json (18), c06_summary.json (c06_analyze.py). Conditions: 4 x (A124 2.5 MHz + A129 gated vff) + slave_floor 1 (lo_floor_a 2 A), 16 phases, 1 kW, step at 800 us; references A129 single-module g125_<row>.

## 0. Verdict
- **The floor removes C05's three failures; every hard constraint holds in all 18 rows:** no overlap, peak <= 185 A (C05: 250 A), locked, 16 gaps T/16 +- 0.05 ns. m1n peak 166-184 A, late 2/6/6/5 (C05 105-327); m3n 164-166 A, late 26/8/15/19 (C05 100-339); j100 completes, 163-164 A (C05 overlap at 198 us).
- **The steady state is the single module's:** m1n / m3n valleys within 0.014 / 0.041 A of the single module; all late fires of m1n and m3n occur before 260 us (260 us reruns give the same counts), i.e. in the post-handover transient.
- **The floor fires only in transients:** 1-2 times per slave in n0 and the load rows (start-up), 23-80 in m1n / m3n, 55 in j100's slave 3, 1-93 in line steps; 0 in m1p, m3p, j30, ls_p5, ls_p10, which are bit-identical to C05 (criterion 7).
- **The registered adoption rule is not met:** criterion 6 (late fires <= single) misses in m1n (19 vs 1), m3n (68 vs 5) and four line rows (1-2 vs 0).
- **One soft regression from the floor:** l_m48_1us Vo extreme +17.9 mV (single +15.7, +14%), back within 1% at 11.1 us (single 5.9 us), peak 185 A (C05 177 A); the floor fired 1/2/4 times there.

## 0b. Post hoc: per-cycle interleave through steps (`matrix.gaps_per_cycle`, 10 us windows)
- Steady state: n0 / m1n max 0.05 ns, j30 0.57 ns, j100 2.2 ns per cycle.
- Steps disturb the per-cycle spacing in the final design already without the floor (C05: up to 35 ns ~ one slot, s_m62 27 ns, l_p48_1us 35 ns), unlike A105's design (C03 <= 2 ns): Ton moves per phase (vff) and the period changes fast.
- The floor enlarges it in line steps: l_p48_1us 65 ns (C05 35), l_m80_10us 56 ns (C05 30), l_m48_1us 27 ns (C05 21); back below 0.5 ns by 950 us (C05 900 us); after 1100 us identical spacing (<= 0.12 ns), valleys -15.65 A, no floor fires.
- **Decision (2026-10-04, by the user, against the registered rule's criterion 6):** slave_floor adopted for the four-module final design with three stated residuals: transient late fires (m1n 19, m3n 68), l_m48_1us +14% Vo / 11.1 us recovery, and the larger transient interleave disturbance in line steps.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | no overlap, peak <= 200 A | met, 18/18 (max 185 A) |
| 2 | locked, gaps T/16 +- 0.1 ns | met, 18/18 |
| 3 | per module like single (n0, m, j) | met except LS turn-on V_DS in j30 (as C05) and j100 (per-phase; module maxima 3.4-5.3 V vs single 5.3 V) |
| 4 | steps like single | l_m48_1us +14% / +5.2 us (new); l_p48_5us and l_m80_10us sign flips with equal magnitude (-10.2 vs +10.9, -27.5 vs +28.6 mV) |
| 5 | ls_p5 / ls_p10 | met (identical to C05) |
| 6 | late fires <= single | MISS in m1n, m3n (transient only) and l_p48_1us, l_p48_5us, l_m48_1us, l_m80_10us (1-2) |
| 7 | no fires -> identical to C05 | met, 5/5 |

## 2. Limits
- One seed; same mismatch on every module; no module spread; phases 2..N stay unfloored.
- The adoption is a decision against the registered rule (criterion 6 missed); see 0b.
