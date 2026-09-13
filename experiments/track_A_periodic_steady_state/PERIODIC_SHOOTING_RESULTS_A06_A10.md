# Periodic shooting results A06-A10

## Current-state convergence

| Experiment | Seed update | Maximum absolute current residual after one period |
|---|---|---:|
| A05 | all inductor currents initially zero | 80.468 A |
| A06 | P24 ideal phase-shifted triangular seed | 30.499 A |
| A07 | A06 final currents fed back | 1.300 A |
| A08 | A07 final currents fed back | 0.461 A |
| A09 | A08 final currents fed back | 0.226 A |
| A10 | all eight A09 slow-state finals fed back | 0.186 A |

The phase-shifted analytical seed and fixed-point shooting method are useful;
the all-zero current seed was not a realistic interleaved periodic state.

## A10 eight-state residual

| State | Final minus initial |
|---|---:|
| VC1 | +0.1126 mV |
| VC2 | -0.1065 mV |
| VC3 | -0.0540 mV |
| Vout | -3.1305 mV |
| IL1 | +0.1245 A |
| IL2 | +0.1576 A |
| IL3 | +0.00485 A |
| IL4 | +0.1859 A |

The flying-capacitor residuals are small on a one-period scale, but the output
state is not closed. Repeating state substitution alone would move the output
operating point rather than enforce 1 V. Output regulation requires a separate
control or operating-point equation and must not be confused with the SCB's
passive flying-capacitor charge balance.

## 8% event status

Across these full four-phase first-period runs, `IL1,min` remains about
`-3.3` to `-3.9 A`. The `-10 A` 8% release event is not reached. Therefore the
full four-phase 8% ZVS question remains unexercised even though the threshold is
present. The isolated/shared-two-phase results must not be substituted for it.

## Next separated experiments

1. Natural-balance test: perturb one flying-capacitor voltage while holding the
   same periodic gate law, then measure whether its deviation decays over many
   cycles relative to an unperturbed control case.
2. Output-regulation test: introduce a separately sourced duty/on-time control
   law only after the natural-balance experiment; do not use capacitor values
   as an output-voltage fitting knob.
3. Full ZVS test: once a periodic current trajectory actually reaches a named
   negative-current boundary, evaluate Coss commutation phase by phase.
