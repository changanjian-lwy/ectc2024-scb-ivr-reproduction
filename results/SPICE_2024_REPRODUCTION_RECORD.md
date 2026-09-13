# ECTC 2024 SPICE Reproduction Record

## Objective

Reproduce the proposed 48 V to 1 V, 1 kW IVR architecture in Fig. 3 of the
2024 ECTC paper. The implemented system contains eight parallel modules,
four interleaved phases per module, and 32 electrical phases in total.

## Input -> Model -> Output

Input parameters:

- System input voltage: 48 V
- Target output voltage: 1 V
- Target output power: 1 kW
- Parallel modules: 8
- Phases per module: 4
- Switching frequency: 5 MHz
- Embedded inductors per phase: 12 in parallel
- Single embedded inductor: 36.7 nH
- Equivalent phase inductance: 3.058 nH

Model transformation:

1. Each module applies the published four-phase series-capacitor buck
   topology.
2. In the reported steady-state runs, the three flying capacitors are
   initialized to 36 V, 24 V and 12 V; the simulation then checks whether the
   converter remains close to this intended voltage staircase.
3. Four phases are shifted by 90 electrical degrees.
4. Eight modules share the 48 V input and 1 V output and are shifted by T/8.
5. The 32 phase currents sum at the common output capacitor and load.

Automatically recorded outputs:

- Average and peak-to-peak output voltage
- Input and output power
- Estimated efficiency for the assumed loss model
- Average output current of every module

## Full-system LTspice Result (2026-09-08)

| Quantity | Paper target / relationship | SPICE result | Assessment |
|---|---:|---:|---|
| Output voltage | 1 V | 0.9942369 V | -0.576% |
| Output power | 1 kW | 988.507 W | -1.15% |
| Output ripple | Not numerically specified | 6.136 mV p-p | Recorded |
| Module current | 125 A nominal | 124.245-124.293 A | Balanced |
| Total architecture | 8 x 4 phases | 32 phases | Matched |
| Input current | Derived by simulation | 27.4137 A | Recorded |
| Estimated input power | Derived by simulation | 1315.86 W | Recorded |
| Estimated efficiency | No 1 kW hardware result in paper | 75.12% | Assumption-sensitive |

Maximum module-current spread is about 0.048 A, or 0.039% of nominal module
current. This confirms output-current sharing in the idealized interleaved
architecture.

## Single-module Validation

- Output voltage: 0.994435 V
- Phase average currents: 31.1205, 30.9693, 30.9732 and 31.2420 A
- Flying-capacitor average voltages: 36.1815, 24.0812 and 11.9825 V
- Phase-1 peak current: 67.7814 A
- Phase-1 negative current: -1.7606 A
- Negative-current magnitude: 2.597% of positive peak
- Minimum high-side VDS: -0.745 V, demonstrating that the commutation path
  crosses the zero-voltage point.

## Flying-Capacitor and Node-Voltage Initialization Boundary

The full-system and single-module results above are periodic steady-state
tests, not startup tests. In both netlists, the flying-capacitor voltages are
explicitly initialized as follows:

| Initialized quantity | Netlist definition | Initial value |
|---|---|---:|
| `VC1 = V(a1, sw1)` | `C1 ... IC=36` | 36 V |
| `VC2 = V(a2, sw2)` | `C2 ... IC=24` | 24 V |
| `VC3 = V(a3, sw3)` | `C3 ... IC=12` | 12 V |
| Output node | `.ic V(out)=1` | 1 V |

The switch nodes `sw1`-`sw4` are not independently forced to 12 V. Their
instantaneous voltages follow from the initialized capacitor voltages, switch
states, output voltage and circuit dynamics. For example, when the first
high-side switch conducts under the ideal staircase assumption,
`V(sw1) ~= Vin - VC1 ~= 12 V`.

After initialization, the single-module steady-state test produced average
flying-capacitor voltages of 36.1815 V, 24.0812 V and 11.9825 V and an average
output voltage of 0.994435 V. This shows that the assumed circuit and control
remain close to the intended periodic operating point. It does **not** show
that discharged flying capacitors naturally acquire this operating point.

### Separate zero-initial-voltage startup experiment

The diagnostic netlist `ectc2024_startup_4phase_module.net` removes the
36/24/12 V initial conditions. It starts the flying capacitors at 0 V, ramps
the input from 0 V to 48 V over 20 us, and includes an assumed 20 mOhm/10 nH
input impedance. No precharge, active balancing, current-mode control or
over-current protection is included because the paper does not publish these
startup details.

At 120 us, the startup experiment gave:

| Quantity | 110-120 us average / measured peak |
|---|---:|
| `VC1` | 9.857 V |
| `VC2` | 6.209 V |
| `VC3` | 3.029 V |
| Output voltage | 0.332 V |
| Peak input-source current | 81.306 A |
| Peak `L1`, `L2`, `L3`, `L4` currents | 78.603, 14.222, 9.169, 6.643 A |

The capacitor averages were still increasing: between the 90-100 us and
110-120 us windows, `VC1`, `VC2` and `VC3` changed by +1.176 V, +0.837 V and
+0.431 V. Therefore the target staircase had not been acquired in the tested
window, and the large unequal phase peaks reveal startup stress under the
assumed open-loop PWM.

This result does not prove that the topology cannot eventually self-balance or
that a hardware implementation cannot start correctly. It demonstrates that
the pre-initialized steady-state result cannot be cited as proof of self-start,
and that a defensible framework needs a separate startup/precharge/current-limit
model once the intended control method is known.

## Published Values Versus Assumptions

Published or directly derived from the paper:

- Topology and phase/module counts
- 48 V, 1 V and 1 kW ratings
- 5 MHz design point
- Duty-ratio relationship
- 12 parallel embedded inductors per phase
- 36.7 nH per embedded inductor at 5 MHz

Explicit assumptions because exact values/models are not published:

- Flying capacitance and ESR
- Output capacitance and ESR
- Switch on-resistance and Coss
- Diode/reverse-conduction approximation
- Gate dead time
- Practical duty command used to compensate the assumed conduction losses
- Ideal 36/24/12 V flying-capacitor initialization and 1 V output initialization
  in the reported periodic steady-state runs

Therefore, voltage conversion, maintenance of the pre-established capacitor
staircase, phase sharing and boundary commutation are valid steady-state
reproduction checks. Natural startup acquisition has not been validated. The
75.12% efficiency result is a model estimate and must not be presented as a
measured result from the paper.

## Modular Modification Points

- Change voltage, power, frequency, module count and phase-related design
  values in the parameter block at the top of the netlist.
- Duplicate or remove an `XMOD` line to change the number of physical modules.
- Modify the `SCB4` subcircuit once to change every module consistently.
- Add series resistance or capacitance inside `SCB4` when studying package
  parasitics.
- Keep paper-derived parameters separate from assumed component parameters so
  every comparison remains auditable.
