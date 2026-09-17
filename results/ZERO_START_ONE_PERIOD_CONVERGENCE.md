# Zero-start theoretical solver: first-period convergence

## Boundary

This is a numerical-method audit of the hybrid mathematical model, not a
startup result. The R04E18 reference boundary is frozen: one 250 W module,
`Cfly=3 uF`, `Cdiv=300 uF`, `Tramp=22.87 us`, ideal switches/diodes and true
zero stored energy. Only the maximum integration step changes.

The observation interval is one 5 MHz period (`200 ns`). At its end the
commanded source ramp has reached only about `0.4198 V`, so millivolt node
voltages and milliampere phase currents are expected and must not be read as a
failed or successful startup.

## Result

| Maximum step | Accepted steps | Diode transitions | a1 | a2 | a3 | L1 | L2 | L3 | L4 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 ns | 104 | 6 | 4.760 mV | 3.148 mV | 1.567 mV | 0.027 mA | 0.917 mA | 3.722 mA | 9.141 mA |
| 1 ns | 204 | 6 | 4.697 mV | 3.107 mV | 1.546 mV | 0.022 mA | 0.846 mA | 3.566 mA | 8.909 mA |
| 0.5 ns | 404 | 7 | 4.666 mV | 3.086 mV | 1.535 mV | 0.019 mA | 0.812 mA | 3.487 mA | 8.793 mA |
| 0.25 ns | 804 | 7 | 4.650 mV | 3.075 mV | 1.530 mV | 0.018 mA | 0.794 mA | 3.447 mA | 8.735 mA |
| 0.125 ns | 1604 | 7 | 4.642 mV | 3.070 mV | 1.528 mV | 0.018 mA | 0.786 mA | 3.428 mA | 8.705 mA |
| 0.0625 ns | 3204 | 7 | 4.638 mV | 3.067 mV | 1.526 mV | 0.018 mA | 0.781 mA | 3.418 mA | 8.691 mA |

The 2 ns and 1 ns runs miss one diode transition and are rejected for future
reference work. At 0.5 ns and below the event count is stable. The 0.125 to
0.0625 ns change is small on the physical project scales (48 V and 125 A),
while the largest relative difference belongs to `L1` only because its value
is close to zero. Descriptor residuals remained below `2.2e-11` in the finest
run.

## Decision

- `0.125 ns` is permitted for exploratory multi-period work.
- `0.0625 ns` is the present reference step for any reported mathematical
  trajectory.
- A long-run conclusion must compare both steps over selected checkpoints; a
  single-step result is not admissible.
- This does not validate the ideal component boundary or the eventual handoff
  controller.

Run `python3 scripts/audit_zero_start_one_period.py` to reproduce the complete
JSON record.
