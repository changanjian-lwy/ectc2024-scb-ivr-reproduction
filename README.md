# Evidence-Bounded SCB-IVR Reproduction

[![Python regression checks](https://github.com/changanjian-lwy/ectc2024-scb-ivr-reproduction/actions/workflows/tests.yml/badge.svg)](https://github.com/changanjian-lwy/ectc2024-scb-ivr-reproduction/actions/workflows/tests.yml)

Modular analytical, numerical and LTspice reproduction of the 2024 ECTC paper
*Package Power Delivery Architecture for High Performance Computing Systems
With a 1 kW IVR Operated in CCM-DCM Boundary Mode Condition*.

This repository turns a research paper into an auditable engineering workflow:
source claims are separated from assumptions, switching events are encoded as
testable modules, and unsuccessful cases are retained as evidence rather than
silently tuned away.

## Project at a glance

- **System target:** 48 V to 1 V, 1 kW package power delivery.
- **Current validated scope:** one four-phase, 250 W module plus a native
  three-phase calibration of the 2025 follow-up method.
- **Tools:** Python/SciPy for equations and event solvers; LTspice for circuit
  inspection and transient experiments; 247 local regression checks for
  boundary and branch integrity, with 228 portable checks run by GitHub CI.
- **Design principle:** 2024 is the primary source. The 2025 paper fills only
  explicitly missing details, and disagreements remain separate branches.
- **Status:** active research reproduction. Periodic-state and commutation
  behavior are under test; this is not yet a complete hardware validation.

For a concise portfolio-level explanation, see
[`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md).

## Current research question

The project first asks whether the paper-derived four-phase topology and
switching events admit a self-consistent periodic trajectory and passive
flying-capacitor restoration. Zero-start, closed-loop regulation, efficiency
and full four-module hardware reproduction remain separate later questions.

## Evidence policy

- The 2024 ECTC paper is the primary source for the target topology, equations
  and operating sequence.
- The 2025 APEC paper supplements only details that the 2024 paper leaves open.
- A disagreement between the papers creates separate branches; values and time
  labels are never silently merged.
- Unreported quantities remain explicit assumptions or blockers. Parameters
  are not tuned merely to obtain a preferred waveform.
- Every active experiment has a `BOUNDARY.md` and `RESULTS.md` stating what
  changed, what was observed and what the result cannot support.

## Main results so far

- Reproduced the reported duty, on-time and peak-current relationships.
- Found an unresolved 5 MHz inductance discrepancy: the printed equation gives
  1.4667 nH while Table I reports 2.68 nH.
- Built a physical-event mapping that prevents the 2024 and 2025 `t1/t2/t3`
  labels from being incorrectly treated as identical events.
- Reduced the maximum four-phase periodic current residual from 80.468 A for an
  all-zero seed to 0.105 A through documented periodic-state iterations.
- Under an explicit ideal 1 V output-isolation boundary, symmetric C1
  perturbations both moved toward the control trajectory over 20 periods,
  providing early evidence of a passive restoring tendency.
- Calibrated the event method on the native 2025 three-phase topology. A
  locally periodic trajectory exists near 563 kHz, but the frozen public
  parameters do not simultaneously reproduce 0.5 MHz, equal phase spacing,
  peak current and flying-capacitor charge balance.
- A strict joint optimization repeatedly places the consistent inductance near
  31–32 nH rather than the prototype table's 22 nH. Even after a labelled
  negative-valley correction, the best tested branch misses the fixed
  per-phase peak-current gate; it remains a diagnostic, not a reproduction
  claim.
- Added a parameter-only feasibility envelope. Before any unknown device value
  is fitted, it reports the available negative current, local inductor-energy
  budget, charge-transfer ceiling and the two explicitly different
  peak-current conventions. Unknown Qoss/dead-time inputs leave the ZVS verdict
  `undetermined` rather than producing a false pass.

These are periodic-state and local commutation results. They are not claims of
zero-start operation, closed-loop output regulation or complete 1 kW hardware
validation.

## Repository map

```text
src/scb_ivr/      Reusable equations, topology, event and controller modules
scripts/          Human-run analytical and startup workflows
validation/       LTspice log readers and accepted-result regressions
paper_locked/     Source hierarchy, formula audit and P24/P25 branch records
symbolic_derivations/ Equation-first P24, P25 and combined evidence branches
experiments/      One-change-at-a-time simulation cases and negative evidence
results/          Parameter provenance and consolidated records
tests/            Automated boundary and regression checks
tools/            Local LTspice execution helpers
reports/          Shareable technical progress summaries
circuit/          Earlier exploratory netlists retained for traceability
```

## Recommended reading order

1. [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) — scope, architecture and
   selected outcomes.
2. [`paper_locked/00_boundaries/PAPER_LOCKED_REPRODUCTION_BASELINE.md`](paper_locked/00_boundaries/PAPER_LOCKED_REPRODUCTION_BASELINE.md)
   — frozen evidence hierarchy.
3. [`paper_locked/00_boundaries/SEQUENCE_SOURCE_MATRIX.md`](paper_locked/00_boundaries/SEQUENCE_SOURCE_MATRIX.md)
   — exact ownership of switching-sequence claims.
4. [`symbolic_derivations/README.md`](symbolic_derivations/README.md) — ordered
   analytical branches and strict joint audit.
5. [`paper_locked/00_boundaries/EXPERIMENT_REGISTRY.md`](paper_locked/00_boundaries/EXPERIMENT_REGISTRY.md)
   — traceable experiment history.
6. [`experiments/README.md`](experiments/README.md) — simulation layout and
   boundaries.
7. [`results/PARAMETRIC_FEASIBILITY_ENVELOPE.md`](results/PARAMETRIC_FEASIBILITY_ENVELOPE.md)
   — what can and cannot be proved before missing device data arrive.
8. [`results/ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md`](results/ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md)
   — Track-B boundary audit and the hybrid descriptor-model definition.
9. [`results/ZERO_START_ONE_PERIOD_CONVERGENCE.md`](results/ZERO_START_ONE_PERIOD_CONVERGENCE.md)
   — first-period step-size and diode-event convergence gate.
10. [`results/ZERO_START_TEN_PERIOD_CONVERGENCE.md`](results/ZERO_START_TEN_PERIOD_CONVERGENCE.md)
    — multi-period convergence and passive-divider current law.
11. [`results/ZERO_START_FULL_RAMP_REFERENCE.md`](results/ZERO_START_FULL_RAMP_REFERENCE.md)
    — complete input-ramp reference solve and handoff-state audit.
12. [`results/ZERO_START_POST_RAMP_POINCARE_AUDIT.md`](results/ZERO_START_POST_RAMP_POINCARE_AUDIT.md)
    — restartable fixed-event sampling, long-envelope audit and three-level
    time-step check.
13. [`results/ZERO_START_AFFINE_PERIOD_FIXED_POINT.md`](results/ZERO_START_AFFINE_PERIOD_FIXED_POINT.md)
    — direct affine-period solution, rank audit and Table-1 boundary
    consistency metrics.
14. [`results/model_interface/`](results/model_interface/)
    — canonical synchronized four-phase JSON/CSV data for downstream model
    construction, including all raw variables and event-boundary states.

## Run the checks

```bash
python3 -m pip install -r requirements.txt
python3 tests/run_portable_suite.py
```

LTspice netlists are supplied for inspection and reproduction. Generated raw
waveforms, optimizer traces and database files are intentionally excluded from
version control; the scripts and concise result reports needed to regenerate
or audit them remain tracked. The complete 247-test local suite additionally
checks recorded LTspice `.log` files after those files have been generated:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Current boundaries

- Active mainline: one four-phase, 250 W module of the 2024 architecture.
- Target operating point: 48 V to 1 V, 5 MHz.
- Active source branch: P24-derived 2% negative-current control.
- Periodic balance studies presently use an explicitly labelled ideal 1 V
  output clamp.
- The 36/24/12 V capacitor values are periodic-state coordinates, not
  demonstrated zero-start outcomes.
- Full nonlinear device, gate-driver delay, package parasitic, thermal, EMI and
  reliability models are not yet included.
