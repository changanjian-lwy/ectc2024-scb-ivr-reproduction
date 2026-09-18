# Post-ramp Poincare-map audit

## Scope and frozen boundary

This audit continues the theoretical full-ramp state documented in
`ZERO_START_FULL_RAMP_REFERENCE.md`.  It does not change topology, passive
values, 5 MHz PWM, load, ramp, or initial stored energy.  The sampling section
is the left limit immediately before each phase-1 high-side rising edge.

This remains a `CROSS_PAPER_EXTENSION`, not a P24-authored startup method and
not a hardware-ZVS claim.

## Why a restartable full state was required

The descriptor model has 20 MNA variables.  Capacitor voltages and inductor
currents alone are not a complete restart state because the algebraic node and
source-current variables also determine the next descriptor step.  The solver
therefore now serializes every named variable and rejects incomplete or extra
checkpoint fields.

## First 50 periods at 0.125 ns

Starting at the end of the 22.87 us input ramp and continuing for 50 periods:

- no complementarity or singular-matrix failure occurred;
- voltage proximity improved, but adjacent-period differences remained large;
- over the last 12 samples the largest capacitor, output, phase-current and
  input-current differences were approximately 48.7 mV, 7.1 mV, 5.9 A and
  0.69 A respectively.

Therefore period 50 was not accepted as a periodic state.

## Long-window exploratory result

A 0.5 ns exploratory continuation was used only to inspect the slow envelope.
After 1000 post-ramp periods (200 us):

- the second 500-period block contained no precharge-diode transitions;
- its last ten samples had maximum adjacent-period differences of about
  2.06 mV (flying capacitors), 8.3 uV (`Vout`), 0.078 A (phase currents), and
  4.1 mA (input-inductor current);
- the maximum normalized linear-system backward error was `3.6e-17`.

The earlier absolute residual near 4.95 is therefore a scale-dependent number,
not a failed linear solve.  It must not be used without normalization.

This long run supports a damped approach toward a candidate periodic orbit,
but it does not provide the final orbit values because 0.5 ns has appreciable
time-discretization bias.

## Three-level step-size check from the same saved state

All three cases start from the identical complete 20-variable checkpoint and
continue for the same 20 periods.  No precharge diode changes state.

| Comparison | max capacitor difference | max `Vout` difference | max phase-current difference | max input-current difference |
|---|---:|---:|---:|---:|
| 0.5 ns vs 0.25 ns | 6.121 mV | 0.698 mV | 0.417 A | 0.0575 A |
| 0.25 ns vs 0.125 ns | 3.068 mV | 0.343 mV | 0.207 A | 0.0291 A |

The differences approximately halve when the step halves, consistent with the
first-order backward-Euler method.  The 0.5 ns long trajectory is thus useful
for envelope discovery only.  Its terminal values are prohibited as a paper
reproduction result.

## Current conclusion and next gate

The passive-divider zero-start trajectory is mathematically reachable under
the frozen ideal boundary and approaches a diode-off periodic regime.  A
periodic fixed point has not yet been declared because brute-force fine-step
settling is inefficient and the long-window state contains coarse-step bias.

The next gate is to exploit the observed diode-off branch: construct the
one-period affine map of that fixed switching sequence, solve its fixed-point
equation, and then check both descriptor consistency and diode
complementarity over the entire recovered orbit.  Failure of either check must
be retained as a negative result.
