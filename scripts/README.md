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

- `cosim_benchmark.py` times the co-simulation against archived runs and
  checks every result bit for bit (`--batch`: A92's batch; `--plants`:
  every plant implementation on one configuration).

Co-simulation runs themselves:
`PYTHONPATH=src python3 -m scb_ivr.cosim.run cfg.json ...` (see
`src/scb_ivr/cosim/README.md`).

Install the project first with `python3 -m pip install -e .`, then run a script
from the repository root, for example `python3 scripts/run_reproduction.py`.
