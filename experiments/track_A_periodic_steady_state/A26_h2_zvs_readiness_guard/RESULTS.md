# A26 results - SH2 readiness guard

## Detector result

| Event | Time/value |
|---|---:|
| Nominal phase-2 request | 50.000 ns |
| `Vds(SH2)` at request | 21.561 V |
| First natural `Vds(SH2)<=0` | 54.286 ns |
| First permitted `SH2` gate-on | 54.287 ns |
| Added wait from nominal request | 4.286 ns |

The guard passes its safety function: it blocks the hard 50 ns transition and
admits `SH2` only after the switch voltage reaches zero. Phase-2 ZVS is achieved
in this guarded local handoff.

## Why the apparent wait is 4.286 ns

This is not the duration of one slow Coss commutation. `SL2` releases at
23.737 ns and `Vds(SH2)` first reaches zero at 25.834 ns, only about 2.097 ns
later. The subsequent zero crossings are approximately 35.314 ns, 44.799 ns
and 54.286 ns. The nominal 50 ns request misses the first three opportunities,
so the readiness guard catches a later resonant crossing 4.286 ns after it is
armed.

The repeated crossings occur because the current A25/A26 switch plug-in has
scalar Coss but no GaN off-state reverse-conduction clamp. P25 explicitly notes
GaN reverse conduction and its Mode 5-prime interval. A prior auxiliary model
represented that path with a zero-Qrr numerical diode, but it has not yet been
promoted into the main-line device module. Therefore A26 demonstrates the
timing mismatch and guard logic, but its free ringing after the first zero is
not yet a complete P25 device representation.

## Newly exposed scheduler boundary

A26 retains the original absolute request-window end at 66.667 ns. Because the
gate starts late, only about 12.38 ns remains, rather than the paper-derived
`TON=16.667 ns`. Thus A26 does **not** yet preserve the P24 duty/volt-second
condition or prove a complete four-phase cycle.

The papers define the desired ZVS event and nominal on-time but do not state how
a four-phase controller should recover from a 4.286 ns readiness delay. Two
different policies must not be silently merged:

1. keep the original end time, shortening the pulse and disturbing energy/
   volt-second balance;
2. preserve full `TON` after ZVS, shifting later phase requests and changing
   the interleaving period/schedule.

## Status

**Readiness detector: pass. Full scheduler: unresolved.** The next experiment
requires an explicitly selected, provenance-labelled recovery policy. Until
then the guard must not be copied to later phases as though the full timing
problem were solved.
