# `scb_ivr` model package

This package contains reusable project logic rather than one-off experiment
outputs. Its modules fall into four groups:

- analytical models: `ivr_framework`, `apec2025_supplements` and
  `commutation_feasibility`;
- parameter-independent audits: `feasibility_envelope` and
  `parameter_contract`;
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
