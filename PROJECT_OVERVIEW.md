# Project Overview

## Objective

Turn the 2024 ECTC SCB-IVR paper into an auditable computational model, using
the 2025 APEC paper as an explicitly separated reference where appropriate.
The target is 48 V to 1 V, 1 kW across four four-phase modules. This is the
research target, **not an achieved simulation or hardware rating**.

## Approach: vertical layers, horizontal switching events

Vertically, the project separates sources, equations, event/control logic,
device models, experiments and verification. Horizontally, a switching cycle
is broken into physical events: high-side conduction, turn-off commutation,
low-side ZVS admission, freewheeling, negative-current preparation and the
next high-side admission.

These directions interact. Device capacitance affects commutation time;
a late commutation changes the other phases' currents; a locally valid
transition may fail in the complete circuit. The model must retain
simultaneous phase and capacitor states rather than concatenate isolated
single-phase successes.

## Implementation

- **Python/SciPy:** reusable node equations, constrained derivatives, affine
  propagation, event guards, control memory and diagnostics.
- **LTspice:** inspectable netlists and independent transient checks.
- **Automated tests:** identities, branch separation, invalid-state rejection,
  event ordering and historical regressions.
- **Evidence records:** source, changed variables, assumptions and limitations.

## What the work demonstrates

| Engineering capability | Concrete evidence |
|---|---|
| Translate literature into executable models | Native P25 15-mode mapping on one shared topology |
| Design modular scientific software | Separate equations, controller memory, event guards and device contracts |
| Diagnose rather than retune blindly | First failed event and integrated volt-second/charge accounting |
| Verify independently | Python-to-LTspice comparison in A52, under its reduced-power boundary |
| Question assumptions | Separate capacitance, timing, temperature and load sensitivity studies |
| Report negative results honestly | Partial handoffs are not promoted to complete reproduction |

## Where it stands (2026-10-07)

- **Achieved in simulation:** the 1 kW system (four four-phase modules, 48 V to 1 V) runs closed loop in co-simulation
  (Verilog controller against a circuit plant with datasheet Coss and reverse conduction), from a zero start through the
  handover to regulation; both controller designs are frozen after randomised tests; the package drive is specified as
  formulas in loop inductance and di/dt. Every step registered its criteria first ([status](reports/CURRENT_STATUS.md),
  [Mihai summary](reports/MIHAI_SUMMARY_2026-10-06.md)).
- **Where P24's assumptions do not hold together:** its 1-2 % negative current cannot give high-side ZVS with its own
  values (about 27 % would be needed); the design runs at 12.5 % with partial ZVS instead.
- **Not done:** hardware validation; the paper's unpublished values (loop inductance and damping, inductor technology,
  driver, transient specification) are covered by sweeps and stated as questions.

## Limits of the early work (to 2026-09-28)

The strict P25-native core is **three-phase, single-module**; its all-mode
algebra is tested, but its full-cycle event orchestration is incomplete.
Four-phase engineering experiments form a separate model family with their
own device, timing and output assumptions. They are not automatic validation
of the new mathematical core.

Neither a paper-consistent zero-start handoff nor complete 1 kW hardware
performance has been established. Earlier ideal-output-clamp results remain
isolation experiments, not output-regulation demonstrations.

See [current status](reports/CURRENT_STATUS.md) for progress and unresolved
steps, or [README](README.md) to run the tests.
