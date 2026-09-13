# A11 results - isolated passive C1 balance

## Outcome

Both signs of the C1 perturbation move toward the unperturbed control case.
This supports a weak, bidirectional passive restoring tendency in the modeled
P24 four-phase charge-transfer network. It does **not** establish convergence,
regulated output operation, or a complete zero-start solution.

## Cycle-boundary comparison

`delta VC1 = VC1_perturbed - VC1_control`.

| Cycle | `DV1=-0.5 V` delta VC1 | `DV1=+0.5 V` delta VC1 |
|---:|---:|---:|
| 1 | -0.498252 V | +0.498261 V |
| 2 | -0.495630 V | +0.497602 V |
| 3 | -0.493244 V | +0.496658 V |
| 4 | -0.490743 V | +0.495856 V |
| 5 | -0.488309 V | +0.494994 V |

Over five periods, the negative perturbation magnitude decreases by about
2.34%, while the positive perturbation magnitude decreases by about 1.00%.
The response is therefore restoring but asymmetric under the selected current
seed and switching state.

## Cross-coupling observed at the fifth boundary

Relative to the control case:

- For `DV1=-0.5 V`, C2 differs by -6.587 mV and C3 by +0.103 mV.
- For `DV1=+0.5 V`, C2 differs by +2.710 mV and C3 by -0.082 mV.

The correction is not confined to C1; charge is redistributed through the
coupled ladder. That is consistent with the topology, but these five-period
data are insufficient to identify the final equilibrium.

## Boundaries that must accompany this result

- The ideal 1 V output clamp is an isolation fixture, not part of the main
  reproduction and not evidence of output-voltage regulation.
- Initial capacitor voltages are deliberately imposed for this perturbation
  experiment. This experiment does not claim natural startup from zero.
- Initial inductor currents are the A09 shooting seed, not a proven periodic
  fixed point for each perturbation.
- Control is fixed P24-style four-phase interleaving with the source-native 2%
  branch. No P25 5-10% threshold is substituted here.
- Device commutation capacitance is active; external snubber capacitance is
  explicitly zero.
- No parameter was tuned between the three stepped cases.

## Next justified experiment

Extend the same three cases to a longer horizon without changing parameters,
and track all capacitor-state deviations once per cycle. The decision test is
whether both signs continue monotonically toward zero or settle into a biased
orbit. Output regulation remains a separate experiment and must not be added
until this passive-balance check is characterized.
