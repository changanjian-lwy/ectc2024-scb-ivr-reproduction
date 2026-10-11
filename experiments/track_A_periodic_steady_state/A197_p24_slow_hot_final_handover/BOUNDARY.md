# A197 - the slow corner at 125 C with the adopted handover request (BOUNDARY)
Method: cosim, plant V5, cfg only (hand_vo_v 1.03 -> 1.045 in A191's 12 cfgs; no RTL or plant code change)
Track A, package layer. Written and committed before the runs. A191's records and A194's six hot slow-board draws
were looked at beforehand.
Decision it changes: whether "slow devices hold 200 A after +4.8 V / 1 us at 125 C with the 9.5 ns lead" is a
statement about the final configuration. It is the row the lead was adopted on, and it ran with A186's handover
request (1.03 V), not the adopted one (1.045 V, A188).
Cheaper check done first: the steady state before the step, from existing records (Section 1). It agrees within
0.2 A, but the post-step peak moves 2.8 A with the step position and the margin is 3.1 A.
Budget: 12 runs of 900 us, --jobs 10, about 2.2 h.

## 1. What and why
- Found while checking A194: A191's cfgs come from A187's, which use A186's start-up (handover requested at Vo
  1.03 V). A188 raised the request to 1.045 V and that is the adopted start-up. A192, A193 and A194 use 1.045 V.
  A191's RESULTS header says "A186's start-up"; reports/FINAL_SPEC_COVERAGE.md lists the row under "the A188
  start-up", which is not what ran.
- What the request level changes at 125 C: mode P is entered at 131.4 us instead of 129.8 us (S75). The handover
  peak is 184.5 A with 1.045 V (A194 r04, r21) against 188.5 A (A191); S80 182.0 against 185.4 A.
- Steady state before the step (459-499 us), S75 at 125 C: mean valleys -13.7..-14.4 A with 1.045 V (A194 r21)
  against -13.9..-14.6 A (A191 p0); largest peak 149.0 against 149.2 A; ladder voltages equal to 1 mV. A194's hot
  slow draws are milder events (+1.3..+2.7 V, 2.6-19 us), so none of them is this row.
- Runs: A191's 12 (boards S75 and S80, 125 C, +4.8 V / 1 us at 500 us + k T / 6, k = 0..5, lead 9.5 ns), only
  hand_vo_v changed (make_cfgs.py asserts it). Reference: A191, run for run. The steps are at absolute times, so the
  step phases will differ from A191's.

## 2. Criteria (A191's, a187_analyze.run)
 c1 start-up and handover peak <= 200 A.
 c2 post-step peak <= 200 A.
 c3 COMPLETED, 0 shoot-throughs, 0 overlaps, V_DS <= 40 V.
 c7 Vo <= 1.05 V over 0-300 us.
Diagnostics: step phase, late fires on phases 3-4 in the first 30 us after the step, post-step Vo minimum.

## 3. Predictions (not criteria)
- All four pass on all 12. Start-up 136-139 A, handover 184.5 A (S75) and 182.0 A (S80).
- Post-step: S75 192-199 A (A191: 194.1-196.9 A), S80 188-195 A (A191: 190.6-192.8 A). A c2 miss on S75 is
  unlikely but not excluded (about 1 in 10).

## 4. Decision rule
- All pass: FINAL_SPEC_COVERAGE cites A197 for the 125 C slow rows on the final configuration and labels A191's
  figures with their 1.03 V request. No further runs.
- A c2 miss: the final configuration does not hold 200 A on that row at 125 C. The coverage file states it with the
  position and the value. The record is read for the mechanism; any remedy (request level, lead) is a new decision
  with its own number, not run under this one.
- c1, c3 or c7 miss: stated the same way.
