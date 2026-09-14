# A20 - P24 Interval 3, 2% threshold and cross-phase timing audit

## Source requirements kept simultaneously

P24 requires both of the following:

1. after `iL1` crosses zero it becomes slightly negative, and `QL1` turns off
   at 1-2% of the phase peak current;
2. by rotational symmetry, the phase-1 low side is the adjacent low-side path
   during the phase-4 high-side interval, just as `QS2` conducts with `QH1` in
   P24 Interval 1.

A20 checks whether the unchanged A16 periodic candidate satisfies both events
at the same time. Neither requirement is dropped to obtain a favorable result.

## Locked boundaries

- Electrical parent: unchanged A16 P24 2% periodic candidate.
- `IPEAK=125 A`; P24 upper threshold is `-2.5 A`.
- Four high-side commands remain spaced by `T/4` with the paper-derived
  `TON=16.6666667 ns`.
- All topology, initial state, component/Coss candidates, output clamp and 5 ps
  maximum timestep remain unchanged.
- P25 5-10% control is not used in this experiment.

## Acceptance checks

1. Find the first phase-1 current zero after A19.
2. Find the first `iL1<=-2.5 A` event.
3. Check whether the phase-4 adjacent-low-side support obligation has ended at
   that event.
4. At the actual allowed `QL1` release, check whether negative current can bring
   `Vds(QH1)` to zero before the next `QH1` command.

Failure is retained; no parameter or event time may be adjusted after the run.
