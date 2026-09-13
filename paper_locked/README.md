# Paper-locked reproduction workspace

This directory contains the formal reproduction path. Files outside this
directory are historical exploration unless explicitly promoted here.

## Directory map

- `00_boundaries/`: frozen scope, source hierarchy, acceptance criteria and
  unresolved paper inputs.
- `01_common_physics/`: topology-independent equations and reusable component
  interfaces.
- `02_ectc2024_main/`: the requested 48 V/1 V, 1 kW,
  four-phase/four-module reproduction. This is the only main line.
- `03_apec2025_auxiliary/`: supporting evidence for switch connections,
  Mode 1-6 interpretation and later hardware practice. Its 12 V component
  values never enter the 2024 main model without explicit confirmation.
- `04_component_models/`: replaceable GaN, driver, inductor and capacitor
  parameter sets, each with provenance.
- `05_framework/`: later orchestration and topology/component substitution.
- `90_legacy/`: index of earlier exploratory E/I0/APEC files; they are not
  paper-reproduction evidence.

## Naming rule

- `PF-A24-*`: analytical audit of the 2024 paper.
- `PF-S24-*`: SPICE experiments for the 2024 paper.
- `AUX-A25-*` / `AUX-S25-*`: 2025 supporting analyses and simulations.
- `CM-*`: component models.
- `FW-*`: framework-level tests.

Every experiment record states the parent experiment, the single changed
variable, fixed paper boundary, unresolved inputs, result and next action.
