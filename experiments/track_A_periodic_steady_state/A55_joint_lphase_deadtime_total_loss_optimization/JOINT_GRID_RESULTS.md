# A55: local inductance/dead-time sensitivity

Source: `joint_local_grid.json`; boundary: `JOINT_GRID_BOUNDARY.md`.

This is an A51/A55 control extension, not native P24/P25 reproduction. One four-phase module, 48 V, 5 MHz, fixed 4 mOhm load; nominal 250 W means 250 W only at 1 V. Device population and all passive/source parameters are unchanged. Every point was independently re-solved.

Automated full-boundary comparison confirms that only phase inductance and dead time differ across probes, and every metering replay uses exactly the same parameter boundary as its solve.

The three L anchors come from existing calculations. Dead times are half/reference/twice 2.15 ns, chosen for sensitivity, not from a driver specification. Changing dead time moves PWM window edges and may change actual channel-active duration.

| L (nH) | DT (ns) | H1–H4 ZVS | L1–L4 ZVS | Actual Pout (W) | Channel loss (W) | Peak abs I (A) | Max negative entry/peak (%) | First failed gate |
|---:|---:|---|---|---:|---:|---:|---:|---|
| 0.621524 | 2.150 | T/T/T/T | T/T/T/T | 219.928 | 24.968 | 205.854 | 39.38 | none of numerical/current/ZVS gates |
| 0.621524 | 1.075 | F/F/F/F | T/T/T/T | 225.084 | 26.424 | 207.956 | 39.62 | high_side_zvs |
| 0.621524 | 4.300 | T/T/T/T | T/T/T/T | 219.936 | 24.970 | 205.860 | 39.38 | none of numerical/current/ZVS gates |
| 0.627406 | 2.150 | F/F/F/T | T/T/T/T | 219.476 | 24.614 | 204.243 | 39.03 | high_side_zvs |
| 0.627406 | 1.075 | F/F/F/F | T/T/T/T | 224.945 | 26.139 | 206.498 | 39.27 | high_side_zvs |
| 0.627406 | 4.300 | T/T/T/T | T/T/T/T | 219.479 | 24.617 | 204.247 | 39.03 | none of numerical/current/ZVS gates |
| 1.466667 | 2.150 | F/F/F/F | T/T/T/T | 192.228 | 14.905 | 113.887 | 0.98 | high_side_zvs |
| 1.466667 | 1.075 | F/F/F/F | F/F/F/T | 218.848 | 16.597 | 121.079 | 1.28 | high_side_zvs |
| 1.466667 | 4.300 | F/F/F/F | T/T/T/T | 144.094 | 12.014 | 99.624 | 0.50 | high_side_zvs |

“No failed gate” does not mean rated-power or paper acceptance. No target tolerance is invented: actual voltage and power errors remain in the JSON. Negative entry ratio uses current at the start of the high-side dead-time window relative to that phase’s positive peak; full-cycle valley ratios are stored separately. These are observed currents, not threshold-controlled values.

Channel loss uses actual branch voltages squared divided by resistance, integrated only on accepted enabled-channel samples. Load power uses mean(Vout²/R). Neither is the legacy phase-current proxy. Third-quadrant device physics, gate drive, magnetic and thermal loss remain incomplete. No efficiency ranking is justified by comparing losses at unequal power.

## Step refinement

Selection: `new_passing_dt_x2`. Chosen for smallest rated-power error among the sampled all-eight-ZVS current-screen-passing points, not as a loss optimum.

- Commutation step 2.5 ps / normal step 31.25 ps: relative closure 5.71e-08; H-ZVS T/T/T/T; Pout 219.9718 W; modeled channel loss 24.9560 W; maximum negative-entry ratio 39.38%.
- Commutation step 1.25 ps / normal step 15.625 ps: relative closure 1.01e-08; H-ZVS T/T/T/T; Pout 219.9895 W; modeled channel loss 24.9491 W; maximum negative-entry ratio 39.38%.

## Timing mechanism identified

In the inherited scheduler the nominal high-side interval is 16.6667 ns. When high-side zero-voltage admission never occurs, actual commanded high-channel duration is Ton_nominal minus dead time. Thus the nominal-L row has widths approximately 15.5917, 14.5167 and 12.3667 ns for 1.075, 2.15 and 4.3 ns dead times. This explains why extending the window can reduce delivered power; it is not a test with fixed actual high-side conduction time. For naturally admitted points, conduction starts at a state-dependent crossing, and the refined metrics export the actual modeled channel-active durations.

These are properties of the implemented A51 window scheduler. They must not be attributed to the native paper controller without a separate physical-event mapping. Preserve these runs as sensitivity evidence and audit that mapping before silently changing on-time.

Existing source mapping: `src/scb_ivr/p24_operating_sequence.py` defines t1 as the end of the high-side conduction interval; `symbolic_derivations/03_P24_primary_P25_supplement/29_LOCAL_PHASE_VS_GLOBAL_HANDOFF_MAPPING.md` separates local phase events from inter-phase handoffs. The next timing audit should use these definitions and state explicitly whether Ton is measured from actual admission or from a nominal command edge.

## What this experiment can decide

It tests whether this limited L/dead-time adjustment improves simultaneous ZVS, delivered power and current behavior under the declared scheduler. It cannot establish a global optimum or disprove the paper. Before a rated-power loss optimization, specify the output-regulation/control boundary and validate a sourced reverse-conduction model. Do not silently change duty or load to force 250 W.

Validation: 267 local tests; 248 portable tests. Historical results and failed candidates retained. No new LTspice confirmation in this run.
