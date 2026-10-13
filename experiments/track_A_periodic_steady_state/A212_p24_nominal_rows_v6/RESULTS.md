# A212 - the nominal board's other rows on plant V6 with the present configuration (RESULTS)
Boundary: 21161e0. Records: release records-a212 (8 cosim records, logs). Analysis: a212_analyze.py ->
a212_summary.json. Runs from 21161e0, cosim_sources_modified False. Board N0, 25 C, one module, final configuration
on plant V6 with low sides at 0.3 ohm, A206's trim and ton_min_ns 4.0 ns; stimulus at 500 us, end 620 us.

## 0. Verdict
- **All eight rows hold on V6** (c6 and c7): peaks <= 184.1 A, V_DS <= 33.3 V, 0 shoot-throughs, no late fire after
  any stimulus, Vo within 26.5 mV of 1 V and back within 0.5 mV at the end.
- **The peaks sit within 3 A of V5's, not below them**: +4.8 V over 2 / 3 / 4 / 5 / 10 us 184.1 / 184.0 / 182.9 /
  183.4 / 183.8 A (V5 182.9 / 181.8 / 182.5 / 182.3 / 183.7); -4.8 V / 1 us 171.7 A (172.4); -8 V / 10 us 169.5 A
  (166.7); +62.5 A 181.5 A (181.4). The rising rows' largest peak comes 26-29 us after the step, on phase 1.
- **The falling step keeps its known oracle events**: -4.8 V / 1 us shows 3 K3 restarts and 3 NEW events (V5: 3
  restarts, 6 NEW spikes). Phases 2-4 losing their valley is the controller's, not the plant version's.
- **One row uses the new limit**: after -8 V / 10 us the Ton register goes down to 20.44 ns, below the old
  22.25 ns limit. With the old limit that row would have been clamped there; it was not rerun that way.
- With A206's twelve rows, A207's 75 % row and these, the nominal L0 column of the coverage table is on V6.

## 1. Criteria
| row | c6 | c7 | peak after the stimulus | V5 | Vo - 1 V after | register after | oracle after |
|---|---|---|---|---|---|---|---|
| +4.8 V / 2 us | pass | pass | 184.10 A (phase 1, +25.6 us) | 182.9 A | -6.6 / +8.0 mV | 28.75-36.34 ns | - |
| +4.8 V / 3 us | pass | pass | 184.00 A (+26.3 us) | 181.8 | -6.5 / +8.1 | 28.72-36.41 | - |
| +4.8 V / 4 us | pass | pass | 182.90 A (+26.9 us) | 182.5 | -4.9 / +7.5 | 28.69-35.91 | - |
| +4.8 V / 5 us | pass | pass | 183.43 A (+26.9 us) | 182.3 | -9.1 / +9.9 | 28.66-37.44 | - |
| +4.8 V / 10 us | pass | pass | 183.77 A (+28.7 us) | 183.7 | -9.3 / +9.9 | 28.34-37.97 | - |
| -4.8 V / 1 us | pass | pass | 171.68 A (phase 4, +41.1 us) | 172.4 | -9.1 / +2.9 | 32.88-37.66 | 3 K3, 3 NEW |
| -8 V / 10 us | pass | pass | 169.53 A (phase 4, +7.3 us) | 166.7 | -26.5 / +21.4 | 20.44-41.53 | - |
| +62.5 A | pass | pass | 181.54 A (phase 4, +68.2 us) | 181.4 | -15.0 / +0.3 | 32.88-41.84 | - |
- V5's figures are the coverage table's (A173, A175: stimulus at 1000 us, 3.0 ohm on the low sides).

## 2. Predictions
- Held: c6 and c7 on every row; -4.8 V / 1 us (166-174 A) and the load step (176-182 A); the register above the old
  limit on the rising rows and the load step; NEW events on -4.8 V / 1 us.
- Missed: the rising ramps, which I put 1-5 A below V5 (177-182 A) from A206's 1 us row: they are 0.1-2.2 A above;
  -8 V / 10 us (161-168 A: 169.5 A); and "the falling rows raise Ton": after the -8 V ramp the register dips
  to 20.44 ns.

## 3. Limits
- One step position per row, 120 us after it; nominal board at 25 C only. The other columns of the coverage table
  (device corners, L x 0.7 / 1.3, four modules) remain V5 results with 3.0 ohm on the low sides.
