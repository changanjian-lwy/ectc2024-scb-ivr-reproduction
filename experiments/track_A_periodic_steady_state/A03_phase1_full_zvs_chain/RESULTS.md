# A03 results - naturally chained first-phase events

## Controlled sweep

The only changed variable is the negative-current threshold. Device Coss,
topology, timing, initial states and switch parameters remain fixed.

| Negative fraction | Current at low-side turn-off | Minimum HS Vds after turn-off | HS Vds-zero event | Result |
|---:|---:|---:|---:|---|
| 8% | -10.0007 A | 1.1809 V | none | fail |
| 9% | -11.2510 A | -4.65 mV | 183.5056 ns | pass |
| 10% | -12.5007 A | -36.11 mV | 184.8357 ns | pass |

At 9%, the high-side gate rises at 183.5057 ns, about 0.000121 ns after its
Vds-zero event. The measured high-/low-side gate-overlap monitor remains zero.
The corresponding low-side-off to high-side-on interval is 2.3752 ns.

## Why the isolated 8% result did not survive chaining

R04D3E represented only one switching leg initialized directly at the start of
its negative-current/ZVS exit. A03 retains the adjacent phase and the shared
flying-capacitor ladder from the preceding energy-transfer interval. During
the high-side return commutation, that connected branch adds state and charge
demand. Consequently the same -10 A release reaches only 1.1809 V rather than
zero high-side Vds.

This is a model-boundary result, not permission to replace P24's 1%-2% with
9%. It shows that the minimum negative current depends on the complete
connected commutation network, not only the selected transistor Coss.

## Next required topology step

The four phases do not execute complete cycles sequentially. With 5 MHz and
four phases, phase-2 begins at `T/4=50 ns`, while phase-1 is still in its
freewheel interval. The next experiment must therefore add the phase-2 event
at its true interleaved origin and retain the phase-1 state concurrently. It
must not wait until the 183.5 ns phase-1 return event and then manually start
phase 2.
