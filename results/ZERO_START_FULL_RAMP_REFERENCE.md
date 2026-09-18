# Zero-start theoretical full-ramp reference

## Frozen boundary

- One 250 W, four-phase P24-connected module.
- `Vin: 0 -> 48 V` in `22.87 us`.
- Fixed 5 MHz PWM from `t=0`.
- `Cfly=3 uF`, `Cdiv=300 uF`, `Cout=4.672 mF`.
- Ideal-switch/ideal-diode Track-B boundary, zero initial stored energy.
- No 36/24/12 V initialization and no 1 V output clamp.

This is a `CROSS_PAPER_EXTENSION` theoretical trajectory, not a P24 startup
reproduction. The simulation stops at the end of the input ramp; unlike the
R04E18 LTspice cases, it does not include the following 300 us settling
interval.

## Step-size comparison at `t=22.87 us`

| Quantity | 0.125 ns exploratory | 0.0625 ns reference | Difference |
|---|---:|---:|---:|
| Diode transitions | 713 | 715 | +2 |
| `VC1` | 34.272248 V | 34.272129 V | -0.119 mV |
| `VC2` | 23.453860 V | 23.454040 V | +0.180 mV |
| `VC3` | 11.244628 V | 11.245119 V | +0.490 mV |
| `Vout` | 0.988063 V | 0.988487 V | +0.424 mV |
| `IL1` | 161.6450 A | 161.7325 A | +0.0875 A |
| `IL2` | 197.4037 A | 197.6394 A | +0.2356 A |
| `IL3` | 73.3771 A | 73.5862 A | +0.2092 A |
| `IL4` | 95.7864 A | 95.7507 A | -0.0357 A |
| Input-inductor current | 173.9991 A | 173.9999 A | +0.0008 A |
| Full-run peak phase-current magnitude | 205.493 A | 205.859 A | +0.366 A |
| Full-run peak input-current magnitude | 177.317 A | 177.319 A | +0.002 A |
| Full-run peak output voltage | 0.988063 V | 0.988487 V | +0.424 mV |

The primary electrical state is converged on the project's 48 V/125 A scales.
The finest run's maximum linear-system residual is `2.5e-7`, small relative
to the conductance/current scales of this idealized MNA system.

## Event audit

The exploratory and reference runs first differ in cumulative diode-event
count between 20 and 21 us. The reference step resolves two additional short
submodes. The first newly visible off/on pair is separated by one reference
step (`62.5 ps`) immediately after a PWM boundary; later instances become
longer. This is consistent with a short commutation submode emerging as the
ladder approaches its target, not with pervasive timestep-by-timestep chatter.

Nevertheless, exact diode-event timing is not declared converged. The valid
current conclusion is:

- state trajectory: converged sufficiently for the next reduced-model step;
- exact onset/duration of the shortest diode submode: still step-sensitive;
- hardware switching loss or dead-time conclusion: prohibited under the ideal
  boundary.

## Physical result at the end of the ramp

All three flying-capacitor voltages and `Vout` rose monotonically at the stored
period checkpoints. Their end-of-ramp errors relative to 36/24/12/1 V are
approximately `-4.80%`, `-2.27%`, `-6.29%`, and `-1.15%` respectively.

The voltage proximity is not a handoff pass. At the same instant the four phase
currents are approximately `161.7/197.6/73.6/95.8 A`, so the system is not on
a demonstrated Track-A periodic state and is not at a zero-current release
surface. A post-ramp periodic-state acquisition/handoff calculation remains
required.

The peak input current (`177.3 A`) remains close to the divider-only analytical
base current (`157.4 A`). This reinforces the conclusion that passive-divider
charge demand is the dominant first-order startup-current mechanism in this
boundary.

## Next mathematical gate

1. Preserve the full end-of-ramp state and continue with `Vin=48 V`.
2. Build a post-ramp Poincare map sampled at one fixed PWM event.
3. Check convergence toward a Track-A periodic state using capacitor voltage,
   all four phase currents and mode identity—not voltage proximity alone.
4. Calibrate a reduced period map against selected reference checkpoints before
   using it for parameter sweeps.
