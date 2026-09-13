# Ideal model experiment index

The generated netlists remain in one directory so LTspice can open them
without broken references. They are classified here by research purpose.

## A - Topology and timing

- `experiment_I0A_ideal_1module.net`: one module, four phases, 250 W.
- `experiment_I0B_ideal_4modules.net`: four modules, 16 phases, 1 kW.
- `experiment_I0C_ideal_eq4_inductance.net`: printed Eq. (4) value.
- `experiment_I0D_ideal_inductance_sweep.net`: L-only sweep.
- `experiment_I0G_ideal_near_boundary.net`: 1.55 nH full-model check.

## B - Conservation and numerical assumptions

- `experiment_I0E_ideal_table1_long_settle.net`: 2.68 nH long run.
- `experiment_I0F_ideal_eq4_long_settle.net`: 1.467 nH long run.
- `experiment_I0H_ideal_ron_check.net`: switch-Ron sensitivity.
- `experiment_I0K_pure_lossless_zero_start.net`: Rser=0 failed stability test.
- `experiment_I0L_inductor_damping_sweep.net`: explicit Rser regularization.

## C - Ideal control

- `experiment_I0M_ideal_voltage_control.net`: short PI-control run.
- `experiment_I0N_ideal_voltage_control_long.net`: converged 1 V/1 kA run.
- `experiment_I0O_ideal_control_L165_long.net`: peak-current cross-check.
- `experiment_I0P_ideal_zero_cross_latch.net`: analog-latch diagnostic.
- `experiment_I0Q_zero_cross_1module_debug.net`: one-module latch debug.
- `experiment_I0R_zero_cross_hysteresis_1module.net`: hysteresis diagnostic.
- `experiment_I0S_zero_cross_schmitt_1module.net`: Schmitt diagnostic.
- `experiment_I0T_lossless_after_balanced_startup.net`: damping-removal test.
- `experiment_I0U_zero_cross_takeover_full.net`: takeover diagnostic.
- `experiment_I0V_zero_cross_delayed_takeover_full.net`: delayed takeover.
- `experiment_I0W_variable_offtime_Z*.net`: ideal turn-off-time scan.

## Generator

`build_ideal_hierarchy.py` is the single source used to regenerate these
netlists. Each experiment changes only the variables documented in
`../results/IDEAL_HIERARCHY_EXPERIMENT_LOG.md`.
