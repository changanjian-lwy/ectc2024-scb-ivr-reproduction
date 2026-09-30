# A84 - perturbation test: is the soft state the only one? (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question

A82 showed that with a corrector that also samples at restart turn-ons,
zero starts at 3-5% settle with every phase soft. D43's escape test showed
that every restart orbit leads back to the soft orbit once phase 4's delay
follows its valley.

A start from zero samples one transient only. **Is the soft state the only
attractor?** The test pushes an established soft state into the restart
state's basin and checks whether it comes back.

## 2. Model used, and why

**The physical model** (A82's simulator plus a kick). Recovery from a
perturbation involves the corrector and loop dynamics, which the fixed-
point map D43 does not simulate.

## 3. Kick

At the first phase-1 section at or after 250 us (mode P, steady soft
state), phase 4's `dt_pred` is set once to 20.2 ns, above the 20 ns
restart. The restart then fires first: this is exactly how the lock-up
state forms.

## 4. Runs

A82's sequence and controller: predictive, trim 0.5, no reactive ZVS,
10 ns latency, fixed shifts, restart 20 / 400 ns, ki 0.25, 388.61 us.

| run | target | learn at restart | kick | expectation |
|---|---:|---|---|---|
| k0 | 3% | on | none | gate: replays A82 run 3 bit-identically |
| k1 | 5% | on | yes | returns to soft |
| k2 | 5% | off | yes | stays restart (lock-up) |
| k3 | 3% | on | yes | returns to soft |
| k4 | 3% | off | yes | stays restart (lock-up) |

The runs without learning (k2, k4) start in the soft state too, if the
zero-start transient lands there. If it does not, their kick is redundant,
and the record says so.

## 5. Reporting

- Phase 4's turn-on kind over the last 50 cycles;
- the cycles from the kick until phase 4 is predictive again;
- criterion 2.

## 6. Decides / does not decide

Decides:
- whether the fixed corrector returns from the restart state's basin at
  3% and 5%, and the old corrector does not.

Does not decide:
- other perturbations: load or line steps, a phase-state kick;
- basins far from these two states.
