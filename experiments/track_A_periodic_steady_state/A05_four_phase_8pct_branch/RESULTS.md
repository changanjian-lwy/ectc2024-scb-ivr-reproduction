# A05 result - 8% inserted into the full four-phase first seed

## Outcome

The run completed, but it did **not exercise the 8% turn-off event**. Its
waveforms and one-period residuals are identical to A04's 2% case.

- `IL1,min = -3.3367 A`, corresponding to only 2.67% of the 125 A target peak.
- The 8% boundary requires `IL1 = -10 A`, which is never reached.
- Therefore this run cannot be counted as an 8% ZVS pass or fail.

In the 2% case, the low-side release condition can also be masked while the
same low-side device is commanded as the adjacent support switch for another
phase. P24 explicitly gives `QH1 + QL2` for phase-1 interval 1 and says later
phases operate identically, but it does not print a complete simultaneous
four-phase gate table resolving every overlapping role.

The immediate cause is not a capacitance adjustment: the all-zero current seed
is not the periodic interleaved state, so phase currents and event times are
misaligned during the first simulated period. A periodic-state solve (including
all four inductor currents and fast Coss node voltages) is required before the
full four-phase 8% event can be judged.

## Natural balance boundary

The SCB power stage contains the passive charge-transfer mechanism: each flying
capacitor is charged by its own phase and discharged by the adjacent phase.
There is no active voltage-error feedback loop in A04/A05. The voltage
supervisor only permits or delays a phase; it does not command a correction
toward 36/24/12 V. A one-period first-seed run cannot establish asymptotic
self-balancing.
