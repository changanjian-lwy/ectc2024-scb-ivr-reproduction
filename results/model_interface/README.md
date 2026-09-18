# Synchronized model-data interface

## Files

- `P24_CONNECTED_FAST_PERIODIC_SYNCHRONIZED_STATE.json` is the canonical
  structured interface.  It contains the full boundary, topology endpoint
  mappings, variable order/units/reliability, solver audit, period metrics and
  nine synchronized PWM-event snapshots.  It also contains the complete
  20-by-20 discrete affine period matrix and 20-element offset in the same
  variable order.
- `P24_CONNECTED_FAST_PERIODIC_EVENT_STATES.csv` contains the same event
  snapshots in one-row-per-event form.  Every row includes all 20 raw MNA
  variables, global quantities, precharge-diode fields and four complete phase
  blocks.

## Sampling convention

All event rows are left limits.  For example,
`P1_high_side_turn_on_0.000000ns` is the state immediately before the phase-1
high-side command rises.  Capacitor voltages and inductor currents are
continuous through an ideal switching event, but algebraic switch-node
right-limit values are not supplied because this model has not performed a
zero-time DAE projection.

## Reliability boundary

`tap3`, `tap2` and `tap1` are explicitly marked
`NONUNIQUE_SLOW_COORDINATE_DO_NOT_USE_AS_PHYSICAL_STARTUP_STATE`.  The affine
period map has rank 17 out of 20 because these three isolated divider-charge
coordinates are nearly neutral over one 200 ns period.  Their minimum-norm
values, and diode voltages computed from them, must not be used as physical
zero-start initial conditions.

The remaining variables are labelled `FAST_PERIODIC_MANIFOLD_STATE` and may be
used together only under the exported boundary:

- one P24-connected four-phase module;
- fixed 5 MHz interleaved PWM;
- ideal Track-B switch boundary;
- all three precharge diodes on the audited off branch;
- no P24/P25 event-driven ZVS controller and no four-module coupling.

## Regeneration

From the repository root:

```text
python3 scripts/export_synchronized_model_data.py \
  --step-ns 0.0625 \
  --json-output results/model_interface/P24_CONNECTED_FAST_PERIODIC_SYNCHRONIZED_STATE.json \
  --csv-output results/model_interface/P24_CONNECTED_FAST_PERIODIC_EVENT_STATES.csv
```
