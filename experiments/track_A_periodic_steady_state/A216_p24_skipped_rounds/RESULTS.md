# A216 - skipped rounds: one module regulates below its lower Ton limit (RESULTS)
Boundary: c4b810a (branch a216-skip, merged into main with db7efde). Records: release records-a216 (11 cosim records,
logs). Analysis: a216_analyze.py -> a216_summary.json. Runs from c4b810a, cosim_sources_modified False. Final
configuration on plant V6 (low sides 0.3 ohm x the board's factor, A206's trims, ton_min_ns 4.0 ns, ton_lat 16),
skip hi 5 mV / lo 1 mV, one module, load released at 300 us, end 450 us (+62.5 A row: re-applied at 380 us).

## 0. Verdict
- **Skipping regulates a module below its lower limit, but is not adopted as it is**: s3 misses by more than 5 A
  (decision rule), so the resume was reworked (A217, A220).
- **Regulation (s1, s2, s4) holds on all seven rows.** N0 with no load ends at 1.0011-1.0069 V (before: 1.56 V with
  the old limit, A207), N0 10 % at 0.9989-1.0078 V, N75 10 % at 0.9992-1.0089 V; Vo's mean sits 2.3-4.2 mV above 1 V
  while skipping. +62.5 A out of skipping at 5 %: peak 58.66 A, Vo 0.9905-1.0053 V. Peaks <= 181.1 A, V_DS <= 31.2 V,
  no late fire. Semiconductor loss 0.53 W at no load, 2.59 / 2.44 W at 10 % (N0 / N75; 25 W out).
- **s3 misses on the three skipping rows**: N0 no load -39.7 A (phase 4), N0 10 % -4.4 A (phase 4), N75 10 % -27.4 /
  -6.4 A (phase 3), band -20..-12 A. Cause (A217, A220): the resume's first valleys and the alternation they start.
- **The slow board does not skip at 10 %**: its Ton register stays at 6.9-7.1 ns (25 C) / 5.4 ns (125 C), above the
  4.0 ns limit, at about 8.25 MHz; 13.67 / 12.72 W of loss for 25 W out. N0 at 20 % skips only in the release's
  transient (2 pauses) and regulates as before.
- **The raised limit on the slow board (information, 20.78 ns, 30 %) skips but misses s2**: Vo 0.9937-1.0144 V, and
  valleys up to +7.0 A (no zero-voltage turn-on); loss 10.85 W against A211's 17.57 W. Not adopted; the slow board's
  light-load loss is left to shedding whole modules (decision rule).
- **Large re-applications break 200 A on V6** (information; problem 9): +200 A from 20 % without skipping 249.83 A,
  Vo down to 0.9456 V, 140 late fires; +237.5 A from 5 % with skipping 235.37 A, Vo 0.9482 V, 26 late fires
  (records cosim/run_w_N0_25_20_up_ns.json, run_w_N0_25_5_up.json). The loop's upper Ton limit (twice the seed)
  bounds nothing at these steps; the specification's load step stays 62.5 A.

## 1. Criteria
| row | s1 | s2 | s3 | s4 | Vo, last 20 us | valleys, last 20 us (A) | rounds / ticks | loss |
|---|---|---|---|---|---|---|---|---|
| N0 no load | pass | pass | **miss** | - | 1.0011-1.0069 V | -39.7 .. -16.9 | 6 / 92 | 0.53 W |
| N0 10 % | pass | pass | **miss** | - | 0.9989-1.0078 V | -21.0 .. -4.4 | 57 / 50 | 2.59 W |
| N0 20 % | pass | pass | pass | - | 0.9997-1.0003 V | -16.3 .. -13.8 | 104 / 0 | 3.39 W |
| N75 10 % | pass | pass | **miss** | - | 0.9992-1.0089 V | -27.4 .. -6.4 | 46 / 70 | 2.44 W |
| S75 25 C 10 % | pass | pass | pass | - | 0.9997-1.0000 V | -17.1 .. -13.8 (no skip) | 166 / 0 | 13.67 W |
| S75 125 C 10 % | pass | pass | pass | - | 0.9999-1.0002 V | -16.7 .. -14.5 (no skip) | 166 / 0 | 12.72 W |
| N0 5 %, +62.5 A | pass | pass | pass | pass | 1.0001-1.0003 V | -16.7 .. -15.1 | 85 / 0 | 4.12 W |
- i1: unit tests 100 of 100, regression quick and full bit for bit. i2: A215's +62.5 A row with skip configured gives
  the same sections, edge log and gate records (1621 sections, no tick).
- A216's s3 passes a row with no turn-off in its 20 us; no criteria row here had none.

## 2. Predictions
- Held: s1 and s2 on all seven rows; Vo's mean 2-4 mV above 1 V (4.2 on N75); +62.5 A out of skipping 57-63 A
  (58.66); N0 at 20 % skipping only in the transient; s3 missing on phases 2-4; the large re-applications over
  200 A; the raised limit's band (20.7 mV peak to peak) and loss (-38 %).
- Missed: the +62.5 A dip (9.5 mV, not 12-16); the slow board (it never reaches the limit); N0's no-load phase 4
  (-39.7 A, far outside the expected few amperes).

## 3. Limits
- One module, one step position, 25 C on the nominal boards; four modules not run (the slaves do not follow a pause).
- The idle phases ring without damping in V6 (A220): the valleys after a resume depend on it.
