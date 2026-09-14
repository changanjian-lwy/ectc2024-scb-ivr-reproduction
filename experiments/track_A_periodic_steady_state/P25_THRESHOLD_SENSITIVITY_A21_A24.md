# P25 all-inactive-low phase-1 threshold sensitivity

## Evidence and comparison contract

- P25 Mode 1 explicitly turns on the active high side and all other low sides
  in its three-phase converter. Applying the same rule to four phases is a
  labelled `CROSS_PAPER_EXTENSION`.
- P25 states a 5-10% negative-current range; 5%, 8%, 9% and 10% are therefore
  source-bounded sensitivity points, not arbitrary tuning values.
- Every case starts from the identical A16 state and retains the same topology,
  48/1 V condition, 5 MHz timing, 1.4667 nH inductance, switch resistance,
  scalar Coss candidates, flying capacitors, output clamp and 5 ps timestep.
- A21 establishes the P25 branch and 5% point. A22/A24/A23 change only
  `NEG_FRAC` to 8%/9%/10%, respectively.

## Controller correction made before accepting the results

The first generated version incorrectly required `Vds<=0` continuously and
therefore released the low side as soon as current reversed. Those runs are
rejected. In the retained version, `Vds<=0` is a one-time admission event;
phase-1 low-side conduction is latched until the negative threshold is reached
after the phase-4 support interval. This follows the event order in P25 Modes
2-5 and changes no power-stage parameter.

Only the phase-1 latch needed for this handoff has been promoted in these cases.
The remaining phase latches have not yet been globally implemented, so this is
a phase-1 handoff sensitivity inside the four-phase network, not yet proof of a
complete repetitive P25-derived four-phase controller.

## Results

| Case | Negative target | Release time | Minimum `Vds(QH1)` | Natural zero before next command | Result |
|---|---:|---:|---:|---:|---|
| A21 | 5% = 6.25 A | 169.987 ns | 4.826 V | No | fail |
| A22 | 8% = 10.00 A | 175.698 ns | 1.199 V | No | fail, near |
| A24 | 9% = 11.25 A | 177.602 ns | -0.0146 V | Yes, 180.020 ns | pass, marginal |
| A23 | 10% = 12.50 A | 179.515 ns | -1.229 V | Yes, 181.318 ns | pass, excess margin |

## Interpretation

For the locked candidate capacitance model, the transition lies between 8% and
9%; 9% is the smallest tested successful point. This is not a universal design
value. Nonlinear Qoss, actual added snubber capacitance, driver delay and a fully
latched four-phase controller can move the boundary.

Increasing the target supplies more commutation energy and voltage margin but
also increases reverse circulating current, conduction loss and the time spent
building negative current. Therefore 10% is easier for ZVS but is not
automatically the preferred operating point. A final controller should choose
the lowest target that retains adequate margin across component, voltage,
temperature and delay variation.
