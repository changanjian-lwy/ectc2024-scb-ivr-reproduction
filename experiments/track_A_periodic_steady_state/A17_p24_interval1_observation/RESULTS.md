# A17 results - P24 Interval 1

## Run performed

The unchanged A16 netlist was re-run in LTspice and its `t0-t1` window was
extracted with `analyze_interval1.py`. The extraction starts at 2 ps to avoid
sampling the exact ideal-switch discontinuity at zero time.

## Measurements

| Quantity | Result |
|---|---:|
| Paper-derived `TON` | 16.6666667 ns |
| `iL1` at start sample | -0.888913 A |
| `iL1` at end sample | 119.334801 A |
| Increase over Interval 1 | 120.223713 A |
| Average `di/dt` | 7.213433 A/ns |
| Effective average `vL=L*di/dt` | 10.579702 V |
| P24 ideal peak target | 125 A |
| End current / ideal target | 95.467841% |
| End-current error | -5.665199 A |

The current rises monotonically over the sampled interval. Therefore the
primary causal check passes: the P24 Interval-1 command state applies positive
average voltage to `L1` and charges its current on the correct timescale.

## Interpretation without tuning

The run does not exactly reach the P24 ideal `125 A` target. The electrical
model already contains the P25-sourced `7 mOhm` high-side resistance, finite
commutation capacitance and a periodic shooting seed whose residual is small
but nonzero. Those locked conditions reduce the average inductor voltage from
the approximate ideal `12 V - 1 V = 11 V` to an extracted `10.58 V`, and the
start current is `-0.889 A` rather than exactly zero. No inductance, pulse width,
initial state or device parameter was changed after seeing the result.

## Claim boundary

This is a successful **Interval-1 mechanism and scale check** on the current
periodic candidate. It is not yet an exact reproduction of the P24 peak, and it
does not establish zero startup, ZVS, loss, passive voltage balancing, removal
of the output clamp, or four-module performance.

The next logically separate experiment is the `t1` turn-off/Coss commutation
event. Before starting it, the stage-entry state should be taken from this
unchanged run and the acceptance condition must be defined as the low-side
`Vds` reaching zero, not as a tuned dead time.
