# A70 - a valley-switching fallback for the high-side turn-on (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question

A69 found a controller deadlock. Its 4.9 mOhm run was started from the
*lossless* D41 orbit (Vo 1.035 V vs the damped orbit's 0.844 V), and it
stopped at t = 7.85 us with the phase states (LOW, UP, UP). The sequence
was:
- phases 2 and 3 turned their low sides off on their timers;
- their high sides then waited for `Vds <= 0`, which never came;
- the constant-current load pulled Vo down, and phase 1's current could
  no longer reach its -2.5 A target.

The rule "turn the high side on only at `Vds <= 0`" has no way out when
the resonance cannot reach zero volts. Track B hit the same stall in its
event-gated start-up controller (R04E21-R04E26, state
`COMMUTATE_HIGH_TO_ZVS`), and A67 explains it: the negative current is too
small for the node to swing fully.

Does adding the published fallback remove the deadlock, and does the
circuit then return to the D42 orbit? Does the fallback leave the orbit
itself untouched?

## 2. Source of the rule

Chiang and Chen, "Zero-Voltage-Switching Control for a PWM Buck Converter
Under DCM/CCM Boundary", IEEE TPEL 24(9), 2009,
DOI 10.1109/TPEL.2009.2021186 (Sec. II-III).
- Their controller has two OR-ed turn-on paths into one latch. A
  "VDD/Peak detecting" path is active in transients where ZVS cannot be
  reached (their case: Vout < Vdd/2). It follows the switch node to its
  resonant peak and turns the switch on when the node falls back below the
  held peak. A "ZVS" path takes over in steady state, once the node
  reaches Vdd.
- The fallback always fires within one resonant half-period, so the
  controller cannot wait forever.
- Peak switching is the least-loss option when ZVS is out of reach
  (their Fig. 3).

The transfer to the SCB high sides is `CROSS_PAPER_EXTENSION`.
- Chiang's converter is a single-switch buck with a diode.
- Here each SCB high side's `Vds` plays the role of `Vdd - V_LX`: its
  valley is the node's peak.

## 3. Rule implemented

This is a copy of A69's simulator, `a70_transient.py`. A69's files are not
modified. The only change is in the UP state of each phase k, i.e. after
SLk has turned off and before SHk turns on:

- **ZVS path** (unchanged): SHk turns on when `Vds(SHk) <= 0`.
- **Valley path** (new): the minimum of `Vds(SHk)` since entering UP is
  tracked. SHk turns on when `Vds(SHk) >= Vds_min + dV_hys`, i.e. once the
  node has passed its peak and fallen back by the comparator hysteresis.
  - `dV_hys = 0.05 V` (`PROJECT_DECISION`: comparator hysteresis; Chiang
    gives no number).
  - The comparator delay is not modelled (`NUMERICAL_IDEALIZATION`).
- The first path to fire wins. The event is landed by interpolation, as
  for every other A69 event.

Nothing else changes:
- circuit, values and integration (A69 BOUNDARY Sections 3 and 5a);
- phase 1's current-target low-side turn-off;
- the fixed phase shifts;
- the load, which remains a constant current.

## 4. Runs

All at h = 10 ps with A69's 0.1 uOhm ON resistance.

1. **Regression.** 4.9 mOhm per phase, started from A69's perturbed start
   (`start_D42_R4p9mohm_perturbed.json`), 80 cycles.
   - Expected: the valley path never fires, and the sections equal A69's
     `run_damped4p9_perturbed` to round-off.
2. **Deadlock case.** 4.9 mOhm, started from the lossless D41 orbit
   (A69's deadlocked start), 250 cycles.
3. **Hysteresis sensitivity.** Run 2 with `dV_hys = 0.2 V`, 250 cycles.
4. **Unenergized inductors (exploratory).** 4.9 mOhm, started from the
   D42 4.9 mOhm section voltages with all three inductor currents set to
   zero, 250 cycles.

Records: `run_*.json`, each holding the section states and every
valley-path firing (time, phase, `Vds` at turn-on).

## 5. Acceptance

- **Run 1 passes if:**
  - the valley path makes zero firings;
  - every section matches A69's within 1e-6 A and 1e-6 V.
- **Runs 2-4 are reported as they fall.** The outcome is one of:
  - (a) converges to D42's 4.9 mOhm orbit: the last section within
    0.05 A / 5 mV of `z*`, and no valley firing in the last 20 cycles;
  - (b) settles on a different periodic state; report its valley usage;
  - (c) stalls again; report the stalled states.

## 6. Decides / does not decide

Decides:
- whether Chiang's fallback removes the A69 deadlock in this circuit
  without disturbing the ZVS orbit;
- whether the D42 orbit attracts the A69 deadlock start once the fallback
  is present.

Does not decide:
- P24 four-phase start-up (Track B), where A67 says ZVS is out of reach
  and the fallback would be the steady-state path;
- real devices;
- closed-loop Ton;
- stalls of phase 1's current-target wait from causes other than the
  high sides;
- start-up with the output disconnected (Stillwell and
  Pilawa-Podgurski, TPEL 2019, DOI 10.1109/TPEL.2018.2843777).

## 7. Amendment (after runs 1-3, before rerunning run 4)

Run 4's first attempt printed no section in ~10 minutes and was stopped.
- **Cause.** A69's stall check (inherited) only armed after the first
  returned section: `len(sections) >= 2`. A stall inside the first cycle
  therefore ran on silently until the step guard.
- **Fix.** The check now also measures from the start section (t = 0).
  This changes only when a stalled run is reported, not the controller
  or the integration.
- **Effect on other runs.** Runs 1-3 never stalled, so they are
  unaffected. Run 4 is rerun with the fix.
