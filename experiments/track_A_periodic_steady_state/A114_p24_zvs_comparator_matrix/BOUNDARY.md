# A114 - the 20% and 25% designs with the comparator phase-1 turn-off, on the standard matrix (BOUNDARY)

Track A. **Written before any A114 run.**

**One factor against A112** (the same designs with the timed turn-off):
the comparator-decided phase-1 turn-off (`lo_pred` = 0, A105's I1).

**Source:** A113. At 25% the comparator fixed the load step (183 →
8.9 µs) and the fast falling line step (182 → 2.8 µs) at no steady-state
cost. 32 runs (`make_cfgs.py`).

## 1. Registered predictions and criteria (A112's statistics)

1. **No overlap** in any run.
2. **Steady state (n0, m rows):** each phase's high side within ±0.3 V
   of A112's row; low side ≤ 0 in the m rows; efficiency (n0) within
   ±0.2 points of A112's (90.17 / 90.14%).
3. **Jitter rows:** the comparator's timing noise adds to the spread.
   Turn-off sd ≤ A112's × 1.3 at 30 ps and × 1.8 at 100 ps. A105:
   I1 / I2 = 1.07-1.13 at 30 ps, ~1.6 at 100 ps.
4. **Load steps:** all back within 1% in ≤ 15 µs.
5. **Line steps:**
   - ±4.8 V steps back in ≤ 20 µs;
   - **−8 V / 10 µs (to 40 V)** registered as still slow: back in ≥ 50 µs,
     as A113 (175 µs). It is a separate mechanism, reported, not graded
     beyond this;
   - peaks after 150 µs within A112's + 5 A.

## 2. What stays assumed

As A112.
