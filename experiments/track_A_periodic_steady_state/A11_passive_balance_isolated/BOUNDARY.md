# A11 - isolated passive flying-capacitor balance

## Purpose

Test whether a small C1 voltage perturbation decays relative to an otherwise
identical control case. This isolates the P24 adjacent-phase charge-transfer
mechanism from the unresolved output-voltage regulation problem.

## Shared boundaries

- Full four-phase single-module ladder and fixed `T/4` interleaving.
- P24 source-native 2% low-side release branch; no 8% model threshold.
- GS61008T scalar device Coss; external snubber remains zero.
- `Vin=48 V`, `Vout=1 V`, `fsw=5 MHz`, `L=1.4666667 nH`.
- The output is clamped by an ideal 1 V source in both cases. This is a new,
  explicit isolation assumption and is not retained in the main reproduction.
- Initial currents use the latest current-only shooting seed. They are equal in
  both cases and are not claimed as the final periodic solution.
- Five periods are simulated. This is an early trend test, not proof of global
  asymptotic stability.

## Only changed variable between cases

- Negative perturbation: `DV1=-0.5 V`, so `VC1=35.5 V`.
- Control: `DV1=0`, so `VC1=36 V`.
- Positive perturbation: `DV1=+0.5 V`, so `VC1=36.5 V`.
- `VC2=24 V` and `VC3=12 V` are identical in both cases.

## Acceptance

At each cycle boundary calculate
`delta_VC1 = VC1_perturbed - VC1_control`. Passive correction is supported
only if both positive and negative deviations trend toward zero without
changing any gate, component or initial-current condition between cases.
