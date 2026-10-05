# C12 - floor_late on the four-module matrix (RESULTS)
Boundary: 663617a. Records: cosim/run_*.json (22), c12_summary.json; analysis c12_analyze.py.
## 0. Verdict
- **Pass, 5/5 criteria on 22/22 rows** (C10's 18 rows at L0 + C11's L x 1.2 x3 / L x 1.3 x1, each + cfg floor_late 1).
- Floor-first duplicate turn-ons: 0 in all 22 runs (C10/C11 records: 44 in the same window, e.g. 25 on l_p48_1us, 7 on l120_l_p48_1us).
- Peaks: whole-run <= 188.0 A (l120_l_p48_1us, = its C11 value); at L0 <= 184.0 A (l_m48_1us, C10 188.7 A); every row within -4.7 / +2.0 A of its reference (l_m80_10us 173.9 vs 171.9 A).
- Handover: slave rail 1 <= 12.56 V at L0, <= 12.87 V at L x 1.3, 0 us above 13.3 V; no lock at L x 1.2 / 1.3.
- Late fires: m3n 108 (C10 90, limit 183), others <= 5; overlaps 0.
- **Four-module final design = C10 + floor_late 1** (adopted, same setting as the single module).
## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | 0 floor-first duplicates, every module | pass, 22/22 |
| 2 | peak <= ref + 2 A or <= 189 A (whole run, post-step) | pass, 22/22 |
| 3 | slave rail 1 <= 13.5 V, <= 5 us above 13.3 V | pass, 22/22 |
| 4 | late fires <= 2 x ref + 3, overlaps 0 | pass, 22/22 |
| 5 | L rows: no lock; all peaks <= 200 A | pass, 4/4 |
## 2. Limits
- m3n's late fires rose 90 -> 108 (inside the registered limit); its ADC limit cycle is history-dependent (C09), not traced.
- L x 0.7-0.9 on four modules, Cs / Coss corners and other step offsets were not run.
- The L0 steady rows differ from C10 only from ~145.5 us on, as predicted; other rows are bit-identical in peak.
