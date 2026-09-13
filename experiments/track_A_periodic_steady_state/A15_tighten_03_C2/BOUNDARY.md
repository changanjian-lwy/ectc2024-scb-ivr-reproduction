# A15 - periodic-state tightening 03: C2 only

## Parent and only change

- Parent: A14 initial-state vector.
- Only `VC2` is updated to A14's measured final value:
  `23.9999142326 V`.
- With `V(a2)=24 V`, the compatible node seed becomes
  `V(x2)=0.0000857674 V`.
- C1, C3 and all four current seeds remain exactly as in A14.

All topology, P24 2% control, component/Coss data, zero snubber, ideal 1 V
isolation clamp, timing and numerical boundaries remain locked. Acceptance is
based on the full seven-state residual, not C2 alone.
