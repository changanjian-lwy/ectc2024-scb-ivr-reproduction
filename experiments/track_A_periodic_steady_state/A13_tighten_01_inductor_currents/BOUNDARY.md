# A13 - periodic-state tightening 01: inductor currents

## Parent and single state-group change

- Structural parent: A11/A12 unperturbed (`DV1=0`) isolated-balance model.
- Only the four inductor-current initial conditions are updated, using the
  unperturbed A12 values measured at the cycle-20 boundary:
  `[-0.935686, 4.755554, 41.578270, 84.144743] A`.
- Flying-capacitor initial values remain `36/24/12 V`.

The four currents are treated as one coupled state group because interleaving
ties their phase ages together. Updating only one phase current would destroy
the shared phase relationship rather than perform a clean group iteration.

## Locked boundaries

- Full four-phase, single-module P24 topology and P24 2% control.
- `Vin=48 V`, ideal `Vout=1 V` isolation clamp, `fsw=5 MHz`,
  `L=1.4666667 nH` and 5 ps maximum step.
- Same switch/component libraries and device commutation capacitance.
- External snubber remains zero; no startup or regulation loop is added.
- Exactly one complete period is measured.

## Acceptance

Compare the complete seven-state residual vector with its parent. A smaller
current residual is useful, but the experiment is not accepted as the next
baseline if it materially worsens capacitor-state closure. No parameter or
control timing may be modified after viewing the result.
