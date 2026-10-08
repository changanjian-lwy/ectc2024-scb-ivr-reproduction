# A172 - the final gate-level plant: L x 0.7 re-trimmed and four modules (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, threshold-form driver interlock; frozen RTL controller;
cfg only)
Track A, package layer. Written and committed before the runs.
Looked at beforehand: A171 (all eight runs).
- With the threshold interlock, S50 nom / ff / hot / ss pass. The slow corner improves on A167: 194 late fires
  against 260.
- S50 L x 0.7 misses only criterion 2. Its Vo(143.5 us) is 1.010 V because A164's trim was set with ideal low
  sides; everything else passes (handover 187.3 A, post-step 199.2 A, late 4).
- Four modules were last run with ideal low sides and no interlock (A164 m4).
Decision it changes: whether A171's form becomes the package spec without exceptions. A per-board trim is part of
the spec, so the L x 0.7 board must pass with a trim measured under this plant. The four-module system must hold too.
Cheaper check done first: none beyond A171. The trim is one shot from A171's own start-up:
ton = 34.813 + (1.035 - 1.0101) / 0.026 = 35.769 ns.
Budget: 2 runs (single module ~1.5 h, four modules ~4-5 h).

## 1. What and why
- The plant: 50 pH; 3.0 / 0.3 ohm per device +-20 %; 8 ns lead ramped over 20 us after mode P; all switches
  gate-driven; interlock "threshold" with t_il 0.5 ns.
- Rows:
  - nom L07_l_p48_1us, board re-trimmed (ton 35.769 ns);
  - four modules, nom l_p48_1us (A164's m4 cfg and trim).
- Reference: A167's L x 0.7 row; A164's four-module row.

## 2. Criteria (A168's, a168_analyze.judge; criterion 4 not applied to four modules, as in A164)
1. Whole-run max V_DS <= 40.0 V.
2. Vo(143.5 us) within 1.035 +- 0.02 V; physical start-up and handover peaks <= 200 A (<= ref + 3 A where the
   reference is above 197 A).
3. Post-step:
   - physical peak <= 200 A and <= ref + 5 A;
   - 0 overlaps, 0 shoot-throughs, COMPLETED;
   - late fires <= 1.5 x ref + 5;
   - NEW 0 where the reference has none, else <= 1.5 x ref + 5.
4. Vo: |extreme| <= |ref| + 2 mV; where |extreme| > 11 mV, back within 1 % <= ref + 2 us.

## 3. Predictions (not criteria)
- L x 0.7: Vo(143.5) 1.030-1.040 V. Mode S's start-up peak rises with the longer on-time: 202-206 A, within
  ref + 3 = 205.5 A. Handover <= 192 A; post-step 196-200 A; late <= 8.
- Four modules: as A164 m4 within +-3 A (post-step 182.6 A, 0 late), holds rare, 0 shoot-throughs.

## 4. Decision rule
- Both pass: the package spec is A167's drive plus gate-driven low sides (sink <= 0.3 ohm) plus a threshold-form
  driver interlock (<= 0.5 ns). The interlock open item closes without an RTL change, and D79 / the scorecard /
  the Mihai summary are updated.
- L x 0.7 misses on mode S's start-up peak only: same, with the frozen design's open-loop start at L x 0.7 still
  named as its limit (as in A167).
- Anything else: reported, and the spec stays at A171 with that row named open.
