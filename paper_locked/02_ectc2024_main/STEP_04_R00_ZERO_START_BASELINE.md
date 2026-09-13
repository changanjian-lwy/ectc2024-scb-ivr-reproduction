# Step 04 - R00 single-module four-phase zero-start baseline

## Locked objective

Test whether the grounded-low-side interpretation of the ECTC 2024 four-phase
module can enter the Table-I operating point from zero capacitor voltage under
ordinary interleaved PWM. Failure is accepted and must not trigger parameter
fitting.

## Experiment definition

The represented module is the `nP=4, nM=4` Table-I case. One module therefore
serves a 250 W load. The run uses the published 5 MHz row: 8.4% duty (with the
exact Eq. (1) value 1/12 in the executable model), 16.7 ns on-time, 2.68 nH per
phase, and 125 A peak-current target.

The ECTC paper does not report flying/output capacitance. R00 therefore uses the
nominal, unmodified component-bank sums in EPE 2019 Table I: 53.8 uF per flying
capacitor and 4.672 mF at the output. These values are tagged cross-source and
will not be tuned to improve agreement.

All capacitor initial voltages are zero. There is no 36/24/12 V preset, no
precharge source, no active balancing, no soft-start, and no closed-loop
zero-crossing controller.

## Start-up source compatibility finding

EPE 2019 Fig. 5 is not directly inserted. Its conventional four-phase SCB
drawing uses cascaded low-side connections in the charge-redistribution loops,
whereas the project topology follows the grounded SL1-SL4 terminals explicitly
shown in APEC 2025 Fig. 1. Therefore the EPE sequence is retained as an
adaptation candidate, not treated as proof that U05 is resolved for ECTC 2024.

## Pass/fail rules

The run passes the zero-start baseline only if all of the following occur
without changing any source value:

1. Vout settles near 1 V.
2. Four phase currents are balanced and have the expected boundary waveform.
3. Their peaks are consistent with 125 A.
4. The three flying-capacitor voltages settle without a forced initial value.
5. No startup inrush or node voltage violates the ideal topology interpretation.

If any item fails, R00 is recorded as a failed zero-start experiment. The next
experiment may change only the control/startup module and must cite that change.

## First execution record

- Execution: **completed manually in LTspice 26.0.2 on 2026-09-12**.
- Numerical status: the transient solution completed without a convergence
  error and produced `.log`, `.raw`, `.db`, and `.op.raw` files.
- Electrical classification: **FAILED_ZERO_START_BASELINE**.

Measured over 40-50 us unless otherwise stated:

| Quantity | R00 result | Required interpretation |
|---|---:|---|
| Average output voltage | 0.99583 V | Near the 1 V target, but insufficient by itself |
| Output peak-to-peak ripple | 0.10250 V | About 10.3% of output; not a valid low-ripple state |
| Average `VC1` | 26.3778 V | Self-established, not preset |
| Average `VC2` | 10.3732 V | Self-established, not preset |
| Average `VC3` | 2.34071 V | Self-established, not preset |
| `IL1` min / max | -2010.04 / 996.57 A | Grossly exceeds the 125 A Table-I target |
| `IL2` min / max | -842.10 / 429.57 A | Grossly exceeds target and is not balanced with phase 1 |
| `IL3` min / max | -253.50 / 1044.22 A | Grossly exceeds target and is not balanced |
| `IL4` min / max | -846.01 / 2161.57 A | Grossly exceeds target and is not balanced |
| Peak input current, 0-5 us | 710.91 A | Large uncontrolled start-up inrush |

### Conclusion

The near-1 V average is a misleading scalar coincidence. The four phase
currents are neither balanced nor at the CCM-DCM boundary, and the capacitor
state is not the intended steady operating state. Ordinary 5 MHz interleaved
PWM cannot be used as a justified zero-state startup procedure for this model.

No source value was changed after this failure. In particular, the capacitor
voltages were not replaced with 36/24/12 V initial conditions. R01 must address
the topology-compatible startup/control transition rather than tune L, C,
duty, or load to make the reported numbers look better.
