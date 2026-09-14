# A28B results - labelled P25 9% extension

LTspice completed normally with the same topology, state, Coss, clamp and event
scheduler as A28. The only changed control input is `NEG_FRAC=9%`.

| Event | Result |
|---|---:|
| `SL2` release | 23.79273 ns |
| `SH2` event-controlled turn-on | 26.09940 ns |
| local commutation interval | 2.30667 ns |
| `Vds(SH2)` at turn-on | -0.000454 V |
| `iL2` at turn-on | -1.38283 A |
| `SH2` turn-off at current peak | 43.86540 ns |

Status: **LOCAL PHASE-2 EVENT CHAIN PASS**.

This run demonstrates that the event scheduler captures the first ZVS window
when the separately labelled 9% extension supplies sufficient commutation. It
does not reproduce the 50 ns phase origin and does not authorize replacing the
P24 1-2% boundary with 9%. The mismatch is now isolated to commutation-energy
inputs/state, rather than the ZVS event detector.
