# A04 - full four-phase local-segment readiness supervisor

- Compared with A01.
- Only functional change: phases 2-4 high-side commands pass through a
  detachable local-voltage readiness gate.
- P24 source-native negative-current branch remains 2%; this experiment does
  not yet import the A03 9% model branch.
- Phase origins remain `0/50/100/150 ns` for the 5 MHz four-phase case.
- The release variable is each adjacent rail difference, targeting 12 V.
  Absolute ladder-node values are monitors, not equality constraints.
- The provisional window is 10-14 V, inherited from the already recorded
  exploratory supervisor (`+/-2 V` at 48 V). P24/P25 do not publish this
  detector or tolerance.
- Pass for this step means the second-phase command is admitted at its 50 ns
  origin when the local segment is inside the window. It does not mean the
  one-period state closes or that all four phases achieve ZVS.

## First-run failure and bounded correction

- The direct, continuously evaluated voltage-window gate chattered at about
  50.0008 ns and the simulation made no useful forward progress. The run was
  terminated after the repeated convergence warnings were captured.
- Cause: the gate action changes the same segment voltage used by the ideal
  comparator, so the permission repeatedly asserts and clears.
- Corrected implementation changes only the realization of the same readiness
  condition: once the local segment enters the window after its phase origin,
  a state machine latches that phase ON until its already-fixed `Ton` endpoint.
  The target, tolerance, topology and timing are unchanged.
- A first latch placement inside the power-stage subcircuit completed but left
  the internal gate nodes floating because LTspice did not bind the state
  outputs at that hierarchy. It produced no accepted electrical result. The
  same latch is therefore moved to the top-level controller and connected
  through explicit gate-command ports; power connections remain unchanged.
