# Step 05 - R01 current-limited startup experiments

## Locked change from R00

Only the gate-control module changes. All power-stage and source parameters
remain identical to R00. High-side conduction is limited by the earlier of the
ECTC 2024 Table-I values: 125 A phase current or 16.7 ns on-time.

## R01 result

- Status: **FAILED_NUMERICAL_CONTROLLER**.
- Failure time: 2.514586 us.
- LTspice message: timestep too small at node \`xmod:gl2\`; iteration limit.
- Interpretation: the instantaneous expression that commanded the low-side
  gate changed state repeatedly around the ideal zero-current boundary.
- This is not evidence that the power-stage startup succeeds or fails.
- No paper or cross-source power-stage value was changed after the failure.

## R01A isolated change

Replace only each low-side instantaneous comparator with a state latch:

1. set after its high-side turns off while phase current is positive;
2. hold the low-side command through the falling-current interval;
3. reset after current crosses the 10 mA numerical zero band;
4. keep the low side reset while its high side is on.

The 10 mA band is a solver/event regularization, not a claimed detector
threshold from either paper. R01A must be rejected if it permits material
negative current or otherwise changes the intended zero-current startup state.

## R01A result

- Status: **FAILED_UNDEFINED_DC_INITIALIZATION**.
- LTspice stopped at the operating-point calculation with a singular matrix at
  \`xmod:r1\`.
- Cause: all controlled switches are initially off, so the ideal capacitor
  ladder has no unique DC reference.
- No electrical transient was calculated and no conclusion about startup
  current can be drawn.

## R01B isolated change

Add LTspice \`UIC\` to bypass the undefined DC operating point and start
transient integration from zero stored energy. No resistor, preset flying-
capacitor voltage, source ramp, or power-stage parameter is added or changed.

### R01B long-run execution note

R01B passed the initialization point and continued calculating, but the
50-us/0.5-ns event-driven run produced more than 660 MB of raw data before
completion. It was stopped as an inefficient experiment, with no electrical
pass/fail classification.

R01B-short changes only the observation horizon to 5 us (maximum step 0.25 ns)
to test peak limiting, zero-current turnoff, and four-phase activation before a
long settling run is justified. Electrical and controller values are unchanged.

## R01B-short result

- Status: **FAILED_NUMERICAL_OVERFLOW**.
- The simulation passed initialization and ran through 5 us, but values became
  infinite after a convergence relaxation near 2.7444 us.
- The saved measurements are therefore invalid (infinite currents/ripple).
- Gate-integral data confirms that phase-1 high-side pulses were generated.
- Review found a controller implementation error: the low-side latch required
  finite time to reset when the high-side latch set, so both ideal gates could
  be asserted briefly.

## R01C isolated change

Add Boolean high/low mutual exclusion to every low-side gate output. A low-side
command is passed only when its latch is set **and** its high-side latch is
already reset. This adds no numerical dead time and changes no paper, passive,
source, load, or threshold value.

## R01C result

- Status: **FAILED_WRONG_DECOUPLED_CONTROL_STATE**.
- The run completed numerically but produced nonphysical growth: output voltage
  exceeded 1e9 V and phase currents reached roughly 1e12 A.
- The 125 A command therefore did not create a bounded converter state.
- Root cause identified in the model logic: it treated the four phases as
  independent bucks and did not command the other phases' low-side switches
  during an active phase's energy-transfer interval.

## R01D isolated change

Implement the coupled state explicitly described by APEC 2025 Interval 1 and
extended to four phases: while phase k high side is active, the other three
low-side switches are commanded on to provide their freewheel paths. Own-leg
high/low mutual exclusion remains absolute. No power-stage or numeric control
value changes.

## R01D execution status

- Status: **INTERRUPTED_EVENT_CHATTER / NO ELECTRICAL VERDICT**.
- The 5-us run had generated approximately 849 MB of raw data without reaching
  completion and was stopped.
- The log contains no circuit convergence error before interruption.
- Interpretation: the coupled Boolean state is closer to the paper mode, but
  ideal instantaneous latch/comparator transitions create excessive internal
  timesteps. The next revision must replace the analog behavioral latch model
  with a discrete event/state-table controller; changing power-stage data is
  not justified by this result.
