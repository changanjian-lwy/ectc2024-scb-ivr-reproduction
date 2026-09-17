# P25-native method calibration

## Purpose

This audit asks whether the event method used in the P24-primary/P25-
supplement branch can reproduce the P25 prototype on P25's own topology and
reported operating point.  It is a calibration of the method, not a new P25
hardware-reproduction claim.

## Frozen paper boundaries

- P25 three-phase SCB module, three interleaved modules.
- 12 V input, 1 V output, 200 W total and about 67 W/module.
- Nominal switching frequency 0.5 MHz.
- `nP=3`, `nM=3`, `L=22 nH`, winding resistance 0.5 mOhm.
- One GS61008T high-side and two parallel GS61008T low-side devices.
- P25 textual sequence: high-side on interval; active-phase low-side
  commutation; all-low freewheel; next-phase negative-current detection;
  next low-side off; next high-side turn-on at its Vds-zero event.
- Negative current is restricted to P25's published 5%-10% design interval.
- Eq. (17) gives `D=nP*Vo/Vin=0.25`, so `Ton=500 ns` at 0.5 MHz.  Table II's
  printed `D=0.26%` cannot literally mean 0.26 percent because that conflicts
  with Eq. (17); it is treated as an ambiguous/typographical presentation,
  not used to override the equation.

## Explicit unresolved assumptions

- The periodic ladder is initialized; this is not a zero-start test.
- P25 omits the complete series/output-capacitor suffixes and added CH/CL
  snubber values.  `Cfly=120 uF` remains the documented sensitivity baseline.
- `CH=385 pF`, `CL=770 pF` are the existing GS61008T time-equivalent plug-in
  values, not values reported by P25.
- The output is treated as a stiff 1 V boundary in the analytical ring.
- Reverse conduction is the same zero-Qrr linear numerical branch used by the
  P24 analytical audit, not a manufacturer dynamic GaN model.

## Experiment 1: fixed nominal phase slots

With phase slots fixed at `T/3=666.667 ns` and the 5% target derived from
`2Io/(nP*nM)=44.444 A`, the first high-side interval reaches 59.919 A.  At the
next fixed slot, high-side Vds is still +65.86 mV, so strict ZVS admission
fails.

Scanning only the published 5%-10% interval shows that 5.25%-6.5% can admit
the first handoff for the documented seed, but no scanned case completes the
full three-phase ring.  The maximum is two handoffs.  This is an initial-state
sensitivity result, not a unique hardware threshold.

## Experiment 2: literal P25 event timing

When the next high side is fired at the first Vds-zero event, one ring completes
all three local ZVS events at the 5% target.  The first-ring phase spacings are
650.38, 604.43 and 515.74 ns; the ring period is 1770.55 ns (564.8 kHz), and
the state drifts.  Feeding the final state into a second ring fails when the
next negative-current target has already been passed.

Therefore a one-ring event pass proves local causal feasibility only.  It is
not a periodic or 0.5-MHz reproduction.

## Experiment 3: periodic event shooting

A seven-state shooting solve finds a locally periodic event-controlled point:

- maximum voltage return error: 1.74 mV;
- maximum current return error: 0.718 mA;
- period: 1776.02 ns (563.06 kHz);
- phase spacings: 678.70, 502.20 and 595.11 ns.

This is a useful event-machine fixed point, but it violates nominal 0.5 MHz
and equal 120-degree phase spacing.  It is retained as a diagnostic, not a
paper match.

## Experiment 4: periodicity plus equal-spacing fit

The local joint fit allows the negative-current fraction to vary only from 5%
to 10% and simultaneously penalizes state-return and spacing errors.  It ends
at the 10% upper bound.  The three spacings become nearly equal at 617.29,
617.41 and 617.03 ns, but remain about 49.6 ns short of 666.67 ns.  Current
return errors remain 2.68-3.54 A.  The optimizer's numerical termination flag
is therefore **not** a feasibility pass.

This local result is not a proof of global infeasibility.  It shows that the
current public parameter set and the present device abstraction do not yet
simultaneously satisfy periodic return, nominal frequency/equal interleaving,
the published negative-current band and all three ZVS admissions.

## Consequence for the P24 main line

The method reproduces the P25 local Mode-4/5/6 causal chain and can find a
periodic event-machine state.  Therefore the P24 full-ring failure cannot be
assigned solely to a broken event-order implementation.  The remaining gap is
concentrated in the unpublished commutation/device/control data and in the
reported-operating-point consistency:

1. exact CH/CL added snubber values and effective nonlinear Coss/Qoss;
2. complete series/output capacitor values, ESR and ESL;
3. actual zero-cross/negative-current detector delays and gate-driver dead
   times;
4. measured high-side phase spacings (whether 0.5 MHz/120 degrees is exact or
   nominal under event control);
5. clarification of the 22 nH, 500 ns and measured-current relationship.

## Files

- `p25_native_fixed_slot_ring.py`: common P25-native event engine.
- `scan_p25_native_target.py`: 5%-10% fixed-slot scan.
- `shoot_p25_event_fixed_point.py`: unconstrained event-period shooting.
- `fit_p25_equal_spacing.py`: local periodic/equal-spacing joint audit.
- `numerical_runs/01_full_ring_calibration/`: CSV, JSON and solver logs.
