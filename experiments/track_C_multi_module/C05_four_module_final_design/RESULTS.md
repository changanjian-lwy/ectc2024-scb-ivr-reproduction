# C05 - Four modules of the final single-module design (RESULTS)
Boundary: 8125ffb. Records: cosim/run_*.json (18), c05_summary.json (c05_analyze.py). Conditions: 4 x (A124 2.5 MHz + A129 gated vff), 16 phases, 1 kW, A129's step timing (800 us), references = A129 single-module g125_<row>.

## 0. Verdict
- **"x4" does not hold for every row. Three rows fail hard that the single module passes:**
  - m1n (driver mismatch -1 ns): late fires 105/259/106/327 per module (single: 1), peak 250/231/250/226 A, no overlap, runs to the end.
  - m3n (-3.4 ns): late 100/102/275/339 (single 5), peak 203/209/188/188 A.
  - j100 (jitter 100 ps): module 4 overlap at ~198 us, run stopped, peaks 225-237 A, Vo 0.947 V, gaps 28.7-32.6 ns.
  - The positive mismatches m1p, m3p and j30 are clean (late 0, peak 163 A). A105's design (C03; period 232 ns, T/16 14.5 ns) passed all of these.
- **Passes as registered:** n0 (gaps 31.56-31.63 ns vs T/16 31.57, valleys / HS / LS within the single module's), all four load steps (peak 163-179 A, extreme and recovery as single), all five line steps <= 200 A after the step (l_p48_1us 184-186, l_p48_5us 177, l_m48_1us 175-178, l_m48_5us 175-178, l_m80_10us 172-174 A), ls_p5 / ls_p10 (slave 1 current and zero-voltage criteria ok, interleave gaps stay at T/16).
- Minor misses (no hard constraint): Vo extreme vs single beyond +-10% in l_p48_5us (12.04 vs 10.85 mV, +11%) and l_m80_10us (-32.7 vs +28.6 mV, sign flip, known D63 blind spot); one phase's LS turn-on V_DS in j30 above single + 0.3 V; line rows show 1 late fire where the single has 0.
- Cause: diagnosed post hoc in 0b (the slaves' unregulated phase-1 valley), not the slot spacing.

## 0b. Diagnosis (post hoc, reruns in tmp/ to 260 us with full records; m1n reproduces bit for bit)
- All three failures are in the post-handover transient (handover 144 us; m1n peaks 243-255 us, m3n before 243 us, j100 overlap 198.5 us); after ~260 us every row is the single module's steady state.
- **Mechanism: the slaves' phase-1 valley is not regulated** (slotted at master t_lo1 + m T/16, no current comparison; C01 Section 3). The master's phase-1 valley stays at -15.6 A; slave M3's runs to -96 A (m1n) / -130 A (j100), M1's to -93 A (m1n). The slave then sinks current, the master's loop raises Ton (to its cap 2272 LSB = 71 ns), the period grows 0.40 -> 0.71 us, which deepens the slaves' valleys further: positive feedback; late fires and the 203-250 A peaks follow from the capped Ton.
- **Two modules (T/8 slot spacing) do not run away:** m1n with 2 modules, the slave's valley dips to -25 A and returns to -15.6 A (late 6/4, peak 163/174 A).
- Slave slots are placed correctly (offset = m T/16 of the current period, no skipped periods); the defect is the open-loop valley, not the slot.
- Candidate fix (C06): A118's floor on the slaves' phase 1 (front end armed at i_target - lo_floor_a; fires before the slot if the current gets there first), cfg-gated, bit-identical when off; it bounds the slave valley near -17.6 A. The full version is D61 scheme B (per-slave valley loop).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | no overlap, peak <= 200 A | MISS: j100 (overlap); m1n, m3n, j100 peaks; all other 15 rows ok |
| 2 | locked, 16 gaps T/16 +- 0.1 ns | ok in 17 rows; j100 MISS |
| 3 | per module like single (n0, m, j) | ok in n0, m1p, m3p; m3n sd band MISS, j30 LS MISS, j100 MISS; m1n valleys / HS ok |
| 4 | steps like single | 2 of 9 step rows miss the Vo +-10% band (see above); recovery and ladder ok |
| 5 | ls_p5 / ls_p10 | ok: current, zero voltage, valleys |
| 6 | late fires | MISS: m1n, m3n, j100, plus 1 late fire in four line rows |

## 2. Limits
- Failures are for one seed (1) and the matrix's same-on-every-module mismatch; no module spread (C04 covers the old design).
- Fixed in C06 (slave floor); the multi-module summary Section 8 restates the level for the final design.
- Erratum (2026-10-04): BOUNDARY Sections 0 and 3 treat the 31.6 ns T/16 as a narrower spacing to test; A105's (C03) was 14.5 ns (period 232 ns), so the spacing is wider in the final design. The diagnosis does not rest on it.
