# A88 - a predicted low-side turn-on (dead time) in the P24 module (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`.

**Boundary:** `BOUNDARY.md`, written before any run and unmodified.

**Records:**
- `run_*.json`;
- `a88_summary.json`;
- `gate_pairs.json`.

**Model: the physical model** (A87's simulator: datasheet Coss(V) and
reverse drop), plus one controller change: the low side turns on at a
timed edge, t_off + dtl. dtl is learned from the V_DS = 0 crossing.

**The mathematical-model counterpart is D47**
(`symbolic_derivations/03_P24_native/D47_P24_PREDICTED_LOW_SIDE_EVENT_MAP.md`).

## 0. Verdict

1. **The reverse-conduction loss disappears: from 56 W (A87) to 0.000 W**
   at 2%, 3%, 5% and 7.5%. The early low-side edges' turn-on proxy is also
   0.000 W.
2. **Why it is exactly zero: the GaN threshold leaves a free timing
   window.**
   - The corrector's edges alternate:
     - at the crossing (early by a hair; V_DS +0.01 to +0.08 V);
     - about 0.05 ns after it (late; V_DS -0.46 to -0.65 V).
   - Reverse conduction needs V_DS < -Vf = -2.09 V. At the crossing the
     node falls at about 9.4 V/ns (phases 1-3) and 12.8 V/ns (phase 4),
     measured in D47. In D47 an edge 0.20 ns late gives the first reverse-
     conduction energy on phase 4, and 0.25 ns late on phases 1-3.
   - So an edge up to about 0.16 ns (phase 4) or 0.22 ns (phases 1-3)
     after the crossing costs no reverse conduction.
   - On the early side, a full step (0.05 ns) early would mean about
     +0.5 V of hard turn-on. The observed early edges see at most +0.08 V,
     which is negligible.
3. **The whole orbit returns to A86's ideal-diode orbit.** At 3%:

   | | A88 | A86 n3 | A87 r1 (reactive low side) |
   |---|---:|---:|---:|
   | Ton | 17.519 ns | 17.518 ns | 19.356 ns |
   | phase 4 at its turn-off | -3.19 A | -3.19 A | -3.36 A |
   | phase-4 turn-on voltage | 9.90 V | 9.90 V | 9.88 V |
   | period | 226.38 ns | 226.38 ns | 225.21 ns |
   | Vo settles after the handover | 68.7 us | 68.0 us | 105.6 us |

4. **Every phase soft once per cycle, no restart, at all four targets.**
   The dither is 0.86 A (3%, 5%), 1.01 A (2%) and 1.14 A (7.5%).
   - At 2% and 7.5% it exceeds the 1 A `PROJECT_DECISION`: a margin
     statement.
   - The same targets gave 0.97-1.04 A and 0.49-1.18 A in earlier runs
     (A86 n1/n8; A86 n5, A79 r3).
   - The low-side rule itself moves each phase current by only about
     0.02 A per edge (0.5 V x 0.05 ns / 1.47 nH), so it is not the source.
5. **The learned dead time is 0.94-1.24 ns**, as predicted (about
   13 nF x 12 V / 150 A):
   - phases 1-3 cross at 1.12-1.19 ns;
   - phase 4 (smaller node capacitance) at 0.94-0.98 ns.
6. **The two models agree** (D47 at matched settings):

   | quantity | difference |
   |---|---:|
   | Ton | within 0.02 ns |
   | period | within 0.23 ns |
   | phase-4 current | within 0.04 A |
   | turn-on voltage | within 0.03 V |
   | zero-crossing times | within 3.5 ps |

   D47's orbits coincide with D45's ideal-diode orbits: the drop never
   engages.

## 1. Runs (last 50 cycles)

A87's module (datasheet Coss(V), reverse drop Vf 2.0894 V + 6.013 mOhm
per device) and controller otherwise:
- predictive valley high side, with learning at restarts;
- trim 0.5, no reactive ZVS;
- restart 20 / 400 ns;
- ki 0.25 ns/V;
- t_d 10 ns;
- zero start, 388.61 us.

| run | target | low side | phase 4: current at turn-off, mean [min, max]; Vds at turn-on | phases 1-3 Vds at turn-on | Ton | period | dither | low-side dead time dtl (final) | low-side zero crossing (mean) | low-side V_DS at the late / early edges | P_rev | P_cond | criterion 2 |
|---|---:|---|---|---:|---:|---:|---:|---|---|---|---:|---:|---|
| r0 (gate) | 3% | reactive | -3.36 [-3.74, -3.00] A; 9.88 V | 9.61-9.69 V | 19.356 ns | 225.21 ns | 0.79 A | - | - | - | 56.58 W | 12.34 W | pass (= A87 r1) |
| r2 | 2% | predicted | -1.85 [-2.35, -1.37] A; 10.24 V | 9.87-9.90 V | 17.442 ns | 224.41 ns | 1.01 A | 1.19 / 1.17 / 1.22 / 1.03 ns | 1.19 / 1.17 / 1.17 / 0.98 ns | -0.63 to -0.46 / +0.01 to +0.08 V | 0.000 W | 12.17 W | soft, no restart; dither 1.01 A |
| r1 | 3% | predicted | -3.19 [-3.59, -2.78] A; 9.90 V | 9.61-9.63 V | 17.519 ns | 226.38 ns | 0.86 A | 1.24 / 1.16 / 1.21 / 1.02 ns | 1.19 / 1.16 / 1.16 / 0.97 ns | -0.63 to -0.46 / +0.02 to +0.06 V | 0.000 W | 12.23 W | pass |
| r3 | 5% | predicted | -5.75 [-6.15, -5.33] A; 9.11 V | 8.94-8.97 V | 17.739 ns | 231.73 ns | 0.86 A | 1.22 / 1.20 / 1.20 / 0.96 ns | 1.17 / 1.15 / 1.15 / 0.96 ns | -0.64 to -0.47 / +0.03 to +0.06 V | 0.000 W | 12.41 W | pass |
| r4 | 7.5% | predicted | -8.95 [-9.15, -8.75] A; 8.02 V | 8.00-8.04 V | 18.072 ns | 239.64 ns | 1.14 A | 1.20 / 1.18 / 1.12 / 0.94 ns | 1.15 / 1.13 / 1.12 / 0.94 ns | -0.65 to -0.48 / +0.04 to +0.07 V | 0.000 W | 12.69 W | soft, no restart; dither 1.14 A |

**Notes.**
- **Edge pattern.** Over the last 50 cycles, each phase's low-side edges
  alternate between late (25-26) and early (25-26). The corrector
  therefore sits within one early step (0.05 ns) of the crossing.
- **Timing.** Vo is 1.0000 V in every run, and settles 68.6-69.9 us after
  the handover.
- **Peak Vds** is 26.7-27.2 V over the whole run (EPC2067: 40 V). In steady
  state the node goes at most 0.65 V below zero. The peak includes the
  start-up, where mode S keeps its fixed 2.15 ns dead time and the node
  reaches -2.4 V; when it occurs was not recorded.
- **The P_on proxy** (high-side turn-on, 1/2 C V^2 f) is unchanged from
  A86: 8.4-10.6 W.

## 2. Checks

- **Regression gate.** r0 (low_mode reactive) replays A87 run r1
  bit-identically: 1790 sections, difference 0.0, equal end state.
- **Smoke run** (before the runs, not kept): dtl converged from 2.15 ns to
  1.1-1.37 ns within about 10 cycles after the handover.

## 3. Predictions (BOUNDARY Section 6) against the results

| | predicted | result |
|---|---|---|
| P_rev | below 2 W | 0.000 W |
| low-side turn-on proxy | below 1 W | 0.000 W |
| Ton at 3% | about 17.5 ns | 17.519 ns |
| phase 4 at 3% | -3.19 A, 9.90 V | -3.19 A, 9.90 V |
| dtl | about 1 ns | 0.94-1.24 ns |
| criterion 2 at 2-7.5% | pass | soft at all four; the dither exceeds 1 A at 2% (1.01) and 7.5% (1.14) |

## 4. Consequences

- **The adopted mode-P controller changes.** A75's reactive low side
  (comparator + 10 ns latency) is replaced by a timed edge with a
  zero-crossing corrector.
  - With ideal diodes both give the same orbit; with the datasheet drop
    only the timed one avoids 56 W.
  - This is the rule P25 describes (a timed dead time that minimises the
    reverse-conduction modes). It is also what a PWM-mode GaN driver with
    programmable dead time (LMG1210) provides.
- **Device realism at this level so far:**
  1. Coss(V) (A86): P24's 2% works.
  2. Reverse drop (A87): soft switching holds, but 56 W is lost with the
     reactive low side.
  3. Predicted low side (A88): back to 0 W, and every earlier conclusion
     holds with the realistic device.
- **Implementation margin.** The free window extends 0.16-0.22 ns after
  the crossing, much wider than the Verilog controller's 31 ps delay line
  (A85, 7 fine bits). The rule is implementable at that resolution; that
  is the next step.

## 5. Limits

- **The circuit.** A87's module:
  - lumped R;
  - no package or PCB parasitics (next level);
  - Cout 4.672 mF (inherited, suspect);
  - one module.
- **The device.** Static datasheet curves at 25 C, 0 V off-state; no
  dynamic threshold (A87 Section 4a).
- **The switches are ideal.** The channel turns on and off at once.
  - The gate driver's ramp, delay and jitter (Zhang et al.; LMG1210's
    3.4 ns high/low mismatch) are absent.
  - Hypothesis, not tested here: a static mismatch is learned into dtl, as
    long as early/late is judged from the node at the actual edge. The
    jitter is what must stay inside the 0.16-0.22 ns window.
- **The rule's parameters** (0.05 ns step, no margin, 10 ns cap) are
  `PROJECT_DECISION`s. The zero-crossing comparator's own delay is taken
  as known (its timestamp is exact here).
- **The dither threshold (1 A) is a `PROJECT_DECISION`.**

## 5a. Reproduction

```
zsh run_a88.sh
python3 a88_analyze.py
```

The mathematical-model side:

```
python3 -m scripts.audit_p24_lowpred_orbits --pct 3.0      # and 2.0, 5.0, 7.5
```
