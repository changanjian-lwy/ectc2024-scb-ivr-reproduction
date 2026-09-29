# A78 - P24 single module: the negative-current target (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question

A76 found that the size of phase 1's negative current at its low-side turn-
off decides whether phase 4 rings.
- At P24's -2.5 A, phase 4 is restart-driven.
- At -8.8 A (the untrimmed 10 ns run), every phase switches softly.

The two papers state different targets:
- **P24:** 1-2% of the peak current (`P24_EXPLICIT`): -1.25 to -2.5 A of
  125 A.
- **P25:** 5-10% (`P25_SUPPLEMENT`): -6.25 to -12.5 A at P24's peak.

**Questions.**
1. At P24's operating point, which target is the smallest that meets the
   single-module criterion (every phase soft once per cycle, no restart,
   Vds < 40 V, < 1 A dither)?
2. What does a larger target cost in conduction loss, and what does it save
   in turn-on voltage?
3. Is P24's stated 1-2% enough in this model?

## 2. Model used, and why

**The physical model.** The target is a quantitative operating-point
question in P24's four-phase circuit with the adopted A76 controller. The
mathematical model is three-phase P25-native. A parameter sweep in the
simulator is the cheapest discriminating experiment.

## 3. Controller

These are A76's adopted rules:
- predictive valley turn-on (A75);
- comparator self-trim, gain 0.5;
- no reactive ZVS decision;
- restart timers of 20 ns (high) and 400 ns (low);
- a 10 ns comparator-to-gate latency (LMG1210 typical);
- fixed shifts `k*T0/N`, open-loop Ton 16.667 ns.

The target applies to phase 1's comparator, whose trimmed edge current
tracks it. Phases 2-4 stay timed.

## 4. Code

`a78_transient.py` is a copy of A76's, with three additions:
- an `--i-target` option;
- a per-section record of each phase's `integral of i^2 dt`. The step
  that lands on a section is counted in the next section, an error of one
  step (≤ 10 ps of ~220 ns);
- nothing else. The dynamics are unchanged.

**Regression gate (run 0).** Run 0 uses A76 run 1's settings and must replay
it bit-identically.

## 5. Runs

P24 sequence as in A76: 30x ramp, load and handover at 88.61 us,
t_end 388.61 us, and the settings of Section 3.

| run | `i_target` | % of 125 A | source range |
|---|---:|---:|---|
| 0 | -2.5 A, reactive ZVS on | 2% | gate (= A76 run 1) |
| 1 | -1.25 A | 1% | P24 |
| 2 | -2.5 A | 2% | P24 |
| 3 | -3.75 A | 3% | between |
| 4 | -5.0 A | 4% | between |
| 5 | -6.25 A | 5% | P25 |
| 6 | -9.375 A | 7.5% | P25 |
| 7 | -12.5 A | 10% | P25 |

## 6. Reporting

As in A76, plus the following, over the last 50 cycles:
- **Conduction loss.** `P_cond = R * sum_k mean(integral of i_k^2 dt) /
  T`, with R = 0.54 mOhm per phase, the plant's lumped value.
- **A turn-on proxy.** `P_on = f * sum 1/2 * C_node,k * Vds_on^2`, with
  `C_node` = `C_low + 2*C_high` (13.02 nF) for phases 1-3 and
  `C_low + C_high` (9.30 nF) for phase 4. This is a proxy, not a loss
  figure.
- **Output power.** `P_out = Vo^2 / R_load` (4 mOhm). Vo varies with the
  target, because Ton is open loop.
- **Criterion 2**, pass or fail.

## 7. Decides / does not decide

Decides:
- the smallest target that meets criterion 2 in this model;
- the conduction and turn-on trade-off across the two papers' ranges.

Does not decide:
- **total efficiency.** The model omits reverse-conduction drop, gate
  charge, magnetics and nonlinear Coss;
- the target under closed-loop Vo;
- the target under nonlinear Coss;
- whether a different rule (for example a per-phase on-time trim, as in
  UCC28063A's differential on-time modulation) could meet the criterion at
  1-2%.
