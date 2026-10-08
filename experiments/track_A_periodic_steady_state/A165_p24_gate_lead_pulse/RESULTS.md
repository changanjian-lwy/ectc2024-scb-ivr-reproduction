# A165 - A164's drive spec with the lead as a pulse shift (RESULTS)
Boundary: 55e61d7. Records: release records-a165 (16 runs + cosim_pre). Outputs: a165_summary.json (a165_analyze.py,
side by side with A164), a165_pre.json.

## 0. Verdict
- **Not adopted.** The pulse shift fixes A164's handover step but slows the recovery after the L x 0.7 line step
  (decision rule, second branch).
  - **Handover peaks fall on every board:** nominal 150.6 -> 144.4 A, L x 0.7 218.6 -> 191.5 A, slow corner
    199.5 -> 174.7 A, hot 152.0 -> 145.2 A, ff 147.3 -> 143.5 A.
  - **L x 0.7 after +4.8 V / 1 us: 211.0 A physical, 195.7 A command-time** (A164: 192.1 / 177.2 A). Phase 1
    loses ZVS on the rising step, the known A148 mechanism: its low side turns off at +2 A instead of -15 A, and its
    high side turns on at 15-17 V. In A164 it recovers by ~12-15 us; here it is still at +0.2..+2.6 A at 15 us, and
    the peaks grow to 211 A at 21-22 us. Vo then peaks at +12.8 mV (11.7 mV allowed; A164 -9.0 mV) and takes 35.4 us
    to return within 1 %.
  - Cause: the bridge moves the pulse's edges in the plant. The RTL still times phase 1's low-side turn-off on its own,
    unmoved timeline, so the low side's on-interval grows by the lead and the dlo learning has to absorb it. A
    controller with a real signed dt_pred would move that timeline too. The bridge cannot emulate that, so this is a
    limit of the emulation, not a verdict on signed dt_pred.
- **Four modules pass:** 33.8 V, handover 144.6 A (A164 151.0 A), post-step 185.4 / 174.7 A, 0 late fires.
- **Everything else as A164** (within +-2 A, +-0.6 V, the same edge power):
  - nominal, hot, ff and L x 1.3 rows pass, 0 late fires, 0 shoot-throughs;
  - ff -8 V / 10 us again misses Vo by 0.8 mV (+28.7 mV);
  - L x 0.7 mode S again peaks at 202.5 A (criterion 2), as predicted.
- **Slow corner:** the handover is gentler, but the timing faults stay.
  - 82 late fires in the handover and ~160 after rising line steps; NEW spikes 7-22 after the steps; peaks <= 183 A,
    V_DS <= 31.7 V.
  - The high side was commanded ahead of the low side's turn-off 1650-1940 times per run. The 7.5 ns minimum gate
    delay against the 8 ns lead kept every channel start after the low side's turn-off: 0 shoot-throughs.
  - Three lead variants (A164, A165, A166) leave the line-step late fires alike. The slow corner's hard turn-ons after
    a rising step take up to 16.6 ns, more than any lead below t_drv can cover.
- **Pre runs (a165_pre.json) showed the hazard A166 addresses.** The slow corner at +-10 % with 8 ns, and at +-20 %
  with 12 ns, each stopped on a physical shoot-through on phase 4 (146-153 us), after its dt_pred fell to ~0.

## 1. Criteria
| rows | 1 V_DS | 2 start / Vo | 3 post / late / NEW | 4 Vo | misses |
|---|---|---|---|---|---|
| nom (6) | 6/6 | 5/6 | 5/6 | 5/6 | L07: mode S 202.5 A; post 211.0 / 195.7 A; Vo +12.8 mV (11.7 allowed), back 35.4 us |
| ff (3) | 3/3 | 3/3 | 3/3 | 2/3 | l_m80 +28.7 mV |
| ss (4) | 4/4 | 4/4 | 0/4 | 4/4 | late 82-243, NEW 7-22 |
| hot (2) | 2/2 | 2/2 | 2/2 | 2/2 | |
| four modules | 33.8 V | 162.9 A | 185.4 / 174.7 A, late 0 | - | handover 144.6 A (A164 151.0) |

## 2. Limits
- The pulse shift is a bridge-level emulation (plant edges only). The RTL's internal timeline is unchanged.
- Otherwise as A164 (low sides on ramps, identical devices within a board, lead bounded by t_drv).
