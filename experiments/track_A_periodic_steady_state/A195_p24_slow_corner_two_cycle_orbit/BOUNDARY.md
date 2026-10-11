# A195 - the slow corner's two-cycle orbit: what sustains it (BOUNDARY)
Method: mixed (analysis of existing records, then cosim, plant V5, cfg only: registers of the frozen controller's
high-side turn-on corrector on slow boards; no RTL or plant code change)
Track A, package layer. Written and committed before the runs. The records in Section 1 were looked at beforehand.
Decision it changes: whether the slow corner's steady alternation can be removed by a per-board-class setting (as the
lead and the trims are), which would return about 2.4 A of peak current to a corner with a 2.2 A margin; or whether it
is a property of the plant that the specification has to state.
Cheaper check done first: 22 existing records (a195_records.json), no simulation.
Budget: 5 runs of 330 us (1.8 run-equivalents of 900 us), --jobs 4 beside A194, about 1 h.

## 1. What was found in the records
- Tracing A192's open point (why the 9.5 ns lead "deepens the valleys") showed that the mean hides the behaviour.
  **On every slow-device record the valley and the peak alternate from one cycle to the next**: the low-side
  turn-off current changes by 3.7-7.2 A cycle to cycle, the peak by 4.0-7.9 A, and phase 1's timed-edge reports are
  early exactly half of the time (0.49-0.51). Nominal and fast boards: 0.01-0.9 A.
- It is there on V2 and V5 (since A164), with the 8 and the 9.5 ns lead, on S0 / S75 / S80, at -40, 0, 25 and
  125 C; larger cold (6.0-7.2 A at -40 C) and with a smaller inductance. It goes with the high-side gate delay:
  8.2-10.7 ns on slow boards, 2.8 ns nominal, 1.7 ns fast.
- One period of S75 (25 C, 9.5 ns), phase 1: valley -12.85 A -> turn-on at 5.75 V, reported early -> peak 144.0 A ->
  valley -17.29 A -> turn-on at 3.98 V, reported late -> peak 148.8 A -> valley -12.85 A. The low-side interval
  (343.0 ns) and the commanded on-time (40.38 ns) do not alternate; the turn-on command moves by 0.28 ns, the
  corrector's step.
- So A192's "deeper valleys" are the mean of an alternating pair that moved (8 ns: -16.1 / -11.3 A; 9.5 ns:
  -17.3 / -12.9 A). In steady state the channel starts 11.2 ns after the low-side turn-off with either lead: the
  loop absorbs the lead into dt_pred (10.0 -> 11.3 ns).
- No RESULTS file, D79 or FINAL_SPEC_COVERAGE mentions it. Reported means and maxima include it.

## 2. Question and runs
- The corrector's law (scb_phase): an early report adds dt_step (0.28 ns); a late one removes (error - 94 ps) / 2.
  With a slow gate each 0.28 ns of turn-on instant is worth ~1.4 A, and the next valley moves the next report. Is the
  alternation the corrector hunting (then a smaller step or gain removes it), or does the plant's valley-to-valley map
  have a slope near -1 by itself (then the corrector only excites it)?
- Runs: S0 (slow L0) with step4, shift2, tgt4, step4_shift2; S75 with step4 (make_cfgs.py). To 330 us, no event.
  Window 290-330 us. Reference: the existing final-cfg records of the same boards in the same window (S0 4.1-4.8 A,
  S75 5.3-6.2 A valley alternation; 459-499 us gives 3.8-4.4 and 4.7-5.5 A, about 10 % less).

## 3. Criteria (diagnostic)
 c1 the alternation is removed: mean cycle-to-cycle valley change <= 1.0 A on every phase (nominal boards: <= 0.9 A).
 c2 nothing else moves: COMPLETED, 0 shoot-throughs, mean Vo within 1 mV of the reference, every phase's mean valley
    within 1.5 A of -15.6 A, late fires in the window <= the reference's.

## 4. Predictions (not criteria)
- step4 lowers the alternation but does not remove it (2-3 A left): the measured rise from a deep valley exceeds the
  rise from a shallow one by 9.3 A for 4.4 A of valley, a map slope near -1.1, which a smaller step cannot change.
- shift2 and tgt4 change little.

## 5. Decision rule
- A variant passes c1 and c2 on S0 (and step4 on S75): a follow-up with its own number runs it on the slow rows
  (A192's rows, hot and cold) and on a rising step before anything is adopted; a step change touches the tracking
  that A143 fixed.
- None passes: the orbit belongs to the plant with a slow gate. FINAL_SPEC_COVERAGE states it (slow boards alternate
  by 4-7 A cycle to cycle; their margins include it), A192's open point is closed with Section 1, and a remedy in
  the controller is listed as needing authorisation.
