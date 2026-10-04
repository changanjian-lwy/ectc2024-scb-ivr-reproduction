# A135 - a relative phase-1 cap that cannot lock the ladder (RESULTS)
Boundary: eb006cb. Records: cosim/run_*.json (91), identity reruns in tmp/identity_a135/; a135_summary.json.

## 0. Verdict
- **Not adopted.** The relative cap (rel 333, on the loop's ton) never locks: every row at L x 0.7-1.3 ends with the
  ladder within 0.5 points of L0 and Vo within 1 %, phase 1's end Ton equals phases 2-4's (the cap is idle), and the
  matrix passes 8/8 at every L. But on the rising rows it is weaker than A128's absolute cap: at L0 +4.8 V / 1 us
  203.1 A vs 183.0 A (f100, same timing), +4.8 V / 5 us 195.2 vs 174.7 A, +8 V / 10 us 225.7 vs 197.7 A; rising rows
  201-212 A at L x 0.7 / 1.0 / 1.15 / 1.3 (192.8 A at 0.85).
- Mechanism (trace r100 vs f100, l_p48_1us): for ~5 us both hold phase 1 (Ton 31-34 ns, 162-186 A). Then the
  slotted phases' valleys deepen, Vo dips 6-10 mV and the loop raises ton 37.8 -> 41.6 ns. The absolute cap keeps
  phase 1 at 34-36 ns; the relative one scales with ton, and its margin 1.3 x rss / rail ~ 0.95 lets phase 1 back to
  37.8 ns while rail 1 is still 16 V; with phase 1's valley at +28 A (its timed turn-off is early) the peak is 203 A.
  D63 does not model the loop's rise and predicted 187 A (inside A125's band, 219 A, but wrong in rank vs f100).
- **Steps at 1000 us remove A134's L x 1.3 transients:** with phase 1 timed (812 us), r130's rows recover in 13-34 us
  with 0 late fires (A134, comparator phase: 272-285 A, up to 129 late fires).
- Where the cap is idle the design is unchanged: L0 tails of n0, s_p62, s_m62 and the matrix within 0.09 A and
  0.012 V of A129's g125; load / falling rows within 0.7 A of f100.
- Next (A136): the same cap on ton's low-pass, so the loop's transient rise does not move it.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | identity (rel off), unit tests | pass: g125_n0, g125_l_p48_1us bit-identical; 75/75 |
| 2 | L0 unchanged where the cap is idle | **fail** on the rising rows only (+20.5 / +20.1 A vs f100); tails pass (<= 0.09 A, <= 0.012 V); falling and load rows -0.1 to +0.7 A |
| 3 | no lock at any L | pass (L x 0.7-1.3, every row) |
| 4 | A124 rows <= 200 A, matrix rule | **fail**: rising rows 201.1 / 203.1 / 209.3 / 211.9 A at L x 0.7 / 1.0 / 1.15 / 1.3; matrix 8/8 at every L |
| 5 | recovery, late <= 100, no overlap | pass: back <= 34 us, late <= 47 |
| 6 | reported | +8 V / 10 us 227.9 / 225.7 / 222.5 A at L x 0.7 / 1.0 / 1.3 (f100 197.7 A); start-up peaks 200-217 A (g125 184 A) |
Predictions: no lock - right; peaks 187-195 A - low by 8-17 A on the rising rows (D63 misses the loop's rise).

## 2. Limits
- Start-up peaks rise with the relative cap (195-217 A vs 184 A): it acts from mode P on while lp20 still trails
  the start-up ramp; reported, not judged.
- One module, equal L per phase; Cs, Coss and the four-module design untested.
