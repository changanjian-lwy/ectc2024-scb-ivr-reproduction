# A43 7.77% transplant into the full four-phase event machine

Track: A. Branch: `P25_DEVICE_AUGMENTED`. This is a boundary-propagation test,
not a P24 reproduction claim and not a periodic-state solve.

## Parent

The electrical parent is A37's archived best-candidate netlist:
`A37_p25_9pct_joint_seven_state_200ns_periodic_solve.cir`.

A37 is selected because it contains the complete four-phase rotating event
machine with fixed relative `TON`, negative-current low-side release,
event-gated high-side ZVS admission and nominal 50-ns phase-slot guards.

## The only electrical change

`NEG_FRAC` changes from A37's 9% sensitivity value to A42's first local-pass
value, 7.77%. Thus `INEG` changes from 11.25 A to 9.7125 A.

Classification: `P25_DEVICE_AUGMENTED / SENSITIVITY_ONLY`. The 7.77% value
must never replace or be reported as P24's explicit 1%-2% control statement.

## Everything held fixed

- topology and all 20 event-machine states/rules;
- `Vin=48 V`, `Vo=1 V`, `nP=4`, `nM=1`, 5 MHz and 50-ns slot origins;
- fixed `TON=16.6667 ns` and `L=1.4667 nH`;
- A37's 385/770-pF device-capacitance abstraction and switch resistances;
- ideal reverse-conduction clamp;
- ideal 1-V output-isolation boundary;
- A37's seven `LOCAL_SOLVED_SEED` coordinates, including the approximately
  36/24/12-V periodic-state coordinates;
- timestep, solver options and 205-ns observation window.

No initial state is re-solved. This is essential: otherwise a threshold change
and a periodic-state optimization would be mixed into one experiment.

## Question and grading

How far does the unchanged complete event machine advance at 7.77%, and what
is the first physical event or slot boundary it fails?

Report every high-side admission actually reached, every fixed-`TON` turn-off
actually reached, the state occupied at 50/100/150/200 ns, and each relevant
high-side `Vds` at its nominal slot. A blocked hard turn-on is a controller-
guard pass but an electrical handoff failure.

## Prohibited claims

This experiment cannot establish a valid periodic initial state, full P24
operation, zero-start, four-module operation, loss, or hardware feasibility.
Its parent A37 is already nonperiodic; A43 deliberately preserves that fact.
