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

Install the project first with `python3 -m pip install -e .`, then run a script
from the repository root, for example `python3 scripts/run_reproduction.py`.
