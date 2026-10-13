# A212 - the nominal board's other rows on plant V6 with the present configuration (BOUNDARY)
Method: cosim with the frozen RTL (cfg only) on plant V6. No code change. Track A, main line. Written and committed
before the runs. Looked at beforehand: nothing of these rows on V6 (A206 ran +4.8 V / 1 us only: 179.0 A).
Decision it changes: whether the nominal column of the final-plant coverage table (a V5 result with 3.0 ohm on the
low sides) still stands after the two configuration changes since: low sides at 0.3 ohm with new trims (A206) and
the lower Ton limit at 4.0 ns (A208). A row that fails is reported as "does not hold on V6".
Cheaper check done first: none shorter than the runs. Budget: 8 runs of 620 us, about 50 min each, 3 then more jobs.

## 1. What and why
- Rows, board N0, 25 C, one module, stimulus at 500 us, end 620 us: +4.8 V over 2, 3, 4, 5, 10 us; -4.8 V over
  1 us; -8 V over 10 us; a +62.5 A load step. V5 (A173 / A175, stimulus at 1000 us): 182.9 / 181.8 / 182.5 /
  182.3 / 183.7 A; 172.4 A with 3 restarts and 6 NEW spikes; 166.7 A; 181.4 A.
- The -62.5 A release is A207's 75 % row (regulates; 146.6 A). +4.8 V / 1 us is A206's (179.0 A).
- Not here: the device corners, L x 0.7 / 1.3, four modules, the other boards' rows beyond A206's twelve.

## 2. Criteria (every row)
 c6 as A206: COMPLETED, 0 shoot-throughs, 0 forced edges, whole-run peak <= 200 A, V_DS <= 40 V, Vo <= 1.05 V up
    to 300 us and within 1 V +- 50 mV from 20 us after the handover.
 c7 Vo within 1 V +- 10 mV over the last 20 us.
Reported with them: the post-stimulus peak against V5's, Vo's extremes, late fires after the stimulus, the oracle's
events (a142_oracles.check) by class, and the lowest Ton register after the stimulus (below 22.25 ns the row
depends on the new limit).

## 3. Predictions (not criteria)
- c6 and c7 pass on every row.
- Peaks: rising ramps 177-182 A (V5 minus 1-5 A, as A206 found on 1 us); -4.8 V / 1 us 166-174 A; -8 V / 10 us
  161-168 A; the load step 176-182 A.
- The register stays above 22.25 ns on the rising rows and the load step; the falling rows raise Ton.
- The oracle still reports NEW events on -4.8 V / 1 us (the valley loss on phases 2-4 is the controller's).

## 4. Decision rule
- Every row passes: the coverage table's nominal column is restated with the V6 figures.
- A miss: reported with its record as "the row does not hold on V6"; a remedy is a new experiment.
