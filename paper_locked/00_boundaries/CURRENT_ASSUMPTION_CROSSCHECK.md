# Current-model assumption cross-check: P24, P25 and Track A01

## Scope and rule

This comparison applies to the Track-A single-module, four-phase periodic-state
experiment. It does not claim zero-start operation, complete hardware ZVS,
loss, thermal or package reproduction.

Device-inherent output capacitance and added snubber capacitance are separate
inputs. The P24/P25 negative-current boundary is a control input and is not
fitted by changing either capacitance.

## Assumption comparison

| Topic | P24 treatment | P25 treatment | Current A01 treatment | Remaining difference |
|---|---|---|---|---|
| Operating point | 48 V to 1 V, 1 kW, 4 phases, 4 modules, 5 MHz analytical design | 12 V to 1 V, 200 W, 3 phases, 3 modules, 0.5 MHz prototype | One 250 W module of the P24 system, 4 phases, 5 MHz | Four-module system is a later Track-A gate |
| Periodic versus startup | Derives steady boundary operation; no startup sequence | Analyses periodic modes; no complete startup/precharge sequence | Periodic-state seed only; 36/24/12 V and 1 V are initial guesses, not forced final results | A01 cannot claim zero-start behavior |
| Flying-capacitor ripple | Uses steady charge/volt-second balance; no complete numeric capacitor model | Initially assumes C1/C2 ripple is zero for mode derivation, then includes ripple in design considerations | Finite 53.8 uF candidate capacitors, so ripple is allowed | Value is cross-source candidate, not a P24 value |
| Output capacitor | Conceptual/ripple discussion; no complete populated value | Gives capacitor family but incomplete suffix/value | Finite candidate bank | Not paper-unique |
| Switch model | Switching modes use inherent Coss and idealized switching arguments | GaN prototype, RDS(on), inherent Coss plus added snubbers; detailed nonlinear model omitted | Ideal voltage-controlled switches with P25/datasheet Ron | No gate-charge, temperature or full GaN behavioral model |
| Device Coss | Explicit physical commutation mechanism; no number | Explicit physical mechanism; no number in paper | Independent device module: GS61008T Co(tr), 385 pF HS and 770 pF LS | Scalar 0-50 V timing equivalent is extrapolated to the local voltage swing |
| Added snubber | Says an extra nanofarad-range parallel capacitor can reduce overlap | States added snubbers exist on all switches, but omits their values | Independent snubber slots, both set to zero | Hardware snubber value remains unknown |
| Coss nonlinearity | Not numerically specified | Not numerically specified | Constant time-equivalent capacitance | Qoss/Coss(Vds) model remains a later plug-in |
| Negative current | 1-2% of phase peak | Mode text 5-10%; design section says up to 5% | P24 branch fixed at 2% of 125 A | Threshold is not recalibrated to make Coss commutation pass |
| Dead time and delay | No numeric dead time/controller delay | Discusses Mode 2'/5' and high-frequency ZCD, but omits numeric settings | No inserted numeric dead time or delay | Cannot claim hardware switching-loss reproduction |
| Inductor | Printed equation and Table I disagree; user selected equation result | 22 nH hardware case at a different operating point | 1.4667 nH from P24 printed equation | Table-I 2.68 nH discrepancy remains documented |
| Interleaving | Four phases and parallel modules | Explicit phase/module shifts and three-phase mode detail | Four phases shifted by T/4; one module only | Module interleaving not exercised yet |
| Balance | Periodic volt-second and capacitor charge balance | Natural balance under stated operating constraints | Full slow-state residual is measured after one period | First all-zero-current seed does not close the periodic orbit |
| Parasitic R/L, ESR/ESL | Package implications discussed, but no extracted circuit set | Prototype exists, but full layout parasitic set omitted | Excluded except explicit switch Ron and 1 uOhm numerical inductor damping | Not a hardware-loss/EMI model |

## Active capacitance interface

- `CH_DEVICE = 1 x 385 pF`
- `CL_DEVICE = 2 x 385 pF = 770 pF`
- `CH_SNUBBER = 0`
- `CL_SNUBBER = 0`
- `CH_TOTAL = CH_DEVICE + CH_SNUBBER`
- `CL_TOTAL = CL_DEVICE + CL_SNUBBER`

Changing a future snubber value changes only the snubber slot. It does not
modify the device data, topology, phase count, negative-current threshold,
initial state or controller sequence.

## Verification status

- Python modular/regression suite: 110 tests pass.
- The capacitance module has tests for device population, zero-snubber
  preservation, independent addition and rejection of negative capacitance.
- A01's electrical values are intentionally unchanged from its preceding
  device-Coss run; only the parameter assembly is separated.
- The modular A01 netlist was re-run successfully through the direct CrossOver
  launcher. LTspice loaded both the device-data and commutation-capacitance
  libraries. The measured values are identical to the preceding A01 result,
  confirming that this refactor changed parameter assembly but not the
  electrical case.
