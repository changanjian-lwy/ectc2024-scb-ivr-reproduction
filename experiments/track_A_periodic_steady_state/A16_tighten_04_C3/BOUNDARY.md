# A16 - periodic-state tightening 04: C3 only

## Parent and only change

- Parent: A15 initial-state vector.
- Only `VC3` is updated to A15's measured final value:
  `12.0006048777 V`.
- With `V(a3)=12 V`, its compatible node seed becomes
  `V(x3)=-0.0006048777 V`.
- C1, C2 and all four current seeds remain exactly as in A15.

All topology, P24 2% control, component/Coss data, zero snubber, ideal 1 V
isolation clamp, timing and numerical boundaries remain locked. Acceptance is
based on the complete seven-state residual; no post-result tuning is allowed.
