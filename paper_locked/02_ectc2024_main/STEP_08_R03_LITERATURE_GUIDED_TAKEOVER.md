# Step 08 - R03 literature-guided takeover experiments

## Purpose

Determine why the physically generated capacitor ladder in R03A cannot be
handed directly to the 2024 one-module/four-phase power stage. The topology,
paper operating point, phase order, inductance and final duty are locked.
Failures are retained and are not repaired by fitting paper parameters.

## Common boundary

- Primary power stage: P24 Fig. 3, one module and four phases.
- `Vin=48 V`, `Vout target=1 V`, `Pmodule=250 W`, `fsw=5 MHz`.
- `D=1/12`, `Lphase=2.68 nH`.
- No capacitor initial conditions or fixed `36/24/12 V` sources.
- R02B passive precharge remains the source of the imperfect ladder.
- `Cfly=53.8 uF` and `Cout=4.672 mF` are cross-source values from EPE2019,
  not values reported by P24/P25.

## R03B - instantaneous ideal-ZCD comparator

Changed relative to R03A: fixed complementary takeover was replaced by a
current-dependent high-side release and instantaneous low-side zero-current
turn-off.

Result: **FAILED_NUMERICAL_ZCD_CHATTER**.

- The solver became trapped at approximately `TSTART + 2.48 ns`.
- Repeated tolerance-relaxation messages show that the instantaneous current
  comparator repeatedly changed the circuit topology at the zero boundary.
- No electrical performance claim can be extracted from the incomplete raw
  data.

Conclusion: an algebraic `I(L)=0` gate expression is not an executable model of
the P24/P25 ZCD. A detector needs state memory, delay/blanking/hysteresis, or a
different physically continuous surrogate.

## R03C - ideal-diode current-extinction surrogate

Changed relative to R03B: after takeover, the low-side current path was replaced
by an ideal antiparallel diode so positive current could extinguish naturally at
zero without directly switching from an algebraic comparator.

Result: **FAILED_NUMERICAL_COMMUTATION**.

- Simulation reached approximately `TSTART + 117 ns`.
- LTspice then reported a time-step-too-small failure at ladder node `a1`.
- This model is not treated as evidence for or against the physical converter.

Conclusion: replacing synchronous low-side operation by an ideal diode does not
provide a stable or paper-faithful takeover model. It also omits the negative
current interval required by P25 for high-side capacitance commutation.

## R03D - EPE2019 gradual-duty takeover

Changed relative to R03A: only commanded on-time was ramped linearly from zero
to the locked P24 value over `TSOFT=100 us`. The 100-us ramp is a declared
sensitivity value, not a paper parameter. EPE2019 explicitly recommends
gradually increasing duty after startup, but does not report the ramp duration
for the P24 converter.

Result: **PARTIAL_SUCCESS_OUTPUT / FAILED_PHASE_CURRENT_BOUNDARY**.

| Quantity | R03A fixed takeover | R03D duty ramp |
|---|---:|---:|
| `Vout` final | 1.53694 V | 0.994016 V |
| `Vout` peak | 1.53732 V | 1.00730 V |
| post-takeover input-current peak | 42.44 A | 25.99 A |
| capacitor ladder before takeover | 34.0456/21.7934/10.6309 V | same |
| capacitor ladder at end | 34.6071/22.3057/10.9179 V | 36.6825/25.3497/13.1401 V |

R03D phase-current extrema were:

| Phase | Minimum | Maximum |
|---|---:|---:|
| L1 | -225.75 A | 382.55 A |
| L2 | -100.24 A | 198.39 A |
| L3 | -110.69 A | 193.56 A |
| L4 | -268.49 A | 390.96 A |

The duty ramp solves the immediate output overshoot and reduces source-current
shock, but it does not enforce the approximately 125-A per-phase peak or the
small controlled negative-current interval described by P24/P25. Large positive
and negative phase currents therefore remain.

## Resulting next gate

Do not tune `TSOFT` merely to improve current extrema. The next controller must
combine three paper-supported functions as separate blocks:

1. high-side turn-off from a per-phase peak-current condition;
2. low-side ZCD followed by the P25 5%-10% controlled negative-current target;
3. an explicit latched/blanked phase-state machine so switch commands cannot
   chatter at an instantaneous comparison boundary.

Numeric detector threshold, delay, blanking and hardware propagation values
remain unavailable in P24/P25. Their ideal functional version may be tested
next, but any numeric realization must remain labelled as a sensitivity value
or be obtained from a cited source/author data.
