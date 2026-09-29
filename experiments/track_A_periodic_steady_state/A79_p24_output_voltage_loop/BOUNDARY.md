# A79 - P24 single module: output-voltage loop (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run, while A78 was
still running. The target is therefore fixed by a rule stated here
(Section 3), not chosen after seeing A79.

## 1. Question

Every P24 result so far runs Ton open loop. Vo settles at 0.91-0.97 V,
depending on the controller and the target. P24's module must deliver 1 V
(`P24_EXPLICIT`).
1. Does a digital voltage loop acting on the common Ton regulate Vo to
   1 V without disturbing the switching orbit?
2. Does single-module criterion 2 hold under the loop (every phase soft
   once per cycle, no restart, Vds < 40 V, dither < 1 A)?

## 2. Model used, and why

**The physical model** (A78's simulator, copied). The loop acts through
the full switching dynamics: Ton changes the period, the phase-1 current
timing and the ladder. The mathematical model is open loop and three-
phase.

The RTL version follows once the rule is confirmed here (A77 Section 4).

## 3. Controller

**Switching rules.** A76's adopted rules, as in A78:
- predictive valley turn-on;
- comparator self-trim, gain 0.5;
- no reactive ZVS;
- restart timers of 20 and 400 ns;
- 10 ns latency;
- fixed shifts `k*T0/N`.

**Negative-current target.** Fixed by this rule: the smallest A78 target
that passes criterion 2. If none passes, -2.5 A (P24's 2%).

**Voltage loop** (`vo_loop_ki > 0`, mode P only). This is digital
voltage-mode control sampled once per switching period, as in the TI
C2000 firmware of the GitHub SCB prototype SeR_BUCK_IBC. That firmware
runs a PI / 2-pole-2-zero voltage loop on the duty.
- **Sampling.** Vo is sampled at each phase-1 high-side turn-on.
- **Integrator.** `Ton += ki * (1 V - Vo)`, clamped to [0.5, 2] x
  16.667 ns.
- **When it acts.** The new Ton applies from the next turn-ons, the same
  for all phases.
- **Gain.**
  - `dVo/dTon` ≈ `Vin/(N*T)` = 48 V / (4 * 222 ns) ≈ 54 mV/ns.
  - A crossover near 10 kHz at a ~4.5 MHz update rate needs
    `ki = 2*pi*f_c / (f_s * dVo/dTon)` ≈ 0.26 ns/V.
  - This is well below the output-filter resonance, `1/(2*pi*sqrt((L/4)
    * Cout))` = 121.6 kHz.
  - The gain is a `PROJECT_DECISION`: P24 publishes no compensator.

## 4. Runs

A78's sequence: 30x ramp; load and handover at 88.61 us. The loop starts at
the handover. t_end is 388.61 us, i.e. 300 us of closed loop, about 20
time constants at 10 kHz.

| run | ki (ns of Ton per V per cycle) | purpose |
|---|---:|---|
| 0 | 0 | gate: replays A78's run at the selected target bit-identically |
| 1 | 0.25 | design value (~10 kHz crossover) |
| 2 | 1.0 | 4x faster (~40 kHz), stability margin |

## 5. Reporting

- Vo over time: the time to stay within 1% of 1 V, the final Vo, and the
  last-20-cycle ripple of Vo.
- The final Ton and period.
- Criterion 2, and the per-phase turn-on voltages.
- Peak Vds and current.
- Conduction loss, as in A78.

## 6. Decides / does not decide

Decides:
- whether an integral Ton loop regulates P24's module to 1 V at the
  adopted rules, and whether criterion 2 survives it.

Does not decide:
- load-step or line-step response (deferred with the wider scenarios);
- compensator optimisation;
- ADC resolution and delay;
- the RTL loop, where the Ton quantisation is 125 ps, about 6.7 mV of Vo
  (A77).

## 7. Target selected by the Section 3 rule (after A78, before any A79 run)

A78 run 5, -6.25 A (5% of 125 A), is the smallest target that passes
criterion 2. Every A79 run uses it. The gate, run 0, replays A78 run 5.

## 8. Amendment (after runs 0-2, before runs 3-4)

**Both gains regulate Vo to 1.0000 V.**
- At ki = 0.25, every phase is soft, with a dither of 1.03 A (threshold
  1 A).
- At ki = 1.0, phase 4 settles in the restart state: -0.63 A at its
  turn-off, 11.97 V turn-on. The operating point is nearly the same:
  Ton 17.74 against 17.70 ns.

So at the 5% target both phase-4 states exist at the regulated point, and
the transient decides between them.

**Added runs.** These test whether a larger target removes the restart
state. Target -9.375 A (7.5% of 125 A, inside P25's 5-10%; A78 run 6),
all else as runs 1-2:

| run | ki (ns/V) |
|---|---:|
| 3 | 0.25 |
| 4 | 1.0 |
