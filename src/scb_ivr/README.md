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
  all six commutation-mode event screening; not certified first-event detection or gate control.
- `p25_entry_direction`: P25 nP=3/nM=1 exact-zero reverse-gap direction;
  no epsilon steps, gate actions or four-phase schedule reuse.
- `p25_seed_evaluation`: runs a fixed-boundary candidate; failed trajectories
  have no invented periodic residual. Only completed section returns reach D08.
- `p25_shooting_contract`: six-coordinate SH1 section with frozen device,
  timing, ports and design-peak references; not a periodic solver or observer.
- `p25_period_attempt`: one M1–M15 attempt, full per-step records and
  first-failure return; independently rejects state resets. Section reachability
  is explicitly separate from periodic-state closure.
- `p25_trace_balance`: accepted-segment charge/volt-second ledger; excludes
  failed trial endpoints and distinguishes prefixes from full-cycle coverage.
- `p25_high_on`: sampled competing-event screening through the original
  common on-time; no peak estimation, resumed-history skip or forced handoff.
- `p25_handoff`: conditional P25 nP=3/nM=1 low admission and next-phase
  zero crossing for all three handoffs; state identity and causal peak requirement.
- `p25_negative_handoff`: latched negative target and next-high admission
  for all three handoffs, including M15-to-M1 cycle increment; competing
  boundaries stop the chain. Legacy “second” APIs remain phase-1-only.
- `p25_freewheel_margin`: P25 nP=3/nM=1 endpoint volt-second accounting,
  keeping winding and node-residual terms; no fixed-output or periodic claim.
- `p25_all_low_necessity`: conditional common-volt-second current-order bound;
  rejects or explicitly excludes nonzero winding/node-residual pairs.
- `p25_commutation_charge`: full-network affine target-voltage accounting
  normalized by the active current coefficient; not isolated-device Qoss.
- `p25_commutation_closed_form`: independent P25 M5/M10/M15 capacitor
  elimination formulas; phase positions are not assumed interchangeable.
- `p25_commutation_dynamics`: checks the forced second-order target-Vds
  equation with actual dynamic Vo and winding R; distinguishes Cn from Cx.
- `p25_reduced_commutation`: independently assembled five-state local flow,
  retaining all phase currents and dynamic output; D27 reconstructs all nodes
  from entry constants, but does not replace the main guard scanner.
- `p25_cycle_modes`: P25 M1–M15 main-mode indexing on the same physical
  topology, shared current-sign domains and six physical commutation targets;
  later modes labelled cyclic mapping, not four-phase extension.
- `p25_watch_contract`: model-specific required event names/quantities and
  independent algebraic checks; checks installation coverage, not callbacks.
- `p25_commutation_necessity`: D30 conservative charge/flux obstruction under
  exact zero-R/zero-ON-node assumptions; rejects residual-bearing old seeds,
  and never labels a necessary-condition pass as ZVS success.
- `p25_residual_charge_bound`: D31 retains constant ON-node offsets in the
  affine-continuation charge bound; not an ideal-state/error certificate.
- `p25_energy_ledger`: D32 accepted-prefix input/load/winding/stored-energy
  audit; ON-residual work is explicit and is not physical MOS loss.
- `p25_section_necessity`: D33 distinguishes a general SH1-on debug entry
  from the negative-current section required by M15→M1 periodic return.
- `p25_down_commutation_charge`: D35 separates low-side node-normalized Cx
  from high-side Cn, checking three-phase charge accounting on the same flow.
- `p25_periodic_section`: SH1-on full capacitor/current/control-memory return,
  explicit model identity and dimensionally scaled residuals. Does not establish
  an intervening trajectory, external forcing periodicity, or stability.
