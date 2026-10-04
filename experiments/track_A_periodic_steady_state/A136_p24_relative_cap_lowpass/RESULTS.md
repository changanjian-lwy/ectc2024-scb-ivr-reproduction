# A136 - the relative phase-1 cap on Ton's low-pass (RESULTS)
Boundary: 8348904. Records: cosim/run_*.json (15 stage 1 + 68 stage 2; the BOUNDARY's "76" was a miscount of A135's
plan minus stage 1), identity rerun in tmp/identity_a136/; a136_summary_stage1.json, a136_summary.json.

## 0. Verdict
- **Adopted for the operating mode, with a start-up regression open.** In operation the cap on Ton's low-pass
  (rel_q8 320, rel_lp 1) matches A128's absolute cap at L0 and holds L x 0.7-1.3 without a lock: every A124 row
  <= 189.2 A at every L (worst: L x 0.7 +4.8 V / 5 us), L0 within 2.8 A of f100 on all seven step rows (rising rows
  180.9 / 176.6 vs 183.0 / 174.7 A), the idle design unchanged (L0 tails as A129's g125), Vo back in <= 45 us,
  phase 1's end Ton equal to phases 2-4's at every L (the cap is idle in steady state).
- Against the absolute cap (A134, f): L x 0.7 rising rows 189 vs 206 A; L x 0.85 182 vs 214 A; L x 1.1-1.3 s_p62 no
  lock vs lock. +8 V / 10 us: 194.0 / 195.0 A at L0 / L x 1.3 (f100 197.7 A), 215.8 A at L x 0.7 (reported).
- **Registered criterion 3c fails on m3n** (driver -3.4 ns): late fires 107 / 158 / 173 at L x 1.0 / 1.15 / 1.3
  (> 100; A129's g125_m3n 5, A135's r100 43). None falls inside the records (from 442 us at L0, 220 us at L x 1.3; a
  slot-offset scan finds 0 off-slot periods, and finds 95 in A134's cl130_l_p48_5us): they are in the handover. So
  is the start-up peak: 185-218 A (g125 184 A).
- Mechanism of the start-up regression (by the formula, not traced): Vin ramps 0 -> 48 V in 137 us, so at the 144 us
  handover lp20 trails Vin by ~10 V; the cap's rail model (Vc1 = 3/4 lp20) then reads rail 1 ~19 V while the ladder
  sits near 12 V, and the relative cap holds phase 1 near half its Ton (the absolute cap near 3/4) for tens of us.
- Tolerance: by the registered criteria L x 0.7-0.85 (m3n's start-up late fires fail L >= 1.0); post hoc, without the
  start-up, L x 0.7-1.3 on every row. Next (A137): restart the feed-forward's low-passes at mode P's entry.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | identity (A135 r100_l_p48_1us rerun), unit tests | pass; 76/76 |
| 2 | stage-1 gate | pass: L0 rising -2.1 / +1.9 A vs f100; no lock; rising rows <= 189 A at L x 0.7 / 1.0 / 1.3 |
| 3a | L0 unchanged | pass: tails within A135's limits; step rows -2.8 to +1.9 A vs f100 |
| 3b | no lock | pass, every row at L x 0.7-1.3 |
| 3c | A124 rows <= 200 A, matrix rule | **fail**: A124 rows pass (<= 189.2 A); matrix m3n at L x 1.0 / 1.15 / 1.3 on late fires (start-up, above); the rest 8/8 |
| 3d | recovery | pass: back <= 45.1 us, no overlap |
| 4 | reported | +8 V / 10 us above; start-up peaks 218 / 185 / 197 / 215 / 206 A at L x 0.7-1.3; m1n late 16 / 8 / 16 / 64 / 53 |
Predictions (D63): no lock, no binding in steady state - right; A124 rows 186-195 A - cosim 177-189 A (inside).

## 2. Limits
- The start-up claim rests on the counters and the scan of the recorded window, not on a trace of the handover.
- One module, equal L per phase; Cs, Coss and the four-module design untested here (C08).
