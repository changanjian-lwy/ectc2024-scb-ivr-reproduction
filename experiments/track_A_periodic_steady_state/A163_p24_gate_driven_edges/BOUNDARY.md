# A163 - the package drive as gate resistances, with gate-driven edges in the plant (BOUNDARY)
Method: mixed (device: EPC's EPC2067 model, D79; plant: cosim/gate.py; RTL cosim, frozen controller, cfg only)
Track A, package layer. Written and committed before the matrix runs, after D79 (single edges, checked against
LTspice) and the start-up calibration runs (to 150 us, Section 3).
Decision it changes: whether the drive spec becomes D79's resistances (50 pH: r_on 2.5 / r_off 0.3 ohm; 75 pH: 3.5 /
0.3 ohm; strong sink, loop <= 75 pH) instead of the ramp spec (turn-on <= 3.0-3.2 V / L, turn-off 72 A/ns, 125-150 pH).
Cheaper check done first: D79's single edges (444 plant edges, 9 LTspice comparisons, dv/dt check). Budget: 28 runs
+ four modules, ~5 h at 10 jobs.

## 1. What and why
- The ramp model had no gate. D79 found three changes: turn-on overshoot 3.5-5 V lower at equal slope, turn-on and
  turn-off losses of several W unless both edges are fast, and a gate delay that the valley learning must absorb
  (bridge "meas" "act": the valley measured when the channel starts to conduct).
- A: S50 (50 pH Q 7, gate 2.5 / 0.3 ohm per device, start-up ton 37.887 ns) on A152's 13 rows and four modules.
- B: S50 with the spread: threshold -0.3 / +1.5 V, C_ISS x 1.5, driver resistance x 0.7 (l_p48_1us, s_p62).
- C: S50 with the valley measured at the command (l_p48_1us, s_p62): diagnostic, not judged.
- D: S75 (75 pH, 3.5 / 0.3 ohm, ton 39.485 ns) on l_p48_1us, s_p62, L13_l_p48_1us, l_m80_10us, slew2.
- References: A152's 50 pH run of the same row (ramp edges 36 / 72 A/ns). Low sides keep A152's edges.

## 2. Criteria (A, B, D: each row; four modules 1-3), a163_analyze with A152's judge
1. Whole-run max V_DS <= 40.0 V.
2. Start-up peak (physical turn-off current, t < 300 us) <= max(200 A, ref + 5 A).
3. Post-step peak (physical) <= min(ref + 5, 200) A; 0 NEW oracle events; late fires <= ref + 2; COMPLETED.
4. Vo: |extreme| <= |ref| + 4 mV; if |extreme| > 11 mV, back within 1 % <= ref + 2 us.

## 3. Predictions (a163_predictions.json; not criteria)
- Start-up calibration (to 150 us, done before registering): at ton 36.5 ns Vo(143.5 us) 0.976 V (S50) / 0.931 V (S75),
  handover peaks 195 / 307 A (S75 47.4 V); at the registered tons 1.012 / 1.006 V, 156.8 / 164.7 A, <= 31.3 V.
- A: whole-run V_DS 33-37 V (D79 worst single edge 34.7 V nominal; A152 32.9-37.6 V); peaks within +-5 A of A152;
  steady edge power 4-6 W per module (D79: 294 + 286 nJ per phase period; A152's ramps 3.9 W); late fires 0-5.
- B: V_DS <= 39 V (r x 0.7 the highest, D79 39.0 V single edge); threshold max: edge power ~2x and the largest start-up
  Vo deficit (slow turn-on), possibly criterion 2 on its handover.
- C: turn-ons later than the valley by the gate delay (1.5-2.5 ns), higher V_DS at the channel start than in A.
- D: V_DS <= 38.5 V; post-step peaks as A; edge power ~6 W.

## 4. Decision rule
- A and D pass: the drive spec becomes D79's resistances, the loop bound 75 pH (50 pH for 260 A excursions); the
  ramp spec's 125-150 pH bound and A151's 0.1-0.4 W are withdrawn; Mihai's question 1 is rewritten.
- A passes, D fails: bound 50 pH.
- A fails on V_DS or peaks: raise r_on along D79's curve and retest (A164); on late fires / NEW / regulation: the gate
  delay or the deferred measurement is the cause; diagnose with C (A164).
- B fails: state which spread breaks which criterion; the spec then needs a margin or a calibrated r_on.
