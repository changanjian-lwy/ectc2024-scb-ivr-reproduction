# A32 constant-Coss sufficiency sweep at the locally aligned P24 2% event

## Fixed boundary

A31 topology, L=1.4667 nH, local `iL2` alignment, 2% target, ideal reverse
clamp, event scheduler and 5 ps maximum timestep are unchanged. Only every
commutation capacitance is multiplied by the declared sensitivity scale.

| Coss scale | `iL2` at release | Minimum `Vds(SH2)` | Minimum time | SH2 ZVS |
|---:|---:|---:|---:|---:|
| 5% | -2.5872 A | -0.000679 V | 17.1434 ns | Yes |
| 10% | -2.5867 A | 2.8641 V | 17.4900 ns | No |
| 25% | -2.5866 A | 5.7366 V | 18.0310 ns | No |
| 50% | -2.5859 A | 7.1543 V | 18.6960 ns | No |
| 75% | -2.5857 A | 7.7654 V | 19.2413 ns | No |
| 100% (A31) | -2.5852 A | 8.1203 V | 19.7251 ns | No |

## Conclusion boundary

The local 2% event reaches ZVS only after the constant timing-equivalent Coss
is reduced to between 5% and 10% of the present datasheet-derived candidate.
This is not permission to select 5% as a fitted device value. At the successful
5% point, the effective values are only 19.25 pF per high-side position and
38.5 pF per two-device low-side position.

Because the source candidate is already an extrapolation from a 0-50 V timing
equivalent, the large discrepancy requires a topology/state audit and a
nonlinear Qoss model. It must not be hidden by capacitance fitting.

## Timing implication

Even the successful 5% sensitivity reaches phase-2 ZVS at 17.143 ns, not near
the nominal 50 ns phase origin. This proves that the present initial-mode
assignment for phase 2 is not yet a valid four-phase periodic rotation. The
next work item is to reconstruct which mode phase 2 occupies at the selected
global `t=0`, then solve the full phase-shifted periodic state.
