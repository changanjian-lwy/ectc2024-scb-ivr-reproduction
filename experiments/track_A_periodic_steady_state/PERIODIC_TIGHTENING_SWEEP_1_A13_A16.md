# Periodic-state tightening sweep 1: A13-A16

The isolated model has seven free periodic states because output voltage is
held by the explicit 1 V isolation fixture: four coupled inductor currents and
three flying-capacitor voltages. One state group is updated per folder.

| Experiment | Only newly updated state/group | Max abs capacitor residual | Max abs current residual | Decision |
|---|---|---:|---:|---|
| A11 control | parent seed | 2.934 mV | 1.340 A | reference |
| A13 | IL1-IL4 coupled group | 0.597 mV | 0.11114 A | accept |
| A14 | VC1 | 0.597 mV | 0.11113 A | accept; small change |
| A15 | VC2 | 0.596 mV | 0.11110 A | accept; small change |
| A16 | VC3 | 0.595 mV | 0.10491 A | accept |

## Interpretation boundary

This is a numerical periodic-state solve around the P24-derived, output-clamped
model. It does not alter or identify component values, does not implement
startup, and does not demonstrate output regulation. The `36/24/12 V` values
are initial state coordinates in this isolated solve, not claimed zero-start
outcomes.

## Next sweep

Start a new folder by updating only the four-current coupled group from A16's
measured final currents. Then repeat C1, C2 and C3 as separate descendants only
when each parent passes the complete-state residual check.
