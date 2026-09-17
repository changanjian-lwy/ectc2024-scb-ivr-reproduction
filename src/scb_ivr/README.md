# `scb_ivr` model package

This package contains reusable project logic rather than one-off experiment
outputs. Its modules fall into four groups:

- analytical models: `ivr_framework`, `apec2025_supplements` and
  `commutation_feasibility`;
- topology and event semantics: `physical_events`, `gate_truth_tables`,
  `interval*_branches` and `four_phase_event_ring`;
- modular assembly and evidence control: `evidence`, `model_contracts`,
  `module_registry` and `assembly_planner`;
- controller and startup logic: `p25_np4_controller_emitter`,
  `startup_rotation_controller` and `startup_voltage_supervisor`.

Experiment-specific builders remain under `experiments`; human-run entry
points remain under `scripts`; LTspice measurement readers remain under
`validation`.
