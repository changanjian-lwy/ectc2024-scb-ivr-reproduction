# SCB-IVR · From Paper to Reproducible Model

[![Python regression checks](https://github.com/changanjian-lwy/ectc2024-scb-ivr-reproduction/actions/workflows/tests.yml/badge.svg)](https://github.com/changanjian-lwy/ectc2024-scb-ivr-reproduction/actions/workflows/tests.yml)

**Power electronics · Mathematical modeling · Python/SciPy · LTspice**

An evidence-bounded investigation of series-capacitor buck integrated voltage
regulators for high-performance computing. The system target comes from the
2024 ECTC paper: **48 V → 1 V, 1 kW**, using four four-phase modules.
The 2025 APEC follow-up supplies a separate native three-phase reference.

The engineering question: **can the published topology, switching sequence and
device assumptions coexist in one physically consistent operating cycle?**

[Project overview](PROJECT_OVERVIEW.md) · [Current status](reports/CURRENT_STATUS.md) ·
[Derivations](symbolic_derivations/README.md) · [Experiments](experiments/README.md)

> Research in progress—not a completed 1 kW reproduction or hardware validation.
> A local ZVS event, a passing unit test and a full periodic solution are different evidence levels.

**Status, 6 October 2026.** One P24 module and the four-module, 16-phase
1 kW system run closed-loop in co-simulation (Verilog controller, circuit
plant with nonlinear Coss); both controller designs are frozen. At the
package level the switch overshoot is solved by the gate drive (loop
<= 50 pH, a separate 36 A/ns turn-on). Summary:
[reports/MIHAI_SUMMARY_2026-10-06.md](reports/MIHAI_SUMMARY_2026-10-06.md).

| Line (2026-10-06) | Model | State |
|---|---|---|
| Mathematical model | P24-native event maps and the cycle-by-cycle valley map ([D43-D67](symbolic_derivations/03_P24_native/)) | registers a prediction before every co-simulated experiment; the P25-native form (D39-D42) is closed |
| Physical model, one module | Verilog controller + circuit plant ([Track A](experiments/track_A_periodic_steady_state/)) | design frozen (A143) |
| Physical model, four modules | [Track C](experiments/track_C_multi_module/) | design frozen (C13) |
| Package | loop inductance, finite edges, gate drive (A144-A152) | spec: loop <= 50 pH, separate 36 A/ns turn-on |
| Machine learning (extension) | [ml_design_assist](extensions/ml_design_assist/README.md) | A120-A150; assists, the co-simulation decides |
| Zero-start | the co-simulated start-up sequence (A103); Track B's LTspice records kept | carried by the co-simulation |

The workstream table below describes the earlier stages (to 2026-09-29).

## Three workstreams, explicit boundaries

| Workstream | Model and purpose | Current evidence |
|---|---|---|
| **Mathematical core** | Native P25, **3 phases / 1 module**; shared-node equations, physical events and control memory | All 15 main modes assembled algebraically; first handoff tested; full-cycle event orchestration still incomplete |
| **Periodic-state engineering** | P24-derived **4-phase module**; separately declared device and timing variants | Conditional periodic/ZVS solutions, independent LTspice cross-check and loss-sensitivity studies; not a paper operating-point match |
| **Zero-start** | Separate four-phase startup models and boundary audits | Startup trajectories and convergence diagnostics; no demonstrated paper-consistent zero-start-to-ZVS handoff |

Output boundaries differ **between named experiments**, never implicitly:
older isolation studies use an ideal 1 V source; the new P25 core retains a
dynamic output capacitor. Check the case boundary before transferring results.

## Selected evidence

- **Equations before tuning.** The P24 5 MHz inductance calculation gives
  1.4667 nH, versus 2.68 nH in Table I. The discrepancy is recorded, not hidden.
  [Source and formula records](paper_locked/README.md)
- **A failure localized to its physical event.** A synthetic P25 trajectory
  reaches M5, but phase 3 current reaches zero before SH2 achieves ZVS.
  Volt-second and output-charge accounting explains the failed continuation;
  this is not a paper-parameter experiment.
  [D13](symbolic_derivations/02_P25_native/D13_NEGATIVE_TARGET_AND_HIGH_HANDOFF.md) ·
  [D14](symbolic_derivations/02_P25_native/D14_FREEWHEEL_MARGIN_AND_SEED_SCOPE.md)
- **Independent cross-check.** A52 compares a corrected four-phase periodic
  state against LTspice at **89.92 W delivered power**, under a uniform 7 mΩ
  switch model—not the 250 W/module target.
  [A52 results](experiments/track_A_periodic_steady_state/A52_spice_crosscheck_reduced_load_zvs/RESULTS.md)
- **ZVS is not automatically an efficiency win.** Separate sensitivity studies
  examine nonlinear capacitance, dead time, temperature, winding-loss budget
  and load. Conclusions remain attached to their modeled boundaries.
  [A59: capacitance](experiments/track_A_periodic_steady_state/A59_nonlinear_coss_epc2067/RESULTS.md) ·
  [A60: temperature](experiments/track_A_periodic_steady_state/A60_temperature_ron_sensitivity/RESULTS.md) ·
  [A62: load](experiments/track_A_periodic_steady_state/A62_load_sweep_fixed_deadtime/RESULTS.md)

## How the project is built

| Layer | Responsibility | Entry point |
|---|---|---|
| Sources & assumptions | Paper claims, extensions and unknowns | [paper_locked](paper_locked/README.md) |
| Equations & state | KCL/KVL, charge, flux and energy | [derivations](symbolic_derivations/README.md) |
| Events & control | Zero crossings, ZVS admission, latched targets and gate transitions | [reusable modules](src/scb_ivr/README.md) |
| Devices & experiments | Explicit models and controlled comparisons | [experiments](experiments/README.md) |
| Verification | Tests, first-failure diagnostics and circuit cross-checks | [tests](tests/README.md) · [validation](validation/README.md) |
| Extensions | Our additions beyond P24 and P25 (topology or hardware the papers do not have), kept apart from the reproduction | [extensions](extensions/README.md) |

P24/P25 conflicts create separate branches. A three-phase result is never
silently relabeled as four-phase. Capacitor/current states are not reset to
force a successful event, and unsuccessful cases remain part of the record.

## Run the checks

Python 3.11+:

```bash
python3 -m pip install -r requirements.txt
python3 tests/run_portable_suite.py
```

Verified locally on **2026-09-28: 416 portable tests passed**. GitHub Actions
runs this suite. The full suite also checks locally generated LTspice logs:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

**435 full-suite tests passed** on the same date. These are software and model
contract checks, not 435 reproduced paper operating points. Local log fixtures
are not published.

## Where to go next

- **Technical reviewer:** [overview](PROJECT_OVERVIEW.md) → [status and limitations](reports/CURRENT_STATUS.md).
- **Model developer:** [module guide](src/scb_ivr/README.md) → [15-mode assembly](symbolic_derivations/02_P25_native/D15_THREE_PHASE_MODE_ASSEMBLY.md).
- **Experiment reviewer:** [experiment index](experiments/README.md) → the selected case's boundary and results.
- **Historical context:** [experiment registry](paper_locked/00_boundaries/EXPERIMENT_REGISTRY.md). Older reports are dated snapshots, not the current baseline.

Source papers, private meeting notes, raw waveforms and temporary solver outputs
are excluded from publication. Existing paths are retained to preserve scripts
and evidence references.
