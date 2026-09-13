# Step 01 - 2024 ECTC analytical baseline

## Scope

This step verifies only equations (1)-(6) and the 4-phase, 4-module row of
Table I. It does not claim that the switched circuit, startup process, flying
capacitor balance, ZVS commutation, or the complete 1 kW converter has been
reproduced.

## Locked inputs

- Input voltage: 48 V
- Output voltage: 1 V
- Output power: 1 kW
- Number of phases per module: 4
- Number of parallel modules: 4
- Minimum high-side on-time used by the paper: 3.4 ns
- Table-I frequencies: 1, 5, 10, 50, and 100 MHz

No flying-capacitor voltage, capacitance, ESR/ESL, switch parasitic, dead time,
startup state, or controller parameter is introduced in this analytical step.

## Acceptance rules

1. Paper equations are transcribed literally and evaluated in SI units.
2. A table entry passes the numerical-transcription check when the relative
   difference is at most 2%. This accommodates the printed table's coarse and
   inconsistent display precision (for example 1.666... ns is printed 1.7 ns)
   but remains far below the 45%-48% Equation-(4) discrepancy.
3. A paper-equation/table mismatch is recorded as `CONFLICT`; no coefficient,
   boundary, input, or formula may be changed to improve agreement.
4. Results in this step are analytical checks, not SPICE reproduction claims.

## Current outcome

- Equation (1): locked.
- Equation (2): locked.
- Equation (3): locked; the 4-phase on-time row agrees with Table I within 1%.
- Equation (4): locked as printed, but its calculated inductance does not agree
  with the 4-phase/4-module Table-I row. The disagreement is retained as a
  paper-internal conflict pending author clarification or a documented missing
  assumption.
- Equations (5)-(6): locked from the printed paper; their Table-III audit is a
  separate step.

Machine-readable details are written to
`outputs/table1_4phase_4module_audit.json`; the corresponding flat table is
`outputs/table1_4phase_4module_audit.csv`.
