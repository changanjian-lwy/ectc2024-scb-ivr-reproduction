# A42 zero-snubber negative-current threshold boundary

Track: A, local P24 `t2->t3` mechanism experiment. This is not a periodic-orbit
or startup experiment.

## Parent and fixed quantities

Electrical parent:
`paper_locked/02_ectc2024_main/spice/R04D3A_P24_interval3_same_phase_ZVS.cir`.

The following remain identical to A41's zero-snubber baseline:

- P24 topology, local state sequence and R04D2A-chained initial state;
- `Vin=48 V`, `Vo=1 V`, `nP=4`, `nM=1`, `Ipk=125 A`;
- locked Eq.-(4) `L=1.4667 nH`;
- P25/external GS61008T charge-equivalent `CH=385 pF`, `CL=770 pF`;
- high/low switch resistance 7/3.5 mOhm;
- no added snubber, delay, dead time, nonlinear `Coss(V)` or retuning;
- exact event latch and 50-ns observation window.

## Only changed variable

`NEG_FRAC` is swept from 1% through 10% in 1-percentage-point increments.

- 1%-2% are `P24_EXPLICIT` rows.
- 5%-10% are `P25_SUPPLEMENT` rows.
- 3%-4% are `DIAGNOSTIC_BRIDGE` rows only.

No row may be relabelled as belonging to a different source merely because it
passes or fails.

## Success and extraction

A row passes the local event only when the low side releases at its exact
target and high-side `Vds` subsequently reaches zero naturally. The high side
may turn on only after that voltage event. Extract release time/current, ZVS
time, commutation duration and current at ZVS.

The coarse grid is intended to bracket the threshold. A later refinement may
search only inside the first pass/fail bracket and must remain a sensitivity
result, not a paper value.

## Prohibited claims

A local pass cannot establish the P24 1%-2% claim, a four-phase handoff,
periodic closure, startup, hardware loss, or the authors' unpublished device
capacitances.
