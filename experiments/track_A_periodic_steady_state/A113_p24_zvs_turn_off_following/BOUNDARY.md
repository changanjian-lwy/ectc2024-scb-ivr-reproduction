# A113 - phase 1's turn-off following Ton in the 25% design (BOUNDARY)

Track A. **Written before any A113 run.**

**Source:** A112 RESULTS 0.3. In the 25% design, phase 1's learned
on-low interval (dlo) does not follow Ton's changes.
- After a load decrease or a falling line step the valleys swing −88 to
  −3 A.
- Vo oscillates 0.990-1.010 V for 160-180 µs.

## 1. The two options (existing RTL; one factor each against A112's p25 rows)

**ff:** A100's feed-forward, cfg `lo_ff` = 1, `lo_kff` = 11.
- dlo moves by 11 LSB per LSB of Ton change.
- The on-low interval is the fall from the peak to the target, (peak −
  valley) L / Vo = (V_rail − Vo) Ton / Vo, so d dlo / d Ton =
  (12.2 − 1)/1 ≈ 11.

**cmp:** the comparator-decided phase-1 turn-off (A105's I1), cfg
`lo_pred` = 0.
- It tracks the current's crossing of the target physically.
- The cost is its timing jitter (A105: 0.63-0.72 A spread at 30 ps for
  I1 against 0.49-0.53 A for I2).

**Rows:** n0 (steady state), s_m62, l_m48_1us, l_m80_10us. 8 runs.

## 2. Registered predictions and criteria

1. **Both options remove the slow oscillation:**
   - s_m62 back within 1% in ≤ 15 µs (A112: 183 µs);
   - l_m48_1us and l_m80_10us in ≤ 25 µs (182, 162 µs);
   - s_m62's extreme positive (an overshoot), within ±30% of the 5%
     design's +11.65 mV.
2. **The steady state (n0):** the high side within ±0.3 V of A112 p25_n0
   (−0.16 to +0.86 V); no overlap. Turn-off spread:
   - ff: ≤ 0.3 A, Ton's ±1 LSB dither moving dlo by ±11 LSB;
   - cmp: ≤ 0.8 A.
3. **Peaks:** after 150 µs ≤ 200 A in n0 and s_m62. The falling line
   steps ≤ A112's (219.5 / 193.6 A).

**What would falsify:**
- the oscillation remaining with ff, meaning the coupling is not
  (only) dlo;
- cmp losing zero voltage in steady state.

## 3. What stays assumed

As A112.
