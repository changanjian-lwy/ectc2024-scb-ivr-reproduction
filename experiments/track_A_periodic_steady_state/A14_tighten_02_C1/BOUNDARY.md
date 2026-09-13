# A14 - periodic-state tightening 02: C1 only

## Parent and only change

- Parent: accepted A13 initial-state vector.
- Only `VC1` is updated to A13's measured one-period final value:
  `36.000066454 V`.
- The compatible node seed is changed from `V(x1)=12 V` to
  `V(x1)=11.999933546 V` while `V(a1)=48 V` remains fixed.
- A13's four current seeds and the `24/12 V` C2/C3 seeds are unchanged.

## Locked boundaries

Topology, P24 2% switching law, component data, device Coss, zero external
snubber, ideal 1 V output isolation clamp, frequency, inductance, numerical
step and one-period measurement window are identical to A13.

## Acceptance

Accept only if the complete seven-state residual does not materially worsen.
In particular, reducing VC1 error is not sufficient if another capacitor or
the coupled current group becomes less periodic. No post-result tuning is
allowed inside A14.
