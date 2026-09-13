# Step 13 - R04C four-phase local-boundary replay

## Single changed variable relative to R04A

R04A contained one local phase. R04C instantiates four identical local phases
and offsets their declared origins by `T/nP`. No electrical value, current
threshold or inductance is tuned.

The schedule explicitly retains `nP=4`, `nM=1`, global `TREF`, phase spacing
`DTP=T/nP`, and module spacing `DTM=T/nM`. With one module, no module offset is
applied, but the architectural variable is not removed.

## Evidence and boundary

- P24 Eq. (1)/(3): duty and high-side on-time.
- P24 Eq. (4): recalculated `Lcrit=1.46667 nH` selected for the main branch.
- P24 Sec. II-B: high-side interval, current decay, zero crossing and the
  `-1%` to `-2%` low-side turn-off target.
- P24 states that phases are interleaved and use equal switching frequency and
  duty. Equal origins separated by `T/nP` are tested for the one-module case.

The derived `Vin/nP` rails and stiff `Vo` are the same local analytical
boundary as R04A. Therefore R04C does not test Fig. 3 flying-capacitor charge
balance, output ripple, startup, Coss commutation, dead time, ZVS or losses.
Each phase deliberately stops at the `-2%` event because P24/P25 do not publish
the numerical capacitance/dead-time needed for the next transition.

## Acceptance checks

1. All four phase peaks reproduce the R04A equation-derived peak within the
   same numerical tolerance.
2. Each zero crossing and `-2%` event is displaced from the previous phase by
   `T/nP=50 ns`.
3. `nP=4` and `nM=1` appear explicitly in the measurements.
4. No periodic-reset or complementary-PWM rule is introduced.

## Result

Status: **PASSED_WITH_LOCAL_BOUNDARY_ONLY**.

| Check | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---:|---:|---:|---:|
| Peak current | 125.109 A | 125.109 A | 125.109 A | 125.109 A |
| Zero crossing | 201.147 ns | 251.147 ns | 301.147 ns | 351.147 ns |
| Reaches -2.5 A | 204.813 ns | 254.813 ns | 304.813 ns | 354.813 ns |

The measured zero-crossing separations are `50.0000 ns`, `50.0000 ns` and
`50.0000 ns`, equal to `T/nP`. The `-2%` events have the same displacement.
The run also records `nP=4`, `nM=1`, `DTP=50 ns` and `DTM=200 ns` explicitly.

This validates the scheduling layer and four replicated local state machines.
It does not upgrade the claim boundary: the electrical interaction among the
four phases through the flying-capacitor ladder remains untested.

## Next permitted change

Do not repeat the rejected R04B complementary-PWM construction. The next
electrical expansion must introduce the P24 Fig. 3 shared ladder together with
the P24 adjacent-phase conduction rule. Its post-negative-current commutation
must remain blocked or symbolic until switch capacitance and dead time are
sourced.
