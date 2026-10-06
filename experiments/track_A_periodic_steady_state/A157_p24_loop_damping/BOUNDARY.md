# A157 - the drive spec under weaker loop damping (BOUNDARY)
Method: mixed (math: single-edge harness Q sweep and predictions; RTL cosim cfg only, frozen design)
Track A, package layer. Written and committed before the runs.
Decision it changes: whether the package spec needs a loop-damping requirement (ring Q) next to L and di/dt. Every
package run so far used Q 7 (a parallel damper on the loop); A144 found the undamped loop breaks the valley tracking
(8000+ late fires, 225 A), but with instantaneous edges and no slow turn-on.
Cheaper check done first: A145's harness, turn-on (V_DS 17 V) and turn-off (143 A) at Q 3 / 7 / 10 / 15 / 30 / undamped:
at x_on 1.8 V the turn-on peak moves +0.1 / +0.3 / +0.8-1.6 V (Q 15 / 30 / undamped); at x_on 3.0 V +1.8 / +2.8 / +5.5 V;
the 72 A/ns turn-off at 150 pH +1.3 / +1.9 / +2.6 V. Budget: 5 runs, ~1 h at 10 jobs.

## 1. What and why
- Rows (A152's s100_l_p48_1us cfg: frozen design, +4.8 V / 1 us at 1000 us, turn-off 72 A/ns; start-up ton by A155):
  q15_s50 / q30_s50 / q0_s50 (50 pH, turn-on 36 A/ns: the adopted S50 point at Q 15, 30, undamped), q0_s100 (100 pH,
  18 A/ns, undamped), q0_s125 (125 pH, 24 A/ns, x_on 3.0 V, undamped: predicted over 40 V).
- The question is mainly the controller: does the slow turn-on keep the valley tracking alive without a damper?
- Not tested: other rows, corners, four modules, Q between 30 and undamped.

## 2. Criteria
1. Whole-run max V_DS within +-1.5 V of the prediction on all 5 rows.
2. V_DS <= 40 V on q15_s50, q30_s50, q0_s50, q0_s100.
3. Controller on all 5 rows (A152's judge against the ideal-plant l_p48_1us reference): COMPLETED, start-up peak
   <= max(200, ref + 5) A, post-step peak <= min(ref + 5, 200) A, 0 NEW oracle events, late fires <= ref + 2, Vo
   extreme within ref + 4 mV.

## 3. Predictions (a157_predictions.json)
V_DS = the Q 7 measurement of the same point (A152 S50 37.1, S100 36.4; A153 125 pH x 24 39.1 V) + the harness's Q
offset: q15_s50 37.2, q30_s50 37.4, q0_s50 38.7, q0_s100 37.2, q0_s125 44.6 V. Controller: unknown (the question).

## 4. Decision rule
- 2 and 3 pass on the S50 / S100 rows: the spec needs no damping requirement at x_on <= 1.8 V.
- 3 fails undamped but passes at Q 30 / 15: the spec adds "ring Q <= 30" (or 15).
- 3 fails at Q 15: damping becomes a spec item at Q <= 7-10, and the loop Q joins the questions for Mihai.
