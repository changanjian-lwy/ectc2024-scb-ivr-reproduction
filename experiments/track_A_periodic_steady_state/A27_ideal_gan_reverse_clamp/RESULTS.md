# A27 results

## Run status

LTspice completed the A27 netlist with the ideal GaN reverse-conduction
plug-in loaded. No topology, component, initial-state, threshold or timestep
parameter was changed from A26.

## Phase-2 measurements

| Event | A27 result |
|---|---:|
| `SL2` release at the -9% current target | 23.79275 ns |
| `iL2` at release | -11.2514 A |
| `Vds(SH2)` at release | 11.8905 V |
| first `Vds(SH2)=0` after release | 26.09869 ns |
| release-to-first-zero interval | 2.30594 ns |
| `iL2` at the first zero | -1.388 A |
| `Vds(SH2)` at the fixed 50 ns request | 9.958 V |

`SH2` therefore remains blocked by the readiness guard at 50 ns. There is no
same-leg command overlap.

## Interpretation

The reverse path works as a **polarity-dependent clamp**, not a sample-and-hold
element. While negative inductor current supports reverse conduction, it clips
the negative `Vds` excursion and supplies the GaN Mode-5' path. After that
current is exhausted and reverses polarity, the reverse path turns off and the
switch-node voltage is free to leave zero. Consequently, the clamp does not
hold `Vds(SH2)=0` from 26.10 ns until the fixed 50 ns high-side request.

This corrects the A26 interpretation. A26's apparent 4.286 ns wait after the
50 ns request was caused by catching a later, unclamped LC zero crossing. With
the physically required reverse path present, that repeated negative-voltage
ringing is clipped; the relevant ZVS opportunity is the finite window around
the first zero crossing.

## Boundary conclusion

- **PASS:** reverse-conduction/clamp module is present and suppresses the
  unphysical negative `Vds` excursion of the no-clamp ideal model.
- **PASS:** the first phase-2 ZVS opportunity is identified without changing
  the -9% threshold or component data.
- **FAIL:** the fixed `T/4 = 50 ns` request does not fall inside that ZVS
  opportunity.
- **Next required module:** schedule/latch the high-side command from the
  paper-defined `Vds=0` event (with dead-time/Mode-5' handling), rather than
  treating the nominal interleaving clock edge as the physical turn-on event.
