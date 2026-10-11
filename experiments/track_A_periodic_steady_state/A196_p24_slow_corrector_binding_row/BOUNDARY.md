# A196 - the slow boards' corrector setting on the binding row (BOUNDARY)
Method: cosim, plant V5, cfg only (two registers of the frozen controller's high-side turn-on corrector: dt_step_ns
0.2828 -> 0.0625, err_shift 1 -> 2; no RTL or plant code change)
Track A, package layer. Written and committed before the runs. A195's five records were looked at beforehand
(RESULTS 299ba60); no run of this setting with a line step exists.
Decision it changes: whether slow boards get a per-class corrector setting, as they have a per-class lead. It is
worth a setting only if it widens the slow corner's margin (2.2 A: 197.8 A on S75 at 0 C, A193).
Cheaper check done first: none possible. D63 has no dt_pred block (its listed blind spot), and A195 measured steady
state only (largest steady peak -0.9 A, handover +6.0 A on S0).
Budget: 6 runs of 900 us, --jobs 6 beside A194, about 2.5 h.

## 1. What and why
- A195: slow boards alternate by 4-7 A from one cycle to the next because the corrector hunts; step 0.0625 ns with
  late gain 1/4 removes it on S0 at 25 C (0.3-0.85 A). Its decision rule asks for the slow rows and a rising step
  before adoption.
- The slow corner's post-step peak moves 1.3-3.3 A with the step position inside one period (A192, A193). If the
  step landing on a deep or a shallow cycle is part of that, removing the orbit lowers the worst case. Against it:
  the setting's valleys are 1.1-1.2 A deeper on average, and the corrector now follows a transient four times
  slower upward and two times slower downward. A143 traced a 254 A oscillation to this corrector's dynamics.
- Runs: board S75 (slow devices, L x 0.75), +4.8 V / 1 us at 500 us + k T / 3, k = 0, 1, 2, at 0 C and 25 C. The
  cfgs are A193's and A192's with only the two registers changed (make_cfgs.py asserts it). Reference: those
  records, same step positions.
- Not tested here: -40 and 125 C, S0 and S80, falling steps, load steps, slower ramps, four modules.

## 2. Criteria
 c1 every run COMPLETED, 0 shoot-throughs, 0 overlaps, V_DS <= 40 V.
 c2 physical peak <= 200 A over the whole run, every phase (start-up, handover, before and after the step).
 c3 Vo <= 1.05 V over 0-300 us.
 c4 the orbit is gone on S75: mean cycle-to-cycle valley change <= 1.0 A on every phase over 459-499 us
    (reference 4.7-5.9 A).
 c5 the margin widens: at each temperature the worst post-step peak of the three positions is <= 195.5 A
    (reference 197.8 A at 0 C, 197.1 A at 25 C; 195.5 A doubles the 2.2 A margin), and no position is more than
    1.0 A above its reference.
Diagnostics, no criterion: handover peak, post-step late fires, oracle NEW events, Vo extreme, time back within
1 %, spread over the positions.

## 3. Predictions (not criteria)
- c1-c3 pass. Handover 156-162 A (reference 150.7 / 154.0 A; S0 moved +6.0 A).
- c4 passes at 25 C (step alone left 1.1-1.4 A on S75); at 0 C the orbit is larger, 0.5-1.5 A left.
- c5 is open, about even odds. Worst post-step peak 193-199 A at both temperatures. The spread over the positions
  falls below 1.5 A at 0 C (reference 3.3 A) if the orbit is what makes the position matter.

## 4. Decision rule
- c1-c5 pass: a second stage with its own number checks the setting for harm before the user is asked whether to
  adopt it: S75 at -40 and 125 C, S80 at 125 C, S0's falling and load rows, and a 4 us ramp (A143's row), at most
  12 runs. The controller's register values were frozen by the user's decision; adoption is theirs.
- c1-c4 pass, c5 fails: not adopted. The orbit is removable but the margin does not widen. FINAL_SPEC_COVERAGE
  states the orbit as a slow-corner property and names the setting as a known remedy for the alternation only.
  No further runs on this line.
- c4 fails: the setting does not carry to the binding board. Same statement, no further register search.
- c1, c2 or c3 fails: the setting is unsafe on this row; recorded as such, not adopted.
