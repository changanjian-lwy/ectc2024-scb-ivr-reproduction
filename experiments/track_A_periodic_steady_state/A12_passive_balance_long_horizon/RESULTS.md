# A12 results - 20-cycle passive-balance continuation

## Outcome

Both signs of the C1 perturbation continue moving toward the simultaneous
control case over 20 periods. No reversal is observed at the sampled cycle
boundaries. This strengthens the evidence for a passive restoring tendency,
but does not prove asymptotic convergence because the shared control orbit is
not yet an exact periodic fixed point.

## Perturbation relative to control at the same cycle

| Cycle | `DV1=-0.5 V` delta VC1 | `DV1=+0.5 V` delta VC1 |
|---:|---:|---:|
| 1 | -0.498252 V | +0.498261 V |
| 5 | -0.488309 V | +0.494994 V |
| 10 | -0.476060 V | +0.490839 V |
| 15 | -0.463916 V | +0.486727 V |
| 20 | -0.451861 V | +0.482663 V |

From the nominal +/-0.5 V perturbations to cycle 20:

- Negative-side error magnitude decreases by about 9.63%.
- Positive-side error magnitude decreases by about 3.47%.

The correction remains asymmetric. The experiment does not fit or alter any
parameter to force this trend.

## State-drift qualification

- The control-case C1 changes from 36.000156 V at the initial sample to
  36.002877 V at cycle 20: +2.720 mV.
- The control-case current residuals over 20 periods are approximately
  `[-0.278, +0.312, +0.313, -1.254] A` for L1-L4.
- Consequently, the comparison rejects common-mode drift by using a
  simultaneous control case, but it is not a Floquet/stability proof around an
  exact periodic orbit.

## Boundary statement

The only change from A11 is 5 -> 20 simulated periods. The ideal 1 V output
clamp remains an isolation fixture; imposed capacitor initial conditions remain
perturbation-test inputs; P24 2% control remains active; P25 5-10% control is not
used; device commutation capacitance remains included; external snubber remains
zero. This result is neither zero-start validation nor output regulation.

## Next controlled step

Before extending much farther, solve a tighter common periodic orbit for the
unperturbed control case and repeat the same symmetric perturbation around that
orbit. This separates true capacitor-balancing dynamics from residual current
seed drift without changing the topology or paper-derived control law.
