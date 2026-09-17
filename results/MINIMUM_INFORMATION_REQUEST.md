# Minimum missing-information request

The list is claim-dependent. It deliberately avoids asking for values that can
be obtained from the published operating point or explored as labelled
sensitivity variables.

## Minimum needed to decide a local ZVS event

1. Which switch population belongs to the Section II-B P24 mechanism:
   P24 Table-III EPC2067 population, P25 GS61008T population, or another
   device implementation.
2. The corresponding nonlinear `Qoss(V)`/validated switching model and the
   exact high-/low-side devices participating in the commutation path.
3. Any added high-/low-side snubber capacitance and its connection.
4. Commanded dead time, gate-driver propagation mismatch and detector delay.
5. The inductor's large-signal `L(I,f,T)`, DCR and tolerance rather than only
   its nominal inductance.
6. Whether the reported 1-2% or 5-10% negative current references the printed
   zero-valley peak, the actual measured peak, or another current definition;
   also where that current is detected.

## Additional minimum needed for a periodic four-phase claim

7. `C1..C3`, ESR, ESL and DC-bias derating for the flying-capacitor network.
8. The complete gate-timing policy, including whether `Ton` is common or
   phase-corrected and how a missed event is handled.
9. One measured or simulated periodic-state snapshot: the three flying-node
   voltages and four phase currents at the same defined timestamp.

## What may be swept while waiting

- Keep P24 1-2% and the P25-supplement 5-10% as separately named branches.
- Sweep reported/equation-derived inductance and declared tolerances.
- Sweep symbolic commutation energy, charge and time to return maximum
  admissible burdens; do not relabel them as hardware values.
- Use periodic-state seeds only for shooting/continuation; never call them a
  demonstrated zero-start solution.

## Short question to Mihai

For the 48-to-1 V Section II-B switching mechanism, could you confirm the
actual switch population, nonlinear output-charge model, any added snubber,
the dead-time/driver/detector timing, the negative-current reference
definition, and the flying-capacitor values/parasitics? One periodic-state
snapshot of `VC1..VC3` and `IL1..IL4` at a defined switching event would also
let us validate the full four-phase state return without assuming the initial
state.
