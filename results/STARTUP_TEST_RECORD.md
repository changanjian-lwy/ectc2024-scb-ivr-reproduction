# ECTC 2024 four-phase module: startup versus steady-state tests

## Test separation

- Periodic steady-state test: `ectc2024_verified_4phase_module.net` starts the
  flying capacitors at 36 V, 24 V and 12 V. It verifies operation near the
  intended staircase, not acquisition of that staircase.
- Zero-initial-voltage startup test: `ectc2024_startup_4phase_module.net` starts
  all three flying capacitors discharged. It uses a 0-to-48 V input ramp from
  2 us to 22 us and an assumed 20 mOhm/10 nH input impedance. Fixed 5 MHz PWM
  begins at 2 us. No published startup/precharge/balancing controller exists in
  the model.

## First startup diagnostic run

Simulation window: 0-120 us. Final averages use 110-120 us; drift compares the
90-100 us and 110-120 us windows.

| Quantity | Result |
|---|---:|
| Average `VC1`, final window | 9.857 V |
| Average `VC2`, final window | 6.209 V |
| Average `VC3`, final window | 3.029 V |
| `VC1` drift over comparison windows | +1.176 V |
| `VC2` drift over comparison windows | +0.837 V |
| `VC3` drift over comparison windows | +0.431 V |
| Average output voltage, final window | 0.332 V |
| Peak input-source current | 81.306 A |
| Peak `L1` current | 78.603 A |
| Peak `L2` current | 14.222 A |
| Peak `L3` current | 9.169 A |
| Peak `L4` current | 6.643 A |

## Interpretation boundary

The target 36/24/12 V staircase was not acquired within 120 us, and all three
capacitor averages were still drifting upward. The large and unequal phase
current peaks expose a startup-stress problem under the assumed open-loop PWM.
This does not prove that the published topology cannot self-balance over a
longer interval or with a proper controller. It proves only that the existing
precharged steady-state test cannot be used as evidence of safe self-starting,
and that startup/precharge/current-limit strategy is a required open design
input for a defensible framework.
