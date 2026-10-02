# Runnable workflows

- `run_reproduction.py` generates the analytical design-space sweep.
- `reproduce_table1_4phase_4module.py` audits the P24 Table-I target row.
- `startup_rotation_experiment.py` records the two startup-sequence branches.
- `startup_supervisor_experiment.py` evaluates the startup-readiness observer.
- `analyze_parameter_envelope.py` prints the P24/P25 necessary-condition
  envelope and the claim-level minimum-information contract without fitting
  unpublished device values.
- `audit_zero_start_one_period.py` performs the mandatory first-period
  time-step refinement for the hybrid zero-start DAE solver.
- `run_zero_start_full_ramp.py` runs the memory-bounded theoretical full-ramp
  trajectory at either the exploratory or reference step size.
- `run_zero_start_post_ramp.py` resumes a complete saved MNA state and samples
  the left limit of one fixed PWM event; partial voltage/current snapshots are
  deliberately rejected as restart states.
- `solve_zero_start_affine_period.py` constructs the fixed-diode one-period
  affine map and reports its rank, closure and diode-complementarity audit.
- `export_synchronized_model_data.py` exports the finest audited affine-period
  solution as a canonical JSON model interface and a flat event-state CSV.

- `cosim_regression.py` replays archived co-simulation runs with the shared
  package `src/scb_ivr/cosim/`, bit for bit (`--quick` to 100 us, `--full`
  to the end, `--plant` to choose the plant). Run it after any change
  there.
- `p24_orbits.py` computes the P24 timed-low-side orbits of D47-D51 with
  one solver (`src/scb_ivr/p24_orbit_solver.py`, `--variant`). `--gate`
  recomputes the 13 archived orbits and compares them bit for bit. The
  older per-derivation scripts `audit_p24_*_orbits.py` stay as they were.
- `p24_closed_loop_modes.py` (D52) linearises the P24 map with the
  error-based correctors, the voltage loop and a slot rule (fixed, follow,
  average) at D50's/D51's orbits (`src/scb_ivr/p24_closed_loop.py`).
  - It gives the closed-loop eigenvalues and the gain from phase 1's
    current threshold (the trim) to each phase's turn-off current, the
    period and the edge errors.
  - `--step-check` repeats the Jacobian with half and twice the
    finite-difference steps.
- `p24_jitter_modes.py` (D53) adds one input per gate edge
  (`src/scb_ivr/p24_jitter.py`). It computes:
  - the closed loop's linear covariance under independent edge jitter;
  - a Monte Carlo of the linearised circuit with the controller's exact
    RTL rules, for the fixed, follow and average slot rules.
  - `--reuse` keeps the stored Jacobians.
- `p24_timed_modes.py` (D54) applies the same model with phase 1's
  low-side turn-off timed instead of comparator-decided (option
  `timed1`): the orbit gate, the Jacobian, and error-based and sign
  dlo rules under jitter.
- `p24_dlo_rules.py` (D55) replays dlo rules against the interval phase 1
  needs, measured in A100's comparator load-step runs, and runs D54's
  Monte Carlo for each rule: tracking against jitter.
- The auxiliary-branch scripts (D56, D57) are an extension: `extensions/aux_commutation_branch/scripts/`.

- `cosim_benchmark.py` times the co-simulation against archived runs and
  checks every result bit for bit (`--batch`: A92's batch; `--plants`:
  every plant implementation on one configuration).

Co-simulation runs themselves:
`PYTHONPATH=src python3 -m scb_ivr.cosim.run cfg.json ...` (see
`src/scb_ivr/cosim/README.md`).

Install the project first with `python3 -m pip install -e .`, then run a script
from the repository root, for example `python3 scripts/run_reproduction.py`.
