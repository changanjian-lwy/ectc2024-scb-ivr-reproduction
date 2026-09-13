# A12 - long-horizon passive-balance continuation

## Single changed variable relative to A11

- Simulation horizon: 5 periods -> 20 periods.

## Unchanged boundaries

- Same full four-phase, single-module P24 topology and switching sequence.
- Same P24 2% negative-current branch; P25 5-10% is not substituted.
- Same `Vin=48 V`, ideal `Vout=1 V` isolation clamp, `fsw=5 MHz`,
  `L=1.4666667 nH`, component models, current seed and capacitances.
- Same symmetric `C1` initial perturbations: `-0.5/0/+0.5 V`.
- Device commutation capacitance is included; external snubber is zero.
- No startup, voltage-loop, current-loop or output-regulation claim is made.

## Measurements and decision rule

- Sample `VC1` at cycles 1, 5, 10, 15 and 20.
- Compare each perturbed case against the control case at the same time.
- Restoring behavior requires both signed deviations to continue toward zero.
- A reversal, growing magnitude or persistent nonzero orbit must be reported as
  observed; no parameter may be changed inside this experiment.
