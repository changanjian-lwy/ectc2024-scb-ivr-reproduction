# A20 results - P24 Interval 3, 2% timing audit

## Measurements

| Event | Time | `iL1` / result |
|---|---:|---:|
| Phase-1 current zero | 160.719743 ns | approximately 0 A |
| P24 2% threshold | 164.404743 ns | -2.502284 A |
| Phase-4 support interval ends | 166.666667 ns | - |
| Actual allowed `QL1` release sample | 166.668667 ns | -4.028227 A |

The P24 2% threshold occurs **2.261923 ns before** the phase-4 high-side
interval ends. At the actual release, the negative current is 3.22258% of the
125 A phase peak rather than 1-2%.

After actual release:

- `Vds(QH1)` begins at 11.98264 V;
- its minimum before the next `QH1` command is 6.95018 V at 169.39670 ns;
- it never reaches zero naturally.

## Result

**Fail: the unchanged candidate does not satisfy the complete P24 Interval-3
boundary.** It fails in two linked ways:

1. the 2% negative-current event is not coincident with the end of the required
   cross-phase low-side support interval;
2. even the larger 3.22% current present at the allowed release does not provide
   enough commutation to reduce `Vds(QH1)` to zero before the next command.

Consequently, the next `QH1` edge in this candidate would be a commanded hard
transition rather than demonstrated P24 ZVS.

## What was not changed

No inductance, Coss, snubber capacitance, phase offset, current threshold,
initial state, gate timing, timestep or output boundary was changed. In
particular, A20 does not substitute the previously successful P25/8% local
commutation result for the failed P24 2% result.

## Diagnostic implication, not a new assumption

The model now exposes a concrete missing closure condition: the selected
inductance/current trajectory, interleaved phase timing and commutation charge
must satisfy the 1-2% release event simultaneously. P24 states the desired
events but does not publish the detailed four-phase controller, Coss/additional
capacitance, dead time, or measured timing needed to resolve that closure.

The next action must therefore be a source/parameter reconciliation, not an
unbounded tuning run. The printed P24 equation gives 1.4667 nH for this case,
whereas Table I gives 2.68 nH; that unresolved discrepancy directly affects the
zero-crossing and negative-current timing.
