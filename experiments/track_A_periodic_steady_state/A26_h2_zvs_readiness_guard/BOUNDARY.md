# A26 - SH2 ZVS-readiness guard

## Parent and only change

- Parent: A25 four-low-side-latch, 9% branch.
- Only change: the fixed `SH2` gate is replaced by a modular readiness guard.
- At 50 ns the phase-2 request is armed. `SH2` may turn on only if its own
  `Vds=V(a1,a2)<=0`, following the ZVS condition stated in P24/P25.
- The original 16.667 ns request window is retained as a diagnostic deadline.
  The papers do not define a maximum waiting policy, so A26 reports expiry and
  does not invent an unlimited rescheduling rule.

All power-stage parameters, initial states, low-side latches, 9% target, other
high-side clocks, output clamp and timestep remain unchanged.

## Acceptance

Pass only if `Vds(SH2)` reaches zero after the request is armed and before the
original request window expires. Otherwise `SH2` must remain OFF and the first
failure is classified as insufficient/unfinished phase-2 commutation rather
than a hard-switching command.
