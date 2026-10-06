# A161 - 150 pH with a faster turn-on (x_on 3.0 V), on A152's robustness matrix (BOUNDARY)
Method: mixed (math: D68 / A155 formulas, A156 offsets; RTL cosim cfg only, frozen design)
Track A, package layer. Written and committed before the runs, after A159 / A160.
Decision it changes: whether the recommended loop bound is 125 pH (A159: at 150 pH the 12 A/ns turn-on of x_on 1.8 V
costs regulation) or 150 pH with a faster turn-on at the voltage limit.
Cheaper check done first: D68's x-curve (39.2 V at x 3.0) and A156's per-row offsets at x 3.0 (125 pH).
Budget: 13 runs + four modules, ~3 h at 10 jobs.

## 1. What and why
- Point: 150 pH (Q 7), turn-on 20 A/ns (x_on 3.0 V), turn-off 72 A/ns (x_off 10.8 V), start-up ton 37.607 ns (A155).
- Rows, references and criteria as A156 / A159 (judge in a152_analyze), load-step Vo price 4.4 us.
- Two limits meet here: the overshoot (x_on <= 3.0-3.2 V) and the regulation (A159: 12 A/ns too slow at 150 pH;
  A156: 24 A/ns fine at 125 pH).

## 2. Criteria (all 13 rows; four modules for 5)
1. Whole-run max V_DS <= 40.0 V.
2. Start-up peak <= max(200 A, ref + 5 A).
3. Post-step peak <= min(ref + 5, 200) A; 0 NEW oracle events; late fires <= ref + 2; COMPLETED.
4. Vo: |extreme| <= |ref| + 4 mV; if |extreme| > 11 mV, back within 1 % <= ref + 2 us (+ 4.4 us on load steps).
5. Four modules: criteria 1-3.

## 3. Predictions (a161_predictions.json; not criteria)
V_DS 39.3 V nominal; L x 1.3 l_p48_1us 39.6 V, slew2 39.3 V, four modules 39.4 V (all within 0.7 V of the limit).
Criterion 4 recovers (s_p62 dip near A156's), late fires on l_m80_10us 20-40, NEW flags from the K4 window likely
(A160: K4 stays 1 us).

## 4. Decision rule
- 1, 2, 4 and 5 pass: the recommended bound can be 150 pH with x_on 3.0 V (20 A/ns), at a voltage margin of < 1 V;
  criterion 3 is judged by its causes as in A156 / A159.
- 1 fails: at 150 pH no turn-on rate meets both limits (A159 below, A161 above); the bound stays 125 pH.
- 4 fails: the regulation limit needs > 20 A/ns at 150 pH; the bound stays 125 pH.
