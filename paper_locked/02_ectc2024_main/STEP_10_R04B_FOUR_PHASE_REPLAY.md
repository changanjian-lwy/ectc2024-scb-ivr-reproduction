# Step 10 - R04B four-phase periodic replay

## Experiment boundary

This experiment tested whether ordinary complementary `1->2->3->4`
interleaving could reproduce the P24 four-phase periodic state once the flying
capacitors were initialized to the ideal ladder. It was explicitly a
steady-state replay, not startup or ZVS.

- Capacitor `IC=36/24/12 V` values were derived periodic-state initial
  conditions, not independent voltage sources.
- `Cfly=53.8 uF` and `Cout=4.672 mF` were cross-source EPE2019 values, not P24
  values.
- Two locked inductance branches were retained: printed Eq.(4) `1.46667 nH`
  and Table-I `2.68 nH`.
- No Coss, CH/CL, dead time, ZCD delay, startup or loss claim was made.

## R04B 10-us result

Status: **NUMERICALLY_COMPLETED / NOT_CONVERGED_TO_CHARGE_BALANCE**.

The output was near the target but capacitor-average currents were not all near
zero and phase extrema were unequal. A longer observation window was required
before deciding whether this was merely initial-state settling.

## R04B-LONG 100-us result

No electrical or switching parameter was changed. Only the observation time
was extended from 10 us to 100 us; the final 2 us were measured.

Status: **FAILED_FOUR_PHASE_CHARGE_BALANCE_AND_CURRENT_SHARING**.

| Quantity | Eq.(4) L=1.46667 nH | Table-I L=2.68 nH |
|---|---:|---:|
| Vout average | 0.99929 V | 1.00317 V |
| C1 average voltage | 35.8886 V | 35.8916 V |
| C2 average voltage | 23.8840 V | 23.8151 V |
| C3 average voltage | 11.8981 V | 11.8771 V |
| C1 average current | -2.108 A | -0.968 A |
| C2 average current | -2.505 A | -0.774 A |
| C3 average current | -2.221 A | -0.947 A |

Phase-current extrema in the final window were not equal. The Eq.(4) branch
ranged from `L1=-49.1/88.8 A` to `L4=34.2/167.2 A`; the Table-I branch ranged
from `L1=7.55/80.14 A` to `L4=37.57/114.11 A`.

## Interpretation and corrected boundary

The near-1-V output is not a success criterion by itself. Persistent nonzero
flying-capacitor average current and unequal phase extrema reject the ordinary
complementary-PWM construction.

P24 explicitly describes Interval 1 with `QH1` and the adjacent-phase `QS2`
conducting. The R04B construction instead drove every low side as the simple
complement of its own high side. That rule was an earlier inference and is not
supported strongly enough to remain in the primary model.

This failure must not be repaired by changing capacitance, inductance, initial
voltage or phase order. The next allowed change is structural control only:
transcribe the adjacent-phase paired states from P24 Figs. 3-4 and the expanded
P25 Fig. 3 sequence into a four-phase latched state table, then regenerate gate
commands from that table.

## Claim boundary

R04B may be reused only as a rejected baseline demonstrating that ordinary
complementary interleaving is insufficient. Its waveforms and final capacitor
voltages are not valid steady-state parameters for later experiments.
