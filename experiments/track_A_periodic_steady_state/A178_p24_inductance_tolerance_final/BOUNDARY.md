# A178 - where the final plant's 200 A budget holds in inductance (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, threshold-form driver interlock; frozen RTL controller;
cfg only)
Track A, package layer. Written and committed before the runs. Looked at beforehand: A174 (L x 0.7 after +4.8 V /
1 us: 199.5-201.5 A over five step phases), A171 / A173 (L0 182.5 A, L x 1.3 188.7 A).
Decision it changes: the inductance tolerance stated with the spec. Now it reads "−30 % sits at the edge of the
200 A budget". The aim is the largest tested tolerance at which every step phase stays <= 200 A.
Cheaper check done first: linear interpolation between L x 0.7 and L0 (≈ 60 A per unit of L) gives ~197.5 /
194.5 A at L x 0.75 / 0.8 plus ~2 A of phase spread - too close to 200 A at 0.75 to skip the runs.
Budget: 2 start-up runs (~15 min) + 10 runs, --jobs 6 next to A177, ~3 h.

## 1. What and why
- Boards L x 0.75 and L x 0.8 (nominal devices; A171's S50 nominal cfg with circuit L scaled - the only difference
  between A143's L rows; identity-checked against A172's L x 0.7 cfg). Each is re-trimmed under the final plant
  from a 150 us start-up (one shot, A164's slope 0.026 V/ns). First guess: linear between A172's L x 0.7 trim
  and L0.
- +4.8 V / 1 us with the step at 1000 us + k T / 5, k = 0..4, T = 510.1 ns × (L / L0).
- Not tested: other rows at these boards; other corners with an inductance spread.

## 2. Criteria (every run)
1. V_DS <= 40.0 V. 2. Vo(143.5 us) 1.035 ± 0.02 V; start-up and handover <= 200 A.
3. Post-step physical peak <= 200 A; 0 overlaps / shoot-throughs; COMPLETED; NEW 0; late <= 8 (1.5 x A172's
   L x 0.7 late 2 + 5).
4. Vo back within 1 % before the end.
Decision quantity: per board, the maximum post-step peak over the five phases.

## 3. Predictions (not criteria)
- L x 0.75: maximum 196-200 A; L x 0.8: 192-197 A. Start-up 180-195 A. Trim moves < 0.5 ns from the first guess.

## 4. Decision rule
- The spec states the largest tolerance whose five phases all stay <= 200 A, for example "inductance ≥ 0.8 L0
  keeps ≤ 200 A at every tested step phase; 0.7 L0 reaches 201.5 A".
- If L x 0.75 passes, it is that board; if only L x 0.8 passes, it is L x 0.8. If neither passes, the inductor
  tolerance must be tighter than −20 % for the 200 A budget, or the budget is revised. That is named open.
