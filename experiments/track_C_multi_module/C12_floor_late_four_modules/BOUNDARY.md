# C12 - floor_late on the four-module matrix (BOUNDARY)
Track C. Written and committed before any C12 run. Looked at beforehand: A141 RESULTS (single module, 4-module v1/v2 on two rows), C10 / C11 summaries.
Decision it changes: whether the four-module final design becomes C10 + floor_late 1 (floor_late changes every row's handover: C10 has one floor-first duplicate per slave at 145.1 us).
Cheaper check done first: none (RTL-level effect; A141 already passed on one module and on l_p48_1us / l_p48_5us at four modules).
Budget: 22 four-module runs, ~70 min at --jobs 10.

## 1. What and why
- Rows: C10's 18 four-module rows + C11's L x 1.2 (s_p62, m3n, l_p48_1us) and L x 1.3 (s_p62), each with cfg floor_late 1 and nothing else changed (cosim/cfg_*.json).
- Reference per row: C10's (C11's for the L rows) record of the same name.
- Not tested: Cs / Coss corners, steps at other offsets, seeds.

## 2. Criteria (every row, every module)
1. Floor-first duplicate turn-ons (A141 make_cfgs.floor_first, modules_rest included): 0 in the recorded window.
2. Whole-run peak and post-step peak <= the reference row + 2 A, or <= 189 A.
3. Handover lock gate: every slave's rail 1 (mode P, before 242 us) <= 13.5 V and above 13.3 V for <= 5 us.
4. Late fires <= 2 x the reference row + 3; overlaps 0.
5. L rows: no lock (A134.lock vs the C10 row at L0 as in C11); all rows peak <= 200 A.

## 3. Predictions (not criteria)
- Criterion 1 passes everywhere; rows differ from C10 from ~145.5 us on (the slaves' handover duplicate is gone).
- Peaks within +-2 A of the reference; late fires equal or lower.

## 4. Decision rule
- All pass: four-module final design = C10 + floor_late 1; CURRENT_STATUS item 51, scorecard, scb-map updated.
- A row fails: trace on that row's record (Opus); the four-module design stays C10, single module keeps floor_late.
