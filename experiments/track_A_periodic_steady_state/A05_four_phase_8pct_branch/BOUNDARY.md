# A05 - full four-phase 8% model branch

- Compared with A04.
- Only changed variable: `NEG_FRAC`, from the P24 source-native 2% branch to
  the previously selected 8% model branch.
- This is a sensitivity/model branch. It is not promoted to a P24 value.
- The same full four-phase ladder, local-segment readiness latch, 0/50/100/150
  ns phase origins, device Coss, capacitor seeds and all-zero inductor-current
  seed are retained.
- The local voltage supervisor is not an active balancing loop. Natural SCB
  charge redistribution is present in the power stage, but one-cycle residuals
  cannot establish convergence or self-balancing.
