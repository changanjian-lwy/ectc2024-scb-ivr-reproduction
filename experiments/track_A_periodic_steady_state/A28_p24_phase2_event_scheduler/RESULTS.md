# A28 results - P24 2% event scheduler

LTspice completed normally. `SL2` released at 16.66748 ns, but the current at
release was -6.5405 A, or 5.23% of the 125 A peak. Therefore the labelled P24
2% boundary was **not** captured: the controller inhibited release until the
preceding `TON` support interval ended, by which time current had overshot the
-2.5 A target. The phase-2 event controller armed, but
`Vds(SH2)` never reached zero; its minimum after release was 4.3713 V at
19.4043 ns. Consequently `SH2` correctly remained off and all SH2 turn-on/off
measurements failed by design.

Status: **PHYSICAL BOUNDARY FAIL / CONTROLLER GUARD PASS**.

The result must not be repaired by moving the clock or changing a component.
This run cannot be used to judge the published 2% threshold because the actual
release occurred at 5.23%. It does show that the inherited phase-2 initial
current and the mandatory preceding support interval are inconsistent with a
2% release at that event boundary. The next gate is to recompute/solve the
periodic phase state so the threshold is reached at the allowed release event.
