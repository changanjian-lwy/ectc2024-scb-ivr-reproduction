# A04 results - interleaved phase readiness on the full four-phase ladder

## Accepted run

The corrected controller is a detachable top-level latch. It observes the full
four-phase power stage and drives explicit gate-command ports. The power-stage
connections are unchanged from A01. The P24 2% branch remains selected.

| Phase | Nominal origin | Absolute node monitor | Local segment at origin | Actual gate-on | Release delay | Local segment at release |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 50 ns | `a2=25.2817 V` | `a1-a2=10.4231 V` | 50.00086 ns | 0.000855 ns | 10.4233 V |
| 3 | 100 ns | `a3=12.9343 V` | `a2-a3=10.7876 V` | 100.00113 ns | 0.001127 ns | 10.7869 V |
| 4 | 150 ns | monitored through local segment | `a3-x4=9.7419 V` | 150.82665 ns | 0.826653 ns | 9.9989 V |

Phases 2 and 3 enter the 10-14 V readiness window at their nominal origins and
are released essentially immediately. Phase 4 is below the lower boundary at
150 ns, so the latch correctly waits until its local segment reaches about
10 V instead of forcing the nominal timing.

## What this establishes

1. An absolute `a2=24 V` equality is not a suitable release condition. The
   accepted run has `a2=25.2817 V`, while the physically relevant local segment
   is available and phase 2 is released.
2. The full ladder couples the phases: preceding phase currents and capacitor
   charge alter the voltage presented to each later high-side switch.
3. A continuously evaluated ideal comparator is not numerically or physically
   adequate because its own gate action perturbs the observed voltage. A
   sampled/latched release realization is required.
4. The one-period state still does not close: current residuals remain large,
   especially `dIL3=40.62 A` and `dIL4=80.47 A`. This is expected from the
   all-zero-current first seed and the retained P24 2% branch. The readiness
   result must not be reported as a complete periodic-orbit or all-phase-ZVS
   success.

## Failed implementations retained

- Direct continuous window gating chattered near 50 ns and was terminated.
- Moving `.machine` inside the subcircuit left gate outputs unbound in this
  LTspice hierarchy. It was rejected without an electrical claim.
- The accepted implementation keeps the controller at top level and the SCB4
  power stage behind explicit gate ports.
