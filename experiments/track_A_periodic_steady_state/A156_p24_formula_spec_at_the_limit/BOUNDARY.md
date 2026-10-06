# A156 - the formula spec at its limit, on A152's robustness matrix (BOUNDARY)
Method: mixed (math: D68 / A155 formulas and offset predictions; RTL cosim cfg only, frozen design)
Track A, package layer. Written and committed before the runs, after A153-A155.
Decision it changes: whether the drive spec may be written up to D68's limit (L * di/dt_on <= 3.2 V) or needs a margin
on the corners; A152 checked the matrix only at x_on 1.8 V.
Cheaper check done first: A153's nominal row at this point (125 pH x 24 A/ns: 39.1 V) plus A152 S100's per-row offsets.
Budget: 13 single-module runs (~45 min each) + four modules (~2.5 h), ~3 h at 10 jobs.

## 1. What and why
- Point S125: loop 125 pH (Q 7, rp 1.3003), turn-on 24 A/ns (x_on 3.0 V), turn-off 72 A/ns (x_off 9.0 V), start-up ton
  37.149 ns from A155's law (V_T 1.015 V).
- Rows: A152's 13 (l_p48_1us, s_p62, l_m48_1us, l_m80_10us, L x 0.7 / 1.3 on l_p48_1us and s_p62, +4.8 V ramps of
  2 / 3 / 4 / 5 / 10 us), references = the same rows of the frozen design on the ideal plant; four modules on l_p48_1us.
- Criteria = A152's (judge in a152_analyze), load-step Vo price 4.1 us at 125 pH (3.2 / 3.8 at 50 / 100 pH).
- Not tested: Cs corners, > 150 pH on the matrix, a gate model.

## 2. Criteria (all 13 rows; four modules for 5)
1. Whole-run max V_DS <= 40.0 V.
2. Start-up peak (t < 300 us) <= max(200 A, ref + 5 A).
3. Post-step peak <= min(ref + 5, 200) A; 0 NEW oracle events; late fires <= ref + 2; COMPLETED.
4. Vo: |extreme| <= |ref| + 4 mV; if |extreme| > 11 mV, back within 1 % <= ref + 2 us (+ 4.1 us on load steps).
5. Four modules: criteria 1-3.

## 3. Predictions (a156_predictions.json; not criteria)
V_DS = 39.1 V + A152 S100's row offset: L x 1.3 l_p48_1us 39.7 V (0.3 V below the limit), four modules 39.1 V, slew rows
37.2-38.3 V, L x 0.7 l_p48_1us 38.7 V, falling and load rows 34.8-35.8 V. Start-up ~150 A (L x 0.7 ~198 A, as its ideal
reference); post-step peaks as A152 (<= 185 A).

## 4. Decision rule
- 1-5 pass: the spec is written to D68's limit, x_on <= 3.2 V (with the corners inside).
- 1 fails on a corner only: the spec keeps a margin, x_on <= 3.2 V minus the measured excess (e.g. <= 2.8 V).
- 2-4 fail: that drive is not adopted at the limit; the spec stays at x_on <= 1.8 V (A152's checked value).
