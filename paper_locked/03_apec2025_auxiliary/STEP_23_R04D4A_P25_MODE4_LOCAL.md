# Step 23 - R04D4A P25-native local Mode 4

## Source and event boundary

- Start (`P25 t3`): `iL2=0` and begins moving negative.
- Conducting low sides in the source nP=3 case: `SL1`, `SL2`, `SL3`.
- Other-phase contract: `iL1>0` and `iL3>0`, both decreasing. Their numerical
  values are not reported and are not invented in the local phase-2 replay.
- End (`P25 t4`): controller turns `SL2` off when `iL2` reaches the selected
  negative target.
- P25-native design target: 5% of phase peak. The Mode-4 textual 10% upper
  boundary remains stored but is not used in this baseline.

## Paper-native parameters used

- Vin=12 V, Vo=1 V, Pout=200 W, nP=3, nM=3.
- L2=22 nH, winding resistance=0.5 mOhm.
- Two parallel GS61008T low-side switches: typical effective Ron=3.5 mOhm.
- Derived phase peak: `2*(200 A)/(3*3)=44.4444 A`.
- Five-percent negative target: `-2.22222 A`.

## Result

- `SL2` gate-off / P25 t4: 49.1084 ns after the `iL2=0` entrance.
- Current at the gate event: -2.22231 A.
- The local Mode-4 boundary is reproduced.

## Claim limit

This run validates only the phase-2 negative-current build interval. It does
not claim a full three-phase periodic state because P25 does not report the
numerical `iL1(t3)` and `iL3(t3)` values. Mode 5 commutation begins only after
this accepted t4 exit and must add the high-side/low-side capacitance network
as a separate stage.
