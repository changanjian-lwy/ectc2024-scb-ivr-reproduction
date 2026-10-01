# A99 / D54 - a timed phase-1 low-side turn-off against gate-driver jitter (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`.
Written before any code or run of A99 and D54.

## 1. Question

A98/D53 found where gate-driver jitter is amplified.
- Phase 1's low side turns off when its current comparator trips (-6.25 A,
  trimmed).
- An on-time error δ changes the peak current on the steep on-slope, and
  the comparator converts it back to time on the shallow off-slope. So the
  period moves by 10.5·δ.
- Phases 2-4's slots inherit that error at 0.68 A/ns.
- Phase 1's on-time edges carry about 60% of the turn-off current variance
  at 30 ps. The trim is a secondary path.

**If phase 1's turn-off is timed instead,** the period no longer follows
the current, and an on-time error moves phase 1's turn-off current
instead. **How much of the spread goes away, and what does it cost?**

## 2. Prior work

**Prediction in place of a comparator:**
- **Zhou, Peng, Liang, Fu, Wang, IEEE TPEL 38(7):8513-8527, 2023, DOI
  10.1109/TPEL.2023.3259984.** An inductor-current estimator predicts the
  zero crossings and replaces the noisy zero-current comparator in CRM
  control.
- **Zhou, Pan, Fu, Liang, Wang, IEEE TIE 72(6):6038-6048, 2025, DOI
  10.1109/TIE.2024.3493174.** A predicted switching cycle replaces the
  measured one for interleaving.

**Sign-based adaptive correction and its step:**
- **Dong et al., IEEE PEAC 2022, DOI 10.1109/PEAC56338.2022.9959609**;
- **Thuc and Chen, IEEE TIA 60(6), 2024, DOI 10.1109/TIA.2024.3454198.**

**This project:**
- **A89 already replaced a comparator by a timed edge**, the low-side
  turn-on, corrected from the measured crossing. A99 applies the same
  structure to phase 1's low-side turn-off, with the current comparator
  kept as the measurement.
- **A97/A98** give the adopted design and its jitter response (A97 j30 and
  j100, A98 s10-s50).

## 3. The change

### 3.1 Controller rule (opt-in, shared RTL)

New bit `cfg_lo_pred`. In mode P, phase 1's low-side turn-off is a timed
edge at t_lon + dlo, where dlo is a register in LSB.

**Learning.** For the first `cfg_lo_learn` mode-P cycles, the turn-off
stays comparator-decided (the asynchronous path, as now). Each cycle dlo is
set to the measured on-interval, the latch's commanded time minus t_lon.
The handover and start-up therefore stay as A97's.

**Then timed, with error-based correction like dtl:**
- The comparator now only measures. The bridge records when the current
  crosses the target (-6.25 A).
- At the turn-off it reports err = actual turn-off − crossing, rounded to
  the LSB, or "early" if the current never reached the target.
- Update: dlo ← dlo − ((err − tgt) >>> shift), clamped. Early:
  dlo ← dlo + step.
- Phase 1's high side then turns on predictively at t_lo + dt_pred, as
  phases 2-4 do after their slots.

**The asynchronous latch no longer turns phase 1 off once timed.** The trim
stays frozen.

**With the bit at 0, every path is as now.**
- **Gates:**
  - RTL unit tests;
  - `scripts/cosim_regression.py --full`, bit-identical;
  - synthesis.

### 3.2 D54 (mathematical model)

**The timed turn-off needs no new map code.** In D47's map:
- set phase 1's current threshold out of reach;
- set its restart time, the timed turn-off, to the orbit's phase-1 on-low
  interval.
- The periodic orbit is then exactly D51's, with the same edges and phase
  1's turn-off at -6.25 A.
- Only the cycle-to-cycle dynamics change.

**Model:**
- D53's per-edge core map, with phase 1's low interval as an input in
  place of the threshold;
- the dlo corrector in the loop. The measured error is (−6.25 A −
  i_off,1)/(Vo/L), since phase 1's current falls linearly while its low
  side conducts.
- The linear covariance and the Monte Carlo with the exact rules, as D53,
  without the trim.
- Gains 1/2, 1/4 and 1/8 for dlo; the other correctors as adopted.

**Gate:** with the timed turn-off at the orbit's interval, the map
reproduces D51's orbit section to the orbit's residual.

## 4. Predictions (before D54 is built and before A99 runs)

**D54, average slots, 30 ps (A97/A98 values in brackets):**
1. **The period's spread falls** from 0.55 ns to ≤ 0.30 ns with dlo gain
   1/2, and to ≤ 0.15 ns with gain 1/8.
2. **Phases 2-4's turn-off current spread falls by 20-35%** with gain 1/2
   (from 0.59-0.65 A). It approaches the bound of D53/A98 Section 8, about
   0.63 times the spread, at gain 1/8.
3. **Phase 1's turn-off current spread rises** from 0.17 A to 0.3-0.5 A.
   The on-time error now lands on its current, at the on-slope (about
   7 A/ns) times the on-time jitter (√2·30 ps).
4. **The high-side early fraction of phases 2-4 falls** with the valley
   spread, to 15-20% (from 25%).
5. **Without jitter,** the deterministic two-cycle components fall, since
   the trim's ±1 LSB forcing disappears: phases 2-4 to ≤ 0.10 A (from
   0.16 A).

**A99 predictions are filled in from D54 before A99 runs (Section 5),** as
in A98.
- Planned runs, the adopted preset plus `lo_pred` at the gain D54 selects:
  - n0;
  - m3n (the start-up/handover case);
  - j30 and j100.
- Criteria:
  - no cross-conduction, and peaks ≤ 200 A in every run;
  - m3n's peak within 10% of A97's 156 A, since the handover is still
    comparator-decided;
  - steady-state Ton, Vo and flying-capacitor voltages as A97's.

## 5. Amendment (written after D54, before any A99 code or run; 2026-10-01)

### 5.1 What D54 found

Details in D54. Average slots, Monte Carlo of the linearised circuit with
the exact rules.

**The gate holds.**
- With phase 1's turn-off timed at the orbit's interval (203.447 ns), the
  map reproduces the comparator map's cycle to 2.7e-8.
- ∂T/∂ton_1 falls from +10.5 to **+1.000**.
- An on-time error now moves phase 1's turn-off current instead, by +6.5
  A/ns.

**With the dlo rule of Section 3.1** (error-based, early +2 LSB), against
the comparator design at 30 ps:

| | comparator (adopted) | error-based, gain 1/2 | error-based, gain 1/8 |
|---|---:|---:|---:|
| phases 2-4 spread (A) | 0.59-0.65 | 0.44-0.46 | 0.42-0.43 |
| period spread (ns) | 0.55 | 0.28 | 0.19 |
| dither (A) | 2.03 | 1.47 | 1.43 |

- **But the rule is biased under noise.** An early turn-off (before the
  crossing) can only add a fixed step, while a late one is corrected in
  proportion.
- At gain 1/2, phase 1 turns off on average 0.31 ns before reaching
  -6.25 A (mean -6.04 A, 68% early), and -4.9 A at 100 ps.

**A sign rule removes the bias and is the best on every measure.**
- The rule: dlo ± 1 LSB per cycle, + when early or err < 3 LSB.
- At 30 ps:
  - phases 2-4 spread 0.40-0.42 A, which is −32 to −36%;
  - period spread 0.15 ns;
  - dither 1.39 A;
  - high-side early 16-17%;
  - phase 1's mean turn-off current -6.31 A, unbiased.
- At 100 ps: 1.17-1.22 A against 1.70-1.91 A.
- Without jitter, the trim's limit cycle is gone: spread 0.02 A, dither
  0.04 A.
- This is the class of correction of Dong et al. 2022, applied to time,
  with steps of 31 ps (0.02 A) instead of the trim's 0.25 A.

**The cost: phase 1's turn-off current spread** rises from 0.17 A to
0.38 A at 30 ps, and 44% of its turn-offs come before -6.25 A is reached.

### 5.2 The rule and the runs

**The sign rule's limit.** It moves dlo by at most 31 ps per cycle. After
the handover, the period settles over about 500 cycles, and the on-low
interval changes by about 0.2 ns per cycle. The timed mode must therefore
start after the settling.

**RTL (Section 3.1, with these changes):**
- dlo ± 1 LSB from the bridge's report: + when early or err < `cfg_lo_tgt`
  (3 LSB = 93.75 ps), else −;
- `cfg_lo_learn` = 1024 mode-P phase-1 cycles of comparator-decided
  turn-offs (learning, about 230 us), then timed.

**Runs:**
- n0, m3n, j30 and j100: the adopted preset with `lo_pred` on;
- **to 500 us instead of 388.61 us**, so that about 800 cycles are timed;
- statistics over the last 200 cycles.

### 5.3 Gate and predictions (D54's 5-95% band over 200-cycle windows, `d54_predictions.json`)

**Gate.** During learning, dlo only records; no edge changes. Each A99 run
is therefore **bit-identical to the A97 run of the same configuration**
(n0, m3n_avg_guard, j30, j100, same driver seed) in every section before
its first timed turn-off.

**Predictions:**

| run | turn-off current spread, phases 1 / 2 / 3 / 4, median [5-95%] (A) | high-side early, phases 2-4 | period spread (ns) | phase 1's mean turn-off current (A) | dither (A) |
|---|---|---|---|---|---:|
| n0 | 0.02 / 0.02 / 0.02 / 0.02 | 0% | 0.016 | -6.30 | 0.04 |
| j30 | 0.38 / 0.40 / 0.39 / 0.41 [0.33-0.46] | 16-18% | 0.14 [0.13-0.16] | -6.31 [-6.34 to -6.28] | 1.40 |
| j100 | 1.15 / 1.17 / 1.16 / 1.20 [1.03-1.34] | 39-40% | 0.32 [0.28-0.36] | -6.31 [-6.39 to -6.24] | 4.13 |

**Criteria:**
- **j30 and j100:**
  - each phase's spread within ±20% of the median;
  - period spread within ±30%;
  - phase 1's mean turn-off current within 0.15 A;
  - high-side early within ±8 points.
- **n0:** phases 2-4 spread ≤ 0.10 A and dither ≤ 0.2 A. These allow for
  quantisation effects that D54 lacks.
- **m3n:**
  - bit-identical to A97 m3n_avg_guard up to the switch, so its peak is
    156 A;
  - no cross-conduction after the switch;
  - the same steady state as n0.
- **All runs:**
  - no cross-conduction;
  - peaks ≤ 200 A;
  - Ton and Vo as A97's;
  - phase 1's high-side turn-on V_DS and P_rev reported against A97's.

## 6. Decides / does not decide

**Decides:**
- whether a timed phase-1 turn-off reduces the jitter amplification found
  in A98, by how much, and at what cost to phase 1's turn-off current;
- the choice of the dlo gain.

**Does not decide:**
- load and line steps, where a timed turn-off must track a moving optimum.
  The learning and the corrector gain set how fast it does, and that is
  not tested here;
- the loss trade-off of a varying phase-1 turn-off current. ZVS energy
  depends on it; the turn-on V_DS and P_rev are reported, not optimised.
