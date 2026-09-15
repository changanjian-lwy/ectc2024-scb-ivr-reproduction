# Track B - zero-start engineering extension

Canonical records remain at `paper_locked/02_ectc2024_main/STEP_27` through
`STEP_31`; their netlists remain beside those records to preserve links.

| Experiment | Changed variable | Status |
|---|---|---|
| R04E0 | add observer-only voltage-difference detector | static pass only |
| R04E1 | add one calculated QH1+QS2 narrow pulse | local current increment pass |
| R04E2 | repeat period 10/4/2/1 ns | unsafe negative current; no full ladder |
| R04E3 | add event controller to zero-energy P24 local cycle | stops before t3 |
| R04E4 | sweep QH1 gate-off current | first hard turn-on dominates |
| R04E5 | ramped on-time ceiling (R03D) grafted onto the event-gated latched controller (R04E3), sweep TSOFT x I_LIMIT | reproduces R04E3's stuck-at-state-4 point (9/12 cells) or an earlier stuck-at-state-3 point (3/12 cells); never returns to ENERGY a second time in any of the 12 cells, so TSOFT has no observed effect and Vout never approaches 1 V; current stays inside the +/-250 A bound in all 12 |

These results are retained but are not Track-A periodic reproduction evidence.

See `R04E5_ramped_duty_event_gated_zero_start/BOUNDARY.md` and `RESULTS.md`
for the full two-parent synthesis provenance and sensitivity grid.
