# Reproduction track boundary

## Track A - P24 periodic steady-state reproduction (main line)

Required outcome: solve a closed single-module/four-phase periodic orbit under
the P24 topology and source-resolved event sequence, then assemble the four-module
1-kW case. A periodic-state solver may start from `36/24/12 V`, but those values
are solver seeds, not imposed final results. Pass requires the complete state
vector after one 200-ns period to return to its initial value within declared
tolerances: three flying-capacitor voltages, four inductor currents and output
voltage. Output average, ripple, charge balance and switching boundaries are
separate acceptance checks.

Peak-current acceptance also has two non-interchangeable layers:
`P24_IDEAL` checks the lossless 125-A analytical target, whereas
`P25_DEVICE_AUGMENTED` checks the phase-local non-ideal endpoint predicted
from the actual admission state. Any locally solved initial current remains a
`LOCAL_SOLVED_SEED` until the complete period closes; only then may it be
called a `VALID_PERIODIC_INITIAL_STATE`.

## Track B - zero-start engineering extension

The startup detector, predictive pulses, repeated-pulse screen and first-ZVS
experiments R04E0-R04E4 belong here. They remain useful and fully recorded, but
P24/P25 do not publish a zero-start controller. Track B is not a prerequisite
for reporting a valid P24 steady-state reproduction, and its assumptions must
not leak into Track A.

## Legacy-file quarantine

`project/circuit/ectc2024_verified_4phase_module.net` is retained for history but
is not verified under the current framework. It uses eight 125-W modules rather
than the selected P24 four-module 250-W row, changes duty to 0.102, uses assumed
capacitor/Coss/dead-time values, and applies ordinary complementary low-side PWM
instead of event-bounded conduction. It cannot seed or validate Track A.

## Immediate Track-A gate

Before emitting the next publication-target netlist:

1. compile a single-module four-phase event schedule without merging P24 and P25
   local time labels;
2. preserve `nP=4`, `nM=1` for the single-module orbit and later `nM=4` for the
   Table-I system row;
3. expose the full eight-state periodic initial vector to the solver;
4. use `36/24/12 V` only as the first Newton/shooting seed;
5. reject a solution if only output voltage matches while capacitor charge or
   any phase current fails periodic closure;
6. keep P24 1%-2% and model-calibrated 8% as separate runs.
