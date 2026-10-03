# A129 - slope gate on the Vin feed-forward's falling term, and the 2.5 MHz standard matrix (BOUNDARY)

Extension `ml_design_assist`. Written and committed before the RTL change and every run.

**Decision it changes:** whether the 2.5 MHz design closes line steps with the Vin feed-forward instead of the ≥ 5 µs
bus-slew spec (A128 missed only on the −8 V / 10 µs cost); stage 2: whether the design, with and without it, holds the
standard matrix (no 2.5 MHz mismatch or jitter data exist).
**Cheaper check done first:** D63 sweep of the threshold (70-140 codes all separate the rows), and the RTL's g and
phase-1 cap recomputed bit-exactly from A124's and A128's cosim Vin samples. **Budget:** 26 runs (~4 min each, 10
cores) + unit tests + full regression, ~45 min.

## 1. What and why
- **A128's cost:** the learned falling term (scale_k = 1 + c_k g, g = max(lp2 − Vin, 0)) acts on every fall. On
  −8 V / 10 µs it holds phase 1's Ton up for the whole ramp: 168.5 → 188.2 A, Vo −28 → +38 mV. Its gain is on fast
  falls (−4.8 V / 1 µs: 215.9 → 175.5 A). D63 does not see the cost (+3.5 A), so the threshold must not depend on it.
- **The gate (RTL, `scb_vff.v`, cfg vff "gth", codes):** opens at the sample where g ≥ gth, closes when g = 0 (lp2 in Q8
  integers reaches Vin exactly); the term acts only while open. gth = 0: always open (= A128, bit for bit). The cap is
  unchanged. A DEVIATION from P24 (Vin sensing), as in A128.
- **gth = 100 codes (2.0 V)**, about 1.3 V/µs sustained (g ≈ 3 × fall per period, period ≈ 0.5 µs). g's maximum,
  recomputed from the cosim samples: −4.8 V / 1 µs 144-147 (opens at the 3rd sample, g 93 → 147); −4.8 V / 5 µs 58-60;
  −8 V / 10 µs 49-51; rising and load rows 0. Margins ×1.67 below / ×1.45 above.
- **When the gate stays closed** only the cap acts; after 300 µs it is ≥ 316 LSB (9.9 ns) above Ton on every row, so
  the slow falls reduce to A124 apart from the start-up (the cap binds in 28 samples near 150 µs, as in A128).
- **Stage 1:** A128's rows (A124's seven step rows + n0) with gth 100; two identity reruns. **Stage 2:** `matrix.ROWS`
  m1n m1p m3n m3p j30 j100 s_m25 s_p25 on A124's p125_n0 (end 1000 µs; load step at 800 µs, end 1200 µs), without
  feed-forward (o125) and with the gated one (g125). Not tested: Vin ADC noise, Cs tolerance, other gth values in cosim.

## 2. Criteria
0. **Identity:** unit tests pass (incl. a new gate test); `scripts/cosim_regression.py --full` passes; A124's
   p125_l_p48_1us (vff off) and A128's v125_l_m48_1us (gth absent) rerun with the new code: sections identical.
1. **Every step row ≤ 200 A** (seven rows; −4.8 V / 1 µs is 215.9 A without the term).
2. **−8 V / 10 µs:** at least |Vo| ≤ 31.2 mV (A124 28.2 + 3); "back to the original level" if also peak ≤ 171.5 A
   (A124 168.5 + 3).
3. **No harm vs A124:** load rows ±3 A; every falling row |Vo| ≤ A124 + 3 mV; no overlap or runaway; n0 as A128
   (efficiency ±0.05 points, start-up ±2 A, HS turn-on V_DS ±0.1 V).
4. **Inert where g = 0:** rising rows, load rows and n0 identical to A128 (sections). A128's +4.8 V / 5 µs |Vo| residual
   (+3.2 mV vs A124, from the cap) therefore stays; it is named in Section 4, not re-judged.
5. **Matrix, both arms:** no overlap or runaway; peak ≤ 200 A; per phase, HS turn-on V_DS within ±0.5 V of the arm's n0
   and LS turn-on V_DS ≤ 0 in the m rows (A112); j30 turn-off sd ≤ 0.5 A per phase (A115); ±25 A back within 1% in
   ≤ 60 µs (A115).
6. **Matrix, gated vs off, per row:** peak ±3 A; load rows' Vo extreme ±3 mV; HS turn-on V_DS ±0.1 V; turn-off sd
   ±20% or ±0.05 A, whichever is larger (amended before the stage 2 runs: without jitter the sd is ~0.01 A, where
   ±20% is numerical noise).

## 3. Predictions (D63 with the RTL law; A125 bands at 80%, peak in A)
| row | D63 gated (A128, none) | M80 | G80 | D63 Vo, mV | cosim expectation |
|---|---|---|---|---|---|
| +4.8 V / 1 µs | 186.4 (186.4, 213.5) | 163-210 | 184-221 | +7.8 | = A128 181.5 |
| +4.8 V / 5 µs | 175.8 (175.8, 186.7) | 154-198 | 173-208 | +5.6 | = A128 175.4 |
| −4.8 V / 1 µs | 166.1 (169.0, 206.2) | 145-187 | 164-197 | +20.8 | ~172 (A128's D63 error +4%) |
| −4.8 V / 5 µs | 168.1 (169.5, 168.1) | 146-190 | 166-199 | +33.2 | A124 173.7 ± 0.5, +22.6 ± 0.5 mV |
| −8 V / 10 µs | 164.5 (168.0, 164.5) | 143-186 | 162-195 | +34.4 | A124 168.5 ± 0.5, −28.2 ± 0.5 mV |
| ±62.5 A | 177.1 / 144.2 (same) | 154-200 / 126-163 | 175-210 / 142-171 | −10.1 / +16.8 | = A128 177.8 / 143.9 |

|Vo| band ×0.56-1.44 of D63 (A125). Outside the matrix (D63 only): −4.8 V / 2 µs opens (161 vs 192 A without the term);
−4.8 V / 3 µs and −8 V / 5 µs stay closed (181 / 186 A; ungated 169 / 193). Stage 2: gated = off within ±0.5 A,
±0.5 mV, ±0.02 V (g = 0, cap slack); ±25 A ≈ 0.4 × A124's ±62.5 A Vo (+6 / −5 mV); j30 sd ≤ 0.5 A.

## 4. Decision rule
- **0-4 hold:** the gated feed-forward is the 2.5 MHz design's line-step closure (extension option): the tested steps
  (±4.8 V at 1 and 5 µs, −8 V / 10 µs) are within 200 A, so the bus-slew requirement relaxes from ≥ 5 µs to ≥ 1 µs for
  steps up to 4.8 V. Recorded deviation: +4.8 V / 5 µs |Vo| 10.9 vs 7.7 mV.
- **5-6 also hold:** the adoption stands on the matrix; the scorecard's 2.5 MHz column gets its matrix entries; the
  feed-forward line (A125-A129) closes and the docs are updated once.
- **2 fails:** the gate is not enough; the bus-slew spec stays. Stage 2 still runs (its off arm is the design's first
  matrix data). **5 fails on the off arm:** a 2.5 MHz design problem, the next item regardless of the feed-forward.
