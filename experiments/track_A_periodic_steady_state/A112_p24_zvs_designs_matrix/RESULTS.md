# A112 - the 20% and 25% negative-current designs on the standard matrix (RESULTS)

Track A, main line.

**Boundary:** `BOUNDARY.md`, committed (df9b177) before any run.

**Records:**
- `cosim/run_*.json`;
- `a112_summary.json` (`a112_analyze.py`; the n0 identity check was
  corrected after the runs to ignore the configurations' note and
  output name, which differ by design).

**Physical model:**
- Verilog RTL;
- A88 kernel2 plant;
- A105's I2 with `slot_lo`, negative-current target 20% or 25%;
- 25 C, one module.

**Reference:** the 5% design's matrix (A105 i2, A106 pi100).

## 0. Verdict

1. **Both designs are robust in steady state.**
   - No overlap in 32 runs.
   - p20_n0 and p25_n0 are identical to A110's n20 and n25.
   - Under driver mismatch (±1, ±3.4 ns) and jitter (30, 100 ps), each
     phase's high-side turn-on stays within ±0.1 V of its design's n0:
     - 20%: 2.2-3.0 V;
     - 25%: −0.18 to +0.92 V, practical zero voltage.
   - The turn-off spread is as the 5% design's (0.36-0.48 A at 30 ps,
     1.1-1.4 A at 100 ps).
2. **20% passes the matrix except at the edges of the line steps:**
   - load steps ±25 / ±62.5 A within the 5% design's (+62.5 A: −10.5
     against −14.7 mV);
   - the 1 µs falling line step recovers in 75 µs (5%: 3 µs);
   - line-step peaks 199-204 A at the 200 A limit (5%: 191-207 A).
3. **25% is not robust in transients.**
   - **The −62.5 A load step** dips (−15.0 mV, where an overshoot is
     expected) and takes 183 µs to settle.
   - **Falling line steps:** −34.0 mV / 182 µs at 1 µs, −17.1 mV /
     162 µs to 40 V.
   - **Line-step peaks:** 212-221 A. The 204 A handover peak is common
     to every row.
   - **Cause** (p25_s_m62 traced):
     - after the step, Vo oscillates between 0.990 and 1.010 V with a
       ~100-150 µs period;
     - Ton swings 547-664 LSB;
     - the valleys swing −88 to −3 A;
     - half the timed turn-offs report early.
   - Phase 1's learned on-low interval does not follow Ton's changes. It
     should move (V_rail − Vo)/Vo ≈ 11 LSB per LSB of Ton. With a large
     negative current the resulting valley error couples with the
     voltage loop into a slow oscillation.
4. **So far:**
   - **20%** is the robust efficiency design: 90.17%, +2.25 points, the
     high side at ~2.6 V (93% of the hard-turn-on loss removed).
   - **25%** gives practical high-side zero voltage in steady state, but
     needs phase 1's turn-off to follow Ton in transients.

## 1. Registered criteria (BOUNDARY Section 1)

| # | criterion | result |
|---|---|---|
| 1 | n0 identical to A110 | pass (after the comparison fix) |
| 2 | no overlap | pass, 32 of 32 |
| 3 | 20% run peak ≤ 200 A | **miss** in l_m48_1us (201), l_p48_1us (203.5), l_p48_10us (203.1) |
| 3 | after 150 µs ≤ 200 A (non-line rows) | pass in both designs (20% ≤ 188 A, 25% ≤ 194 A) |
| 3 | line-step peaks = 5% + 17 / 24 A ± 10 | **miss** in p20/p25 l_p48_1us (199 / 213 against 220 / 227 predicted: lower), p20/p25 l_p48_10us (200 / 202 against 183 / 190: higher); l_m48 within |
| 4 | high-side level ±0.5 V under m and j; low side ≤ 0 in m rows | pass |
| 5 | jitter spread within 5% × (1 ± 0.5) | pass |
| 6 | load steps within ±30%, recovered | 20% pass; **25% s_m62 miss** (sign, 183 µs) |
| 7 | line steps within ±30%, recovered | recovered in all; **extremes miss** in 20% (l_m48_1us −25.7, l_p48_1us −9.1, l_p48_10us −9.6, l_m80_10us −11.6 mV) and 25% (l_m48_1us −34.0, l_p48_1us −12.8, l_m48_10us −7.9, l_p48_10us −11.6, l_m80_10us −17.1 mV) |

**The line-step Vo extremes change sign for rising inputs:** −9 to −13 mV
where the 5% design overshoots +4 to +12 mV. This was not predicted.
With a large negative current the timed turn-off's mismatch after a rail
change (A108's mechanism) moves charge the other way.

## 2. Next

**A113:** phase 1's turn-off following Ton at 25%, on the three failing
rows (s_m62, l_m48_1us, l_m80_10us). Two existing options, no new code:
- A100's Ton feed-forward of dlo (`lo_ff`, k = 11 LSB per LSB);
- the comparator-decided phase-1 turn-off (A105's I1).
