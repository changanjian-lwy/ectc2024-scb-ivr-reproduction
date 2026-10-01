# A99 / D54 - a timed phase-1 low-side turn-off against gate-driver jitter (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`.

**Boundary:** `BOUNDARY.md`.
- Sections 1-4 were written before any code or run.
- Section 5, with D54's results, the chosen rule and the registered bands
  for every A99 run, was committed (df44f43) before the RTL change and the
  runs.

**Records:**
- `cosim/run_*.json` and `cfg_*.json` (commit 041480a, no modified
  sources);
- `a99_summary.json` (`a99_analyze.py`);
- `d54_predictions.json`;
- synthesis `synth/stat_scb_ctrl.txt`.
- The RTL, its tests and the bridge are in `src/scb_ivr/cosim/`.

**Models:**
- **Physical (A99):**
  - the adopted design (preset: A92's correctors, A97's averaged slots and
    guard) with `lo_pred`;
  - Verilog RTL with A88's plant (kernel2), 5%, 25 C;
  - runs to 500 us; statistics over the last 200 cycles, all of them
    timed.
- **Mathematical (D54):** D53's linearised map with phase 1's turn-off
  timed, and the exact controller rules
  (`symbolic_derivations/03_P24_native/D54_P24_TIMED_PHASE1_TURN_OFF.md`).

**The rule:**
- After 1024 comparator-decided mode-P cycles, which set dlo to the
  measured on-low interval, phase 1's low side turns off at t_lon + dlo.
- The current comparator only measures. The bridge reports actual
  turn-off − crossing of -6.25 A.
- dlo steps +1 LSB (31.25 ps) when early or below 3 LSB, else −1.
- The trim is no longer used.

## 0. Verdict

1. **It removes the main amplifier, as D54 predicted.** Against A97, the
   same design with phase 1's comparator turn-off:

   | | A97 (comparator) | **A99 (timed)** | D54 prediction |
   |---|---:|---:|---:|
   | **30 ps:** phases 2-4 turn-off current spread | 0.56-0.66 A | **0.39-0.43 A** (−30 to −38%) | 0.39-0.41 |
   | **30 ps:** period spread | 0.59 ns | **0.19 ns** | 0.14 |
   | **30 ps:** windowed dither | 1.95 A | **1.30 A** | 1.40 |
   | **30 ps:** high-side early, phases 2-4 | 23-26% | **17-18%** | 16-18% |
   | **100 ps:** phases 2-4 spread | 1.59-1.79 A | **1.02-1.16 A** (−31 to −38%) | 1.16-1.20 |
   | **100 ps:** period spread | 1.65 ns | **0.29 ns** | 0.32 |
   | **100 ps:** dither | 5.70 A | **3.47 A** | 4.13 |
   | **Without jitter:** spread | 0.18-0.21 A | **0.018 A** | 0.018 |
   | **Without jitter:** dither | 0.57 A | **0.04 A** | 0.04 |

   **Without jitter, the trim's ±1 LSB limit cycle (D52) is gone.**
2. **The gate holds.** In every run, all 1467 sections before the first
   timed turn-off (312.9-321.5 us) equal A97's. During learning dlo only
   records.
   - m3n's start-up and handover are therefore A97's: peak 156 A, 26.9 V.
   - After the switch, m3n's steady state equals n0's.
3. **The cost is on phase 1 itself.**
   - Its turn-off current now carries the on-time error: spread 0.39 A at
     30 ps (A97 0.17 A) and 1.13 A at 100 ps (range -8.7 to -3.3 A). The
     mean stays at -6.29 to -6.32 A.
   - Its high-side turn-ons before the valley rise: 30 ps 6% → 21%;
     100 ps 18% → 42%.
   - **The loss does not rise.** A91's hard-on estimate is unchanged
     (100 ps: 30-99 against 30-102 mW). P_rev is lower (100 ps: 74
     against 89 mW). The turn-on V_DS of phases 2-4 improves (p95 at
     100 ps: 9.54 against 9.87 V), while phase 1's widens (p95 9.50
     against 9.08 V).
4. **Against the registered criteria** (BOUNDARY Section 5.3):

   | run | criterion | verdict |
   |---|---|---|
   | n0 | spread ≤ 0.10 A, dither ≤ 0.2 A | met (0.018 A, 0.04 A) |
   | m3n | bit-identical to A97 before the switch; no overlap after | met |
   | j100 | the registered bands | all within |
   | j30 | spread, early fraction, phase 1's mean | within |
   | j30 | period spread within ±30% of D54's median | **missed:** 0.190 against 0.141 ns (+35%) |

   No run cross-conducts. Peaks 156-162 A. Ton and Vo as A97's.
5. **Not adopted yet.**
   - The steady state and the jitter response are better in both models.
   - But a sign rule moves dlo by at most 31 ps per cycle, and a load or
     line step needs the on-low interval to move much faster.
   - The 1024-cycle learning works for this start-up only.
   - Adoption needs a load-step test of the timed mode first, and probably
     a coarse/fine version of the rule (Section 6).

## 1. Gates

| check | result |
|---|---|
| RTL unit tests | **42 of 42.** The 3 new tests: learning then timed at t_lon + dlo; the ±1 update; front end not armed when timed. |
| `scripts/cosim_regression.py --full` (bit off) | **PASS**: A89 r2, A92 j100, A92 m3p, A93 m3n_both. |
| `tests/test_cosim_plants.py` | 3 passed. |
| synthesis | 0 problems; 41 605 cells (A97: 40 296); 40 ABC "network is combinational" notices. |
| D54's map gate | the timed map at the orbit's interval (203.447 ns) reproduces the comparator map's cycle to 2.7e-8. |
| bit-identity to A97 before the switch | 1467 of 1467 sections, in all 4 runs. |

## 2. Results (last 200 cycles, all timed)

| run | turn-off current spread, phases 1 / 2 / 3 / 4 (A) | high-side early, phases 2-4 | period spread (ns) | dither (A) | phase 1 turn-off mean (A) | phase 1 reports: early / err mean ± sd | P_rev (W) |
|---|---|---|---:|---:|---:|---|---:|
| A97 n0 | 0.125 / 0.180 / 0.185 / 0.209 | 0 / 0.5 / 2.5% | 0.140 | 0.57 | -6.37 | - | 0 |
| **A99 n0** | **0.019 / 0.018 / 0.018 / 0.018** | 0% | **0.016** | **0.04** | -6.32 | 0% / 0.091 ± 0.028 ns | 0 |
| **A99 m3n** | 0.019 / 0.018 / 0.018 / 0.018 | 0% | 0.016 | 0.04 | -6.32 | 0% / 0.099 ± 0.027 ns | 0 |
| A97 j30 | 0.174 / 0.622 / 0.561 / 0.655 | 26 / 23 / 25% | 0.588 | 1.95 | -6.27 | - | 0.003 |
| **A99 j30** | **0.394 / 0.425 / 0.394 / 0.404** | **17 / 17 / 18%** | **0.190** | **1.30** | -6.29 | 45% / 0.47 ± 0.35 ns | 0.002 |
| A97 j100 | 0.188 / 1.694 / 1.590 / 1.790 | 41 / 47 / 45% | 1.645 | 5.70 | -6.25 | - | 0.089 |
| **A99 j100** | **1.131 / 1.164 / 1.017 / 1.111** | **38 / 35 / 37%** | **0.290** | **3.47** | -6.32 | 47% / 1.36 ± 1.00 ns | 0.074 |

- **About half of phase 1's turn-offs come before the crossing** at 30 and
  100 ps (45-47%). That is what a sign rule does under symmetric noise: it
  holds the median at the target.
- The error of the late ones is 0.47 ns at 30 ps.

**Phase 1's turn-on (last 200 cycles):**

| run | V_DS mean | p95 | max | before the valley |
|---|---:|---:|---:|---:|
| A97 j30 | 8.98 V | 9.07 V | 9.08 V | 6% |
| A99 j30 | 8.97 V | 9.17 V | 9.27 V | 21% |
| A97 j100 | 8.98 V | 9.08 V | 9.11 V | 18% |
| A99 j100 | 8.97 V | 9.50 V | 9.82 V | 42% |

- This topology turns on at the valley, about 9 V, not at zero.
- **Phases 2-4's turn-on V_DS p95:** 9.22 against 9.32 V at 30 ps, and
  9.54 against 9.87 V at 100 ps.
- **A91's hard-on estimate over all phases:**
  - 30 ps: 0.03-0.09 mW (A97 0.04-0.13);
  - 100 ps: 30-99 mW (A97 30-102).

## 3. Against D54's registered predictions (BOUNDARY Section 5.3)

| run | spread, phases 1-4, against median | early, phases 2-4, minus median | period spread against median | phase 1 mean minus median | verdict |
|---|---|---|---:|---:|---|
| j30 | +5% / +6% / 0% / −2% | −0.5 / +1.0 / +0.5 points | **+35%** | +0.02 A | **outside** (period spread, criterion ±30%) |
| j100 | −2% / 0% / −12% / −8% | −1.0 / −4.0 / −3.0 points | −8% | 0.00 A | agrees |
| n0 | 0.018 A against 0.018 A predicted (criterion ≤ 0.10 A) | 0 | 0.016 against 0.016 ns | -6.32 against -6.30 A | met |

**As in A98, the co-simulation is above D53/D54 at small σ.** A plausible
cause, not isolated, is measurement noise that the model lacks: crossings
on 10 ps steps, then rounding to the LSB.

## 4. Predictions against outcomes

**BOUNDARY Section 4,** written before D54 and stated for an error-based
dlo, evaluated in D54:

| prediction | outcome |
|---|---|
| 1. Period spread ≤ 0.30 ns (gain 1/2), ≤ 0.15 ns (gain 1/8) | 0.28 ns: **confirmed**; 0.19 ns: **missed**. |
| 2. Phases 2-4 spread −20-35% at gain 1/2, near 0.63× at 1/8 | **Confirmed**: −25-30%; 0.66-0.71×. |
| 3. Phase 1's spread rises to 0.3-0.5 A | **Confirmed**: D54 0.40-0.42 A; A99 0.39 A. |
| 4. High-side early of phases 2-4 falls to 15-20% | **Confirmed**: D54 17-18%; A99 17-18%. |
| 5. Deterministic two-cycle components ≤ 0.10 A | **Confirmed**: D54 0; A99 n0 spread 0.018 A. |

**Not predicted:** the error-based dlo turns phase 1 off too early on
average under noise (D54: mean -6.04 A at 30 ps, gain 1/2). The sign rule
was chosen for that reason before any A99 run (Section 5 amendment).

## 5. What the timed turn-off changes, in one line each

- **The period** is set by commanded intervals, not by when the current
  reaches the threshold. ∂T/∂ton_1 falls from 10.5 to 1.0.
- **Phases 2-4** no longer inherit a period error.
- **Phase 1's turn-off current** varies instead, by about 6.5 A/ns times
  its on-time error.
- **The trim's limit cycle disappears.** A timed edge is corrected in
  31 ps steps (0.02 A) instead of the trim's 0.25 A.

## 6. Limits and next

- **Load and line steps were not tested.**
  - The sign rule tracks at most 31 ps per cycle.
  - A coarse/fine rule could cover steps: an error-based step when the
    error is large, the sign step near the target (Thuc and Chen 2024's
    structure). The comparator could also act as a backstop beyond a
    window.
  - Both need their own test before adoption.
- **The learning length** (1024 cycles) was chosen to cover this
  start-up's settling. It is not a general rule.
- **Phase 1's turn-off current reaches -3.3 A at 100 ps.** Its ZVS energy
  then falls. The hard-on estimate does not rise, but the margin is
  smaller.
- **The model and the loads:** one load (5%), m = 0, seed 1, 200 cycles per
  statistic.
