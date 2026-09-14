# A46 result — cross-experiment commutation-capacitance scaling

## Outcome

`fit_cross_experiment_scaling.py` rebuilds the combined 102-row dataset
(`combined_dataset.csv`, sourced only from A41/A42/A45's already-committed
result files, no new simulation) and reproduces the fit first reported in
conversation: `Vds_min = V0 - k*Ineg/Ceff^p` with `V0=10.16 V`,
`k=17.33`, `p=0.5117 +/- 0.0118`, `R^2=0.9469`. A fixed-`p=0.5` comparison
gives `R^2=0.9464` — the free exponent is not meaningfully better than the
naive resonant-energy guess. Full numbers in `fit_results.json`.

Grade: **SENSITIVITY_ONLY**, cross-experiment variant. This is a regression
over three already-`SENSITIVITY_ONLY`/`LOCAL_THRESHOLD`-graded sources; it
cannot inherit a higher grade than its inputs.

## Direction — stated explicitly, because an earlier informal description was ambiguous

Two different slices of this model must not be conflated:

1. **At fixed `Ineg`**: `Vds_min` moves *up*, away from zero/ZVS, as `Ceff`
   grows (`Vds_min = V0 - k*Ineg*Ceff^{-p}`, and the subtracted term shrinks
   as `Ceff` grows). In this sense "the achieved swing falls off as
   `Ceff^{-p}`" is correct.
2. **The negative-current threshold** needed to reach `Vds_min=0` is
   `Ineg_threshold = (V0/k)*Ceff^{+p}` — it *increases* with `Ceff`, the
   opposite sign of direction 1's exponent. This is the quantity relevant
   to comparing A42 against A45 (GS61008T needs less negative current than
   EPC2067, because GS61008T's `Ceff` is smaller).

A draft follow-up email described this only as "the minimum achieved Vds
falls off as roughly 1/sqrt(Ceff)," which is direction 1's statement without
saying so, and reads easily (and wrongly, if read as a claim about the
threshold) as direction 2 with the sign flipped. That phrasing has been
corrected in the email — see the project's follow-up-email file — to state
the threshold direction explicitly.

## Consistency check against A42's and A45's own brackets

The fitted global model, evaluated at each experiment's own `Ceff`, predicts:

| Source | `Ceff` (pF) | Model-predicted threshold | Actual bracket | Relative error |
|---|---:|---:|---:|---:|
| A42 (GS61008T) | 256.7 | 8.02% | 7.76%-7.77% | +3.3% |
| A45 (EPC2067) | 2232.0 | 24.25% | 22.04%-22.05% | +10.0% |

The global fit (which also includes A41's snubber-sweep rows, run at fixed
1%/2% negative current rather than swept to a threshold) does not exactly
reproduce either experiment's own directly-measured bracket — it is
systematically about 3%-10% high. This is expected: the global model is a
compromise fit across three experiments with different measurement designs,
not a re-derivation of either threshold from scratch, and the two
experiments' own directly-measured brackets (7.76%-7.77%, 22.04%-22.05%)
remain the authoritative numbers for those two specific `Ceff` values. This
fit's role is to describe the trend and its rough magnitude, not to replace
either direct measurement.

## What this resolves and what it does not

Resolves: gives a citable, rerunnable regression showing the three
experiments' results are mutually consistent with a single constant-
capacitance LC-energy-style model, with the correct sign, to about 5-10%
accuracy in threshold terms.

Does not resolve: which capacitance (or device) is actually correct for
2024's Sec. II-B mechanism; whether a nonlinear `Coss(V)` model would fit
better than a constant-capacitance one; any four-phase or startup behavior;
or a validated `Ron` for EPC2067 (still frozen at GS61008T's value across
every A45 row used here).
