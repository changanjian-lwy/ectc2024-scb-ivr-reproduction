# P25 inductance/operating-point closure

This check uses only the paper-level equations and reported prototype values;
it does not depend on Coss, snubber, dead time or the event solver.

For 12 V to 1 V, `nP=3`, `nM=3`, 200 W and 0.5 MHz:

- `D=nP*Vo/Vin=0.25`;
- `Ton=D/fsw=500 ns`;
- `Ipk=2Io/(nP*nM)=44.444 A`;
- the 5% negative target is 2.222 A;
- the ideal phase rail is 4 V, hence the ideal net inductor voltage is 3 V.

The direct current-ramp closure then requires

`L = (4-1)*500 ns/(44.444+2.222) = 32.143 nH`.

P25 Eq. (20), evaluated through the source-locked framework, gives
`32.0625 nH`.  The small difference comes from the precise way the printed
0.95 factor is applied.  Both are close to 32 nH, not the 22 nH listed for the
prototype in Table III.

If 22 nH and a 500 ns on-time are both retained with an ideal 4 V phase rail,
the ramp predicts a 65.96 A peak from a -2.222 A entrance.  Conversely, to
reach 44.444 A with 22 nH requires one of the following idealized changes:

- `Ton=342.22 ns` instead of 500 ns;
- about 730.5 kHz if `D=0.25` is retained; or
- only 2.053 V net across the inductor (about a 3.053 V phase rail before
  accounting for losses) during a 500 ns on-time.

The detailed event model gives about 59-61 A peaks because finite resistance
and flying-capacitor dynamics reduce the ideal ramp, but it does not close the
gap to 44.444 A.  This is an operating-point consistency gap to clarify, not a
permission to replace the reported 22 nH or 0.5 MHz in the reproduction.
