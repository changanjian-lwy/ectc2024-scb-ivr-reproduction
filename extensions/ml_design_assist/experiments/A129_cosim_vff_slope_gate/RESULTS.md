# A129 - slope gate on the Vin feed-forward's falling term, and the 2.5 MHz standard matrix (RESULTS)

Boundary: d5af292 (amendment 3848406); RTL 6bb363e. Records: `cosim/run_g125_*` (stage 1 and the gated matrix arm),
`run_o125_*` (matrix without feed-forward), post hoc `run_d125_*`, `run_x125_*`, `run_no125_*`, `run_ng125_*`;
`a129_predictions.json` (registered), `a129_summary.json` (`a129_analyze.py`).

## 0. Verdict
1. **The gate removes A128's cost and keeps its gain.** Peak after the step, A, and Vo extreme (2.5 MHz, Cs 6 µF):

   | row | A124 (none) | A128 | **A129** | D63 gated (M80) | Vo, mV: A124 → A128 → A129 |
   |---|---|---|---|---|---|
   | +4.8 V / 1 µs | 217.7 | 181.5 | **181.5** | 186 (163-210) | +13.7 → −12.3 → −12.3 |
   | +4.8 V / 5 µs | 210.2 | 175.4 | **175.4** | 176 (154-198) | −7.6 → +10.9 → +10.9 |
   | −4.8 V / 1 µs | 215.9 | 175.5 | **173.6** | 166 (145-187) | +42.9 → +17.2 → +15.7 |
   | −4.8 V / 5 µs | 173.7 | 175.3 | **174.3** | 168 (146-190) | +22.6 → +17.6 → +22.8 |
   | −8 V / 10 µs | 168.5 | 188.2 | **170.9** | 164 (143-186) | −28.2 → +38.1 → +28.6 |
   | ±62.5 A | 177.7 / 143.9 | 177.8 / 143.9 | 177.8 / 143.9 | 177 / 144 | −12.0 / +15.9 → −11.8 / +15.8 (same) |

   The gate opened only on −4.8 V / 1 µs (0.66 µs after the step, g up to 145 codes); slow falls stayed below 60. The
   worst row is now 181.5 A (A128 188.2). −8 V / 10 µs has two near-equal Vo lobes (A124 +27.5 / −28.2, A129
   +28.6 / −27.9 mV), so the sign of the extreme is not meaningful.
2. **Identity and inertness:** vff off and gth 0 rerun bit-identical (A124 and A128, 2458 / 2453 sections); full
   regression PASS; unit tests 60/60; rising rows, load rows and n0 bit-identical to A128.
3. **Registered prediction missed on the slow falls:** "A124 ± 0.5 A" came in at +2.4 A (−8 V / 10 µs) and +0.6 A.
   Post hoc, with the cap off (k 0) the gated −8 V / 10 µs run is **bit-identical to A124**: the gate is exactly inert;
   the +2.4 A is the pre-step state left by the cap's start-up action (28 samples near 150 µs, since A128). Moving the
   step by 1/3 and 2/3 of a period gives 168.5 / 170.5 / 170.9 A without feed-forward (Vo −28.2 / +28.2 / +28.5 mV):
   the +2.4 A is that step-phase spread.
4. **Matrix (stage 2), both arms:** no overlap or runaway; peaks 162-164 A (start-up) and ≤ 158.3 A after ±25 A; HS
   turn-on V_DS within 0.07 V of n0; LS turn-on ≤ 0 in the m rows; j30 turn-off sd 0.23-0.31 A (≤ 0.5); ±25 A Vo
   +6.1 / −4.6 mV (off), +5.4 / −4.7 mV (gated), never outside 1%. Gated = off within 0.1 A, 0.03 V and 0.05 A sd on
   every row **except s_m25's post-step peak: 153.0 vs 156.9 A (−3.9 A, registered ±3 A)**. That peak is a sporadic
   single-period phase-1 spike in both arms (off 157/150/148, gated 153/151/146 A); its step-phase spread is 150.3-156.9 A off, 150.4-153.0 A gated.
5. **Post hoc, intermediate slews (gated, registered D63 x rows; all inside M80):** −4.8 V / 2 µs 162.0 A, −4.8 V /
   3 µs 187.3 A (gate closed in both, g 97 / 86), **−8 V / 5 µs 207.9 A > 200 A** (gate closed, g 86; D63 186). The
   ≥ 5 µs bus-slew spec was only ever tested on ±4.8 V; an 8 V fall needs more than 5 µs, with or without the gate.
6. **Decision (Section 4):** criteria 0-5 hold; 6 misses on one row in the favourable direction, within the step-phase
   spread. The gated feed-forward is adopted as the 2.5 MHz design's line-step closure (extension option, Vin sensor):
   steps up to 4.8 V close at any tested slew ≥ 1 µs (1, 2, 3, 5 µs ≤ 187 A); −8 V needs ≥ 10 µs (5 µs: 208 A).
   Recorded deviations: +4.8 V / 5 µs |Vo| 10.9 vs 7.6 mV (the cap, since A128); criterion 6 on s_m25.

## 1. Criteria (BOUNDARY Section 2)
| # | criterion | result |
|---|---|---|
| 0 | identity (unit, regression, two reruns) | **pass** |
| 1 | every step row ≤ 200 A | **pass** (worst 181.5) |
| 2 | −8 V / 10 µs: \|Vo\| ≤ 31.2 mV; back to level if peak ≤ 171.5 A | **pass, back to level** (28.6 mV, 170.9 A) |
| 3 | no harm vs A124 (loads ±3 A, falls' \|Vo\| + 3 mV, overlap, n0) | **pass** (n0 90.609%, start-up 163.4 A) |
| 4 | inert where g = 0 (identical to A128) | **pass** (5/5 rows) |
| 5 | matrix, both arms (overlap, 200 A, V_DS, j30 sd, ±25 A recovery) | **pass** (16/16) |
| 6 | matrix, gated vs off | **miss on s_m25** (−3.9 A, gated lower); other 7 rows pass |

A125's prospective test: M80 7/7, G80 6/7 (+4.8 V / 1 µs below its lower edge, as in A128), |Vo| band 5/7 (the two
rising rows); the x rows 3/3 in M80, but D63 was −10% on −8 V / 5 µs.

## 2. Limits
- One design, one load level, ideal Vin ADC (noise only closes the latch earlier; opening needs a 2 V drop in g).
- −4.8 V / 2 µs sits just below the threshold (g 97 vs 100); the gate's slew band is narrow but the rows it leaves
  closed stayed ≤ 187 A. Falls of 8 V between 5 and 10 µs and rising 8 V steps are untested.
- Under jitter the low side's worst turn-on reaches +0.5 V (j30) and +5.3 V (j100) in both arms (maximum, not mean).
