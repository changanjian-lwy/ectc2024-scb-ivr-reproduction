# A189 - the adopted start-up below 25 C (BOUNDARY)
Method: mixed (cosim, plant V5, code cfe581f; cfg: A188's start-up, gate temp 0 / -40 C; the EPC model's
temperature factors are linear from 25 C, so below 25 C is an extrapolation)
Track A, package layer. Written and committed before the runs.
Decision it changes: whether A188's start-up spec holds below 25 C with the trims locked at 25 C, or needs a
temperature-compensated trim / a stated lower temperature limit.
Cheaper check done first: A184 / A188 records. At 200 ns every turn-on is hard, so mode S's Vo follows the gates'
temperature. The slow boards drift +91 / +95 mV from 25 to 125 C, about 0.9 mV/K; the 400 ns start-up drifted
~0.3 mV/K. If that held linearly, a slow board at -40 C would sit near 0.97 V at 143.5 us, below A163's cliff
(~0.99 V, where the loop winds Ton up at the handover). Budget: 12 start-ups to 200 us, ~25 min.

## 1. What and why
- A188's limits name "below 25 C not run". This is the first check of the adopted spec outside 25-125 C.
- Runs: S75, S0, N0, F0, N13 at 0 C and -40 C (trims and seeds of A185, request 1.045 V). For comparison, the 400 ns
  start-up on N0 and S0 at -40 C (A181's cfgs, A164's trims).
- Not tested: post-step behaviour cold; four modules; temperatures between the points.

## 2. Criteria (per run)
 c1 start-up / handover (entry .. + 25 us) <= 200 A;  c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs / overlaps;
 c4 Vo at the mode-P entry >= 0.99 V (A163's cliff).
Diagnostic: Vo(143.5 us), handover Vo minimum, ladder, the loop's Ton after entry.

## 3. Predictions (not criteria)
- Mode-S Vo(143.5): slow boards ~1.010 V at 0 C and ~0.97 V at -40 C (c4 fails at -40 C); nominal / ff boards drift
  ~0.15 mV/K (>= 1.02 V at -40 C, pass).
- The 400 ns start-up at -40 C: N0 ~1.025 V, S0 ~1.010 V (pass).

## 4. Decision rule
- All pass: the adopted start-up holds from -40 to 125 C at these points (extrapolated device model below 25 C).
- c4 or c1 fails on a cold board: the spec gets a lower temperature limit at the last passing point, and the fix
  candidate (a temperature-compensated mode-S trim from a board temperature sensor, or a higher 25 C target with
  the request level above it) is named. A follow-up experiment tests it.
- c3 fails anywhere: reported first.
