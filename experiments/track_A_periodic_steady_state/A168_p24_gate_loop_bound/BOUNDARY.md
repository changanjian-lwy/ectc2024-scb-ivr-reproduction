# A168 - the power-loop bound under the adopted gate drive (BOUNDARY)
Method: mixed (EPC2067 gate model, D79; plant cosim/gate.py; frozen RTL controller; cfg only)
Track A, package layer. Written and committed before the calibration and the runs.
Decision it changes: the loop bound in the package spec. Today it reads "50 pH, ~50-60 pH at most". 50 pH is
measured (A164 / A167); 60 pH is interpolated; 75 pH was judged from single edges, before A167's ramped lead.
Cheaper check done first: a168_pre.py (single gate-driven edges, A145 state, 8 s) -> a168_pre.json.
- Fast corner, 17 V hard turn-on (+4.8 V line step), peak V_DS:

  | loop | 3.0 ohm | 3.5 ohm | 4.0 ohm | strong-sink turn-off 200 / 260 A |
  |---|---|---|---|---|
  | 50 pH | 37.0 V | 35.1 V | 33.4 V | 24.6 / 32.1 V |
  | 60 pH | 38.5 V | 36.5 V | 34.8 V | 27.7 / 36.1 V |
  | 75 pH | 40.4 V | 38.4 V | 36.6 V | 32.2 / 41.8 V |

- A164's cosim fast corner reached 38.5 V at 50 pH / 3.0 ohm (ff_l_p48_1us), 1.5 V above the single edge.
- The slow corner's turn-on delay (17 V) is 8.0 / 9.3 / 10.5 ns at 3.0 / 3.5 / 4.0 ohm, the same at every loop.
Budget: 12 start-up calibrations to 150 us, then 13 runs to 1400 us (~3 h at 10 jobs).

## 1. What and why
- The adopted drive: r_on R / r_off 0.3 ohm +-20 %, an 8 ns turn-on lead ramped in over 20 us after mode P, and a
  per-board start-up trim (two stages as in A164: a start-up run, then ton = ton0 + (1.035 - Vo) / 0.026).
- Configurations (loop, R) and rows. Boards and corners are A164's. ss = threshold +1.0 V, Q_G x 1.29, driver x 1.2.
  - P60 (60 pH, 3.0 ohm), the spec as it stands: ff l_p48_1us, nom L07_l_p48_1us, nom l_p48_1us, ss l_p48_1us.
  - Q60 (60 pH, 3.5 ohm), the fallback if P60 passes 40 V: ff l_p48_1us, nom L07_l_p48_1us, ss l_p48_1us, ss s_p62.
  - Q75 (75 pH, 4.0 ohm; ss at 4.8 ohm): ff l_p48_1us, nom L07_l_p48_1us, nom l_p48_1us, ss l_p48_1us, ss s_p62.
- Reference: the same row at 50 pH / 3.0 ohm, A167's run where it exists, otherwise A164's (ff l_p48_1us).
- Not tested: four modules, the hot corner, falling ramps beyond A152's matrix (260 A excursions).

## 2. Criteria (each row, against its 50 pH reference)
1. Whole-run max V_DS <= 40.0 V.
2. Vo(143.5 us) within 1.035 +- 0.02 V. Physical start-up and handover peaks <= 200 A, or <= ref + 3 A where the
   reference is above 197 A (L x 0.7's mode S, 202.5 A).
3. Post-step:
   - physical peak <= 200 A and <= ref + 5 A;
   - 0 NEW oracle events, 0 overlaps, 0 shoot-throughs, COMPLETED;
   - late fires <= 1.5 x ref + 5.
4. Vo: |extreme| <= |ref| + 2 mV; where |extreme| > 11 mV, back within 1 % <= ref + 2 us.

## 3. Predictions (not criteria)
- P60: ff V_DS 40.0 V (39.3-40.7); peaks within +-2 A of 50 pH; late fires as 50 pH +-5 (the delay does not depend on
  the loop); edge power +0.1-0.2 W per module.
- Q60: ff V_DS ~38.0 V; ss late fires ~1.2 x the reference.
- Q75: ff V_DS ~38.1 V; ss late fires 1.3-2 x the reference; peaks within ref + 3 A; edge power +0.5-1 W per module.

## 4. Decision rule
- P60 passes: the loop bound is 60 pH with the drive unchanged.
- P60 misses only criterion 1 and Q60 passes: 60 pH needs 3.5 ohm. The spec lists 50 pH / 3.0 ohm and 60 pH / 3.5 ohm.
- Q75 passes: 75 pH is open at 4.0 ohm +-20 %, and D79's "~50-60 pH" is revised. Q75 misses: the bound stays at
  60 pH (or 50 pH), with the reason named (timing: criterion 3; overshoot: criterion 1).
- Edge power is reported as the price, not judged.
