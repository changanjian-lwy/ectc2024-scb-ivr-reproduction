# A119 - the 1 MHz candidate on the standard matrix (BOUNDARY)

Track A, main line. **Written before any A119 run.**

**The candidate:** A118's f6.
- 1 MHz, Eq. (4)'s 7.333 nH, 10% negative current;
- timed phase-1 turn-off with a 2 A comparator floor;
- Cs 6 µF; D59 loop at 60 kHz.

A118 ran its n0, ±62.5 A and the ±4.8 V steps over 1, 5 and 20 µs.

**This experiment:** the rest of `scb_ivr.cosim.matrix.ROWS`, times ×5
(steps at 2000 µs):
- driver mismatch m1n, m1p, m3n, m3p (±1, ±3.4 ns);
- jitter j30, j100 (30, 100 ps);
- load steps s_m25, s_p25 (±25 A);
- line steps l_m48_10us, l_p48_10us (±4.8 V over 10 µs), l_m80_10us
  (−8 V, to 40 V, over 10 µs).

11 rows.

## 1. Registered predictions

**Driver rows (the floor does not act in steady state):**
- the high side within ±0.1 V of A118 f6_n0, as A112 found at 5 MHz;
- turn-off sd ≤ 0.16 A at j30 (A116 n10_j30: 0.13-0.16 A);
- ≤ 0.6 A at j100 (5 MHz ×1/5 slope: ~1.1 A × 0.5);
- ≤ 0.1 A for m rows;
- start-up peak ≤ 200 A in every row (m3n is the historical start-up
  risk, A92);
- no overlap.

**Step rows (D63, `a119_predictions.json`):**

| row | D63 peak | Vo, back | phase 1 |
|---|---|---|---|
| s_m25 | 140 A | +10.0 mV, 4.8 µs | at the floor |
| s_p25 | 154 A | −6.5 mV, 0 | - |
| l_m48_10us | 154 A | +44.5 mV, 58.7 µs | 3.6 A crossing × 13 |
| l_p48_10us | 178 A (rising: D63 weak) | +10.8 mV, 10.9 µs | - |
| l_m80_10us | 168 A | +75.0 mV, 82.6 µs | **4.7 A × 360: persistent** |

**The risk row is l_m80_10us.**
- At 40 V the rail is 10 V and D57's threshold falls to ~12.3 A, below
  the 12.5 A target.
- So the design operates past its threshold. D63 shows phase 1 held at
  the floor for the rest of the run.
- The timed design at 43.2 V (A116 t30) had a ±18 mV limit cycle there.
  **The floor may or may not prevent it. Registered as the open
  question.**

## 2. Criteria

1. **Driver rows:** as Section 1.
2. **Step rows except l_m80_10us:**
   - no overlap; peak ≤ 200 A;
   - back within 1% ≤ 100 µs;
   - no runaway (late fires ≤ 100, peak ≤ 400 A);
   - the peak within ±10% of D63 (l_p48_10us flagged).
3. **l_m80_10us:**
   - no overlap; peak ≤ 200 A; no runaway;
   - Vo's last 200 periods: peak-to-peak reported (a limit cycle or
     not).

**Decision:** if 1 and 2 hold, the candidate passes the standard matrix
at 1 MHz. l_m80_10us decides whether a 40 V input needs a lower negative
current target (a line-dependent target) or not.
