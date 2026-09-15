# A47 result — nonlinear GS61008T Coss(V) local ZVS threshold

## Outcome

All stages completed normally (no solver failure once the LTspice
implementation issues documented in BOUNDARY.md were worked around; no
missing-model singularity). With the full interval-1->2->3 chain re-run
under a digitized, fitted **nonlinear** `Coss(V)` model for the SAME
GS61008T device A42 used (constant `Co(tr)` replaced, nothing else
changed), the local natural-ZVS threshold is bracketed between **9.63% and
9.64%** of the 125 A phase peak.

**Stated explicitly and unambiguously, per this project's own A46
correction**: the threshold **increased** from A42's constant-capacitance
**7.76%-7.77%** to nonlinear-Coss(V)'s **9.63%-9.64%** — about **1.24x
higher**, moving the local threshold **further away** from P24's stated
1%-2% range, not closer to it. The hypothesis motivating this experiment
(that a constant-capacitance model might be *overestimating* the charge
needed to finish the last part of the ZVS voltage swing, because a real
`Coss(V)` is largest exactly near `Vds=0`) is **not confirmed** by this
result — see "Why the hypothesis did not pan out" below for the direct
reason. Grade: **SENSITIVITY_ONLY** (same grade category as A42/A45, for
the same reasons — see "Prohibited claims" in `BOUNDARY.md`).

## Stage 0 — interval 1 (rerun, unchanged by construction)

`A47_stage0_interval1_shared_ladder.cir` reproduced R04D0's committed
values exactly, confirming interval 1 cannot depend on the commutation-
capacitance model choice (it has no `CH1`/`CL1` element):

| Quantity | R04D0 (committed) | A47 stage 0 (rerun) |
|---|---:|---:|
| `IL1_MAX` (A) | 124.932723999 | 124.932723999 |
| `VC1_END` (V) | 36.0193109995 | 36.0193109995 |
| `IL2_AT_TON` (A) | -11.3505529996 | -11.3505529996 |

## Stage 1 — interval 2 (nonlinear Coss(V), re-derived handoff state)

`A47_stage1_interval2_GS61008T_nonlinear.cir`, chained from stage 0's
`IL1_T1`/`VC1_T1`/`IL2_T1`, with the digitized nonlinear `Coss(V)` model
(same device, same Ron, same population as R04D2A/A42):

| Quantity | R04D2A (constant Co(tr)) | A47 stage 1 (nonlinear Coss(V)) |
|---|---:|---:|
| `CH`/`CL` near `Vds=0` (pF) | 385 / 770 (constant everywhere) | ~702 / ~1405 (near `V=0`; falls to ~204/~408 asymptotically at high V) |
| Low-side ZVS instant (ns) | 0.1105 | 0.0973 |
| `IL1` at low-side ZVS (A) | 125.308 | 125.079 |
| Freewheel duration to `iL1=0` (ns) | 152.38 | 152.148 |
| `VC1_T2` (V, handoff) | 36.0193959392 | 36.0194477751 |
| `VX1_T2` (V, handoff) | -9.6477e-6 | -1.5707e-5 |
| `VA1_T2` (V, handoff) | 36.0193862915 | 36.0194320679 |

The nonlinear model's near-`V=0` capacitance is roughly **1.8x larger**
than the constant `Co(tr)` value for both `CH` and `CL` (this is the
digitized curve's own peak region — see BOUNDARY.md's digitization-
uncertainty note for `V<~5V`). Despite that, the low-side ZVS instant and
overall freewheel duration barely move (within 12% and 0.15% respectively)
and the handoff state to stage 2 is nearly identical to the constant-
capacitance chain's — consistent with A45's own observation that `CF1`
(53.8 uF) so dominates this interval that it acts as a quasi-ideal voltage
source regardless of the commutation-capacitance model.

## Stage 2 — interval 3, coarse 1%-10% grid (A42/A45 convention)

Unlike A45's EPC2067 branch (which needed a much wider bracket search),
**the original 1%-10% grid itself already brackets the transition**, between
9% (no ZVS) and 10% (ZVS):

| Negative target | Source label | Target current (A) | Minimum post-release Vds (V) | ZVS |
|---:|---|---:|---:|:---:|
| 1% | P24 explicit | 1.25 | 9.502 | no |
| 2% | P24 explicit | 2.50 | 8.573 | no |
| 3% | diagnostic bridge | 3.75 | 7.538 | no |
| 4% | diagnostic bridge | 5.00 | 6.463 | no |
| 5% | P25 supplement | 6.25 | 5.364 | no |
| 6% | P25 supplement | 7.50 | 4.243 | no |
| 7% | P25 supplement | 8.75 | 3.103 | no |
| 8% | P25 supplement | 10.00 | 1.943 | no |
| 9% | P25 supplement | 11.25 | 0.760 | no |
| 10% | P25 supplement | 12.50 | -0.021 | **yes** |

`minimum_vds_high_after_release_v` decreases smoothly and monotonically
with negative-current percentage, exactly as physically expected, with no
discontinuity — including across the two rows (4%, and none others in this
particular grid) that needed the solver-tolerance escalation described in
BOUNDARY.md, supporting that the escalation did not bias the physical
result.

## Refinement (0.1% steps, 9.0%-10.0%)

| Negative target | Minimum post-release Vds (V) | ZVS |
|---:|---:|:---:|
| 9.0% | 0.760 | no |
| 9.1% | 0.640 | no |
| 9.2% | 0.520 | no |
| 9.3% | 0.400 | no |
| 9.4% | 0.279 | no |
| 9.5% | 0.158 | no |
| 9.6% | 0.037 | no |
| 9.7% | -0.008 | **yes** |
| 9.8% | -0.014 | yes |
| 9.9% | -0.018 | yes |
| 10.0% | -0.021 | yes |

Bracketed the transition between 9.6% (no ZVS) and 9.7% (ZVS).

## Final bracket (0.01% steps, 9.60%-9.70%)

| Negative target | Target current (A) | Minimum post-release Vds (V) | ZVS | Commutation duration (ns) | Current at ZVS (A) |
|---:|---:|---:|:---:|---:|---:|
| 9.60% | 12.00 | 0.0369 | no | - | - |
| 9.61% | 12.0125 | 0.0249 | no | - | - |
| 9.62% | 12.025 | 0.0128 | no | - | - |
| 9.63% | 12.0375 | 0.000713 | no | - | - |
| 9.64% | 12.05 | -0.00251 | yes | 2.660 | -0.531 |
| 9.65% | 12.0625 | -0.00396 | yes | - | -0.767 |
| 9.66% | 12.075 | -0.00508 | yes | - | -0.942 |
| 9.67% | 12.0875 | -0.00603 | yes | - | -1.090 |
| 9.68% | 12.10 | -0.00689 | yes | - | -1.222 |
| 9.69% | 12.1125 | -0.00765 | yes | - | -1.339 |
| 9.70% | 12.125 | -0.00837 | yes | - | -1.447 |

- **9.63%** (`12.0375 A` negative): no zero crossing; minimum high-side
  `Vds` is `0.71 mV` — i.e. within a millivolt of ZVS but not reaching it.
- **9.64%** (`12.05 A` negative): first zero crossing; high-side
  `Vds=0` occurs at `20.733 ns` (release at `18.073 ns`), `2.660 ns` after
  low-side release. Inductor current at the crossing is `-0.531 A`, so, as
  in A42/A45, this boundary is also close to (though not as extremely
  close as A42/A45's own boundaries) zero-current switching.

Refining beyond 0.01 percentage point would overstate the fidelity of a
raster-digitized, 3-parameter analytic `Coss(V)` approximation, exactly as
A42/A45 concluded for their own constant-capacitance models, so the result
is stored as a bracket.

## Comparison against A42 (same device) and A45 (different device)

| | A42 (GS61008T, constant `Co(tr)`) | A47 (GS61008T, nonlinear `Coss(V)`) | A45 (EPC2067, constant `Co(tr)`) |
|---|---:|---:|---:|
| Near-`V=0` `CH`/`CL` (pF) | 385 / 770 (constant everywhere) | ~702 / ~1405 | 3720 / 5580 (constant everywhere) |
| ZVS threshold bracket | 7.76%-7.77% | **9.63%-9.64%** | 22.04%-22.05% |
| Ratio to A42 | 1.00x | **~1.24x** | ~2.84x |

**Direction, stated explicitly (per A46's own correction to avoid the same
ambiguity)**: replacing GS61008T's constant `Co(tr)` with its digitized
nonlinear `Coss(V)` **increases** the local natural-ZVS negative-current
threshold (from 7.76%-7.77% up to 9.63%-9.64%); it does **not** decrease
it, and it does **not** move the threshold closer to P24's stated 1%-2%
range — it moves it further away, roughly a third of the way from A42's
bracket toward A45's much-larger-capacitance EPC2067 bracket in log-ratio
terms.

## Why the hypothesis did not pan out

The task's motivating hypothesis was: since a real `Coss(V)` is largest
near `Vds=0`, and the local ZVS event only needs to complete the *last*
part of the voltage swing toward 0 V, a constant-capacitance model might
be *overestimating* the charge needed for that last part, versus what a
correctly-shaped nonlinear curve would show.

**What the digitized data actually shows**: near `Vds=0`, GS61008T's real
`Coss` is *higher* than its own constant `Co(tr)` value — not lower. The
digitized/fitted single-device curve gives `Coss(V->0) ~= 702 pF`
(`C_FLOOR+A_COSS`, see BOUNDARY.md), compared to the constant
`Co(tr)=385 pF` used by A42's model — about **1.8x larger**, not smaller.
`Co(tr)` is explicitly a *time-equivalent* capacitance averaged over the
full stated 0-50V range specifically because the true curve is so much
larger near 0V and so much smaller near 50V; a single constant value
necessarily undershoots the true near-zero capacitance to compensate for
overshooting the true high-voltage capacitance. Since finishing the ZVS
swing specifically happens in the near-zero region, using the TRUE
(higher) near-zero capacitance requires MORE charge (and hence more
negative current) to complete that last part of the swing than the
constant-`Co(tr)` model assumed — the opposite of what the hypothesis
proposed. This is a legitimate, informative negative result, not a failed
experiment: it directly tests and refutes a specific, well-motivated
physical hypothesis about a specific device's own published curve.

**Rough consistency check against A46's own scaling model.** A46 fit
`Ineg_threshold = (V0/k) * Ceff^p` (`Ceff = CH*CL/(CH+CL)`, `p=0.512`) over
A41/A42/A45's constant-capacitance rows. Evaluating the near-`V=0`
nonlinear capacitance as if it were a (locally) constant value,
`Ceff(V->0) = 702.26*1404.51/(702.26+1404.51) = 468.2 pF`, versus A42's own
`Ceff=256.7 pF` -- a factor of 1.82x. A46's naive scaling law predicts a
threshold ratio of `1.82^0.512 = 1.35x`; the observed ratio is `1.24x`,
about 8% below that naive prediction. This is a plausibility check only
(the true nonlinear `Coss(V)` is not a constant equal to its own near-zero
peak throughout the whole swing, so exact quantitative agreement is not
expected), but the DIRECTION (increase, roughly this order of magnitude)
is consistent with both A46's own constant-capacitance-based model and the
direct nonlinear simulation here, which is evidence the nonlinear result
is physically sane rather than a numerical artifact.

## Does nonlinear Coss(V) close the gap toward 1%-2%? Stated directly.

**No. It moves the threshold further away from 1%-2%, not closer.** A42's
constant-capacitance GS61008T model already needed 7.76%-7.77%, roughly
4-8x the paper's stated 1%-2%. This experiment's nonlinear, digitized
`Coss(V)` model for the SAME device needs 9.63%-9.64%, roughly 5-10x the
paper's stated range — a materially LARGER gap, not a smaller one. A46's
inverted-constant-capacitance estimate (4-17 pF effective capacitance
needed to reach 1%-2%) remains one to two orders of magnitude below even
this nonlinear model's own asymptotic HIGH-voltage floor value (`C_FLOOR
~=204 pF` per device, itself already above 17 pF), let alone its much
larger near-zero peak. Nothing in this digitized curve comes close to the
4-17 pF range at any voltage in its 0-100V characterized span. This
experiment therefore does not identify a nonlinear-Coss(V) explanation for
the 4-17pF-vs-257pF (or larger) mismatch A46 documented; if anything it
shows the mismatch is somewhat worse than the constant-capacitance model
alone suggested.

## What this resolves and what it does not

Resolves:
1. A real, digitized (not fabricated) `Coss(V)` curve for GS61008T,
   cross-checked against the datasheet's own printed `Coss(50V)`,
   `Co(er)` and `Co(tr)` values to within 1-3% (raw digitized points) or
   1-6% (the fitted closed-form model), with the digitization method,
   calibration points and uncertainty fully documented.
2. A working, validated LTspice nonlinear-capacitor construction
   (floor-capacitor + `ddt()`-based bounded correction, `method=gear`) for
   this class of stiff capacitor-loop circuit, needed because both
   LTspice's native `Q=` device and a naive single-B-source `ddt()`
   implementation failed to converge.
3. A same-device (GS61008T), same-Ron, capacitance-model-only comparison:
   nonlinear `Coss(V)` moves A42's local ZVS threshold from 7.76%-7.77% up
   to 9.63%-9.64% — a modest (~1.24x) but clearly-directioned increase,
   moving AWAY from P24's stated 1%-2%, refuting the motivating hypothesis
   for this specific device's own datasheet curve.

Does not resolve: whether a DIFFERENT device's real `Coss(V)` (e.g.
EPC2067, or an actual manufacturer SPICE model rather than a digitized
graph) would behave differently; any four-phase or startup behavior; a
validated `Ron`/conduction model (unchanged, still A42's own GS61008T
value); or the ultimate cause of the 4-17pF vs 200+pF mismatch A46
documented, which remains open.

## Next permitted action

Do not silently replace A42's bracket, P24's 1%-2%, or any prior result
with this one. Preserve as a fourth, separately labelled branch:

- `GS61008T_NONLINEAR_COSS_9P63_TO_9P64_PERCENT`: a digitized-datasheet-
  curve, capacitance-model-only sensitivity result for the SAME device and
  Ron A42 already used, not chained into the full four-phase event
  machine.

If Mihai wants to pursue closing the 4-17pF gap further, the honest next
steps this result points to are: (a) find and use an actual manufacturer
SPICE model with a validated `Coss(V)` (Step 1's preferred, unavailable
path here) rather than a digitized graph, since this result shows the
digitized graph's near-zero region carries the largest uncertainty and
happens to be exactly the region this question is most sensitive to; or
(b) revisit whether the paper's 1%-2% figure is compatible with a GS61008T-
or EPC2067-class device's Coss AT ALL under this local mechanism, versus a
different, smaller-capacitance device, a snubber, or a different ZVS
mechanism entirely (dead time, active clamp, etc.) not modeled here.
