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
- `p25_event_guards`: simultaneous-state event quantities, downward brackets,
  gate-request voltage criteria, negative-current overshoot and unknown reverse
  thresholds. Not a root locator, controller latch or clamp-current solver.
- `p25_reverse_contract`: explicit ideal/constant-drop OFF reverse-channel
  complementarity, local active sets, all-phase mode-current sign checks and
  unresolved ideal-loop degeneracy. No default real-device reverse drop.
- `p25_control_memory`: ideal zero-delay event controller with causal peak
  records, latched gates/negative target and unchanged electrical coordinates.
  Native common on-time only; root location/plant feasibility stay external.
- `p25_root_location`: numerical root brackets, uncertain event-time ordering,
  and an explicit ideal gate/reverse-boundary batch with pre/post D05 checks.
  Does not certify trajectory continuity or completeness of supplied events.
- `p25_local_flow`: constant-port full-network affine continuation and sampled
  M2/M5 event screening; not certified first-event detection or gate control.
- `p25_entry_direction`: P25 nP=3/nM=1 exact-zero reverse-gap direction;
  no epsilon steps, gate actions or four-phase schedule reuse.
- `p25_handoff`: conditional P25 nP=3/nM=1 M2-to-M3 joint event and M3-to-M4
  entry; electrical state identity, explicit causal peak requirement, no defaults.
- `p25_negative_handoff`: same first-handoff branch, M4 latched target and
  M5-to-M6 joint high-side admission; competing boundaries stop the chain.
- `p25_freewheel_margin`: P25 nP=3/nM=1 endpoint volt-second accounting,
  keeping winding and node-residual terms; no fixed-output or periodic claim.
- `p25_cycle_modes`: P25 M1–M15 main-mode indexing on the same physical
  topology; later modes labelled cyclic mapping, not four-phase extension.
- `p25_watch_contract`: model-specific required event names/quantities and
  independent algebraic checks; checks installation coverage, not callbacks.
- `p25_periodic_section`: SH1-on full capacitor/current/control-memory return,
  explicit model identity and dimensionally scaled residuals. Does not establish
  an intervening trajectory, external forcing periodicity, or stability.
