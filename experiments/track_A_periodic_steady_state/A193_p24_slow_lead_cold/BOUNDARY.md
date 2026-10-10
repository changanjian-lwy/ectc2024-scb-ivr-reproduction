# A193 - the slow boards' 9.5 ns lead below 25 C, +4.8 V / 1 us (BOUNDARY)
Method: mixed (cosim, plant V5, code cfe581f; cfg: A190's cold start-up cfgs with the step, end time and lead changed)
Track A, package layer. Written and committed before the runs.
Decision it changes: whether the slow boards' 9.5 ns lead (adopted by A192) holds over the spec's -40..125 C, or needs a
temperature condition. FINAL_SPEC claims the start-up at -40 / 0 C (A190, runs end at 200 us). Mode P after a step has
not been run cold on any board, with either lead.
Cheaper check done first: records and the device model. A192: at 25 C the 9.5 ns lead costs S75 3-5 A on +4.8 V / 1 us
(195.8-197.1 A, margin 2.9 A), through deeper valleys; why is not traced. The slow device model gives no direction
cold: V_th rises (2.49 -> 2.63 V at -40 C) and gain rises (A1' 73 -> 87). Budget: 9 runs, --jobs 9, ~1.3 h.

## 1. What and why
- The thinnest slow row with 9.5 ns is S75 (L x 0.75) +4.8 V / 1 us. If cold moves it like 25 C moved it from 125 C,
  it crosses 200 A.
- Runs (S75, A188 start-up, A190's cold trim table: 35.982 ns at 0 C, 36.892 ns at -40 C; seed 45.355 ns; t_il 1.0 ns;
  steps at 500 us + k T / 3, k = 0, 1, 2 (A184 / A192's positions), end + 400 us):
  - lead 9.5 ns at -40 C and at 0 C;
  - lead 8 ns at -40 C (the reference, and the fallback if 9.5 fails).
- Not tested: other rows cold; S0 / S80 / four modules cold; nominal boards cold after a step.

## 2. Criteria (per run, a192_analyze definitions)
 c1 start-up / handover <= 200 A;  c2 post-step <= 200 A;  c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs / overlaps;
 c7 Vo <= 1.05 V over 0-300 us.
Diagnostic: late fires, NEW events, Vo extreme and recovery; against A192 (25 C, 9.5 ns) and A184 (25 C, 8 ns).

## 3. Predictions (not criteria)
- c1, c3, c7 pass (A190: cold handovers <= 166.3 A).
- Post-step: no direction from the model. Registered band: 9.5 ns 191-203 A, 8 ns 188-200 A at -40 C. Uncertain
  whether 9.5 ns at -40 C clears 200 A.

## 4. Decision rule
- 9.5 ns passes c1-c3 and c7 at -40 and 0 C at all three positions: the slow lead holds over -40..125 C on this row
  (tested points). FINAL_SPEC states it.
- 9.5 ns fails c2 cold and 8 ns passes at -40 C: the slow lead needs a temperature condition (9.5 ns only above a
  stated temperature, which needs a sensor). Named; the crossover is not located here. The slow L x 0.75 tolerance
  is stated per temperature.
- Both fail at -40 C: slow L x 0.75 does not hold +4.8 V / 1 us at -40 C with either lead. Stated per temperature.
- c1 or c3 fails anywhere: reported first.
