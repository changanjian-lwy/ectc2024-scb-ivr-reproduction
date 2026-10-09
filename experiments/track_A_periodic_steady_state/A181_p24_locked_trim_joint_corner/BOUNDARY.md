# A181 - a start-up trim set once at 25 C, locked, under joint adverse conditions (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, threshold-form driver interlock; frozen RTL controller;
cfg only)
Track A, package layer, plant V5. Written and committed before the runs. Prompted by the second external review
(FINAL_SPEC_COVERAGE Section 6, points 1 and 4). Looked at beforehand: A164 / A173 / A178 records (below).
Decision it changes: (a) whether the per-board start-up trim is a one-time 25 C calibration or needs temperature
compensation; (b) whether "L x 0.75 keeps the 200 A budget" holds only with nominal devices. Cheaper check done
first: from the records - nominal L x 0.75 start-up 191.1 A (A178), slow corner raises the L0 start-up 162.1 ->
188.8 A (A173), so slow + L x 0.75 is estimated at ~218-223 A; a 25 C trim started hot moves Vo(143.5 us) +8.5 mV
(A164: hot trim 0.33 ns shorter, slope 0.026 V/ns). Budget: stage 1 three 150 us start-ups (~15 min), stage 2
ten runs at --jobs 10 (~75 min).

## 1. What and why
- Every corner so far was trimmed at its own condition, 125 C included: that shows "works after re-calibration",
  not "a board calibrated once keeps working". Every limit was also found with the others at nominal.
- Boards, each trimmed once at 25 C at its own device corner (the factory step): N0 nominal L0 (39.615 ns, A164),
  S0 slow corner L0 (48.348 ns, A164), S75 slow corner L x 0.75 (trimmed in stage 1: start-ups at three on-times
  around 44.399 ns, interpolated to Vo(143.5 us) = 1.035 V between the points bracketing it, none below 0.99 V).
- Conditions, trim locked: N0 at 125 C (one position), S0 at 125 C, S75 at 25 C, S75 at 125 C (three positions
  each). All at t_il 1.0 ns. Row +4.8 V / 1 us (the 200 A row); step at 500 us + k T / 3 (T = 0.5048 us x L
  scale), end + 400 us. The step's phase relative to phase 1's last low-side turn-off is measured and reported
  (positions span the period; alignment to the event is read, not imposed).
- Not tested: other rows (falling ramps, load step), four modules, other inductances (the slow corner's own
  inductance limit), a real comparator interlock, cold start below 25 C.

## 2. Criteria (engineering layer, absolute)
1. Start-up and handover peaks <= 200 A (physical, after the gate delays) on every run.
2. Post-step peak <= 200 A at every position.
3. V_DS <= 40 V over the whole run; COMPLETED; 0 shoot-throughs and overlaps.
4. Vo(143.5 us) within A163's benign window 0.99-1.17 V with the locked trim.
Diagnostic layer, reported only: late fires before / after the step, oracle NEW events, Vo extreme and recovery,
interlock holds, pre-step settling (Cs 1 and period, 400-450 against 450-495 us).

## 3. Predictions (not criteria)
- N0 at 125 C: Vo(143.5) 1.040-1.048 V, start-up <= 166 A, post-step <= 186 A: passes.
- S0 at 125 C: Vo(143.5) +5..+12 mV over its 25 C 1.029 V, start-up / handover 185-195 A: passes.
- S75: trim 43.5-45.5 ns; start-up or handover 210-225 A -> criterion 1 fails at 25 C and at 125 C; post-step
  195-205 A.

## 4. Decision rule
- 1-4 pass everywhere: the 25 C trim holds hot and L x 0.75 holds at the slow corner too (tested points);
  FINAL_SPEC states it.
- S75 fails 1 or 2 while N0 / S0 pass: the inductance tolerance depends on the device corner; FINAL_SPEC states
  "L x 0.75 with nominal devices only"; the slow corner's own inductance limit is named open (not run here).
- 4 fails on a 125 C run: the trim needs temperature compensation; named.
- 3 fails anywhere: a spec failure, reported first.
