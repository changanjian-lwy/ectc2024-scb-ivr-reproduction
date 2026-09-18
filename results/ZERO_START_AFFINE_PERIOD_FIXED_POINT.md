# Fixed-diode affine period result

## Question

After the passive-divider startup trajectory enters a region with all three
precharge diodes off, can the ideal four-phase model support a self-consistent
5 MHz periodic orbit without brute-force fine-step settling?

The calculation freezes only the observed diode-off branch.  It retains the
P24-connected four-phase power stage, 48 V/1 V design point, 5 MHz timing,
`Lphase=1.4666667 nH`, one 250 W module load, and the existing ideal Track-B
switch boundary.  It remains a theoretical `CROSS_PAPER_EXTENSION`, not a
P24-authored startup method or a device-level ZVS result.

## Method

For one fixed switching sequence, backward Euler gives an affine Poincare map

`z[k+1] = M z[k] + c`.

The code identifies `M` and `c` by propagating the zero vector and every basis
vector through exactly one PWM period.  It then solves

`(I - M) z* = c`

and independently propagates `z*` through the full period.  Acceptance requires
small map residual, small orbit closure error, and valid diode complementarity
at every stored step.

## Rank result: a fast periodic manifold, not one unique 20-state point

At every tested step size, the 20-variable map has numerical rank 17.  The
three near-null singular directions correspond to the three internal
passive-divider charge coordinates after their precharge diodes open.  Their
artificial 1-Gohm leakage time scale is enormous compared with 200 ns.

Consequently:

- the converter's 17-dimensional fast subsystem has a well-defined local
  periodic solution;
- the full model is a three-parameter slow manifold on this time scale;
- the least-squares minimum-norm divider-node voltages are not physical startup
  voltages and must not be reported as such;
- an exact full-system asymptotic claim would require specifying the divider's
  long-time leakage/charge mechanism.

The 0.0625 ns solve has map residual `2.6e-11`, direct one-period closure error
`2.3e-8`, and satisfies the all-off diode inequalities over the full orbit.

## Step-size convergence of the fast coordinates

| Comparison | max `a1/a2/a3` difference | `Vout` difference | max phase-current difference | input-current difference |
|---|---:|---:|---:|---:|
| 0.5 vs 0.25 ns | 4.201 mV | 0.371 mV | 0.0339 A | 0.0763 A |
| 0.25 vs 0.125 ns | 2.092 mV | 0.182 mV | 0.0166 A | 0.0384 A |
| 0.125 vs 0.0625 ns | 1.044 mV | 0.0898 mV | 0.00819 A | 0.0192 A |

The near-halving is consistent with first-order backward Euler convergence.

## One-period electrical metrics

At 0.0625 ns:

| Quantity | Result |
|---|---:|
| Average flying-capacitor voltages | 35.8448 / 23.8863 / 11.9278 V |
| Average output voltage | 1.00601 V |
| Average one-module load power | 253.013 W |
| Average phase currents | 63.021 / 62.724 / 62.724 / 63.033 A |
| Phase-current maxima | 125.879 / 125.554 / 125.554 / 125.891 A |
| Phase-current minima | 0.111 / -0.214 / -0.214 / 0.123 A |
| Average input-inductor current | 5.298 A |

First-order Richardson extrapolation from 0.125 and 0.0625 ns gives about
`1.00610 V`, `253.06 W`, and phase peaks of
`125.889/125.567/125.567/125.901 A`.

These are a consistency reproduction, not an independent prediction of P24
Table 1: the load resistance, duty relation, phase inductance and 5 MHz design
point are already part of the locked paper-derived boundary.  The useful result
is that the assembled topology and timing admit a periodic orbit consistent
with those inputs without forcing capacitor voltages or phase-current waveforms
to their target values.

This calculation represents one 250 W module.  Four identical parallel modules
would nominally give the paper's 1 kW row; module-to-module current sharing and
coupling are not simulated here.

## Remaining boundary gap

This solves the local fast periodic subsystem only.  It does not prove that the
true-zero initial condition reaches a unique full-system steady state, because
the passive-divider charge coordinates retain startup history after diode
isolation.  It also cannot establish hardware ZVS or loss without the real
device capacitance, driver/dead-time and package parasitics.
