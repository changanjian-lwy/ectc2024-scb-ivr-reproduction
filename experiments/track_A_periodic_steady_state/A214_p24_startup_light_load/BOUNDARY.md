# A214 - start-up into less than the full load (BOUNDARY)
Method: cosim with the frozen RTL (cfg only: the load resistance) on plant V6. No code change. Track A, main line.
Written and committed before the runs. Looked at beforehand: nothing of these rows; every start-up of the project
ran into the full 4 mOhm load (A207 lists a start-up into a light load as not run).
Decision it changes: whether the specification must say what load the module may start into. The start-up (mode S)
is open loop with a per-board Ton trimmed at full load (controller item 6); a processor rail usually starts lightly
loaded. Now that 30 % is the minimum load in operation (A210), the same has to hold for the start.
Cheaper check done first: none; mode S's Vo against the load is not in D63. Budget: 5 runs of 300 us, 25-60 min each.

## 1. What and why
- Mode S delivers a fixed on-time at a 200 ns period; Vo follows what the load takes of it. With less load Vo
  rises faster, and the handover is requested once a sample reaches 1.045 V (A188) instead of at 144 us, possibly
  while Vin is still ramping (ramp ends at 137 us). Mode P then starts from that state with its usual seed.
- Rows (A206's board cfgs, ton_min_ns 4.0 ns, the load resistance 4 mOhm / share from t = 0, end 300 us):
  N0 at 25 C with 75, 50 and 30 % of the load; S75 at 25 C and at 125 C with 50 %.
- Not tested: a load that changes during the start, a current-sink load, other boards, four modules, 0 C.

## 2. Criteria (every row; A206's c6)
 c6 COMPLETED, 0 shoot-throughs, 0 forced edges, whole-run peak <= 200 A, V_DS <= 40 V, Vo <= 1.05 V up to 300 us
    and within 1 V +- 50 mV from 20 us after the handover.
Reported with it: when the handover is requested and Vin there, Vo's maximum and its time, the start-up and
handover peaks, the Ton register and Vo at the end.

## 3. Predictions (not criteria)
- The handover is requested by Vo on every row: around 125-135 us at 75 %, 95-115 us at 50 %, 65-85 us at 30 %,
  the last two before Vin's ramp ends.
- c6 passes at 75 % (Vo at most 1.05 V; the full-load start reaches 1.034-1.048 V). At 50 and 30 % it fails on Vo
  (above 1.05 V after the handover: mode P enters with a seed made for full load and a Ton that cannot fall fast
  enough), on N0 and on S75. Peaks stay under 200 A and V_DS under 40 V everywhere.
- At the end every row regulates at 1 V (the loads are all at or above the 30 % floor).

## 4. Decision rule
- Every row passes: the start is covered from 30 % to 100 % of the load on these boards.
- A row fails: the specification states the smallest load tested to start cleanly, and the failure goes on the
  controller's list under the start-up item (item 6) with its record; a remedy needs RTL or a new seed rule.
- A peak or V_DS failure is reported first.
