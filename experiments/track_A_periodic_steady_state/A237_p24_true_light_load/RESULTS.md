# A237 - light load as a true current: releases to 0 / 2 / 10 % without the 4 mOhm base (RESULTS)
Boundary: 36cbeb2 (runs from it, cosim_sources_modified False). Records: release records-a237 (8 cosim records, logs).
Analysis: a237_analyze.py -> a237_summary.json; figure a237_figure.py -> a237_light_load.png. Plant V7, one module,
final configuration, 25 C except S75h (125 C); release from 250 A at 300 us. References: A229's records on the 4 mOhm base.

## 0. Verdict
- **g0 misses, as predicted: a release to a true no load never comes back down.** N0 peaks +57.6 mV and is still at
  1.0576 V 450 us later (above 1.05 V for 447 us); N75 +46.0 mV, 1.0460 V at the end. Below the lower Ton limit the
  module pauses and nothing discharges Co. On the 4 mOhm base ("no load" = 0 A at 1 V, 250 A/V above) the same N0
  release is above 1.05 V for 1.9 us and back within 1 % after 35.1 us. **The coverage's "N0 with no load regulates at
  1.0017-1.0049 V" (A221 / A222) holds only for a load that sinks above 1 V. Item 6b widens to every overshoot at a
  near-zero load, not only the start-up.**
- **5 A (2 %) comes back by the load alone:** +56.6 mV, above 1.05 V for 7.4 us, within 1 % after 47.5 us (from +56.6 to
  +10 mV at 5 A on 4.67 mF takes 43.5 us). After that it skips at 1.0007-1.0090 V (mean 1.0048 V).
- **25 A (10 %) is as the reference:** back within 1 % after 11.7 / 8.6 us (N0 / N75; reference 10.1 / 7.4 us).
  Skipping valleys −16.0..−13.5 / −16.5..−13.7 A (reference −15.9..−14.3 / −16.2..−14.7 A), Vo 0.999-1.007 V.
- **Re-applications: N0 161.5 A (reference 159.8), S75 125 C 152.6 A (153.7), N75 171.1 A (159.6): g4 misses by 1.5 A.**
  - Traced (figure, lower panels): the same swing in both arms. After the step, phase 2's turn-on delay falls from
    16 ns to 0-4 ns within 4 us (A143's mechanism), its valleys swing up to +55 A, and the delay climbs back at about
    0.28 ns per early report over about 30 us.
  - The current load does not ease as Vo falls, so the dip is 6.7 mV deeper (−30.2 against −23.5 mV), and phase 2's
    peak per 2 us window is higher in 14 of 16 windows (median +6.5 A, −13.7..+33.8 A). 171.1 A is its worst single period, at 397.7 us (+17.7 us), after a turn-on
    at +0.6 A with no reversal. Not a new mechanism; 29 A under 200 A. A229 already saw this peak move by 10 A between arms.
- **VRD 11.1 as a yardstick:** every N0 release from full load peaks near its 50 mV, with either load (+49.3..+57.6 mV here,
  +46.7..+52.5 mV on the base); the time above it is what the load decides. The guideline's regulators use a load
  line, but ours regulates 1.0 V at every load, so this is a comparison, not a pass / fail.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| g0 | 0 A rows: Vo within 1 % over the last 20 us | **miss** (1.0576 / 1.0460 V) |
| g1 | every row: completes, peak <= 200 A, V_DS <= 40 V, no overlap / shoot-through | pass (8 / 8) |
| g2 | rows > 0 A: Vo within 1 % over the last 20 us | pass (6 / 6) |
| g3 | 25 A rows: skipping run test and valleys in −20..−12 A | pass (2 / 2) |
| g4 | re-applications: peak <= 200 A and <= reference + 10 A | **2 / 3: cw5_N75 171.1 A (reference 159.6 A)**; traced, Section 0 |
| id | regression quick + full PASS (fresh outputs), option absent | pass |

## 2. Predictions
- Held: 0 A ends above 1.03 V; N75's 0 A peak (+46.0 mV); 5 A back in 30-60 us (47.5); 25 A back within 15 us; N0 and
  S75 re-application peaks within 5 A (+1.7 / −1.1 A); S75's dip (+0.6 mV).
- Missed: N0's 0 A peak +57.6 mV (predicted 45-55); N75's 25 A upper valley +1.03 A (within 1 A predicted); N75's
  re-application +11.5 A (within 5 A); the dips 6.7-6.8 mV deeper on N0 / N75 (0-5 mV predicted).

## 3. Limits
- One module, one release instant per row, instantaneous load steps; no start-up into these loads (A230 did 1 kOhm),
  four modules, or N0 / N75 at other temperatures.
- That a processor load is a current rather than a resistor is our assumption; VRD 11.1 states no test-load conductance.
