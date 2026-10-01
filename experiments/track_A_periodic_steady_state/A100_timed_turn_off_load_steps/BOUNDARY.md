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

## 5. Amendment slot

To be filled after the reference runs and D55, before the A100 timed
runs.

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
