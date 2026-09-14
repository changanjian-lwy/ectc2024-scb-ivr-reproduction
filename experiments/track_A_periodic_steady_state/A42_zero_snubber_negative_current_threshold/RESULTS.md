# A42 result - local zero-snubber ZVS threshold

## Outcome

With A41's zero-snubber electrical baseline held fixed, the local natural-ZVS
threshold is bracketed between **7.76% and 7.77% of the 125-A phase peak**.

- 7.76% (`9.7000 A` negative): no zero crossing; minimum high-side `Vds` is
  `13.924 mV`.
- 7.77% (`9.7125 A` negative): first zero crossing; high-side `Vds=0` occurs
  at `16.6469 ns`, `2.1551 ns` after low-side release. Inductor current at the
  crossing is `-33.65 mA`, so this boundary is also nearly ZCS.

Refining beyond 0.01 percentage point would overstate the fidelity of the
constant-capacitance device abstraction. The result is therefore stored as a
bracket, not as an exact physical device parameter.

## Coarse sweep

| Negative target | Source label | Target current (A) | Minimum post-release Vds (V) | ZVS | Commutation after release (ns) |
|---:|---|---:|---:|:---:|---:|
| 1% | P24 explicit | 1.25 | 9.257 | no | - |
| 2% | P24 explicit | 2.50 | 7.996 | no | - |
| 3% | diagnostic bridge | 3.75 | 6.644 | no | - |
| 4% | diagnostic bridge | 5.00 | 5.265 | no | - |
| 5% | P25 supplement | 6.25 | 3.874 | no | - |
| 6% | P25 supplement | 7.50 | 2.478 | no | - |
| 7% | P25 supplement | 8.75 | 1.079 | no | - |
| 8% | P25 supplement | 10.00 | 0 event | yes | 1.845 |
| 9% | P25 supplement | 11.25 | 0 event | yes | 1.458 |
| 10% | P25 supplement | 12.50 | 0 event | yes | 1.250 |

The 0.1% refinement first placed the transition between 7.7% and 7.8%. The
predeclared 0.01% grid then produced the final 7.76%-7.77% bracket.

## What this resolves

1. A41 showed that adding passive commutation capacitance moves the P24 1%-2%
   rows away from ZVS.
2. A42 shows that, under the same local state and device-capacitance plug-in,
   the missing resource is commutation energy from negative current: about
   `9.7 A`, not additional capacitance.
3. The independent A42 bracket explains the earlier approximately 7.77%
   observation without using that value as an input.

## Source boundary

The numerical threshold lies inside P25's published 5%-10% control range but
outside P24's published 1%-2% range. That does **not** prove P25 and disprove
P24: the capacitance and resistance plug-ins are P25/external, and the run is a
local P24 state rather than the complete P24 converter. It establishes a
specific model mismatch that can be taken to Mihai:

> With the GS61008T charge-equivalent capacitance plug-in and the chained P24
> local state, ZVS requires 7.76%-7.77%. Which capacitances and participating
> commutation paths were used to obtain the P24 1%-2% statement?

## Next permitted action

Do not silently replace P24 1%-2% with 7.77%. Preserve two branches:

- `P24_EXPLICIT_1_TO_2_PERCENT`: expected to fail under the current device
  plug-in; this is the paper-reproduction branch and blocker.
- `P25_DEVICE_AUGMENTED_7P77_PERCENT`: may be used as a separately labelled
  mechanism branch to test whether the complete four-phase handoff and
  periodic boundaries close.

The next simulation should transplant the bracketed device-augmented threshold
into the existing full four-phase event machine without changing its other
state coordinates, and report the earliest event/boundary failure.
