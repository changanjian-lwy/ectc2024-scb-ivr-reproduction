# Legacy experiment boundary

The following files remain in the original `project/circuit` and
`project/results` directories to avoid breaking historical scripts:

- `experiment_E*`: startup/precharge explorations.
- `experiment_I0*`: ideal-topology, damping and non-paper controller
  diagnostics.
- `apec2025_verified_3phase_module.cir`: fixed-timing topology check; rerun
  proved that it does not achieve high-side ZVS.
- `apec2025_zvs_timing_replay_3phase_module.cir`: manually calibrated timing
  replay at 0.623 MHz and `D=0.298`, not the published nominal point.
- `apec2025_zvs_controlled_3phase_module.cir`: engineering reconstruction of
  an unpublished controller.

Their numerical lessons may inform solver setup, but their assumed values and
control laws must not flow into a `PF-*` model without a new source entry.
