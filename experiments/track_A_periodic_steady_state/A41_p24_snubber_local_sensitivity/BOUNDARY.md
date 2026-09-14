# A41 P24 1%-2% local snubber-sensitivity boundary

Track: A, local P24 `t2->t3` commutation screen. This is not a periodic-orbit
experiment.

## 1. Parent

Electrical parent:
`paper_locked/02_ectc2024_main/spice/R04D3A_P24_interval3_same_phase_ZVS.cir`.
A40 supplies only the analytical questions and measurements; it supplies no
electrical value.

A31 is deliberately not the parent because it changes `IL2_INIT` to align a
cross-phase event and includes downstream scheduling. That state would mix an
initial-condition correction into a snubber-only sensitivity test.

## 2. What changes

Two independent branches are generated:

- `HIGH_ONLY`: add `CH_SNUBBER` at the high-side `CH1` position while
  `CL_SNUBBER=0`.
- `SYMMETRIC`: add the same capacitance at `CH1` and `CL1`.

Within each branch, the only electrical sweep variable is the added snubber:
`0, 50, 100, 250, 500 pF, 1 nF, 2 nF`. P24 1% and 2% are separate control-
boundary rows, never fitted values.

## 3. What stays fixed

- P24 local Interval 3 topology and state sequence.
- `Vin=48 V`, `Vo=1 V`, `nP=4`, `Ipk=125 A`.
- locked Eq.-(4) `L=1.4667 nH`; Table-I 2.68 nH is not used.
- GS61008T charge-equivalent device abstraction: 385 pF high side and 770 pF
  low side before added snubber.
- P25 device population and 7-mOhm/3.5-mOhm switch resistances.
- R04D2A-chained capacitor/node initial state.
- ideal event latch: low side opens only at the exact negative-current target;
  high side is admitted only after its own `Vds=0` event.
- timestep, tolerances and 50-ns local observation window.

## 4. Provenance

- 1%-2%: `P24_EXPLICIT`.
- `CH/CL` locations and Mode-5 mechanism: `P25_SUPPLEMENT`.
- sweep values: `SENSITIVITY_ONLY`, not paper values.
- device capacitances: `EXTERNAL_DEVICE_DATA` constant charge-equivalent
  approximation, not nonlinear `Coss(V)`.

## 5. Question

At an exactly captured P24 1% or 2% low-side release event, how does added
high-side-only or symmetric high/low snubber capacitance change the natural
high-side `Vds=0` event? Does any positive snubber improve ZVS through changed
voltage sharing, or does it only increase the required commutation charge/time?

## 6. Per-case success condition

1. Low-side release occurs at the selected `-1.25 A` or `-2.50 A` target.
2. High-side `Vds` reaches zero naturally after release and within 50 ns.
3. High side is admitted only by that event, with low side remaining off.
4. Report commutation duration, current at ZVS, minimum high-side Vds, maximum
   low-side Vds, and comparison with A40's Eq.-(13) time law.

## 7. Failure condition

- `NO_ZVS_WITHIN_WINDOW`: no high-side zero crossing in 50 ns.
- `CONTROLLER_GUARD_PASS`: high side remains blocked when no ZVS occurs.
- `WRONG_RELEASE_BOUNDARY`: measured low-side release current misses its
  selected target beyond numerical tolerance.
- A numerical failure is reported separately and never converted into an
  electrical conclusion.

No capacitance, threshold, inductance, initial voltage or time window may be
changed after observing a result to manufacture a pass.

## 8. What this cannot prove

This local screen cannot prove the complete four-phase handoff, 50-ns slot
compatibility in the global timeline, 200-ns periodic closure, startup,
hardware loss, or the real unpublished `CH/CL` values.
