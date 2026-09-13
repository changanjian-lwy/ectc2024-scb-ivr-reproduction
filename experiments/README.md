# Canonical experiment layout

New experiments are created only below this directory. Historical files remain
in their original locations so regression tests and citations do not break.

- `track_A_periodic_steady_state`: main P24 reproduction work.
- `track_B_zero_start_extension`: manifests for the completed zero-start work.
- `legacy_quarantine`: historical circuits that must not be treated as current
  reproduction evidence.

Every experiment directory name states the changed variable. Its `BOUNDARY.md`
must identify the comparison baseline, changed variables, fixed variables,
evidence class, pass condition and actual result.
