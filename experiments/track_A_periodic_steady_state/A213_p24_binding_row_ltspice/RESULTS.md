# A213 - the binding row against LTspice: the slow 0.75 L0 board at 125 C, +4.8 V / 1 us (RESULTS)
Boundary: 58c1f16. Records: release records-a213 (the cosim record, logs); the eight replay comparisons are in
replays/ (numbers only). Analysis: a213_analyze.py -> a213_summary.json. Run from 58c1f16, cosim_sources_modified
False. Plant V6, final configuration, board S75 (slow devices, 0.75 L0) at 125 C, one module. LTspice: EPC's model
on all 20 switches at 125 C with its threshold + 1.0 and its gate capacitances x 1.29, started from the plant's
state, the plant's gate commands, two periods per replay.

## 0. Verdict
- **The binding row's peak holds in LTspice.** The plant's largest peak is 197.57 A (phase 1, 20.0 us after the
  step). Replayed from the three snapshots before and at that peak, LTspice's largest peak is 196.79 / 196.98 /
  197.38 A: 0.2-0.8 A below the plant's. c5 passes on all three.
- **So the 2.4 A margin of A206 may be stated with "LTspice 0.2-0.8 A lower at this corner, two periods at fixed
  commands".** It remains a statement about two models, not hardware, and about one step position.
- **V6's error at this corner is larger than at nominal, in the conservative direction.** One period later the
  phase currents are 1.25-1.96 A lower in LTspice in the settled state and at the step (limit 1.5 A; nominal
  devices: within 0.68 A, A206), and up to 3.0 A lower around the peak; later peaks are up to 3.9 A lower. c2
  misses on all eight replays, c1 on four.
- **The loss books agree here too**: settled, 39.93 / 40.35 / 39.93 W in the plant against 39.74 / 40.35 /
  39.75 W in LTspice (within 0.5 %). This board at 125 C books 40 W per module at full load.
- V_DS agrees within 1.21 V on every replay (c3). Hard turn-ons agree within 0.18 ns and 0.6 V in the settled
  state and at the step; around the peak, turn-ons at lost valleys differ by 2.8-9.6 ns and 8-11 V (c4 misses on
  the three peak replays).
- Identity: the record's 1681 sections equal A206's B_S75_hot_p5 bit for bit.

## 1. Criteria (LTspice minus plant)
| replay | c1 peaks <= 2.0 A | c2 one period | c3 V_DS | c4 hard turn-on | largest peak LT / plant | currents one period later | books plant / LT |
|---|---|---|---|---|---|---|---|
| settled k0 | pass (-1.97) | **miss** | pass | pass | 151.98 / 152.42 A | -1.90 -1.26 -1.42 -1.73 A | 39.93 / 39.74 W |
| settled k1 | pass (-1.96) | **miss** | pass | pass | 150.50 / 152.42 | -1.89 -1.25 -1.48 -1.82 | 40.35 / 40.35 |
| settled k2 | pass (-1.96) | **miss** | pass | pass | 151.97 / 152.41 | -1.90 -1.25 -1.42 -1.74 | 39.93 / 39.75 |
| step k8 | **miss** (-2.02) | **miss** | pass | pass | 174.11 / 174.57 | -1.94 -1.25 -1.47 -1.82 | 40.22 / 40.91 |
| step k9 | pass (-1.86) | **miss** | pass | pass | 172.85 / 174.57 | -1.63 -1.26 -1.42 -1.74 | 41.38 / 43.97 |
| peak k53 | **miss** (-3.81) | **miss** | pass | **miss** | **196.79 / 197.57** | -1.82 -1.79 -0.91 -3.02 | 42.04 / 45.53 |
| peak k54 | **miss** (-3.89) | **miss** | pass | **miss** | **196.98 / 197.57** | -1.95 -2.66 -2.59 -0.30 | 40.03 / 42.75 |
| peak k55 | **miss** (-3.64) | **miss** | pass | **miss** | **197.38 / 197.57** | -1.96 -2.60 -0.20 +0.74 | 37.58 / 40.14 |
- c5: pass on k53, k54, k55. i1: pass.
- The start state arrives within 0.003 A; capacitor 1's voltage is 6.3-7.8 mV off at the start, the replay tool's
  known limit (A206).

## 2. Predictions
- Held: i1; c3 on all eight; c5 (0-4 A below predicted: 0.2-0.8 A); the peak replays miss c2 by up to 3.0 A with
  LTspice the lower one; c1 misses on the peak replays.
- Missed: the settled replays miss c2 (1.9 A; I had it as likely as not); c1 also misses at the step by 0.02 A;
  c4 holds in the settled state and at the step, where I expected 0.3-1 ns of difference.

## 3. Limits
- One board, one temperature, one step position; two periods at fixed commands, open loop: where a closed loop
  on the LTspice circuit would settle is not computed.
- The slow corner in LTspice is the vendor's typical model with three changes (temperature, threshold, gate
  capacitances), mirroring what the plant does to the same parameters. Neither is a measured slow device.
- The cause of the 1.3-2.0 A per period at this corner was not traced (A213 changes no model). Candidates from
  A206: the reverse fit kept at the typical 25 C device, and the high side's reverse conduction before its
  threshold.
