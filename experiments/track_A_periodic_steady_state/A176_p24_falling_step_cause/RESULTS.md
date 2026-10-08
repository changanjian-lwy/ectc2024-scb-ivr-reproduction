# A176 - what turns the falling-step valley loss into restarts on the final plant (RESULTS)
Boundary: 0aac286. Records: release records-a176 (run_*.json, run log). Analysis: a176_analyze.py ->
a176_summary.json (a142_oracles after the step; a168_analyze.safe_stats; phase 2-4 valley maxima over step + 45 us).
All runs from committed code.

## 0. Verdict
- **Outcome 3, the combination** (as predicted). The restarts and spikes appear only on the full final plant.
  Neither the lead with ideal low sides (v2lead) nor the gate-driven low sides with the interlock and no lead
  (v5nolead) shows a single post-step event on either row.
- The valley loss itself is the same in all variants: phase 2-4 valleys reach +12..+37 A (nom -4.8 V) and
  +30..+95 A (ff -8 V) after the step. What differs is whether the controller's next predicted turn-on is still
  valid. With the lead, the high side's turn-on comes 8 ns earlier. With gate-driven low sides, the low side
  still conducts for up to ~4.7 ns after its command (A169). Only together do they put the turn-on into the window
  where the controller restarts (K3, how 3). The -4.8 V row restarts with 0 interlock holds, so these events need
  no overlap. This is A169's mechanism without a shoot-through.
- The final plant's +5 A post-step peak and +2.5 mV Vo on ff -8 V against V2 (A173 / A174) come from the
  gate-driven low sides, not the lead (v5nolead 181.7 A / 30.8 mV; v2lead 177.0 A / 28.2 mV; final 181.5 A /
  31.1 mV).

## 1. Criteria
| row | variant | post-step events | post (A) | Vo extreme / back | valley max ph 2-4 (A) | holds |
|---|---|---|---|---|---|---|
| nom -4.8 V / 1 us | final (A175) | 3 K3 + 6 NEW | 172.4 | -10.2 mV / 2.7 us | 12.4 / 25.0 / 34.5 | 0 |
| | v2lead | none | 161.6 | -9.6 / 0 | 12.7 / 12.8 / 30.8 | - |
| | v5nolead | none | 166.6 | -12.5 / 3.2 | 15.1 / 13.7 / 36.8 | 0 |
| ff -8 V / 10 us | final (A173) | 1 K3 + 1 NEW | 181.5 | 31.1 / 24.9 | 32.9 / 70.5 / 94.6 | 6 |
| | v2lead | none | 177.0 | 28.2 / 22.3 | 29.5 / 63.5 / 85.0 | - |
| | v5nolead | none | 181.7 | 30.8 / 22.8 | 33.3 / 70.9 / 95.1 | 0 |

Criterion 1 (v2lead events on both rows): no. Criterion 2 (v5nolead events on both rows): no. So criterion 3.
v2lead ff reproduces A164's run of the row (177.0 vs 176.9 A, 28.2 vs 28.5 mV): the ramped lead changes only
the handover.

## 2. Limits
- Two rows, one step position each. A174 showed the ff spike at 2 of 5 positions, so "none" on a variant is one
  sample of a phase-dependent event.
- The fix this points to, a lead that is held off while a phase's valley is lost (direction- or valley-aware),
  needs an RTL change. It is not run (RTL frozen).
