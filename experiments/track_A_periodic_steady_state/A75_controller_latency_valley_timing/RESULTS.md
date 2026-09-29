# A75 - controller latency and the valley turn-on (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`, with Section 9
(the baseline) fixed before any declared run. Records:
- `run_*.json`;
- `a75_summary.json`;
- `gate_pairs.json`: the regression gate.

**Model: the physical model** (A74's simulator, copied). Latency and timing
are implementation-realism questions, and the event-level mathematical
model has no delays (BOUNDARY Section 2).

## 0. Verdict

1. **At P24, the reactive valley turn-on does not survive a realistic
   latency.** In the zero-latency model, phases 1-3 turn on at 9.8-9.9 V.
   - **5 ns:** the edges land at 10.2-10.6 V.
   - **10 ns (LMG1210 typical):** they land at 11.7-12.1 V, the level the
     node starts from before it rings (Vin/N ≈ 12 V). The valley's benefit
     is gone, and the steady state is no longer periodic.

   The zero-latency controller of A69-A74 therefore hid an implementation
   problem at P24's timescale:
   - the half resonance period of phases 1-3 is 13.7 ns;
   - LMG1210's delay is 10-18 ns.
2. **A predictive (timed, self-corrected) valley turn-on keeps the valley.**
   With latencies up to 10 ns, every phase turns on at or below the zero-
   latency valley voltage (8.1-9.6 V), and no restart timer fires.
   - **18 ns (LMG1210 maximum):** the still-reactive ZVS path becomes the
     weak point. Phases 2-3 alternate between predictive and delayed-ZVS
     turn-ons, with edges up to 11.2 V.
   - **The source.** This is the delay compensation of Chiang and Chen
     (2009), which A70 had dropped. It is also the method of the reference
     P25 names for its zero-cross detection (Section 3).
3. **P25 (45 ns, 1EDBx275F) stays periodic,** but its ZVS turn-ons land at
   0.8-1.7 V instead of ~0 V. The -2.5 A negative current reverses within
   the 45 ns, so reverse conduction ends before the edge. P25 is far more
   tolerant than P24, but not immune.
4. **New evidence on A74's phase-4 problem.** Phase 4 can ring and turn on
   softly:
   - predictive runs 5-7: -4.4 to -12.4 A at its timed turn-off, soft turn-
     on at 7.7-9.6 V, zero restarts;
   - reactive run 1, at nearly the same phase-1 current (-5.8 A against
     -5.7 A in run 5): +7.3 A and restart-driven.

   **Phase 4 is therefore not structurally unable to ring.** Which state it
   settles in depends on the controller. This favours A74's candidate 2, a
   self-reinforcing restart state, over candidate 1, phase N's structure.
   It is not yet a same-parameter demonstration (Section 4).

## 1. Runs (last 50 cycles)

**P24.** Baseline: fixed shifts, restart 20 ns, i.e. A74 run 0 (= A73 run
5). "Phase-1 edge current" is phase 1's current at its actual low-side
turn-off edge.

| run | valley mode | t_d | phase-1 edge current | Vds at turn-on, phases 1 / 2 / 3 | phase 4: current at turn-off -> turn-on | period | Vo | periodic |
|---|---|---:|---:|---|---|---:|---:|---|
| 0 | reactive | 0 | -2.50 A | 9.87 / 9.79 / 9.79 V | +7.08 A -> restart, 11.03 V | 222.891 ns | 0.9653 V | yes |
| 1 | reactive | 5 ns | -5.81 A | 10.56 / 10.15 / 10.15 V | +7.32 A -> restart, 11.95 V | 234.992 ns | 0.9729 V | yes |
| 2 | reactive | 10 ns | -8.96 A | 12.11 / 11.70 / 11.69 V | +1.8 to +6.2 A -> valley 25 / restart 25, up to 13.8 V | 252.2 ns | 0.951 V | no (4.7 A) |
| 3 | reactive | 18 ns | -13.52 A | 12.03 / 11.68 / 11.67 V | -4.2 to +5.2 A -> valley 47 / restart 4, up to 13.4 V | 277.0 ns | 0.902 V | no (5.4 A) |
| 4 | predictive | 0 | -2.50 A | 9.85 / 9.85 / 9.85 V | +6.82 A -> restart, 10.82 V | 221.4 ns | 0.963 V | dither (0.87 A) |
| 5 | predictive | 5 ns | -5.73 A | 9.05 / 9.07 / 9.07 V | **-4.39 A -> predictive, 9.56 V** | 228.5 ns | 0.950 V | dither (0.96 A) |
| 6 | predictive | 10 ns | -8.84 A | 8.12 / 8.12 / 8.12 V | **-7.70 A -> predictive, 8.35 V** | 237.1 ns | 0.932 V | dither (0.43 A) |
| 7 | predictive | 18 ns | -13.62 A | 7.75 / 9.41 / 9.50 V (max 11.2 V) | -12.4 A -> predictive, 7.73 V | 269.9 ns | 0.910 V | no (33.6 A) |

- **"Periodic"** is BOUNDARY Section 6's test: the last 20 sections vary
  by < 1 mA and < 0.1 mV. The figure in brackets is the largest current
  variation over those 20 sections.
- **"Dither"** is the ±0.2 ns bang-bang correction of the predictive rule.
  It is a small limit cycle, the analogue of DPWM limit cycling in digital
  control.
- **Run 7's variation** is a period-2 alternation of phases 2-3 between
  the predictive and the delayed-ZVS turn-on.
- **Peak Vds** is 24.6-25.1 V in every run (EPC2067: 40 V). Peak current is
  161-184 A.

**P25 control run.** The zero-latency reference is A73 run 7.

| run | t_d | phase edge currents | turn-on | Vds at turn-on, phases 1 / 2 / 3 | period | Vo | periodic |
|---|---:|---|---|---|---:|---:|---|
| A73 r7 | 0 | (target -2.5 A) | ZVS | ~0 V (not logged) | 2172.4 ns | 0.8436 V | yes |
| 8 | 45 ns | -3.88 / -4.20 / -3.94 A | ZVS decision; edge after 45 ns | 1.45 / 0.80 / 1.67 V | 2139.1 ns | 0.9296 V | yes |

## 2. Interpretation and a confound

- **The latency also acts on phase 1's current comparator.** After the
  comparator trips at -2.5 A, the current keeps falling at `-Vo/L` ≈
  -0.66 A/ns until the edge. The effective target becomes -5.8 / -9.0 /
  -13.5 A at 5 / 10 / 18 ns.
- **A deeper negative current changes the operating point.** It gives more
  resonant energy (deeper valleys), a longer period, and a different
  open-loop Vo. The predictive runs' lower turn-on voltages (8.1-9.1 V)
  therefore mix two effects: prediction and a deeper negative current.
- **A real design compensates the comparator too.** Schaef et al. trim the
  comparator trip point digitally so that the edge lands on target
  (Section 3). Separating the two effects needs a run with the phase-1
  threshold compensated by the latency (trip at `-2.5 A + 0.66 A/ns * t_d`).
- **The reactive-valley conclusion (item 1) does not depend on this
  confound.** The deeper negative current should *help* the valley, yet
  the reactive edges still land at the off-state level at 10 ns.

## 3. Sources

**Found after the runs.** P25's own reference for its zero-cross detection,
which BOUNDARY Section 3 did not list:
- **C. Schaef et al.**, "A Fully Integrated Voltage Regulator in 14nm CMOS
  with Package-Embedded Air-Core Inductor Featuring Self-Trimmed, Digitally
  Controlled Variable On-Time Discontinuous Conduction Mode Operation,"
  ISSCC 2019, DOI 10.1109/ISSCC.2019.8662294 (P25 ref. [22]; read).
- **What it says.** It states that "compensating for the comparator and
  gate driver delays pose[s] major challenges for accurate and efficient
  zero current detection".
- **What it does.** Its comparator is auto-zeroed and digitally self-
  trimmed. A residual-current detector samples the switching node after
  the low-side turn-off; the sign of the node voltage gives the sign of
  the residual current. A 5-bit capacitive-DAC offset then corrects the
  trip point, which removes the remaining offset and circuit delays.

**Relation to A75.** The predictive rule here uses the same principle:
per-cycle early/late detection, then a digital correction. It uses the
node's early or late state at the edge instead of Schaef's residual-
current sign.

## 4. Limits

- **Circuit.** A74's idealised P24 module (linear Coss, lumped R, ideal
  unidirectional diodes, ideal ramp, Cout 4.672 mF inherited and suspect,
  one module), with open-loop Ton.
- **Latency model.**
  - One lumped `t_d` is applied to the comparator decisions.
  - Timer edges are pre-compensated.
  - There is no channel mismatch (LMG1210: 1-3.4 ns), no comparator offset
    or noise, and no clock quantisation.
- **Predictive rule.** One correction step (0.2 ns) is tested. Its
  starting value used `C_low + C_high` (11.6 ns); phases 1-3 have
  `C_low + 2*C_high` (13.7 ns half period). This is harmless: the
  converged `dt_pred` of phases 1-3 is 7.9-10.6 ns, because the ring starts
  with a negative current.
- **Loss.** The turn-on loss proxy in `a75_summary.json` ignores the
  higher circulating current of the deeper negative targets. It is not
  used here.
- **Phase-4 evidence.** It compares runs with different latencies, periods
  and Vo. It is not a same-parameter test of two coexisting steady states.

## 5. Next (single-module level)

1. **Separate the confound.** Compensate the phase-1 comparator for the
   latency, then rerun predictive at t_d = 10 and 18 ns.
2. **Phase 4.** Two tests:
   - per-phase current sensing (A74 Section 5);
   - a same-parameter test of two steady states: identical settings,
     entered from different transients.
3. **Predictive ZVS path.** At 18 ns the delayed-ZVS decision is the
   remaining weak point. Test a predictive or compensated version.
4. **Controller implementation.** Write the predictive (self-trimmed)
   controller in Verilog, clocked and with finite resolution, and co-
   simulate it with this plant (cocotb + Icarus Verilog; toolchain
   installed in `~/tools`, outside this repository).
5. **The mathematical model.** The four-phase extension with the valley
   trigger.

## 5a. Reproduction

```
zsh run_a75.sh
python3 a75_analyze.py
```

The datasheet and paper PDFs are not in this repository.
