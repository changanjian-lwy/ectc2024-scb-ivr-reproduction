# Step 25 - R04D6A P25 Mode-6 energy interval

## Boundary confirmation

The Mode-6 heading repeats `[t5,t6]`, but its physical start is SH2 ZVS turn-on,
which Mode 5 defines as `t6`. The framework therefore starts Mode 6 at the
stable `PHASE2_HIGH_SIDE_ON` event and ends it at the stable
`PHASE2_INDUCTOR_CURRENT_PEAK` event without inventing a paper time label.

Duration follows P25: `D*T`, with Eq.(17) giving `D=3*1/12=0.25`; at 0.5 MHz,
`D*T=0.5 us`.

## Physical local-circuit result

The accepted Mode-5 exit current (-2.12544 A) is chained without reset. With
the phase-2 rail at `VCS1-VCS2=4 V` and output at 1 V, the circuit places about
3.015 V across L2 initially. After 0.5 us, the GS61008T/22 nH circuit gives:

- `iL2=60.8952 A`, increasing as required qualitatively.

## Quantitative non-closure

- Printed Eq.(15)/(16), using 4 V and not subtracting Vo, predicts 88.7837 A
  after including the chained negative entrance current.
- The prior `2Io/(nP*nM)` phase-peak relation gives 44.4444 A for 200 W,
  `nP=3`, `nM=3`.
- The physical local circuit gives 60.8952 A.

These three values do not agree. No voltage, duty, inductance or initial
current is altered to force agreement. Mode 6 passes as a qualitative physical
transition but fails quantitative peak-current reproduction pending resolution
of the equation/topology/module-count interpretation.
