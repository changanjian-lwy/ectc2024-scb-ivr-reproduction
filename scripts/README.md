# Runnable workflows

- `run_reproduction.py` generates the analytical design-space sweep.
- `reproduce_table1_4phase_4module.py` audits the P24 Table-I target row.
- `startup_rotation_experiment.py` records the two startup-sequence branches.
- `startup_supervisor_experiment.py` evaluates the startup-readiness observer.

Install the project first with `python3 -m pip install -e .`, then run a script
from the repository root, for example `python3 scripts/run_reproduction.py`.
