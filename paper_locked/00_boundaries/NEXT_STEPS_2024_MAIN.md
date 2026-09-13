# Next steps - 2024 main reproduction

## Non-negotiable boundary

Main target: 2024 ECTC, 48 V to 1 V, 1 kW, four phases per module, four
modules, nominal 5 MHz. No 2025 device value, guessed capacitor value,
controller threshold or timing calibration may silently enter this case.

## Gate 1 - Analytical closure

1. Visually transcribe and independently recalculate 2024 Eqs. (1)-(6).
2. Reproduce the selected Table-I row cell-by-cell.
3. Keep 2.68 nH (Table I) and about 1.467 nH (Eq. 4) as separate branches.
4. Write every definition of current, phase, module, duty and effective
   voltage next to its equation.

**Exit condition:** no required 2024 equation remains `TRANSCRIBE`; every
Table-I number either matches, is a documented rounding difference or is a
documented conflict.

## Gate 2 - One four-phase module

1. Reuse only the previously checked circuit-construction code.
2. Build the exact 2024 Fig. 3 four-phase power stage.
3. Use ideal switches and explicitly declared numerical properties.
4. Run a clearly labelled periodic steady-state test separately from a
   zero-energy startup test.
5. Verify each phase's volt-second balance and every flying capacitor's
   amp-second balance before checking attractive headline numbers.

**Exit condition:** correct phase sequence, current paths, balance residuals
and conservation. Output voltage alone is not a pass.

## Gate 3 - Table-I conflict experiments

Run identical one-module cases with only L changed:

- Branch A: 2.68 nH from Table I.
- Branch B: approximately 1.467 nH from Eq. (4).

Report peak, valley, average phase current, balance residuals and ripple. Do
not choose a third fitted L as the paper result.

## Gate 4 - Four-module architecture

Duplicate the validated module. Test only timing conventions supported by
paper text; record ambiguous module interleaving as an explicit branch.

## Gate 5 - ZVS feasibility, not fitted ZVS

Use the 2024 1-2% negative-current boundary to calculate available magnetic
energy. Compare it against a parameterized commutation-energy requirement.
Until Coss, snubber and dead time are known, produce a feasibility map rather
than claiming a unique VDS waveform.

## Gate 6 - Author-data insertion

Insert Mihai's confirmed device, capacitor, timing and startup data as a
versioned component/control parameter set. Only then compare exact ZVS,
losses, efficiency and startup behavior with the authors' reference.
