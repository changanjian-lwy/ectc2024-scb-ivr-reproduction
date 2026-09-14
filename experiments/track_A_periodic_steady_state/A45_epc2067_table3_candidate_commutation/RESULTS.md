# A45 result - EPC2067 Table-3 candidate commutation threshold

## Outcome

All stages completed normally (no solver failure, no missing-model
singularity). With the full interval-1->2->3 chain re-run under the EPC2067
Table-3 candidate commutation-capacitance library and A45's own re-derived
interval-2 handoff state, the local natural-ZVS threshold is bracketed
between **22.04% and 22.05% of the 125-A phase peak** -- roughly **2.8x
higher** than A42's GS61008T-based **7.76%-7.77%** bracket. This is the
expected physical direction: a larger commutation capacitance needs more
charge (and thus more negative current / more available reverse energy) to
swing the same `Vds` voltage. Grade: **SENSITIVITY_ONLY** (same grade
category as A42, for the same reasons -- see "Prohibited claims" in
`BOUNDARY.md`).

## Stage 0 - interval 1 (rerun, unchanged by construction)

`A45_stage0_interval1_shared_ladder.cir` reproduced R04D0's committed values
exactly, confirming interval 1 cannot depend on the commutation-capacitance
library choice (it has no `CH1`/`CL1` element):

| Quantity | R04D0 (committed) | A45 stage 0 (rerun) |
|---|---:|---:|
| `IL1_MAX` (A) | 124.932723999 | 124.932723999 |
| `VC1_END` (V) | 36.0193109995 | 36.0193109995 |
| `IL2_AT_TON` (A) | -11.3505529996 | -11.3505529996 |

## Stage 1 - interval 2 (EPC2067-substituted, re-derived handoff state)

`A45_stage1_interval2_EPC2067_to_IL1_zero.cir`, chained from stage 0's
IL1_T1/VC1_T1/IL2_T1, with the EPC2067 commutation-capacitance library and
Ron frozen at the GS61008T value:

| Quantity | R04D2A (GS61008T chain) | A45 stage 1 (EPC2067 chain) |
|---|---:|---:|
| `CH_TOTAL` (pF) | 385 | 3720 |
| `CL_TOTAL` (pF) | 770 | 5580 |
| Low-side ZVS instant (ns) | 0.1105 | 0.8771 |
| `IL1` at low-side ZVS (A) | 125.308 | 127.930 |
| Freewheel duration to `iL1=0` (ns) | 152.38 | 155.04 |
| `VC1_T2` (V, handoff) | 36.0193959392 | 36.0201391787 |
| `VX1_T2` (V, handoff) | -9.6477e-6 | -7.7686e-5 |
| `VA1_T2` (V, handoff) | 36.0193862915 | 36.0200614929 |

The much larger `CL_TOTAL` takes about 8x longer to discharge to
`V(x1)=0` (0.877 ns vs 0.111 ns), as expected for a larger capacitance
charged/discharged by the same inductor current, and this small state
perturbation is what stage 2 chains forward. `VC1_T2` barely moves (the 53.8
uF flying capacitor is orders of magnitude larger than either commutation
capacitance), confirming the R04D3A/A42 observation that `CF1` acts as a
quasi-ideal voltage source over this interval.

## Stage 2 - interval 3, coarse 1%-10% grid (A42 convention)

Same row labelling as A42. **No row reaches ZVS in this range** -- unlike
A42's GS61008T chain, where 8%-10% already showed natural ZVS.

| Negative target | Source label | Target current (A) | Minimum post-release Vds (V) | ZVS |
|---:|---|---:|---:|:---:|
| 1% | P24 explicit | 1.25 | 9.868 | no |
| 2% | P24 explicit | 2.50 | 9.577 | no |
| 3% | diagnostic bridge | 3.75 | 9.194 | no |
| 4% | diagnostic bridge | 5.00 | 8.765 | no |
| 5% | P25 supplement | 6.25 | 8.313 | no |
| 6% | P25 supplement | 7.50 | 7.847 | no |
| 7% | P25 supplement | 8.75 | 7.373 | no |
| 8% | P25 supplement | 10.00 | 6.894 | no |
| 9% | P25 supplement | 11.25 | 6.411 | no |
| 10% | P25 supplement | 12.50 | 5.926 | no |

This is an honest, expected outcome given EPC2067's ~9.7x/7.2x larger
`CH_TOTAL`/`CL_TOTAL`, not a failure of the run. Per BOUNDARY.md, the search
was therefore widened rather than forced into the original grid.

## Wide-bracket search (P25_SUPPLEMENT / SENSITIVITY_ONLY rows only)

The `.tran` window was widened from 50 ns to 150-200 ns for these rows
because the pre-release ramp itself (1.9-2.0 ns/percentage point) started
consuming most of the original 50 ns window at higher percentages, which
would otherwise have truncated the post-release event before `Vds(QH1)=0`
could be observed (see BOUNDARY.md's fixed-time-vs-physical-event note).

| Negative target | Minimum post-release Vds (V) | ZVS | Commutation duration (ns) |
|---:|---:|:---:|---:|
| 15% | 3.477 | no | - |
| 20% | 1.013 | no | - |
| 21% | 0.519 | no | - |
| 22% | 0.0246 | no | - |
| 23% | -0.047 | yes | 5.031 |
| 24% | -0.072 | yes | 4.585 |
| 25% | -0.091 | yes | 4.260 |
| 30% | -0.164 | yes | 3.272 |
| 35% | -0.223 | yes | 2.704 |
| 40% | -0.276 | yes | 2.317 |

This bracketed the transition between 22% (no ZVS) and 23% (ZVS).

## Refinement (0.1% steps, 22.0%-23.0%)

The transition narrowed to between 22.0% and 22.1%:

| Negative target | Minimum post-release Vds (V) | ZVS |
|---:|---:|:---:|
| 22.0% | 0.0246 | no |
| 22.1% | -0.0076 | yes |
| 22.2% | -0.0156 | yes |
| ... | ... | yes |
| 23.0% | -0.0474 | yes |

(Full 22.0%-23.0% row set in `refinement_results.json`/`.csv`.)

## Final bracket (0.01% steps, 22.00%-22.10%)

| Negative target | Target current (A) | Minimum post-release Vds (V) | ZVS | Commutation duration (ns) | Current at ZVS (A) |
|---:|---:|---:|:---:|---:|---:|
| 22.04% | 27.55 | 0.00484 | no | - | - |
| 22.05% | 27.5625 | -0.00011 | yes | 6.088 | -0.136 |

- **22.04%** (`27.55 A` negative): no zero crossing; minimum high-side `Vds`
  is `4.84 mV`.
- **22.05%** (`27.5625 A` negative): first zero crossing; high-side
  `Vds=0` occurs at `48.595 ns` (release at `42.507 ns`), `6.088 ns` after
  low-side release. Inductor current at the crossing is `-0.136 A`, so, as
  in A42, this boundary is also nearly ZCS.

Refining beyond 0.01 percentage point would overstate the fidelity of the
constant-capacitance device abstraction, exactly as A42 concluded, so the
result is stored as a bracket.

## Comparison against A42 and physical-direction check

| | A42 (GS61008T) | A45 (EPC2067 candidate) | Ratio |
|---|---:|---:|---:|
| `CH_TOTAL` | 385 pF | 3720 pF | 9.66x |
| `CL_TOTAL` | 770 pF | 5580 pF | 7.25x |
| ZVS threshold bracket | 7.76%-7.77% | 22.04%-22.05% | ~2.84x |

**Direction matches physical expectation**: a larger commutation capacitance
needs more charge to swing the same voltage, so the natural-ZVS threshold
moves to a larger negative current, which is what was observed (up, not
down or flat).

**A rough consistency check, not a validation.** Treating the phase-1
commutation loop as a simple series LC resonance (`L1` in series with
`CH1`/`CL1` in series, since `CF1` is quasi-ideal), the achievable voltage
swing for a given release current scales as `1/sqrt(C_eff)`, where
`C_eff = CH*CL/(CH+CL)`. `C_eff` grows from 256.7 pF (GS61008T) to 2232 pF
(EPC2067), a factor of 8.70, so a naive resonant-energy estimate predicts the
threshold should scale by about `sqrt(8.70)=2.95`. The observed ratio is
2.84, about 4% below that naive estimate -- reasonably consistent, given the
naive estimate ignores `Ron` losses, `CF1`'s small but nonzero participation,
and the non-sinusoidal shape of the actual release ramp. This is offered only
as a plausibility check that the direction and rough scale of the result are
physically sane, not as an independent derivation or a validation of either
device assumption.

## What this resolves

1. Table 3's EPC2067 candidate, under the same local P24 state-chaining
   mechanism A42 used, requires roughly 2.8x more negative current than the
   GS61008T-based plug-in to reach natural ZVS at this local state -- both
   numbers remain well outside P24's published 1%-2% range.
2. The direction of the shift (bigger commutation capacitance -> higher
   required negative current) is physically consistent and of a plausible
   magnitude, which is evidence the model mechanism itself (not just the
   device numbers) is behaving sensibly across a >9x capacitance change.
3. Neither A42's 7.76%-7.77% nor A45's 22.04%-22.05% should be read as "the"
   P24/P25 negative-current threshold. They are two device-dependent
   sensitivity results from the same local mechanism, both still open
   questions for Mihai:

   > Under the GS61008T charge-equivalent plug-in, ZVS needs 7.76%-7.77%
   > (A42). Under 2024's own Table-3-named EPC2067 candidate for this
   > nP=4/nM=4 configuration -- with Ron left at the GS61008T value, since
   > Table 3 gives no Ron model -- ZVS needs 22.04%-22.05% (A45). Which
   > device (and which parallel count) did the authors actually use for the
   > Sec. II-B ZVS mechanism itself, as opposed to the Sec. IV
   > embedded-package concept, and is there a validated EPC2067 Ron figure
   > for this configuration?

## Next permitted action

Do not silently replace A42's bracket, P24's 1%-2%, or any prior result with
this one. Preserve as a third, separately labelled branch:

- `EPC2067_TABLE3_CANDIDATE_22P04_TO_22P05_PERCENT`: a Table-3-sourced,
  capacitance-only device-swap sensitivity result, Ron-unvalidated, not
  chained into the full four-phase event machine.

If Mihai confirms EPC2067 (and a validated Ron figure) as the intended
Sec. II-B device, the natural next step mirrors A43: transplant this
bracketed threshold into the existing full four-phase event machine (same
caution A43 already demonstrated -- a locally-bracketed threshold is not
guaranteed to close the full-machine H2/H3/H4 handoff) rather than assuming
it does.
