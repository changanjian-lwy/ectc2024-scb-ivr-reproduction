# A98 / D53 - why gate-driver jitter is amplified, in both models (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`.

**Boundary:** `BOUNDARY.md`.
- Sections 1-4 were written before any code or run.
- Section 5, the amendment with D53's predictions for every A98 run, was
  written after D53 and before any A98 run. It was committed (9155a0c)
  before the runs were started.

**Records:**
- `cosim/run_*.json` and `cosim/cfg_*.json`. All 7 runs are of commit
  9155a0c with no modified sources.
- `a98_summary.json` (`a98_analyze.py`): the co-simulation statistics of
  A98's runs and of the archived A92/A93/A97 runs, and A98 against D53.
- `d53_predictions.json`: D53's bands, as registered before the runs.

**Models:**
- **Physical (A98):**
  - the adopted design (`src/scb_ivr/cosim/presets/p24_5pct_adopted.json`:
    A92's correctors, A97's averaged slots and guard), Verilog RTL and A88's
    plant (kernel2), 5% load, 25 C;
  - Gaussian jitter σ, independent on every gate edge, seed 1;
  - statistics over the last 200 cycles.
- **Mathematical (D53):** D47's map linearised at D51's orbit, with one
  input per gate edge
  (`symbolic_derivations/03_P24_native/D53_P24_GATE_JITTER_CLOSED_LOOP.md`).
  Two calculations:
  - a linear covariance;
  - a Monte Carlo of the linearised circuit with the RTL's exact controller
    rules.

## 0. Verdict

1. **The amplifier is the circuit, through phase 1's current-comparator
   turn-off.** Both models agree.
   - **Phase 1:** an on-time error δ moves its peak current on the steep
     on-slope, and the comparator converts that back to time on the shallow
     off-slope. The period moves by **10.5·δ** (D53: ∂T/∂ton_1 = +10.5).
   - **Phases 2-4:** their slots are referred to phase 1's turn-on, so they
     inherit the period error. Their turn-off current moves by **0.68 A
     per ns** (−Vo/L), and their valley by −0.18 ns per ns.
   - **The on-time edges dominate:** 97% of the turn-off current variance
     at 30 ps (D53). The co-simulation agrees: high-side edges alone give
     the full spread (h30), low-side edges alone 17% of the variance (l30).
   - **Most of it is linear.** The linear covariance (no early rule, no
     quantisation) already gives 0.52-0.57 A at 30 ps, against 0.56-0.66 A
     co-simulated.
2. **D53's Monte Carlo reproduces the co-simulation.**
   - Against the archived runs: fixed, follow and average slots at 0, 30 and
     100 ps, within 10-20%.
   - **Against A98's runs, predicted before they ran: 6 of 7 within the
     registered criterion.** s10 misses it on phase 4's spread (+23%
     against ±20%).
3. **No corrector setting reduces the spread.** D53 found at most −7% for
   any of the variants tried, and A98's gain-1/4 runs confirm it: 0.56-0.62
   against 0.56-0.66 A at 30 ps.
4. **Gain 1/4 halves the turn-ons before the valley, as predicted,** but it
   is not worth it.
   - At 30 ps: 12-16% against 23-26%; at 100 ps: 30-34% against 41-47%.
   - Its reverse-conduction loss rises: 0.003 → 0.011 W at 30 ps,
     0.089 → 0.172 W at 100 ps.
   - That is more than the hard-on loss it saves (A91's estimate:
     ≤ 0.13 mW → 0 at 30 ps; 30-102 → 12-39 mW at 100 ps).
   - Most turn-ons "before the valley" are within a fraction of a ns of
     it, where V_DS is near its minimum. **Not adopted.**
5. **The response per ps of σ falls slowly:**
   - 0.028 / 0.021 / 0.019 / 0.018 / 0.017 A/ps at 10 / 20 / 30 / 50 /
     100 ps;
   - at small σ, the 31.25 ps quantisation adds a floor.
6. **No run cross-conducts:** peaks 156-162 A, 26.6-26.7 V.
7. **The levers are architectural, not in the correctors:**
   - the reference of the slots (a filtered timebase instead of phase 1's
     turn-on, the PLL approach of Huber et al. 2009);
   - phase 1's current-comparator turn-off;
   - the driver's jitter itself.

   **A secondary path: phase 1's trim.**
   - Jitter on phase 1's turn-off edge randomises the trim's ±1 LSB steps
     (0.25 A, about 0.37 ns of period each).
   - It dominates with low-side jitter alone. With all edges it is about 7%
     of the spread at 30 ps and negligible at 100 ps (D53).

## 1. Gates

| check | result |
|---|---|
| `ControlLP` opt-in offsets: `scripts/p24_orbits.py --gate` | **13 of 13 archived orbits bit-identical.** |
| `p24_closed_loop.core_jacobian` takes a map function | D52 recomputed: every field identical except wall time. |
| bridge `driver.jitter_edges`: `scripts/cosim_regression.py --full` | **PASS**: A89 r2, A92 j100 (the jitter path, key absent), A92 m3p, A93 m3n_both. |
| D53's per-edge Jacobian against D52's | On-time columns summed, slot columns weighted (k-1)/4, and the section columns all reproduce D52's to ≤ 6e-5 relative. |

## 2. Co-simulation results (adopted design, last 200 cycles, phases 2-4)

| run | σ | jittered edges | turn-off current spread (A) | jitter part (A/ps) | high-side early | low-side early | high-side error spread (ns) | valley spread (ns) | period spread (ns) | windowed dither (A) |
|---|---:|---|---|---:|---|---|---|---|---:|---:|
| A97 n0 | 0 | - | 0.18 / 0.19 / 0.21 | - | 0 / 0.5 / 2.5% | 0 | 0.06-0.08 | 0.05 | 0.14 | 0.57 |
| s10 | 10 | all | 0.34 / 0.32 / 0.37 | 0.028 | 14 / 10 / 16% | 0 | 0.10-0.12 | 0.07-0.08 | 0.34 | 0.97 |
| s20 | 20 | all | 0.47 / 0.43 / 0.49 | 0.021 | 21 / 19 / 22% | 0 | 0.12-0.14 | 0.09 | 0.45 | 1.55 |
| A97 j30 | 30 | all | 0.62 / 0.56 / 0.66 | 0.019 | 26 / 23 / 25% | 0.5 / 0.5 / 2% | 0.14-0.16 | 0.11-0.12 | 0.59 | 1.95 |
| s50 | 50 | all | 0.94 / 0.84 / 1.00 | 0.018 | 35 / 33 / 35% | 7 / 8 / 12% | 0.18-0.21 | 0.15-0.17 | 0.88 | 3.10 |
| A97 j100 | 100 | all | 1.69 / 1.59 / 1.79 | 0.017 | 41 / 47 / 45% | 25 / 31 / 31% | 0.26-0.28 | 0.23-0.24 | 1.65 | 5.70 |
| h30 | 30 | high | 0.64 / 0.67 / 0.71 | 0.021 | 26 / 28 / 28% | 0 | 0.15-0.16 | 0.11-0.13 | 0.51 | 2.00 |
| l30 | 30 | low | 0.29 / 0.32 / 0.31 | 0.008 | 12 / 12 / 12% | 0 | 0.10-0.11 | 0.07-0.08 | 0.34 | 0.83 |
| g4_j30 | 30 | all, gain 1/4 | 0.58 / 0.56 / 0.62 | 0.018 | 13 / 12 / 16% | 0 | 0.14-0.15 | 0.12 | 0.59 | 1.73 |
| g4_j100 | 100 | all, gain 1/4 | 1.70 / 1.65 / 1.88 | 0.017 | 30 / 31 / 34% | 16 / 14 / 17% | 0.29-0.31 | 0.27 | 1.66 | 5.21 |

Notes:
- **The "jitter part"** is √(spread² − A97 n0's spread²), averaged over
  phases 2-4, divided by σ. A97 j30 and j100 are the adopted design at 30
  and 100 ps (same configuration, seed 1).
- **The high-side error and valley** are measured on the turn-ons that come
  after the valley; an early turn-on has no valley reading.
- **For every run:** no cross-conduction; Ton 17.750 ns; Vo 0.9997-1.0003
  V; settling after the handover 116.6-117.9 us (A97: 117.1).

**Variance shares at 30 ps** (jitter part squared):
- h30: 0.413 A²; l30: 0.057 A²; all edges (A97 j30): 0.339 A².
- So the high-side edges alone give the whole all-edge variance (122%), and
  the low-side edges 17%.
- The sum exceeds 100% by about the sampling error of 200 cycles.
- D53's Monte Carlo predicted 89% and 14%.

## 3. Against D53's registered predictions (BOUNDARY Section 5.3)

Criterion: each phase's spread within ±20% of D53's median, and each phase's
early fraction within ±8 percentage points.

| run | spread against D53's median, phases 2 / 3 / 4 | early fraction minus D53's median (points) | verdict |
|---|---|---|---|
| s10 | +18% / +8% / **+23%** | +4.5 / 0.0 / +5.0 | **outside** (phase 4's spread) |
| s20 | +9% / −6% / +2% | +2.5 / 0.0 / +1.5 | agrees |
| s50 | +4% / −11% / 0% | +1.0 / −1.5 / −0.5 | agrees |
| h30 | +11% / +14% / +16% | +1.5 / +3.5 / +2.5 | agrees |
| l30 | +18% / +18% / +10% | +4.0 / +2.5 / +1.0 | agrees |
| g4_j30 | +3% / −5% / 0% | +0.5 / −1.5 / +1.5 | agrees |
| g4_j100 | +2% / −6% / 0% | −3.0 / −2.5 / −1.5 | agrees |

- **Where the misses are.** The co-simulation is above D53 at small σ
  (s10, l30: +10 to +23%).
- **Possible cause, not isolated:** measurement noise that D53 does not
  have. The co-simulation's valley and crossing are taken on its 10 ps
  plant steps and then rounded to the 31.25 ps LSB, whereas D53's are
  exact.

## 4. The mechanism (D53, confirmed by A98)

**1. The open-loop chain** (D53's Jacobian at D51's orbit):
- ∂T/∂ton_1 = **+10.5 ns/ns**: phase 1's current comparator turns an
  on-time error into a period error.
- ∂i_off,k/∂slot_k = −0.68 A/ns, which is −Vo/L. ∂valley_k/∂slot_k =
  −0.18 ns/ns.
- Phase k's on-time has no direct effect on its own turn-off current in
  the same cycle. It acts through the next cycle's state.

**2. Variance shares at 30 ps** (D53 linear covariance, average slots,
phase 4):

| source | turn-off current | valley |
|---|---:|---:|
| phase 1's on-time edges (η, hoff_1) | 60% | 60% |
| phases 2-4's on-time edges | 37% | 37% |
| low-side edges | 3% | 3% |

The period's spread comes 100% from phase 1's on-time edges.

**3. The co-simulation's decomposition agrees.**
- h30's period spread is 0.51 ns, against 0.59 ns for all edges.
- l30's is 0.34 ns. With low-side edges only, a second path dominates:
  phase 1's trim.
  - Phase 1's turn-off edge jitter randomises the trim's ±1 LSB decisions.
  - Each step moves the threshold by 0.25 A, and the period by
    1.47 ns/A × 0.25 A ≈ 0.37 ns.
- D53, low-side edges at 30 ps:

  | trim | period spread | turn-off current spread |
  |---|---:|---:|
  | frozen | 0.065 ns | 0.10 A |
  | active | 0.29 ns | 0.25-0.28 A |

  Phase 1's turn-off edge alone gives 0.29 ns.
- **With all edges the trim's share is small:**

  | trim, all edges | 30 ps: period / current | 100 ps: period / current |
  |---|---|---|
  | active | 0.545 ns / 0.59-0.65 A | 1.57 ns / 1.70-1.91 A |
  | frozen | 0.473 ns / 0.55-0.59 A | 1.54 ns / 1.69-1.89 A |


**4. The high-side early fraction follows from the spread.**
- The error spread is 0.14-0.16 ns at 30 ps, around a mean of 0.11 ns (the
  corrector's dead band: errors of 3 and 4 LSB give no update).
- So about 25% of turn-ons fall before the valley. The linear model alone
  gets this.
- D50's scalar model gave 3% because it held the valley fixed. The valley
  moves by 0.11-0.12 ns.

## 5. Predictions against outcomes (BOUNDARY Section 4)

| prediction | outcome |
|---|---|
| 1. The linear covariance underestimates the 30 ps spread and the early fraction by at least half; the early rule is the missing part | **Wrong.** The linear covariance gives 0.52-0.57 A (co-simulation 0.56-0.66 A) and an error spread of 0.17-0.19 ns, which puts about 25% of turn-ons early. The valley spread within a factor of 2: yes (0.14-0.15 against 0.11-0.12 ns). |
| 2. The Monte Carlo reproduces 30 ps: spread ±30%, early ±10 points | **Confirmed**: within 10-15% and 4 points for all three slot rules. |
| 3. At 100 ps: spread ×2.5-3 the 30 ps value, early 35-50% | **Confirmed** at the edge of the range: ×2.9-3.0; 45-49% (co-simulation 41-47%). |
| 4. The on-time edges contribute most to the valley spread | **Confirmed**: 97% (D53). |
| 5. Spread close to linear up to 20 ps, less than linear from 50 ps | **Wrong as written:** the response per ps falls from 10 ps on (0.028 → 0.021 A/ps from 10 to 20 ps). The amended form (Section 5.3: falls slowly, with a quantisation floor at small σ) holds. |
| 6. h30 ≥ 70% of the all-edge variance; l30 ≤ 40% | **Confirmed**: 122% (sampling error) and 17%. |
| 7. No cross-conduction; peaks ≤ 200 A | **Confirmed**: 156-162 A. |
| Amendment 5.3: every A98 run within the registered bands | **6 of 7**; s10 misses on phase 4's spread (+23%). |

## 6. The mitigation that was tested (gain 1/4)

| | A97 j30 (gain 1/2) | g4_j30 | A97 j100 (gain 1/2) | g4_j100 |
|---|---:|---:|---:|---:|
| turn-off current spread, phases 2-4 (A) | 0.56-0.66 | 0.56-0.62 | 1.59-1.79 | 1.65-1.88 |
| high-side turn-ons before the valley | 23-26% | 12-16% | 41-47% | 30-34% |
| A91's hard-on loss estimate, mode P (mW) | 0.04-0.13 | ≈ 0 | 30-102 | 12-39 |
| reverse-conduction loss P_rev (mW) | 3 | 11 | 89 | 172 |
| windowed dither (A) | 1.95 | 1.73 | 5.70 | 5.21 |

**Why P_rev rises.** The gain also applies to the low-side corrector, which
then follows the moving crossing more slowly. Fewer low-side turn-ons come
before the crossing (100 ps: 14-17% against 25-31%), and more come after it
by more than the time the node takes to reach the diode's forward drop.

**Net: worse in loss at both σ.** Not adopted. The preset is unchanged.

## 7. Limits

- **The jitter model:** Gaussian and independent per edge, an
  idealisation. Real drivers have correlated, supply- and
  temperature-dependent delays.
- **D53 is linear in the circuit.** At 100 ps its valley spread is 40%
  above the co-simulation's, measured on the same non-early cycles.
- **The early fraction is not a loss.** Only A91's hard-on estimate and
  P_rev were compared. The other losses of mis-timed edges (gate charge,
  overlap) were not modelled.
- **Scope:** one load (5%), m = 0, seed 1, and 200 cycles per run.
  Sampling error on a variance share is about ±20%.
- **The architectural levers of Section 0.7 were not tested.**

## 8. Literature read after the runs (2026-10-01)

**Two of BOUNDARY Section 2's sources:**
- **Peterchev and Sanders (TPEL 2003)** and **Maksimovic and Zane (TPEL
  2007)** were obtained and filed locally.
- **Schirone et al. (IET Power Electronics 2017, DOI
  10.1049/iet-pel.2015.0551) could not be obtained** through NUS. It is
  replaced by Dong et al. 2022 below, which addresses the same question,
  the tuning step of an adaptive ZVS loop.

**Six recent papers (2021-2025)** were then read: three in full, the
others from their abstracts and key sections. The PDFs are kept locally,
not in the repository.

| paper | what it does | bearing on A97/A98 |
|---|---|---|
| **Dong, Yang, Xu, Wei, Wang, IEEE PEAC 2022, pp. 247-251, DOI 10.1109/PEAC56338.2022.9959609** (read in full) | Adaptive ZVS in an interleaved GaN CRM totem-pole PFC. A comparator detects the ~2 V reverse-conduction voltage, and the SR on-time steps ±Δt each control cycle, around the optimum. The step is variable: the predicted rate of change times the control period, plus a small perturbation. Interleaving is open-loop at 180°. | **The same class of sign-based correction** as our early rule and trim. Their step trade-off (too small: ZVS lost while tracking; too large: over-regulation) is A98's: the large early step protects, and a smaller one makes things worse (D53). Their answer is a feedforward of the expected change; ours has none. |
| **Zhou, Pan, Fu, Liang, Wang, IEEE TIE 72(6):6038-6048, 2025, DOI 10.1109/TIE.2024.3493174** (read in full) | Interleaving of a CRM totem-pole rectifier from a **predicted** switching cycle (zero-current prediction), with deadbeat duty for the slave during frequency transitions. | **It names A93's failure for the open-loop rule.** With Ts captured from the previous cycle, a period change produces a transition cycle [Ts(n) − Ts(n−1)]/2 + Ts(n), and slave-current fluctuations proportional to the period difference. The PLL alternative is bandwidth-limited and may oscillate at high frequency. **Their remedy is prediction rather than measurement**: the predicted cycle replaces the measured one. |
| **Zhou, Peng, Liang, Fu, Wang, IEEE TPEL 38(7):8513-8527, 2023, DOI 10.1109/TPEL.2023.3259984** (read in full) | CRM control without a current sensor: an inductor-current estimator, using the executed on-time, predicts the current zero crossings and replaces the noisy zero-current comparator. A disturbance-damping term limits estimator error from inductance, resistance and Coss nonlinearity. | **The counterpart of A98's main lever.** Here, phase 1's current comparator converts on-time jitter into ×10.5 period jitter. A predicted (timed) phase-1 turn-off would instead let the jitter move phase 1's turn-off current, by about the on-slope times δ. |
| **Zhu, Wang, Li, Yang, Chen, IEEE APEC 2021, pp. 1837-1842, DOI 10.1109/APEC42165.2021.9487095** | Detects body-diode conduction of both switches and tunes the SR turn-off and dead time on-line. Insensitive to tolerances and signal delays. | Reverse-conduction detection as the error signal: the loss that A98's gain-1/4 runs raised. |
| **Yu, Fan, Wei, Xu, IEEE ECCE 2024, pp. 2831-2836, DOI 10.1109/ECCE55643.2024.10861218** (Navitas) | Interleaved GaN CrM PFC with dual loops and dual feedforward: a theoretical on-time feedforward, a current-sharing loop and a phase-interleaving loop. Small phase error. | An industrial closed-loop interleaving with feedforward, the alternative to the open-loop slot rules of A93/A97. |
| **Thuc, Chen, IEEE TIA 60(6):9157-9170, 2024, DOI 10.1109/TIA.2024.3454198** | GaN driver IC with dual-edge adaptive dead time. A phase-error detector and a coarse/fine controller reach < 1 ns dead time. | The coarse/fine structure, a large step far from the target and a small one near it, is the pattern A98 found: the 0.2 ns early step protects, and fine correction belongs to the error-based update. |

**Consequences:**
- **D53's levers now have recent precedents:**
  - a predicted rather than measured period for the slots (Zhou et al.
    2025);
  - a predicted turn-off instead of the current comparator (Zhou et al.
    2023);
  - feedforward in the step of a sign-based correction (Dong et al. 2022).
- **Rough bound, not computed with the closed loop:** a timed phase-1
  turn-off removes at most the share of phase 1's on-time edges, 60% of
  the variance at 30 ps. That leaves about √0.4 ≈ 0.63 of the spread.

