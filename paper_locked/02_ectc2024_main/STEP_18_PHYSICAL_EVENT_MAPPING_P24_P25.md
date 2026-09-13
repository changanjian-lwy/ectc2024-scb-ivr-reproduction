# Step 18 - Physical-event mapping for the two papers' interval 3

## Boundary rule

The symbols `t2` and `t3` are local labels, not shared framework events.
The framework keys transitions by measured physical events.

## P24 branch (same phase is followed)

1. `P24 t1`: `QH1` turns off.
2. Unnumbered inside P24 interval 2: the phase-1 low-side voltage reaches zero;
   `QL1` may turn on.
3. `P24 t2`: `iL1 = 0`.
4. P24 interval 3: `QL1` keeps the phase-1 current moving negative.
5. At the specified negative-current target, `QL1` turns off.
6. Reverse `iL1` commutates the phase-1 switch capacitances.
7. `P24 t3`: `Vds(QH1) = 0`, and `QH1` turns on under ZVS.

## P25 branch (handoff toward the next phase is followed)

1. `P25 t1`: `SH1` turns off.
2. `P25 t2`: `Vds(SL1) = 0`, and `SL1` turns on under ZVS.
3. P25 Mode 3: `SL1`, `SL2`, and `SL3` conduct; all phase currents
   freewheel/decrease.
4. `P25 t3`: `iL2 = 0`.  This is the zero-crossing event used by the control
   circuit before preparing phase 2.

For an explicitly labelled `nP=4` extension of P25, `SL4` is added to the
Mode-3 conducting set.  That added command is not claimed as an explicit P24
statement.

## Non-equivalences that tests must enforce

- `P24 t2 != P25 t2`.
- `P24 t3 != P25 t3`.
- `P25 Mode 3 [t2,t3] != P24 interval 3 [t2,t3]`.
- P25 Mode 3 starts at a physical event located inside P24 interval 2.
- P24 interval 3 starts later, when `iL1` crosses zero.

Therefore a simulator may share component, topology and event-detector
modules, but must compile the two gate/event schedules as separate branches.
