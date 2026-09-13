# Model assumptions for the 2024 ECTC SCB-IVR reproduction

> **Legacy-model warning:** this file records assumptions used by early
> no-precharge simulations. It is not an active parameter source for the new
> modular framework. In particular, the old `T/(nP*nM)` module-offset rule is
> superseded by the P25 statement `T/nM` and all netlists using the old rule
> remain historical diagnostics only.

## Scope

Baseline target: 48 V to 1 V, 1 kW, four phases per module and four parallel
modules. Table 1 is an analytical design table; SPICE is used as a separate
time-domain topology and operating-mode check.

## Assumptions stated or directly used by the 2024 paper

- Ideal conversion relationship: `D = nP*Vo/Vin`.
- Identical switching frequency and duty cycle for all high-side switches and
  likewise for the low-side switches.
- Interleaved phases and parallel interleaved modules.
- Every phase operates at the CCM/DCM boundary; ideal phase current is treated
  as a 0-to-peak-to-0 triangle.
- Ideal peak-current relation: `IL,pk = 2*Io/(nP*nM)`.
- Periodic inductor volt-second balance and series-capacitor ampere-second
  balance are assumed.
- The adjacent phases charge and discharge each series capacitor, providing
  natural charge and current sharing under balanced operation.
- A minimum high-side on-time of 3.4 ns is assumed for available power
  semiconductors, without a named switch/driver/controller basis.
- Printed critical-inductance equation:
  `Lcrit = nP*nM*Vo*(1-nP*Vo/Vin)/(2*Io*fsw)`.
- Practical inductance is proposed as 1-2% below `Lcrit` to generate a small
  negative current for ZVS.
- High-side turn-off uses inherent `Coss`; an additional nanofarad-range
  parallel capacitance may reduce voltage/current overlap.
- The package, thermal, mechanical, EMI and reliability discussion is
  conceptual; a complete loss/thermal/startup/controller model is not given.

## Clarifications and additions supplied by the 2025 APEC paper

- The low-side switch sources in the three-phase prototype are explicitly
  drawn connected to common ground.
- Detailed switching intervals show high-side and low-side ZVS/ZVZCS
  commutation and zero-cross detection.
- Up to 5% negative peak current is proposed to discharge high-side snubber
  capacitance while limiting circulating loss.
- The 2025 design equation is `L = 0.95*Lcrit`, reinforcing the printed 2024
  equation rather than the inconsistent Table 1 inductance values.
- The voltage conversion relationship remains `Vo/Vin = D/nP`, with
  `D <= 1/nP` to prevent high-side overlap and preserve balance.
- One current sensor per module is proposed because the module inductors are
  assumed to achieve automatic volt-second balance.
- Experimental validation is 12 V to 1 V, 200 W, 0.5 MHz, three phases and
  three modules; it is not a 48 V, 1 kW packaged prototype.

## Additional assumptions required by the no-precharge SPICE model

These are visible parameters and are not claimed as published values:

- flying capacitance 2 uF and ESR 0.5 mOhm;
- output capacitance 2 mF and ESR 0.1 mOhm;
- idealized switch resistances of 1 mOhm;
- fixed linear high-/low-side output capacitances of 100/200 pF;
- 0.1 V reverse-conduction diode approximation;
- 0.2 ns dead time;
- 5 mOhm and 10 nH input-source impedance;
- a 40 us 0-to-48 V source ramp and fixed open-loop PWM enabled at 5 us;
- no capacitor-voltage initial conditions and no output-voltage initial
  condition;
- no precharge controller, active capacitor-balancing loop, current-mode
  control, over-current protection, detailed gate driver, nonlinear `Coss`,
  temperature dependence, package extraction or FEM model;
- **SUPERSEDED:** the early model offset four modules by `T/(nP*nM)`. P25 Sec.
  II instead states a module shift of `360/nM`, corresponding to `T/nM`.

## Table 1 audit boundary

For four phases and four modules, the printed relationships reproduce 250 W
per module, 8.333% duty cycle, 125 A phase peak current and the reported on-time
values to rounding. Equation (4), however, gives 7.333, 1.467, 0.733, 0.147 and
0.073 nH at 1, 5, 10, 50 and 100 MHz. Table 1 reports 13.44, 2.68, 1.34, 0.28
and 0.14 nH. The mismatch is about a factor of 1.83-1.91 and is not explained by
the 2025 factor of 0.95.

## No-precharge four-module SPICE result

The complete four-module topology ran successfully at the nominal 5 MHz point
with two stepped inductance cases and without any imposed flying-capacitor or
output-voltage initial condition.

| Result at 380-400 us | Eq. (4), 1.4667 nH | Table 1, 2.68 nH |
|---|---:|---:|
| Calculated `Ton` | 16.667 ns | 16.667 ns |
| Calculated duty | 8.333% | 8.333% |
| Table-relation phase peak current | 125 A | 125 A |
| Simulated output voltage | 0.369 V | 0.409 V |
| Simulated Module-1 `VC1` | 14.075 V | 15.942 V |
| Simulated Module-1 `VC2` | 9.405 V | 10.623 V |
| Simulated Module-1 `VC3` | 4.686 V | 5.301 V |
| Simulated Module-1 `L1` maximum, 300-400 us | 33.983 A | 35.246 A |
| Simulated Module-1 `L1` minimum, 300-400 us | -20.608 A | -1.537 A |
| Startup peak input-source current | 162.480 A | 154.956 A |

Neither case acquired the intended 36/24/12 V, 1 V-output periodic state
within 400 us using the assumed source ramp and open-loop PWM. Consequently,
these transient values must not be compared directly with the steady-state
125 A triangular-current relationship as if the converter had already reached
the analytical operating point.

The negative result exposes a missing transition between the papers' analytical
steady-state assumptions and practical operation: a startup/precharge/current-
limit strategy. It does not resolve the Table 1 inductance discrepancy and does
not prove that the topology cannot reach balance under a different startup
controller or over a longer interval.
