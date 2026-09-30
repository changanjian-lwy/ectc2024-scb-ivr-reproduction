# A82 - test D43's prediction: a corrector that also learns at restart edges (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question: the mathematical model pushes the physical model

D43 (the P24 exact event map) reproduced A79's steady states. It found the
mechanism of the phase-4 restart state.
- **At 3-5%.** Phase 4's natural valley on the restart orbit lies at
  10-14 ns, before the 20 ns restart. The state persists only because A75's
  corrector samples at predictive turn-ons only. Once `dt_pred` passes
  20 ns, the restart always fires first, and the corrector gets no more
  samples.
- **At <= 2% (P24's stated range).** Phase 4's current at its turn-off is
  positive. The valley lies at 21-23 ns and recedes as phase 4 turns on
  later, so no self-consistent soft orbit exists.

If the corrector also samples at restart turn-ons, D43 predicts:

| run | target (% of 125 A) | ki (ns/V) | `learn_at_restart` | D43 prediction |
|---|---:|---:|---|---|
| 0 | 5% | 1.0 | off | gate: replays A79 run 2 bit-identically (restart state) |
| 1 | 5% | 1.0 | on | every phase soft; phase-4 delay ~7.2 ns |
| 2 | 4% | 0.25 | on | every phase soft |
| 3 | 3% | 0.25 | on | every phase soft |
| 4 | 2.5% | 0.25 | on | every phase soft (phase-4 delay ~9.5 ns) |
| 5 | 2% | 0.25 | on | phase 4 still restart-driven (valley ~21 ns, after 20 ns) |
| 6 | 3% | 0.25 | off | control: restart state (lock-up) |

## 2. Model used, and why

**The physical model** (A79's simulator, copied), to test a prediction of
the mathematical model at matched settings. This is the cross-check
direction D43 Section 8.3 names.

## 3. Rule (`learn_at_restart`)

In predictive mode, a high-side turn-on made by the restart timer (20 ns)
is used as a correction sample, exactly as a predictive turn-on is:
- node still falling at the edge (early): `dt_pred` += 0.2 ns;
- a dip seen and passed (late): `dt_pred` = the observed valley time;
- flat: no change.

Everything else is A79's controller:
- predictive valley turn-on;
- trim 0.5;
- no reactive ZVS;
- 10 ns latency;
- fixed shifts;
- restart 20 / 400 ns;
- the integral voltage loop from the handover.

Sequence: 30x ramp; load and handover at 88.61 us; 388.61 us.

This is a `PROJECT_DECISION` (a corrector design fix) motivated by D43.
Schaef et al.'s trim loop likewise samples every cycle.

## 4. Reporting

As A79, plus the phase-4 turn-on kind and delay, compared with each run's
prediction in Section 1.

## 5. Decides / does not decide

Decides:
- whether D43's mechanism holds in the physical model;
- the corrected lower target at which every phase is soft with this
  corrector.

Does not decide:
- the corrector's optimal design;
- a restart time longer than 20 ns (D43 found no soft orbit at <= 2%
  even with 30 ns).
