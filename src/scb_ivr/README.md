# `scb_ivr` model package

This package contains reusable project logic rather than one-off experiment
outputs. Its modules fall into four groups:

- analytical models: `ivr_framework`, `apec2025_supplements` and
  `commutation_feasibility`;
- parameter-independent audits: `feasibility_envelope` and
  `parameter_contract`;
- device and partial-loss contracts: `device_library` keeps per-device data
  separate from paper-owned parallel counts, while `conduction_loss` requires
  high-side, low-side and dead-time current paths to be reported separately;
- zero-start mathematics: `zero_start_descriptor` compiles the latest
  cross-paper startup boundary into a mode-dependent MNA descriptor system;
  `zero_start_hybrid_solver` advances that DAE with PWM-edge alignment and
  diode complementarity admission;
- topology and event semantics: `physical_events`, `gate_truth_tables`,
  `interval*_branches` and `four_phase_event_ring`;
- modular assembly and evidence control: `evidence`, `model_contracts`,
  `module_registry` and `assembly_planner`;
- controller and startup logic: `p25_np4_controller_emitter`,
  `startup_rotation_controller` and `startup_voltage_supervisor`.

Experiment-specific builders remain under `experiments`; human-run entry
points remain under `scripts`; LTspice measurement readers remain under
`validation`.

Definition audit additions (not yet wired into legacy solvers):

- `timing_contract`: separates nominal, command, effective-gate and Vds events.
- `p25_native_events`: source-checked P25 three-phase first-handoff specification;
  order-only validation and Eq. (11)-derived negative-ramp time. Does not reuse
  ambiguous printed-time aliases in `physical_events`, extend to four phases,
  or assert electrical feasibility from event order alone.
- `p25_nodal_contract`: the same P25 three-phase topology with explicit finite
  capacitances, ideal gate constraints, dynamic Co/current ports, instantaneous
  KCL and power audit; M2/M5 reductions and continuous-energy-state checks.
  No transient integration or OFF reverse-conduction model is supplied.
