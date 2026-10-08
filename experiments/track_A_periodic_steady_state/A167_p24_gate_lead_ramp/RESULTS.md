# A167 - A164's lead, ramped in after the handover (RESULTS)
Boundary: 06a69fa. Records: release records-a167 (5 runs). Outputs: a167_summary.json (a167_analyze.py, side by side
with A164's run of the same row).

## 0. Verdict
- **Adopted by the decision rule.** The spec's lead is an 8 ns lead on the predictive high-side turn-on, enabled over
  ~20 us after the handover.
  - The L x 0.7 handover is 191.5 A (A164: 218.6 A).
  - The L x 0.7 post-step is as A164: 195.3 A physical / 180.1 A command-time against 192.1 / 177.2 A, with 4 late
    fires, all before 300 us.
  - No regression elsewhere.
- **As registered, 3 of 5 rows pass.**
  - L x 0.7 misses criterion 2 on mode S's 202.5 A, as predicted: the frozen design's open-loop start at L x 0.7,
    already 205.6 A physical with A152's ramps. The handover and everything after it pass.
  - The slow corner misses criterion 3, as in A164-A166.
- **Nominal and hot l_p48_1us pass** with 0 late fires. Their handovers are 147.9 / 148.6 A (A164: 150.6 / 152.0 A),
  and the rest is A164's within 1 A.
- **Slow corner** (3.6 ohm, +1.0 V, Q_G x 1.29):
  - the handover peak falls to 172.9 A (A164: 199.5 A);
  - its late fires rise from 65 to 102, because the lead is small while it ramps in;
  - after the steps it is as A164: ~158 late fires after +4.8 V / 1 us, NEW spikes 4 / 14;
  - peaks <= 183 A, V_DS <= 30.9 V, 0 shoot-throughs.
- **Why the ramp works.** A164's lead is applied to predictive turn-ons only, so mode P's pulses are 8 ns wider than
  mode S's: an on-time step at the handover. Ramped over ~40 periods, the voltage loop and dt_pred follow it. The lead
  is also small while the handover is still settling, which is when the pre runs' collapsed dt_pred shot through.

## 1. Criteria
| row | 1 V_DS | 2 start / Vo | 3 post / late / NEW | 4 Vo |
|---|---|---|---|---|
| nom L07_l_p48_1us | 33.2 V | miss: mode S 202.5 A (handover 191.5 A) | 195.3 / 180.1 A, late 4 | -8.7 mV |
| nom l_p48_1us | 33.7 V | 162.9 A | 181.7 / 171.2 A, late 0 | 8.5 mV |
| hot l_p48_1us | 32.6 V | 162.7 A | 179.9 / 167.5 A, late 0 | 7.1 mV |
| ss l_p48_1us | 30.9 V | 174.7 A | miss: late 260, NEW 4 | -9.4 mV |
| ss s_p62 | 29.0 V | 174.7 A | miss: late 102, NEW 14 | -16.6 mV |

## 2. Limits
- 5 rows; four modules not rerun (A164 / A165's four modules passed with the full lead from the handover).
- The ramp (20 us) was not varied. The interlock is not guaranteed by construction: a dt_pred that collapses after the
  ramp would still meet the full lead.
