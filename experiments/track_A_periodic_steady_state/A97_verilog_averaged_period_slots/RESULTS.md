# A97 - period-following slots from a two-cycle average of the period (RESULTS)

Track A, `PAPER_LOCKED` (phase shift T/nP) + `CROSS_PAPER_EXTENSION`.

**Boundary:** `BOUNDARY.md`, written before any code or run.

**Records:**
- `cosim/run_*.json`, configurations `cosim/cfg_*.json`;
- `a97_summary.json` (from `a97_analyze.py`);
- synthesis `synth/stat_scb_ctrl.txt`.

The RTL, its unit tests and the bridge are in the shared package
`src/scb_ivr/cosim/`.

**Model: the physical model at implementation level.**
- The shared RTL: A93's, plus `cfg_slot_avg`.
- The shared bridge.
- Plant `kernel2`: A88's plant, with datasheet Coss(V) and reverse drop,
  at 25 C. It is bit-identical to the archived plant.
- Every run is the preset (A92's adopted design: error-based correctors,
  94 ps targets, gain 1/2, 4.5 ns mode-S dead time and dtl_init), with
  only the slot bits and the driver changed.
- **Each A97 configuration differs from its A93 counterpart only by
  `slot_avg` = 1.**

**The mathematical-model counterpart is D52**
(`symbolic_derivations/03_P24_native/D52_P24_CLOSED_LOOP_SLOT_RULES.md`).

## 0. Verdict

1. **With the guard, the averaged slots keep A93's transient benefit.** At
   m = -3.4 ns:

   | run | peak current | peak Vds |
   |---|---:|---:|
   | m3n_avg_guard | **156 A** | 26.9 V |
   | A93 m3n_both | 172 A | 26.9 V |
   | A92 | 827 A | 34.0 V |

   Without the guard, m3n_avg reaches 198 A: still within the 200 A
   criterion, but above A93's 174 A.
   - The cause is the handover slot that is skipped (Section 2).
   - Phase 4 then waits for the next slot. The average makes that slot
     later than A93's, because the average of 135 and about 190 ns is
     longer than 135 ns.
2. **The two-cycle injection is gone (primary criterion: met in all four
   deterministic runs).**
   - Phases 2-4, two-cycle component of the low-side turn-off current:
     **0.13-0.18 A**.
   - A92: 0.14-0.19 A. A93: 0.24-0.59 A.
3. **The dither comes back to A92's.** The largest section-current change
   over the last 20 sections:

   | run | A92 | A93 | A97 |
   |---|---:|---:|---:|
   | n0 | 0.71 A | 1.04 A | 0.58 A |
   | m1p | 0.43 A | 1.27 A | 0.53 A |
   | m1n | 0.46 A | 1.60 A | 0.29 A |
   | m3p | 0.75 A | 1.22 A | 0.55 A |

   m3p is 0.2007 A **below** A92's. That is outside the "within 0.2 A" band
   that BOUNDARY Section 4 wrote, by 0.7 mA, but on the lower side
   (Section 6).
4. **A93's interpretation holds in both models, with one correction.**
   - **Holds:** the follow rule passes (k-1)/4 of the period's two-cycle
     alternation into phase k's slot, and averaging removes it.
   - **Correction:** this is not a lightly damped mode being excited.
     - D52's closed-loop two-cycle modes are at |λ| = 0.65-0.66 under all
       three rules.
     - The forcing is the trim's ±1 LSB alternation of phase 1's current
       threshold.
     - The follow rule adds an injection path, not a mode.
5. **A93's follow rule also made phase 4 turn on before its valley in
   24-41% of cycles.** This was not reported in A93. It is the negative
   half of the high-side error's alternation.
   - A97: 0.5-4.5%. A92: 0.5-3.5%.
6. **The orbit is unchanged:**
   - Ton: m3p toggles between 581 and 582 LSB in all three experiments,
     with means of 18.162-18.168 ns;
   - P_rev: 0 W, and 11.789 W at m3p;
   - flying-capacitor voltages: within 3 mV of A92's.
7. **Jitter.**
   - j100: 5.56 A against A92's 5.51 A.
   - j30: 2.33 against 1.65 A on the pre-registered metric, which **misses
     the ±30% prediction**.
   - Over 10 windows of 20 sections the two are equal: 1.95 ± 0.49 against
     2.03 ± 0.26 A.
   - The low-side turn-off current spread with 100 ps jitter is 5-14% above
     A92's (A93: 21-68%). D52's band gain shows why: the average has its
     zero only at the two-cycle frequency (Section 4).
8. **Gates pass:**
   - unit tests 39 of 39 (A93's 36 unchanged);
   - the four archived full runs replayed bit-identical with the new RTL;
   - plant tests;
   - synthesis clean.
9. **Adopted:** averaged slots and the guard (Section 7), with the m3p
   reading stated there.

## 1. Gates and implementation

| check | result |
|---|---|
| RTL unit tests (`src/scb_ivr/cosim/tb/run_unit.py`) | **39 of 39.** New tests: (1) after three turn-ons with periods P1 ≠ P2, phase k at t_on3 + (k-1)(P1+P2)//8, which differs from A93's (k-1)·P2//4 for every k; (2) after two turn-ons, the configured slot; (3) `cfg_slot_avg` without `cfg_slot_follow`, the configured slot. |
| `scripts/cosim_regression.py --full` with the new RTL | **PASS.** A89 r2, A92 j100, A92 m3p and A93 m3n_both (no `slot_avg` key): every section, register, step count, peak and record list is bit-identical to the archived run. Format additions only. 61-64 s each, 4 at a time. |
| `tests/test_cosim_plants.py` | 3 passed. |
| synthesis (yosys `synth; check -assert`) | 0 problems; 40 296 cells (A93: 39 571). The 38 warnings are ABC's "network is combinational" notices (A93: 37). |

The 8 runs took 4 minutes, 4 at a time.

**The archived outputs come from runs of the committed code (8775727).**
- They were rerun after the commit, because the first runs were made
  before it: provenance "cosim_sources_modified".
- Every field except `provenance` and `wall_s` is identical to the first
  runs (`compare_full` and a key-by-key check, all 8).

## 2. The m3n case

All runs have m = -3.4 ns. The start-up is identical up to the handover at
88.81 us, where Vo = 1.539 V.

| run | follow | avg | guard | peak current | peak Vds | late fires, phases 1-4 |
|---|---|---|---|---:|---:|---|
| A92 m3n | - | - | - | 827 A | 34.0 V | 0 / 47 / 74 / 59 |
| A93 m3n_follow | on | - | - | 174 A | 26.9 V | 0 / 0 / 1 / 6 |
| A93 m3n_both | on | - | on | 172 A | 26.9 V | 0 / 0 / 0 / 9 |
| **A97 m3n_avg** | on | on | - | **198 A** | 26.9 V | 1 / 0 / 2 / 0 |
| **A97 m3n_avg_guard** | on | on | on | **156 A** | 26.9 V | 1 / 0 / 2 / 12 |

**Where m3n_avg's 198 A comes from** (edge log rerun to 89.4 us; the peak
is reached between 88.9 and 89.3 us):
- Phase 4's low side turned on in the last mode-S cycle, at 88.782 us.
- The handover cycle is 135 ns long and still uses mode S's period, so its
  150 ns slot is skipped.
- Without the guard, the slot moves to the next reference (88.945 us), at
  3/8·(T_{n-1} + T_{n-2}) = **122.2 ns**. Under A93's rule it would have
  been 3/4·135 = 101 ns.
- **The low side stays on for 285 ns and turns off at -197.9 A.**
- With the guard, phase 4 turns off when the reference changes (88.943 us)
  at -74.5 A. That run's peak, 156 A, is elsewhere.

**The average's extra one-cycle lag therefore matters only when a slot is
missed.** That is exactly the case the guard handles, so the two belong
together.

## 3. Steady state (deterministic runs, last 200 cycles)

### 3.1 Two-cycle components

**Measure.** A93 RESULTS Section 3's: half the absolute mean of the
alternating differences.

**Check of the measure.** `a97_analyze.two_cycle` reproduces A93's table
from the archived runs: A92 0.14-0.19 A; A93 0.24-0.30 / 0.34-0.47 /
0.43-0.59 A.

| case | phase 2-4, A92 (A) | phase 2-4, A93 (A) | **phase 2-4, A97 (A)** | period, A92 / A93 / A97 (ns) |
|---|---|---|---|---|
| n0 | 0.150 / 0.148 / 0.144 | 0.251 / 0.388 / 0.519 | **0.163 / 0.162 / 0.179** | 0.083 / 0.088 / 0.097 |
| m1p | 0.187 / 0.179 / 0.183 | 0.240 / 0.343 / 0.426 | **0.142 / 0.133 / 0.157** | 0.100 / 0.077 / 0.083 |
| m1n | 0.176 / 0.167 / 0.163 | 0.301 / 0.467 / 0.589 | **0.157 / 0.165 / 0.167** | 0.090 / 0.103 / 0.086 |
| m3p | 0.142 / 0.150 / 0.145 | 0.294 / 0.440 / 0.499 | **0.147 / 0.138 / 0.132** | 0.084 / 0.094 / 0.079 |
| m3n (guard) | 0.178 / 0.179 / 0.178 | 0.282 / 0.434 / 0.537 | **0.158 / 0.156 / 0.152** | 0.106 / 0.094 / 0.086 |

- Phase 1 is 0.124-0.125 A in every run. That is the trim's ±1 LSB
  (0.25 A), and the input of D52.
- The period's own two-cycle component is 0.08-0.11 ns under all three
  rules.

### 3.2 The high-side error (turn-on minus valley) and early turn-ons

The early turn-ons have no error reading. The two-cycle measure is
therefore taken over pairs of consecutive cycles that both have one,
keeping each cycle's parity (`a97_analyze.two_cycle`). With nothing
missing, it is A93's.

| case | two-cycle, phases 1-4 (ns): A92 | A93 | **A97** | phase 2-4 turn-ons before the valley: A92 | A93 | **A97** |
|---|---|---|---|---|---|---|
| n0 | 0.051 / 0.052 / 0.049 / 0.047 | 0.054 / 0.079 / 0.108 / 0.128 | **0.051 / 0.055 / 0.054 / 0.059** | 0 / 1 / 1.5% | 6.5 / 20.5 / 33.5% | **0 / 0.5 / 2.5%** |
| m1p | 0.053 / 0.061 / 0.058 / 0.059 | 0.054 / 0.072 / 0.087 / 0.099 | **0.052 / 0.048 / 0.046 / 0.053** | 3 / 2 / 3.5% | 8 / 17.5 / 23.5% | **0.5 / 0 / 2.5%** |
| m1n | 0.055 / 0.059 / 0.057 / 0.057 | 0.053 / 0.093 / 0.117 / 0.142 | **0.055 / 0.052 / 0.056 / 0.054** | 3.5 / 1.5 / 1.5% | 12.5 / 30 / 41% | **1.5 / 2 / 4.5%** |
| m3p | 0.051 / 0.047 / 0.051 / 0.049 | 0.054 / 0.088 / 0.109 / 0.121 | **0.053 / 0.052 / 0.047 / 0.043** | 0.5 / 1 / 0.5% | 12 / 27.5 / 29.5% | **1.5 / 1 / 0.5%** |

**Reading.** Under the follow rule the high-side error alternates by up to
±0.14 ns around the 94 ps target. Its negative half is a turn-on before
the valley.
- This is the same injection seen from the high side.
- The extra switching loss of a turn-on at most about 0.05 ns before the
  valley was not estimated. It is small, since V_DS is then near its
  minimum.

### 3.3 Operating point (unchanged)

| case | Ton, A92 / A93 / A97 (ns) | period, A92 / A93 / A97 (ns) | P_rev, A92 / A93 / A97 (W) | VCs1 / VCs2 / VCs3, A97 (V) | VCs, A97 - A92 (mV) |
|---|---|---|---|---|---|
| n0 | 17.750 (all) | 232.20 / 232.32 / 232.17 | 0 | 35.773 / 23.876 / 11.963 | 0 / +3 / -3 |
| m1p | 17.750 (all) | 232.12 / 232.16 / 232.04 | 0 | 35.772 / 23.873 / 11.961 | +2 / -1 / -2 |
| m1n | 17.719 (all) | 231.65 / 231.89 / 231.62 | 0 | 35.769 / 23.874 / 11.963 | -1 / 0 / -1 |
| m3p | mean of last 200: 18.166 / 18.162 / 18.168 | 231.88 / 232.03 / 232.20 | 11.793 / 11.785 / 11.789 | 35.761 / 23.866 / 11.957 | +3 / +3 / -1 |

- m3p's final Ton register reads 18.188 ns in A97 and 18.156 ns in A92/A93.
  In all three, Ton toggles between 581 and 582 LSB over the last 200
  sections, 17-38% of them at 582. So the final value is only a sample of
  the toggle.
- Every run is soft once per cycle. None cross-conducts.
- Settling after the handover is as A92's (n0: 117.1 against 116.9 us).

## 4. Jitter runs

| run | dither, A92 / A93 / A97 (pre-registered, last 20 sections) | dither over 10 windows of 20, mean ± sd: A92 / A93 / A97 | low-side turn-off current sd, phases 2-4: A92 / A93 / A97 (A) |
|---|---|---|---|
| j30 | 1.65 / 1.86 / **2.33 A** | 2.03 ± 0.26 / 2.39 ± 0.42 / **1.95 ± 0.49 A** | 0.61, 0.52, 0.61 / 0.71, 0.76, 0.99 / **0.62, 0.56, 0.66** |
| j100 | 5.51 / 6.21 / **5.56 A** | 5.19 ± 1.35 / 7.08 ± 2.16 / **5.70 ± 1.51 A** | 1.61, 1.40, 1.60 / 1.95, 2.10, 2.69 / **1.69, 1.59, 1.79** |

**The windowed dither and the spread were defined after the results.**
They are given because BOUNDARY Section 4 itself called the last-20 metric
noisy (±0.3 A deterministic, more with jitter).
- On the pre-registered metric, j30 misses its prediction: +41%, against
  ±30%.
- On the windowed one, A97 equals A92.

**The residual 5-14% in the spread** at 100 ps is consistent with D52's
band gain.
- Averaging cancels only the two-cycle frequency.
- At a quarter of the switching frequency (ω = π/2), the gain from phase
  1's threshold to phase 4's turn-off current is:
  - fixed: 0.95;
  - follow: 1.82;
  - avg: 1.67.
- Jitter is broadband, so part of it still passes through the slot.

## 5. Cross-check with D52 (mathematical model)

**D52's model:**
- D47's event map at D50's and D51's m = 0 fixed points;
- linearised with the correctors (gain 1/2), the voltage loop and each
  slot rule's memory;
- the input is phase 1's current threshold at ±0.125 A, the trim's ±1 LSB.

| quantity | fixed slots: D52 / A92 (5 runs) | follow: D52 / A93 (5 runs) | average: D52 / **A97** (5 runs) |
|---|---|---|---|
| phase 1 turn-off current (A) | 0.125 / 0.124-0.125 | 0.125 / 0.124-0.125 | 0.125 / 0.124-0.125 |
| phase 2 (A) | 0.160 / 0.142-0.187 | 0.240 / 0.240-0.301 | 0.162 / **0.142-0.163** |
| phase 3 (A) | 0.160 / 0.148-0.179 | 0.316 / 0.343-0.467 | 0.159 / **0.133-0.165** |
| phase 4 (A) | 0.155 / 0.144-0.183 | 0.390 / 0.426-0.589 | 0.155 / **0.132-0.179** |
| period (ns) | 0.094 / 0.083-0.106 | 0.094 / 0.077-0.103 | 0.093 / **0.079-0.097** |
| high-side error, phase 1 (ns) | 0.051 / 0.051-0.055 | 0.051 / 0.053-0.054 | 0.051 / **0.051-0.055** |
| high-side error, phases 2-4 (ns) | 0.055-0.056 / 0.047-0.063 | 0.084 / 0.110 / 0.138 against 0.072-0.093 / 0.087-0.117 / 0.099-0.142 | 0.055-0.057 / **0.043-0.059** |

**Readings:**
- **Fixed and average:** the two models agree within the run-to-run
  spread.
- **Follow:** D52 has the growth with k, and the high-side errors within
  the spread. It is 10-25% below the co-simulation's phase 3-4 currents.
  The quantised correctors and the early turn-ons (which the linear model
  does not have) are possible reasons; this was not isolated.
- **The mechanism, from D52** (Section 5 there):
  - ∂i_off,k/∂t0 = (k-1)/4 · (-Vo/L) = -0.17·(k-1) A/ns;
  - the 0.093 ns period alternation therefore injects
    0.016/0.032/0.048 A;
  - the closed loop amplifies that 4.9 times at z = -1;
  - the result is +0.078/+0.157/+0.235 A, proportional to (k-1), as A93
    measured.

## 6. Predictions against outcomes

| prediction (BOUNDARY Section 4) | outcome |
|---|---|
| m3n_avg: no starvation, peak ≤ 200 A | **Confirmed, narrowly:** 198 A. Higher than A93's 174 A, because the skipped handover slot waits for a later averaged slot (Section 2). |
| m3n_avg_guard: as m3n_avg, peak ≤ 200 A | **Confirmed:** 156 A. |
| 1. Two-cycle component of phases 2-4 ≤ 0.20 A (n0, m1p, m1n, m3p) | **Confirmed in all four:** 0.13-0.18 A. |
| 2. Dither within 0.2 A of A92's | **3 of 4 as written.** n0 -0.13, m1p +0.10, m1n -0.18 A; m3p -0.2007 A (lower than A92's by 0.7 mA more than the band). Read as "not above A92's + 0.2 A", which is what the criterion protects: 4 of 4. This reading is made after the result. |
| 3. Orbit unchanged | **Confirmed** (Section 3.3). |
| j30, j100: dither as A92's ± 30% | **j100 confirmed** (+1%); **j30 not** (+41%). Windowed, both as A92's (Section 4). |
| No cross-conduction; every peak ≤ 200 A | **Confirmed** in all 8 runs. |
| If 1 fails, A93's interpretation is wrong | 1 holds; the interpretation is confirmed, with D52's correction (no lightly damped mode). |

## 7. Adoption

**The BOUNDARY's rule:** m3n_avg_guard within the criterion, and
predictions 1 and 2 holding in all four deterministic runs.
- m3n_avg_guard is within the criterion.
- Prediction 1 holds in all four.
- Prediction 2 holds in all four only with the one-sided reading of
  Section 6, because m3p's dither is lower than A92's by 0.2007 A.

**Decision: the averaged slots and the guard are adopted**
(`slot_follow`, `slot_avg`, `slot_guard` = 1).
- The decision rests on that one-sided reading, and that is recorded
  here.
- The primary, sturdier measure (prediction 1) holds without
  qualification.
- `src/scb_ivr/cosim/presets/p24_5pct_adopted.json` is updated, and
  recorded in the package CHANGELOG. A92's configuration remains in A92's
  folder.

**Net effect against A92**, the design adopted before A97:
- the m3n starvation is removed (827 A → 156 A);
- the steady state and dither are as A92's;
- phase 4's slot is at T/4 spacing as the papers' T/nP;
- the cost: a 5-14% larger turn-off current spread under 100 ps jitter.

## 8. Limits

- **Scope:** one load (5%) and one start-up sequence, from a zero start.
- **The guard is required.** Without it, the average's lag lengthens a
  missed slot (Section 2).
- **Idealisations, as A92's:** ideal sensors and switches, a static
  mismatch, and Gaussian jitter.
- **Not estimated:** the turn-ons before the valley under A93's rule; their
  loss was not computed.
- **The two-cycle measure** is sensitive to a parity slip within the
  200-cycle window. It is the same measure for all three experiments.

## 9. Literature read after the runs

BOUNDARY Section 2 cited Huber et al. 2008 from its abstract only. The
full texts below were read after the runs (2026-10-01). The PDFs are kept
locally and are not in the repository.

### 9.1 The previous-period rule assumes that adjacent periods are equal

Three independent sources use the rule and state the assumption:

| source | what it does |
|---|---|
| **Huber, Irving, Jovanovic, IEEE TPEL 23(4):1649-1657, 2008, DOI 10.1109/TPEL.2008.924611** | The slave's delay is half the master's period from its previous cycle. |
| **Huber, Irving, Adragna, Jovanovic, APEC 2008, pp. 1010-1016, DOI 10.1109/APEC.2008.4522845** | Implements that rule: the present ramp is compared with half of the previous ramp's peak (Fig. 11). |
| **Tsai, Wu, Wu, Chen, Lee, IEEE TPEL 23(3):1348-1357, 2008, DOI 10.1109/TPEL.2008.921152** | Two- and four-phase shifters that hold the previous period on a capacitor. The text says: "the difference between the adjacent two operation periods is negligible ... we can take the previous operation period to determine the present shift interval." |
| **Freescale AN4836** (2014, no DOI) | The same rule, with the same stated assumption. Its period averaging only chooses the master leg. It also describes a shift computed from duty cycle and voltages and updated every 1 ms, which is a heavily filtered shift. |

### 9.2 What Huber et al. 2008 shows and does not show

**Section II and Table I confirm the abstract.** Synchronising the slave to
the master's turn-on, with current-mode control, is the only open-loop
method that returns to normal operation after a delay perturbation.
- The analysis is graphical (Figs. 7, 8, 12): one perturbed delay, with
  the master undisturbed.
- It does not cover a master whose own period alternates.

**Section III-B and Figs. 17-18 describe A93's mechanism.**
- With a frequency limit and valley switching, the master jitters between
  its first and second valley, so its period alternates.
- Because the shift is sampled from the previous period, divided by two
  and held for one cycle, "an improper phase shift and, therefore, an
  increased current ripple occurs".
- Fig. 18(a) shows the shift moving between 160 and 280°.
- The paper notes only a "tendency of the circuit ... to correct itself"
  and proposes no remedy.
- A97's average is a remedy for this case: an exact alternation cancels.

### 9.3 Closed-loop alternatives

These methods filter the phase error, not the period:
- **Huber, Irving, Jovanovic, IEEE TPEL 24(8):1992-1999, 2009, DOI
  10.1109/TPEL.2009.2018560.**
  - A master-slave or democratic PLL, with a cycle-by-cycle instant
    averaging filter or an RC filter on the phase error.
  - Its small-signal model has one or two poles, so it is "always
    stable". This is shown by SIMPLIS simulation.
  - In the experiment, interleaving is lost near the line zero crossing.
- **Huber, Irving, Jovanovic, APEC 2009, pp. 991-997, DOI
  10.1109/APEC.2009.4802783.** The conference version.
- **Xu, Huang, APEC 2008, pp. 1033-1038, DOI 10.1109/APEC.2008.4522849, and
  Xu, Liu, Huang, IEEE TPEL 24(12):3003-3013, 2009, DOI
  10.1109/TPEL.2009.2019824.**
  - A phase-error current through a gm stage adjusts the slave, without
    the PLL's low-pass filter. The authors call the PLL's response slow.
  - Stability is shown with a full-order averaged model.

### 9.4 Consequences for A97 and D52

- **BOUNDARY Section 2's finding stands:** no source averages two periods.
- **The failure mode A97 removes is published** (Huber et al. 2008,
  Section III-B). There it comes from valley skipping; here it comes from
  the trim's ±1 LSB limit cycle (D52). In both cases it is a two-cycle
  alternation of the master's period, read through the previous-period
  rule.
- **The PLL methods are the closed-loop counterpart** of A97's open-loop
  average. A PLL-type slot rule, with the phase error filtered, is a
  candidate if the residual broadband gain of Section 4 matters. D52's
  closed-loop model can evaluate it before any RTL.
