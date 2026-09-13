# Step 30 - R04E3 zero-start event controller and P24 plant test

## Inserted module

`startup_rotation_controller.py` is a new controller slot. Existing topology,
formula, device, evidence and sequence modules are unchanged. It provides two
non-merged branches:

- `P24_MINIMAL`: completes only P24's same-phase physical-event chain, then
  deliberately enters `BLOCKED_P24_HANDOFF_UNPUBLISHED`.
- `P25_TO_P24_FOUR_PHASE_EXTENSION`: generalizes P25's three-phase event handoff
  to `1->2->3->4->1` and remains labelled `CROSS_PAPER_EXTENSION`.

The transition inputs are physical events, not paper-local t-labels. Every gate
vector is checked for same-phase high/low shoot-through. A planted out-of-order
ZVS event is rejected.

## Logic verification

The full project suite passes `103 tests`. The P25 extension completes four
logical handoffs and returns from phase 4 to phase 1. The P24 branch stops before
an unsupported handoff. A machine-readable trace is at
`project/outputs/diagnostics/R04E3_rotation_controller_logic.json`.

This proves controller ordering and interlock only, not electrical feasibility.

## P24-minimal zero-energy LTspice boundary

- Full existing single-module/four-phase power-stage connections retained.
- P24-minimal commands begin with `QH1+QS2`; no P25 all-inactive-low extension.
- All flying/output capacitor voltages and inductor currents start at zero.
- `Vin=48 V`, `nP=4`, `nM=4`, `L=1.4666667 nH`.
- The first exploratory gate-off current limit is 10 A.
- P24 source-native negative target is tested at 2% of that commanded limit.
- GS61008T scalar device capacitances and on-resistance are called from the
  existing external-device library; no snubber is added.
- The controller must reach the final high-side zero-Vds event to close P24 t3.

## Actual physical-event results

| Event/quantity | Result |
|---|---:|
| QH1 current-limit/gate-off event | 0.3171 ns |
| `iL1` at gate-off | 10.0625 A |
| QL1 zero-Vds event | 2.0617 ns |
| `iL1=0` event | 1.63145 us |
| negative-current target event | 1.73445 us |
| high-side zero-Vds event | **not reached** |
| final controller state at 20 us | state 4: high-side ZVS commutation |
| maximum `iL1` | 43.6808 A |
| minimum `iL1` | -0.200014 A |
| final `Vout` | 0.3718 mV |
| final `VC1` | 1.0578 mV |
| final `VC2`, `VC3` | approximately 0 V |

## Verdict

Status: **LOGIC_PASS; P24_ZERO_START_LOCAL_CYCLE_FAILS_BEFORE_T3**.

The 10-A gate-off boundary is not a 10-A physical peak boundary. During the
1.745-ns high-to-low commutation interval the positive current continues rising
and reaches 43.68 A. At zero start, the output voltage is initially too small to
produce the steady-state current-down slope; reaching `iL1=0` takes 1.63 us,
far longer than P24's 200-ns period at 5 MHz. The 2% negative current then lacks
enough commutation energy to return QH1 Vds to zero, so the controller correctly
does not rotate.

The next experiment must solve the local peak-control boundary before enabling
the P25 four-phase handoff. Specifically, sweep the earlier QH1 gate-off current
and measure total post-commutation peak; do not alter the 5-MHz paper operating
frequency or force a phase transition for numerical convenience.
