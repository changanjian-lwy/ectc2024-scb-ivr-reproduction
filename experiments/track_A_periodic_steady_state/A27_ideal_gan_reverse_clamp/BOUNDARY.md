# A27 - ideal GaN reverse-conduction clamp

## Parent and only change

- Parent: A26 phase-2 ZVS readiness guard.
- Only electrical change: an antiparallel off-state reverse path is added to
  every high-side and low-side GaN position.
- Topology/function is required by P25's GaN reverse-conduction statement and
  Modes 2'/5'. Four-phase placement is a direct device-by-device extension.
- `Vf=0 V`, `Ron=1 mOhm`, zero-Qrr behavior are ideal/numerical boundary values;
  they are not claimed as published GS61008T values.

All other topology, state, 9% control, fixed high requests, readiness guard,
component values, scalar Coss, output clamp and timestep remain identical to
A26.

## Acceptance

Compare against A26:

1. time of first `Vds(SH2)=0` after `SL2` release;
2. whether the high-side voltage remains clamped near zero until 50 ns;
3. readiness waiting time at the 50 ns request;
4. whether adding the clamp introduces same-leg command overlap.
