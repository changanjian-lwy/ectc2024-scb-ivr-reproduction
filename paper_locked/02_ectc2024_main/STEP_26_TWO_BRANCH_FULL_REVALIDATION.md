# Step 26 - Full revalidation of the P24 and P25 branches

## Audit action

Thirteen critical LTspice netlists were rerun after the latest parameter-library
and event-map changes. All LTspice runs completed normally. The full Python
regression suite then passed. A numerical run completing is not treated as a
physical success; expected failures are checked explicitly.

## Branch A - P24 target topology

| Segment | Result | Boundary |
|---|---|---|
| R04D0 first energy interval | local success | starts from a precharged periodic-state candidate; not zero start |
| R04D1/R04D2 Coss commutation and freewheel | local success | GS61008T scalar-capacitance plug-in; exact paper snubber/dead time absent |
| R04D3A P24 1% negative current | ZVS failure | high-side Vds remains positive |
| P24 2% source upper boundary | source value retained; not allowed to be overwritten | still below the calibrated present-model threshold |
| R04D3C P25 5% mapped control | ZVS failure | cross-paper experiment, not P24 truth |
| R04D3D threshold | 7.77% minimum numerical crossing | model calibration only |
| R04D3E 8% operating point | ideal local ZVS exit success | selected model default; not a P24 paper value or hardware-qualified value |

Conclusion: the P24 source-native 1%-2% branch is not completely reproduced
with the selected device plug-in. A precharged, local, model-calibrated 8%
branch reaches the correct event sequence. Startup, full four-phase charge
balance and hardware robustness remain open.

## Branch B1 - P25 timing extended onto the P24 nP=4/48-V target

| Segment | Result | Boundary |
|---|---|---|
| R04D0E inactive-low-side extension | local result reproduced | SL4 is an explicit nP=4 extension |
| R04D2B Mode-2 extension | low-side zero-Vds event reproduced | P25 t2 is not P24 t2 |
| R04D3B Mode-3 chain | failure | iL2 enters negative and becomes more negative, so P25 t3 cannot occur |

This branch stops at Mode 3. No later local success repairs this discontinuity.

## Branch B2 - P25-native 12-V/nP=3/nM=3 prototype-local stages

| Segment | Result | Boundary |
|---|---|---|
| R04D4A Mode 4 | local success | begins from controlled iL2=0; not inherited from B1 |
| R04D5A Mode 5 | ideal device-plug-in ZVS success | t5=t4 idealization; CH2/CL2 scalar plug-in |
| R04D6A Mode 6 | qualitative success, quantitative failure | current rises, but circuit gives 60.90 A vs Eq.(15)/(16) 88.78 A vs peak relation 44.44 A |

B2 is not continuous with B1 because voltage, phase/module count, inductance and
the Mode-4 entrance state differ. It is a set of source-native local stage
tests, not a complete periodic prototype reproduction.

## Valid report statement

The work has established modular physical-event mappings and individually
reproducible local stages for both source branches. It has not yet reproduced
either paper as a continuous, self-starting, charge-balanced multi-phase
converter. The two immediate blockers are the P25 Mode-3 periodic entrance
state and the P25 Mode-6 non-closing voltage/peak-current equations.
