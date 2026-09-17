# Project Overview

## Objective

This project reproduces and audits a high-step-down integrated voltage
regulator for high-performance computing. The target architecture converts
48 V to 1 V at 1 kW using four interleaved 250 W modules, each containing four
phases. The immediate goal is not to produce attractive waveforms; it is to
determine which paper-reported equations, switching events and component
values can coexist in one reproducible model.

## Why the workflow is modular

The reproduction is separated into six layers so that a failed result can be
localized instead of hidden by retuning unrelated parameters:

1. **Evidence layer** — records whether each claim comes from the 2024 paper,
   the 2025 follow-up, another cited source or an explicit assumption.
2. **Equation layer** — evaluates duty ratio, on-time, current ramps, charge
   balance and commutation energy before circuit simulation.
3. **Event layer** — maps paper time labels to physical events such as current
   zero crossing, negative-current threshold and zero-voltage admission.
4. **Device layer** — inserts switch resistance, output capacitance and other
   parasitics without rewriting the controller or topology.
5. **Experiment layer** — changes one boundary at a time and records both
   successful and unsuccessful cases.
6. **Verification layer** — rejects a candidate unless every predeclared
   timing, state-return, current, power and charge-balance gate passes.

Python/SciPy implements the analytical and event-driven models. LTspice
provides inspectable circuit netlists and transient experiments. Automated
tests protect the source hierarchy, branch separation and numerical contracts.
The complete local suite contains 225 passing checks. GitHub CI runs 206
portable checks because LTspice-generated log fixtures are intentionally not
published.

The Python source is organized by responsibility: reusable models live in
`src/scb_ivr`, human-run workflows in `scripts`, LTspice result readers in
`validation`, and behavioral contracts in `tests`.

## Two evidence branches

- **P24 native:** the 2024 four-phase topology and its explicitly reported
  switching rules.
- **P24 primary + P25 supplement:** the same four-phase target, with only the
  missing switching details extended from the 2025 three-phase paper.

A third, native P25 model is used to calibrate the method before transferring
it to the P24 topology. Conflicting rules are never averaged or silently
merged.

## Selected engineering outcomes

- The published duty, on-time and peak-current relationships were reproduced.
- A 5 MHz inductance inconsistency was isolated: the printed 2024 equation
  gives 1.4667 nH while its Table I reports 2.68 nH.
- The four-phase periodic-current residual was reduced from 80.468 A for an
  all-zero seed to 0.105 A through documented state iterations.
- A native P25 event solve finds a locally periodic trajectory near 563 kHz,
  showing local causal feasibility while also demonstrating that it is not a
  0.5 MHz paper match.
- A strict P25 joint audit repeatedly moves the consistent inductance toward
  31–32 nH instead of the listed 22 nH. With negative-valley correction and
  phase-specific timing, period, power and capacitor charge balance nearly
  close, but the fixed per-phase peak-current gate still fails. The repository
  reports this as a negative result rather than relaxing the tolerance.

## What is deliberately not claimed

- The steady-state 36/24/12 V ladder is not evidence of successful zero-start.
- An ideal 1 V output clamp is a declared isolation boundary, not a completed
  output regulator.
- A local ZVS event is not proof of a periodic, equal-spaced, full-power system.
- The present models do not yet establish hardware efficiency, thermal, EMI or
  reliability performance.

## Reproduce the automated checks

```bash
python3 -m pip install -r requirements.txt
python3 tests/run_portable_suite.py
```

Begin the technical audit with
[`symbolic_derivations/README.md`](symbolic_derivations/README.md) and the
[`experiment registry`](paper_locked/00_boundaries/EXPERIMENT_REGISTRY.md).
