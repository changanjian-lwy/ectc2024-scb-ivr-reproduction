# A159 - the adopted spec at the recommended loop bound (150 pH), on A152's robustness matrix (BOUNDARY)
Method: mixed (math: D68 / A155 formulas and offset predictions; RTL cosim cfg only, frozen design)
Track A, package layer. Written and committed before the runs, after A156-A158.
Decision it changes: whether the recommendation "bound the loop to ~150 pH, turn-on x_on <= 1.8 V" holds on the full
matrix at 150 pH, or the bound must come down (late fires on -8 V / 10 us grew 0 / 6 / 16 at 50 / 100 / 125 pH, A156).
Cheaper check done first: D68's x-curve (36.8 V at x 1.8) and the harness turn-off at 150 pH / 72 A/ns / 172 A
(34.6 V + 2.4 V line-step offset); A152 S100's per-row offsets. Budget: 13 runs + four modules, ~3 h at 10 jobs.

## 1. What and why
- Point S150: loop 150 pH (Q 7, rp 1.4244), turn-on 12 A/ns (x_on 1.8 V, adopted), turn-off 72 A/ns (x_off 10.8 V, just
  over A154's ~10 V rule: A151 measured 38.0 V at 150 pH with 18 A/ns), start-up ton 38.632 ns (A155's law).
- Rows and criteria as A152 / A156 (judge in a152_analyze); load-step Vo price 4.4 us at 150 pH.
- Turn-on at 12 A/ns is near A151's "too slow" 9 A/ns (150 pH: line-step Vo outside 1 % for 44 us there).

## 2. Criteria (all 13 rows; four modules for 5)
1. Whole-run max V_DS <= 40.0 V.
2. Start-up peak (t < 300 us) <= max(200 A, ref + 5 A).
3. Post-step peak <= min(ref + 5, 200) A; 0 NEW oracle events; late fires <= ref + 2; COMPLETED.
4. Vo: |extreme| <= |ref| + 4 mV; if |extreme| > 11 mV, back within 1 % <= ref + 2 us (+ 4.4 us on load steps).
5. Four modules: criteria 1-3.

## 3. Predictions (a159_predictions.json; not criteria)
V_DS 37.0 V nominal + A152 S100's row offsets: L x 1.3 l_p48_1us 37.6 V, ramps 35.1-36.2 V, four modules 37.0 V.
Late fires on l_m80_10us 20-45 (criterion 3 likely fails there); start-up ~150 A (L x 0.7 ~198 A).

## 4. Decision rule
- 1-5 pass: the recommendation stands (loop <= 150 pH, x_on <= 1.8 V).
- 3 fails on late fires only, without peak / voltage / NEW consequence: the recommendation stands for voltage and is
  noted for timing; the late-fire mechanism becomes the next question.
- 1, 2, 4 or 5 fail, or late fires come with consequences: the recommended loop bound comes down to the largest L that
  passed (125 pH at x 3.0 for voltage, A156; 100 pH S100, A152).
