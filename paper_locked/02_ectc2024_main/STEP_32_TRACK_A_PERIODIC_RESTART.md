# Step 32 - Restart Track A: P24 periodic steady-state reproduction

## Decision

Track A is the main reproduction objective. Track B zero-start experiments
R04E0-R04E4 are preserved as an engineering extension and no longer gate the
paper steady-state reproduction.

## Periodic-state boundary

The one-module orbit uses `nP=4`, `nM=1` at the circuit-assembly level while
retaining the system design point `nM=4` for phase-current and Table-I equations.
The later system assembly instantiates four such modules. These two meanings
must not be collapsed into one parameter.

The periodic shooting state contains eight independent values:

- `VC1, VC2, VC3`;
- `iL1, iL2, iL3, iL4` at one declared period origin;
- `Vout`.

`36/24/12 V` is permitted only as the first capacitor-voltage seed. All four
initial currents must remain solver variables; setting them all to zero is not
accepted merely because one phase begins a cycle at zero. Pass requires the
complete final state after 200 ns to match the complete initial state, followed
by independent average-output, ripple, charge-balance and ZVS checks.

## Legacy audit

The historical file `project/circuit/ectc2024_verified_4phase_module.net` is not
a current Track-A result. It uses an eight-module/125-W example, changes duty to
0.102, inserts unsourced capacitor and timing values, and drives low sides with
ordinary complementary PWM. It remains on disk for provenance only.

## Current executable foundation

- Track definitions are executable in `reproduction_tracks.py`.
- The eight-state interface and periodic residual are executable in
  `periodic_state_contract.py`.
- A planted phase-3 current closure error is detected by unit test.
- The full suite passes 106 tests.

## Next netlist gate

Two non-merged one-period command branches must be emitted:

1. P24-source branch with 1%-2% same-phase negative-current exit and explicit
   blocking wherever the four-phase command vector remains unpublished;
2. P25-supplemented four-phase handoff branch, labelled cross-paper extension,
   with 5%-10% retained separately.

Neither branch may use full-off-time complementary low-side PWM. The first
numerical run will use the `36/24/12 V` voltage seed, expose all four current
seeds, and report the full residual even when it fails to close.
