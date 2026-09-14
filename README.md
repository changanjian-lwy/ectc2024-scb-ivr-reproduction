# ECTC 2024 SCB-IVR Reproduction

Evidence-bounded analytical and LTspice reproduction of the 2024 ECTC paper
*Package Power Delivery Architecture for High Performance Computing Systems
With a 1 kW IVR Operated in CCM-DCM Boundary Mode Condition*.

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

These are periodic-state and local commutation results. They are not claims of
zero-start operation, closed-loop output regulation or complete 1 kW hardware
validation.

## Repository map

```text
paper_locked/     Source hierarchy, formula audit and P24/P25 branch records
experiments/      One-change-at-a-time simulation cases and negative evidence
results/          Parameter provenance and consolidated records
tests/            Automated boundary and regression checks
tools/            Local LTspice runner and analysis helpers
reports/          Shareable technical progress summaries
circuit/          Earlier exploratory netlists retained for traceability
```

Start with:

- `paper_locked/00_boundaries/EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md`
- `reports/MIHAI_MEETING_2026-09-14.md`
- `paper_locked/00_boundaries/SEQUENCE_SOURCE_MATRIX.md`
- `paper_locked/00_boundaries/EXPERIMENT_REGISTRY.md`
- `experiments/track_A_periodic_steady_state/PERIODIC_TIGHTENING_SWEEP_1_A13_A16.md`

## Run the checks

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

LTspice netlists are supplied for inspection and reproduction. Generated raw
waveforms and database files are intentionally excluded from version control.

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
