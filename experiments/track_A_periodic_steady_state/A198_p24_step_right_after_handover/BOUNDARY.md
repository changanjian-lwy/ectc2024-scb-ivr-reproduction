# A198 - the worst row right after the handover (BOUNDARY)
Method: cosim, plant V5, one module, final configuration (a194 make_cfgs.board: A188 start-up, lead by class, t_il
1.0 ns); cfg only, no RTL or plant code change
Track A, package layer. Written and committed before the runs. A194's records were looked at beforehand.
Decision it changes: what the specification says about a line step shortly after start-up. Either "+4.8 V / 1 us
is covered from 2 us after the handover", or a stated hold-off (a power-good delay) before which the 200 A budget
is not guaranteed.
Cheaper check done first: none. D63 has no start-up, lead or gate delay. A194's draws would have been the cheap
check, and none landed there.
Budget: 15 runs of 333-424 us = 6.2 run-equivalents of 900 us, --jobs 10 after A197, about 1.2 h.

## 1. What and why
- A194 drew 14 events from 146-300 us to cover the 20 us lead ramp and the settling after the handover, where
  A142's defect was on V0. The earliest landed 37.2 us after mode P's entry, and all 14 were milder than the worst
  known row (largest rising step on S75 / S80: +2.7 V). So the first 37 us are not covered at all, and 37-145 us
  only for mild events.
- Every existing +4.8 V / 1 us run on V5 steps at 500 or 800 us, 356 us or more after the handover.
- The handover has its own peak: 184.5 A on S75 at 125 C (about 19 us after the entry), 154.0 A on S75 and
  165.4 A on N0 at 25 C. The settled row adds about 45 A to a 150 A steady peak (S75: 194-198 A). If the two
  coincide, 200 A is exceeded.
- Runs: +4.8 V / 1 us at 2, 10, 20, 40 and 80 us after mode P's entry, on S75 at 125 C (entry 131.4 us), S75 at
  25 C and N0 at 25 C (entry 144.0 us). End 200 us after the step. 15 runs.
- Not tested: other boards and temperatures, falling steps and load steps in this window, four modules.

## 2. Criteria (A194's, a194_analyze.run)
 c1 COMPLETED, 0 shoot-throughs, 0 overlaps.
 c2 physical peak <= 200 A over the whole run.
 c3 V_DS <= 40 V.
 c4 Vo within 1 V +- 50 mV from 20 us after the handover.
 c5 Vo back inside 1 % at most 60 us after the step ends, and inside from there on.
Diagnostics: the peak after the step with its phase and time, late fires, oracle NEW events.

## 3. Predictions (not criteria)
- c1 and c3 pass on all 15.
- N0: c2 passes at every instant (165-195 A).
- S75 at 25 C: 190-205 A; a c2 miss at one or two of the first three instants is likely.
- S75 at 125 C: 195-215 A; c2 misses at 2 to 4 of the five instants, the largest where the step's peak (about
  24 us after the step) meets the handover's own (about 19 us after the entry), so near the 2 us instant.
- At 80 us every board is within 3 A of its settled value.
- c4 passes; c5 may miss on S75 at the early instants (the loop is still settling).

## 4. Decision rule
- All 15 pass c1-c3: the coverage file states the row as covered from 2 us after the handover on these boards.
- c2 or c3 misses: the coverage file states a hold-off for this row: the earliest tested instant from which every
  later tested instant passes on all three boards, with the largest value before it. No remedy is run under this
  number. A change of the start-up or of the controller to remove the hold-off is a new decision.
- c1 miss (not completed, a shoot-through): read the record first; stated as a failure of the configuration, not
  as a hold-off.
