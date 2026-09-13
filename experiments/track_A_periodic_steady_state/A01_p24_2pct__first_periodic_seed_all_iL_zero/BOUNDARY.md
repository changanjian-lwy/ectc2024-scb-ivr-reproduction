# A01 - first P24 periodic seed, source-native 2% branch

- Compared with: A00 (no electrical run).
- Changed: first executable 200-ns single-module orbit candidate.
- P24 system design: 48 V, 1 V, 1 kW, `nP=4`, `nM_system=4`, 5 MHz.
- Circuit instance: one 250-W module, `nM_instance=1`.
- First solver seed only: `VC1/VC2/VC3=36/24/12 V`, `Vout=1 V`, all `iL=0`.
- Negative target: P24 upper source-native 2% of 125-A phase peak.
- `L=1.4666667 nH`: user-selected recalculation from the printed equation.
- Flying/output capacitance: retained cross-source candidate, not P24 values.
- Commutation capacitance is now assembled modularly without changing the
  electrical case: `CH_DEVICE=385 pF`, `CL_DEVICE=770 pF` from the GS61008T
  time-equivalent datasheet view and P25 switch population;
  `CH_SNUBBER=CL_SNUBBER=0` because neither paper publishes the added value.
- The P24 `NEG_FRAC=2%` control boundary remains an independent paper-derived
  input. It is not fitted to the selected device capacitance.
- Sequence: P24 active-high plus next-low command, symmetrically rotated; this
  rotation is `P24_DERIVED`, not a published zero-start controller.
- Pass: all eight state residuals after exactly 200 ns close; no tuning permitted.
- Result: **ran, periodic closure failed as expected for the first seed**.

Final boundary-corrected run (phase-1-origin fast node/Coss seed included):

| Residual after 200 ns | Value |
|---|---:|
| `dVC1` | +0.3882 mV |
| `dVC2` | +0.2317 mV |
| `dVC3` | -0.2522 mV |
| `dVout` | -4.3868 mV |
| `diL1` | -0.4190 A |
| `diL2` | +4.5928 A |
| `diL3` | +40.4428 A |
| `diL4` | +85.0041 A |

The capacitor seed is close on a single-cycle voltage scale, but the current
state is not remotely periodic. Matching output/capacitor values alone would be
a false pass. Phase-1 current ranges from -3.337 A to 120.621 A; its negative
fraction also exceeds the requested 2% boundary, showing that the present
behavioral low-side release is not yet enforcing the physical event cleanly.

Two earlier runs in the same log-development history exposed invalid initial
fast states. They are not used as the final A01 result. Their lesson is retained:
when device Coss is present, the periodic state includes compatible switching
node voltages in addition to the eight slow variables.
