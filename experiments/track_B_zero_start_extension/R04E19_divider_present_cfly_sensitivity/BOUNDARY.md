# R04E19 - Cfly sensitivity of the divider-present runaway/safe boundary (BOUNDARY)

## 1. Parent and why this experiment exists

**R04E18** (`experiments/track_B_zero_start_extension/
R04E18_divider_present_tramp_boundary/`) localized the runaway/safe
`Tramp` boundary to `5-22.87 us`, but **only at `Cfly=3 uF`** -- its own
Section 6 explicitly states "no claim about any `Cfly` value other than
`3 uF`... whether the threshold's absolute value scales with `Cfly` is
not addressed here." `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`'s own
underlying physics (the flying-capacitor resonance frequency
`f1,4 ∝ 1/√Cfly`) predicts the safe ramp time should scale up with
`Cfly` (a bigger flying capacitor resonates slower, so needs a
proportionally slower ramp to stay below it) -- this experiment tests
whether the complete divider-present ideal-switch PWM model remains
consistent with that predicted direction, not whether the resonance law is
uniquely responsible for the result.

Per explicit user direction 2026-09-17 (approving the second item of
`CONSOLIDATED_FINDINGS_2026-09-16.md`'s updated priority list, after
confirming R04E18's `5-22.87 us` `Cfly=3 uF` localization is precise
enough for practical purposes and does not need further bisection).

## 2. What changed relative to R04E17/R04E18, exactly

**No mechanism or topology change is introduced.** This
experiment reuses R04E17/R04E18's own byte-level-faithful netlist
(R04E16's fixed-timing four-phase power stage + R03A's divider network
at `CDIV=300 uF`, `TSTART=0`, `LPHASE=1.4666667 nH`, `solver=alt
cshunt=1e-15 plotwinsize=0`, `TMAX=50 ps`) completely unchanged. Only
`Cfly` and `Tramp` are swept, at four NEW combinations chosen to
directly test the resonance-scaling prediction (Section 3), not an
arbitrary grid.

**`CDIV=300 uF` is deliberately held FIXED across all four cells, not
re-optimized per `Cfly`.** R04E15's own grid search found `300 uF` to be
a good divider value specifically at `Cfly=3 uF`; re-optimizing `CDIV`
for each new `Cfly` would be a second simultaneous variable change,
violating this project's single-conceptual-change discipline. This
experiment tests `Cfly` sensitivity of the RAMP boundary only, holding
everything else (including `CDIV`) at its already-established value.

**Pre-run attribution limit found by the mathematical boundary audit:**
holding `CDIV` fixed is correct for testing total-system sensitivity, but
changing `Cfly` changes both the normalized resonance/ramp coordinate
`Tramp*f_res` and the passive charge-sharing ratio `CDIV/Cfly` (and related
damping). Therefore this grid cannot attribute an observed difference solely
to the `1/sqrt(Cfly)` resonance law. In the two 30x-margin cells,
`Tramp*f_res` stays near `10.5`, while `CDIV/Cfly` changes from `500` at
`0.6 uF` to about `34.48` at `8.7 uF`. The valid question is whether the
complete divider-present startup model remains safe across the selected
`Cfly` range. Pure resonance-law identification would require a separate
normalized-ratio branch or a multi-variable model.

## 3. Swept grid -- four cells, chosen to test total-system sensitivity
   against the resonance-scaling prediction

| Cell | `Cfly` | `Tramp` | Why this `Tramp` |
|---|---:|---:|---|
| `e19_f0p6_t5` | `0.6 uF` | `5 us` | R04E18's own fast/runaway `Cfly=3uF` value, reused unchanged -- tests whether the SAME absolute `Tramp` that caused runaway at `Cfly=3uF` still does at a `5x` SMALLER `Cfly` (the resonance-scaling prediction says it should be relatively safer, since `f1,4` is higher and `5 us` represents more resonance periods) |
| `e19_f0p6_t30p68` | `0.6 uF` | `30.68 us` | `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`'s own `30x`-margin recommendation for THIS `Cfly` (Section 2 of that document) -- tests whether the model's own predicted-safe value is actually safe once the divider is present |
| `e19_f8p7_t22p87` | `8.7 uF` | `22.87 us` | R04E18's own confirmed-SAFE `Cfly=3uF` boundary value, reused unchanged -- tests whether the SAME absolute `Tramp` that was safe at `Cfly=3uF` becomes UNSAFE at a `2.9x` LARGER `Cfly` (the resonance-scaling prediction says it should, since `f1,4` is lower and `22.87 us` represents fewer resonance periods) |
| `e19_f8p7_t116p84` | `8.7 uF` | `116.84 us` | `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`'s own `30x`-margin recommendation for THIS `Cfly` -- tests whether the model's own predicted-safe value is actually safe once the divider is present |

Every `Tramp` value here is reused from an already-derived or
already-tested source (Section 5); none is a newly invented number.
`TSTOP=Tramp+300 us` per cell, matching R04E16/R04E17/R04E18's own
convention.

## 4. What did not change

Everything else, copied byte-for-byte from R04E17/R04E18's own netlists:
four-phase power-stage connectivity, `TSTART=0` fixed-timing gate
B-sources, `LPHASE=1.4666667 nH`, `COUT=4.672 mF`, `RLOAD=Vout^2/Pout`,
ideal `SWI` switch model, `RLDAMP=1u`, true-zero-energy IC (`UIC`),
`TMAX=50 ps`, `solver=alt cshunt=1e-15 plotwinsize=0`, R03A's own
divider-network topology (`CIN1-4`/`RLEAK1-4`/`DPC1-3`, `CDIV=300 uF`
fixed per Section 2, `IPEC2018 LPAR=5n`/`RPAR=10m`, `RLEAK=1G`, ideal
diode model).

## 5. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `Cfly=0.6 uF`, `8.7 uF` | `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own derived range extremes, already used in R04E16's own grid | `SENSITIVITY_ONLY`, inherited |
| `Tramp=5 us` (at `Cfly=0.6uF`) | R04E18's own already-tested `Cfly=3uF` fast/runaway value, reused unchanged at a new `Cfly` | inherited, reused for direct comparability |
| `Tramp=22.87 us` (at `Cfly=8.7uF`) | R04E18's own already-tested `Cfly=3uF` safe-boundary value, reused unchanged at a new `Cfly` | inherited, reused for direct comparability |
| `Tramp=30.68 us`, `116.84 us` | `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`'s own `30x`-margin recommendation for `Cfly=0.6/8.7 uF` respectively | `CROSS_PAPER_EXTENSION`, inherited |
| `CDIV=300 uF` (fixed, not re-optimized) | R04E15's own best-point value at `Cfly=3 uF`, deliberately held fixed here per Section 2 | `SENSITIVITY_ONLY`, inherited |
| Everything else | See R04E17/R04E18 `BOUNDARY.md` for original provenance | unchanged |

No new paper-sourced, cross-paper, or external-device data is
introduced.

## 6. What question this experiment is meant to answer

Does the runaway/safe boundary shift with `Cfly`, and is its direction
consistent with the underlying `1/√Cfly` resonance-frequency scaling, once
the divider network and ideal-switch PWM model are both present? Because
`CDIV/Cfly` changes too, consistency is not unique proof of that law.
Specifically: (a) is `Tramp=5 us` (runaway at
`Cfly=3uF`) safer, equally dangerous, or MORE dangerous at the smaller
`Cfly=0.6uF`; (b) is `Tramp=22.87 us` (safe at `Cfly=3uF`) still safe,
or does it become unsafe at the larger `Cfly=8.7uF`; (c) does the
model's own `30x`-margin recommendation actually deliver a comfortable
safety margin at both `Cfly` extremes, or does it turn out to be too
tight (or unnecessarily conservative) once the divider's own real
dynamics are included?

## 7. Success/failure conditions

Every outcome is informative, per Ground Rule 7 and R04E17/R04E18's own
precedent -- there is no "wrong" result:

- If `e19_f0p6_t5` is SAFE (unlike the `Cfly=3uF` case at the same
  `Tramp`): confirms the resonance-scaling prediction's qualitative
  direction for the fast/runaway side.
- If `e19_f0p6_t5` still shows runaway: the `1/√Cfly` scaling does not
  transfer cleanly to this divider-present, real-switching construct --
  a genuinely informative negative finding, not a failure requiring
  rework.
- If `e19_f8p7_t22p87` shows runaway (unlike the `Cfly=3uF` case at the
  same `Tramp`): confirms the resonance-scaling prediction's qualitative
  direction for the safe side becoming unsafe at larger `Cfly`.
- If `e19_f8p7_t22p87` remains safe: the boundary does not shift
  detectably over this `Cfly` range at this `Tramp`, itself informative.
- If either `30x`-margin cell (`e19_f0p6_t30p68`, `e19_f8p7_t116p84`)
  shows runaway or even elevated current: a genuine caution about
  relying on Roberts' own `30x`-margin convention as a general-purpose
  safety rule once the real divider/switching dynamics are included --
  report plainly, do not force a favorable reading.

## 8. What this experiment cannot prove

- It does not achieve a precise, continuous `Cfly`-vs-boundary-`Tramp`
  curve -- only two `Cfly` points (`0.6`, `8.7 uF`) at two `Tramp` values
  each, bracketing but not densely mapping the relationship.
- It does not re-optimize `CDIV` per `Cfly` -- `CDIV=300 uF` is held
  fixed throughout (Section 2); whether a different `CDIV` would change
  the picture at these `Cfly` values is untested.
- It cannot separate resonance scaling from the simultaneous change in
  `CDIV/Cfly` and damping caused by the same `Cfly` sweep.
- It does not address `Vout`/handoff bootstrap beyond what R04E16/R04E17/
  R04E18 already report.
- It does not modify, overwrite, or invalidate R04E16/R04E17/R04E18's
  own committed results.
- A P24 reproduction claim of any kind remains out of scope, the same
  standing Track-B limitation as every other experiment in this lineage.
