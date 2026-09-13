# Step 19 - R04D3 separate branch simulations

## Common rule

The branches use physical-event interfaces from Step 18.  Printed `t2/t3`
labels are never used to join the papers.

## R04D3A - P24 same-phase interval 3

Compared with R04D2A, the changed condition is the start event: the run begins
at R04D2A's measured `iL1=0` state.  `QL1` is initially ON.  It is turned OFF
when `iL1=-1.25 A`, the lower (1%) boundary of P24's stated 1%-2% negative
peak-current range.  The selected GS61008T scalar-capacitance plug-in is
unchanged from R04D2.

Measured result:

- `QL1` turn-off: 1.83634 ns, `iL1=-1.25 A`.
- Maximum phase-1 switching-node voltage: 2.72404 V.
- Target `Vds(QH1)=0` event: not reached.
- Therefore P24 `t3` and high-side ZVS turn-on are not reproduced under this
  explicitly selected device plug-in.

Interpretation: this is not a rejection of the P24 mechanism.  It says that
the paper's 1% lower-bound negative current, P24 Eq.(2)/(4) phase values and
the present GS61008T CO(TR) scalar approximation do not jointly supply enough
commutation energy.  Roughly, 1.25 A in 1.4667 nH stores 1.15 nJ, whereas
moving the selected `CH+CL=1.155 nF` through about 12 V has an energy scale of
83.2 nJ.  Nonlinear Coss, the extra parallel capacitor actually used by the
authors, exact topology-equivalent capacitance and the paper's unreported
timing must be resolved before claiming quantitative contradiction.

## R04D3B - P25 Mode 3 extended to nP=4

Compared with R04D2B, the changed condition is that `SL1` joins
`SL2/SL3/SL4`; all low-side switches freewheel.  Initial currents are chained
from the preceding isolated replay without alteration.

Measured result:

- `iL2` at Mode-3 entry: -11.4254 A.
- `iL2` at 50 ns: -42.2749 A.
- Target P25 `t3` (`iL2=0` while decreasing): not reached.

Interpretation: the preceding isolated P24-first-interval replay drove the
inactive phase current negative.  P25 Mode 3 requires phase 2 to enter with a
positive current inherited from its earlier pulse and then fall to zero.
Consequently this failed chain proves that a complete periodic multi-phase
state must be solved before P25 Mode 3 can be reproduced; inventing a positive
`iL2(t2)` would hide the missing state and is prohibited.

## Next controlled experiments

1. Sweep only P24's published 1%-2% negative-current boundary while retaining
   all device assumptions; report whether either endpoint reaches ZVS.
2. Build the preceding P25 phase-2 energy history so that `iL2(t2)` is generated
   by the schedule rather than inserted as an initial condition.
