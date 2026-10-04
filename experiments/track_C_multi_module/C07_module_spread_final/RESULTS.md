# C07 - module spread on the final design (RESULTS)
Boundary: aa23ecd. Records: cosim/run_*.json (6), c07_summary.json. Window: last 200 master periods (before the step for all_s_p62).
## 0. Verdict
- Hard constraints with the floor on (cs20_n0, r30_n0, all_n0, all_s_p62): no overlap, peak 159-193 A (<= 200), locked, 16 gaps within T/16 +-0.1 ns (31.51-31.61 ns). The spread rows pass what the summary needs.
- **R +-30% moves slave valleys by -1.6 / +1.7 A (module 1 deeper)**, as predicted (+-2 A, band 1.5-3); currents -1.24% / +1.32% (predicted -1.2 / +1.3). Same size as C04, so the mechanism (slave = ~3.3 mOhm source) carries over.
- **Floor not active in steady state:** r30_n0 on vs off: valleys 0.030 A, gaps 0.016 ns (pass); all_n0: valleys 0.0526 A, gaps 0.011 ns (0.0026 A over the 0.05 A limit, miss at the edge). Deepest steady valley with floor on: -17.95 A.
- **My registered prediction was wrong:** I put the floor at -17.6 A and expected it to fire in steady state; a -17.95 A valley did not disturb the steady state, so the floor's threshold for phase 1 is deeper than that (not at target - 2 A of the 15.6 A figure; not re-derived here).
- **The floor is needed under spread:** floor off (r30_n0_nf, all_n0_nf) peaks 265 A / 263 A and late fires 29-345 per module; floor on 159-193 A and 0-10. Floor fires over the whole run (not timed): r30_n0 module 1 114, all_n0 module 3 124 vs 1-2 nominal (C06 n0), so it acts in the start-up/handover, not in the window.
- Statement allowed in summary Section 8: holds under C04's spread (Cs +-20%, R +-30%, L +-5%, one module each way) with the slave floor; the floor must stay on. Not allowed: "without the floor".
## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | no overlap / peak <= 200 A / locked / gaps | all four floor-on rows ok |
| 2 | r30_n0 currents -1.2 / +1.3% +-0.5 | ok (-1.24 / +1.32) |
| 2 | all_n0 module 1 -5%, module 3 +5% (+-1.5), valleys +-3 A of n0 | ok (valley change 0.31 A) |
| 2 | all_s_p62 step extreme within 10% of C06 | ok (-12.24 vs -12.20 mV) |
| 2 | cs20_n0 currents +-0.5%, valleys 0.35 A | miss: 251.3 A (+0.52%), valleys 0.48 A (C04 was 0.35 A; Cs 6 uF slightly more) |
| 3 | floor on vs off: valleys 0.05 A, gaps 0.05 ns | r30 ok; all_n0 0.0526 A miss at the edge |
| - | join <= 0.1 mV (C04 rule) | miss 106-118 uV (C06 n0 83 uV); floor off 312-319 uV |
## 2. Limits
- all_s_p62's window current split is not meaningful (step row; C06's reference has the same artefact); step judged by Vo only.
- Floor fires are whole-run counts; steady-state inactivity rests on the on/off agreement, not on a timestamp.
- Coss and per-module driver spread not covered (as C04).
