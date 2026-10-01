# A100 / D55 - the timed phase-1 turn-off under load steps: a faster dlo rule (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`.
Written before any code or run of A100 and D55.

## 1. Question

**A99's timed phase-1 turn-off** cuts the jitter response of phases 2-4 by
30-38% and removes the trim's limit cycle. Its dlo, phase 1's on-low
interval, steps by ±1 LSB (31.25 ps) per cycle.

**But that is slow:**
- D54's Jacobian gives ∂i_off,1/∂ton_1 = +6.5 A/ns and
  ∂i_off,1/∂tlow_1 ≈ −0.68 A/ns.
- So keeping phase 1's turn-off current at its target needs a change in
  dlo of about 9.5 times any change in Ton.
- In a load step the voltage loop moves Ton by several LSB, so the
  required dlo moves faster than 1 LSB per cycle. A lagging dlo moves
  phase 1's turn-off current away from -6.25 A.

**Which dlo rule tracks load steps while keeping A99's jitter benefit?**
And is the result better than the comparator design (A97) on both counts?

This is the trade-off loop to avoid: faster tracking needs more gain, and
more gain passes more noise. Both sides are measured for every candidate.

## 2. Prior work

- **Dong et al., IEEE PEAC 2022, DOI 10.1109/PEAC56338.2022.9959609.** A
  sign-based ±Δt ZVS tuning whose step is a feedforward of the predicted
  change, plus a small perturbation.
- **Thuc and Chen, IEEE TIA 60(6), 2024, DOI 10.1109/TIA.2024.3454198.**
  Coarse/fine adaptive dead-time control: a coarse step far from the
  target, a fine one near it.
- **Zhou et al., IEEE TPEL 38(7), 2023, DOI 10.1109/TPEL.2023.3259984.** A
  predicted turn-off point from an estimator that uses the executed
  on-time.
- **Original source of the adaptive step:** Jayant, "Adaptive Delta
  Modulation with a One-Bit Memory", Bell System Technical Journal
  49(3):321-342, 1970, DOI 10.1002/j.1538-7305.1970.tb01774.x.
  - The step grows while consecutive decisions agree, and falls when they
    alternate.
  - It is symmetric, so it adds no bias, which matters after D54's finding
    on asymmetric rules.
- **This project:** A99/D54 (timed turn-off, sign rule); A79 (the voltage
  loop, ki = 0.25 ns/V).

## 3. Changes (all opt-in, shared package)

### 3.1 A load step (plant and bridge)

**Change:** cfg key `load_step` = {"t_us", "i_a"}. A current i_a is drawn
from the output from t_us on, on top of the resistive load.
- It enters the source term, as the constant-current load does
  (`CircuitParams.load_at`, `plant_kernel.c`'s `load_at`).
- No topology changes.
- With no step, the term is 0.0 + 0.0, so every result is unchanged.

**Change:** cfg key `records_last` (default 1000) keeps more of the
turn-on, turn-off and low-on records, so that a whole transient can be
read.

**Gates:**
- `--full` regression bit-identical;
- `tests/test_cosim_plants.py`.

### 3.2 dlo rules (RTL, phase 1, with `cfg_lo_pred`)

Candidates for D55; only the chosen one is run in A100:

| rule | update |
|---|---|
| **S** (A99) | ±1 LSB on the sign of the report. |
| **ADM** | Adaptive step on the sign. The step doubles while consecutive decisions agree, up to `cfg_lo_smax`, and returns to 1 when they differ. |
| **FF** | S plus a Ton feedforward. When Ton changes by ΔTon, dlo changes by K·ΔTon, with K from D54's Jacobian (about 9.5). |
| **ADM+FF** | Both. |

**With the new bits at 0, A99's rule is unchanged.**

**Gates:**
- unit tests;
- `--full` regression;
- A99's runs replayed bit-identically.

## 4. Plan and predictions

### 4.1 Reference runs (A97 design, comparator)

Load steps at 400 us, runs to 600 us:
- +25 A and −25 A (±10% of the ~250 A load);
- +62.5 A and −62.5 A (±25%).

From each, per cycle:
- the on-low interval of phase 1, which is the interval that keeps its
  turn-off at the target;
- Ton, Vo, the peaks.

**Prediction:** the required interval changes by up to several LSB per
cycle (more than the S rule's 1 LSB per cycle), and mostly through Ton:
ΔL ≈ 9.5·ΔTon.

### 4.2 D55 (mathematical model)

**1. Tracking.** A scalar replay of each rule against the measured
required-interval trajectory (and Ton, for FF). It gives the largest
tracking error in ns, converted to phase 1's turn-off current error at
0.68 A/ns, and the cycles to come back within 2 LSB.

**2. Jitter.** D54's Monte Carlo (linearised circuit, exact rules) for
each rule at 0, 30 and 100 ps.

**Predictions (before D55 is built):**
1. **S:** a largest current error > 2 A in the ±25% steps.
2. **ADM:** errors within 0.5 A in all steps, and a jitter response
   within 10% of S's. Under noise the decisions alternate, so the step
   stays at 1-2.
3. **FF:** removes most of the Ton-driven part. The rest, from Vo, still
   needs ADM in the ±25% steps.
4. **The chosen rule** keeps A99's jitter benefit (phases 2-4 spread at
   30 ps ≤ 0.47 A, against A97's 0.56-0.66) and tracks all four steps
   with phase 1's turn-off current within 1 A of its steady value.

### 4.3 A100 (physical model)

**Runs:**
- the chosen rule under the four load steps;
- A99's S rule under ±25%, to show the lag;
- the chosen rule at j30 and j100.

**Registered before the runs** (amendment, Section 5):
- D55's predicted bands;
- criteria:
  - no cross-conduction;
  - peaks ≤ 200 A;
  - phase 1's turn-off current within the predicted band through the
    step;
  - Vo's dip and recovery no worse than A97's by more than 10%.

## 5. Amendment (after the reference runs and D55, before any timed A100 run; 2026-10-01)

### 5.1 Reference runs (adopted comparator design, step at 400 us)

| step | phase 1's on-low interval | change per cycle, 95th % / largest | Ton | Vo extreme |
|---|---|---|---|---|
| +25 A | 203.7 → 221.6 ns | 13.6 / 31 LSB | 568 → 624 LSB | 0.950 V |
| −25 A | 203.7 → 185.7 ns | 13.4 / 32 LSB | 568 → 512 LSB | 1.050 V |
| +62.5 A | 203.7 → 248.2 ns | 24 / 54 LSB | 568 → 706 LSB | **0.873 V** |
| −62.5 A | 203.7 → 158.9 ns | 16 / 44 LSB | 568 → 427 LSB | **1.122 V** |

**Section 4.1's prediction holds, and the reality is worse than
expected.** The required interval moves 13-54 LSB per cycle, not "several".
- Its ratio to the Ton change is 10.1-10.3, against 9.52 from D54's
  Jacobian.
- The comparator design itself lets Vo move by up to ±12%. The voltage
  loop (A79, ki = 0.25 ns/V) is slow; this is not the dlo rule's doing.

### 5.2 D55 (replay of these trajectories; Monte Carlo for jitter)

| rule | largest phase-1 turn-off current error, +25 / −25 / +62.5 / −62.5 A | 30 ps: phases 2-4 spread | period spread |
|---|---|---|---|
| S (A99) | 12.9 / 12.3 / 39.0 / 34.7 A | 0.40-0.42 A | 0.15 ns |
| ADM16 | 0.7 / 0.8 / 8.6 / 2.8 A | 0.43-0.45 A | 0.27 ns |
| **ADM32** | **0.9 / 0.8 / 2.4 / 1.9 A** | **0.44-0.46 A** | 0.30 ns |
| FF10+S | 6.2 / 5.3 / 21.3 / 13.1 A | 0.40-0.42 A | 0.16 ns |
| FF10+ADM32 | 0.8 / 0.8 / 2.0 / 1.9 A | 0.44-0.46 A | 0.30 ns |
| comparator (A97, for reference) | - | 0.56-0.66 A | 0.55 ns |

- **The feedforward alone fails.** During the transient, Vo's dip changes
  the off-slope, which no Ton feedforward sees.
- **The adaptive step does the tracking.**
- **About 1.9 A is a floor in the −62.5 A step for every rule.** The first
  cycles change by 44-54 LSB, and the measurement comes one cycle late.

**Chosen: ADM32** (`lo_adm` 1, `lo_smax` 32, no feedforward). It is the
simplest rule within 0.4 A of the best tracking, at the same jitter cost.
- **The trade-off, quantified:** against S, ADM32 raises the 30 ps spread
  of phases 2-4 by about 9% and the period spread from 0.15 to 0.30 ns.
- It remains 25-30% below the comparator design.

**Prediction 4 (Section 4.2) is wrong for the ±62.5 A steps:** D55 gives
about 2-2.4 A, not < 1 A. Predictions 1 and 2 hold in D55. Prediction 3
holds only partly: the feedforward removes about half of the error.

### 5.3 A100 runs and registered predictions (`d55_predictions.json`)

**Gate before the runs.** The RTL with `lo_adm` and `lo_ff` at 0 replays
A99 n0 bit-identically, and passes the `--full` regression.

| run | configuration | prediction |
|---|---|---|
| adm_p25 / adm_m25 | ADM32, ±25 A at 400 us, to 600 us | largest phase-1 turn-off current error 0.86 / 0.80 A (relative to its pre-step mean) |
| adm_p62 / adm_m62 | ADM32, ±62.5 A | 2.42 / 1.91 A |
| s_p62 / s_m62 | A99's S rule, ±62.5 A | > 10 A (D55: 39 / 35 A); the run may end on an overlap |
| adm_j30 | ADM32, 30 ps, no step | phases 1-4 spread 0.41 / 0.43 / 0.43 / 0.45 A [0.36-0.52]; period spread 0.27 ns [0.19-0.41]; high-side early 17%; phase 1 mean -6.31 A |
| adm_j100 | ADM32, 100 ps | 1.19 / 1.22 / 1.20 / 1.25 A [1.08-1.40]; period spread 0.57 ns [0.40-0.81]; early 39-40% |

**Criteria:**
- **ADM step runs:**
  - the largest error within ±50% of the prediction (the replay ignores
    the closed-loop feedback of the error);
  - no cross-conduction;
  - peaks ≤ 200 A;
  - Vo's extreme within 10% of the reference run's excursion.
- **Jitter runs:**
  - each phase's spread within ±20% of the median;
  - period spread within ±30%;
  - early within ±8 points;
  - phase 1's mean within 0.15 A.

## 6. Decides / does not decide

**Decides:**
- whether the timed phase-1 turn-off can track load steps;
- with which rule;
- at what cost in jitter. This is the input to the adoption decision
  that A99 postponed.

**Does not decide:**
- line steps;
- loads far from the 250 A operating point;
- the voltage loop itself, which is slow (A79) and is not redesigned
  here.
