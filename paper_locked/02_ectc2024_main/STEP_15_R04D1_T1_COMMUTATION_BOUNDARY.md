# Step 15 - R04D1 t1 commutation boundary

## Locked incoming state

R04D0 supplies the state immediately before `t1`:

- `QH1` and adjacent `QS2` are ON;
- `iL1` is approximately 125 A;
- C1 has received positive charge during P24 interval one;
- `t1=Ton=16.6667 ns` relative to the selected state origin.

No R04D0 electrical value or capacitor initial condition is changed.

## R04D1-A: deliberately empty commutation slot

Only `QH1` is commanded OFF at `t1`; the run continues for 2 ns. The QH1 and
QL1 output-capacitance paths described by P24 are intentionally absent.

This is a negative control. It tests whether the numerical model incorrectly
allows a finite inductor current to disappear or finds an unphysical path
through the ideal switch's `Roff`. A convergence failure or extreme switch-node
voltage is the expected missing-model result. It must not be repaired by
changing `L`, `Ton`, C1/C2 initial voltage or the load boundary.

## R04D1-B admission rule

Only after R04D1-A is recorded may the P24/P25 commutation-capacitance mechanism
be added. Because neither paper publishes numeric CH1/CL1 values, values may be
used only as an explicitly labelled sensitivity variable. No swept point may
be promoted to the 2024 design value.

## Result

The first command encoding used a PWL source beginning at 5 V, but LTspice did
not establish the intended ON state in its initial matrix and stopped at
`node a1` before reaching `t1`. This is retained as a command-source
initialization failure, not the R04D1-A electrical result.

The identical command is re-encoded as a pulse whose explicit initial value is
5 V and whose falling edge remains fixed at `Ton`. No timing or circuit value
is changed.

That encoding also failed before reaching `t1`, so it is not used as electrical
evidence.

The final negative control transfers the measured R04D0 end state directly:
`iL1=124.9327 A`, `VC1=36.01931 V`, and `iL2=-11.35055 A`. QH1 is OFF from the
new simulation origin. These are prior experimental states, not fitted inputs.

Pending transferred-state R04D1-A execution.

Result: **EXPECTED_MISSING_MODEL_FAILURE**. LTspice reports `Singular matrix:
node a1` immediately after the state transfer. With QH1 OFF and no CH1/CL1,
the finite L1 current has no defined commutation path. No parameter was changed
to conceal the failure.

## R04D1-B: symbolic capacitance sensitivity

CH1 and CL1 are now added in the exact physical roles stated by P24 and
symbolically expanded by P25. Their numeric values remain unpublished.
Therefore `CCOMM=0.1/1/10 nF` is a labelled sensitivity sweep around P24's
order-of-magnitude wording, with `CH1=CL1` as an exploratory symmetry
assumption. The sweep tests only:

1. whether low-side Vds moves toward zero;
2. whether high-side Vds rises;
3. how the zero-voltage time changes with capacitance;
4. whether L1 current remains continuous.

It cannot select a device, dead time or valid P24 capacitance, and it cannot
claim commanded QL1 ZVS because QL1 remains OFF throughout this run.

Status: **PASSED_AS_SENSITIVITY_ONLY**.

| CH1=CL1 sensitivity value | low-side Vds first reaches zero | `iL1` at zero | high-side Vds at zero |
|---:|---:|---:|---:|
| 0.1 nF | 19.17 ps | 124.997 A | 11.9807 V |
| 1 nF | 191.09 ps | 125.583 A | 11.9805 V |
| 10 nF | 1.8518 ns | 131.295 A | 11.9785 V |

For all three branches, positive L1 current discharges the low-side
capacitance to zero and charges the high-side capacitance to approximately the
initial phase-node voltage, about 11.98 V. This matches the direction stated
by P24. The zero-voltage time changes by nearly one decade for each decade of
capacitance, demonstrating why the unpublished capacitance prevents a unique
dead-time result.

The 10-nF branch changes L1 current appreciably during commutation, so the
common approximation of constant inductor current becomes weaker as the
transition lengthens. This is an observed sensitivity result, not a reason to
select a smaller capacitance.

After the first zero crossing, low-side voltage becomes strongly negative and
high-side voltage overshoots because QL1 is deliberately not turned on and no
diode clamp is included. Those post-zero extrema are outside the accepted
interval and must not be interpreted as predicted device stress.

## Next permitted experiment

R04D1-C may add an ideal event at `Vds(QL1)=0` to turn QL1 ON and proceed with
the positive-current decay toward the P24 `iL1=0` boundary. The event logic can
be ideal; no numeric detector delay or dead time may be added until sourced.
Each capacitance branch must remain separate because their zero-event times
differ.

## R04D1-B2: P25 GS61008T device-only branch

P25 Table III specifies one GS61008T for each high side and two parallel
GS61008T devices for each low side. The official GS61008T datasheet Rev 200402
provides the following typical scalar views:

- `RDS(on)=7 mOhm` per device at 25 C and `VGS=6 V`;
- `Coss=250 pF` typical;
- `CO(ER)=302 pF` for energy equivalence over 0-50 V;
- `CO(TR)=385 pF` for time equivalence over 0-50 V;
- `Qoss=20 nC` at 50 V.

For this timing experiment, the explicitly selected view is `CO(TR)`. Applying
the P25 population outside the single-device library gives:

- `CH_DEVICE=1*385 pF=385 pF`;
- `CL_DEVICE=2*385 pF=770 pF`;
- high-side typical equivalent on-resistance `7 mOhm`;
- low-side typical equivalent on-resistance `3.5 mOhm`.

Status: **PASSED_DEVICE_ONLY_FIRST_ORDER_ESTIMATE**.

| Quantity | Result |
|---|---:|
| low-side Vds first reaches zero | 110.525 ps |
| `iL1` at that event | 125.308 A |
| high-side Vds at that event | 11.9806 V |
| C1 voltage at that event | 36.0194 V |

The capacitance direction agrees with P24. However, `CO(TR)` is specified as a
0-50-V scalar equivalent while this state swings by about 12 V. Nonlinear
`Coss(Vds)` and any external snubber used in the prototype remain absent.
Therefore 110.5 ps is a device-only first-order estimate, not the final dead
time and not a reproduced hardware timing value.

`RDS(on)` is stored but not electrically applied in this branch because QH1
and QL1 are both OFF during the accepted commutation interval. It belongs in
the subsequent conducting-state/loss model, not in the capacitance-only
transition.
