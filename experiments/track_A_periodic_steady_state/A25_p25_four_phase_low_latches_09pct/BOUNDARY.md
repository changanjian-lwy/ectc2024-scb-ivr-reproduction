# A25 - four-phase low-side event latches, 9% branch

## Parent and only control change

- Electrical/state parent: A16.
- Source branch: P25 all-inactive-low Mode-1 rule, extended from three to four
  phases and labelled `CROSS_PAPER_EXTENSION`.
- Threshold: 9%, selected because A22 failed at 8% and A24 was marginally
  successful at 9% for the phase-1 latch.
- Only implementation change: event memory is applied to all four low sides for
  one 200 ns rotation instead of phase 1 only.

## Locked boundaries

Topology, 48/1 V operating point, `NP=4`, system `NM=4`, single 250 W module,
5 MHz frequency, fixed `T/4` high-side origins, 16.667 ns on-time, 1.4667 nH
inductors, A16 periodic state, device resistance/Coss candidates, flying
capacitors, ideal output clamp and 5 ps maximum timestep are unchanged.

High-side edges are deliberately not made event-driven in A25. The test asks
whether the locked fixed schedule already arrives after each high-side Vds has
reached zero. A failure must be reported at its first physical event rather
than repaired by moving a pulse.

## Claim boundary

A25 is a one-period controller-integration test. It is not startup, output
regulation, periodic re-shooting, loss prediction, or a final P25 four-phase
implementation.
