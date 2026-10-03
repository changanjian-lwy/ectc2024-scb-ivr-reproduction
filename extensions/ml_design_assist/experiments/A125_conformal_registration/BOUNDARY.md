# A125 - conformal intervals for the registered predictions (BOUNDARY)

Extension `ml_design_assist`. **Written and committed with the code
before the sequential test was run.** Only the row counts were looked at
(to check the loader).

## 1. What and why

**The problem:**
- Every main-line experiment registers D63's predictions with a band
  picked by hand, usually ±10% on the peak.
- Two registrations went wrong that way: A118's recovery ≤ 30 µs and
  A124's floor threshold.
- A hand band has no stated coverage, and it is the same in D63's strong
  and weak domains.

**The method: conformal prediction** (`src/scb_ivr/extensions/ml_conformal.py`).
- The band is the ⌈(n+1)(1−α)⌉-th smallest past error.
- If the next error is exchangeable with the past ones, it covers with
  probability ≥ 1 − α. No model of the error is needed.
- Variants:
  - **S:** symmetric (the primary);
  - **G:** signed (narrower when D63 is biased);
  - **M:** Mondrian, calibrated separately on rising line steps (D63's
    known weak domain) and on the other rows;
  - **ACI:** adaptive conformal inference (Gibbs & Candès 2021), whose
    level moves with the observed misses, for errors that drift (the
    designs change from experiment to experiment).
- Unit tests (`tests/extensions/test_ml_conformal.py`, 6 pass) check the
  rank, the guarantee 1 − α ≤ coverage < 1 − α + 1/(n+1) on exchangeable
  data, and ACI under drift.

**Data (`run_a125.py`):**
- 47 step rows of A117, A118, A119, A123 and A124, each with a D63
  prediction registered before the run and a co-simulation record.
- 43 are bounded by D63's outcome rule (15 rising line steps, 28 other);
  the 4 that D63 called slow or runaway carry no point prediction.
- **Quantities:** the peak after the step (relative score), the Vo
  extreme (mV), the recovery within 1% (log score).

**Test, in the order the experiments ran:**
- For each experiment from A118 on, calibrate on the earlier experiments
  only, band its rows, and count the co-simulation inside the band.
- **34 test rows** (A118 12, A119 5, A123 9, A124 8).
- Nominal 80% (primary) and 90%.

**What this is and is not:**
- **Retrospective for the method:** I have read these experiments'
  RESULTS, so I know D63's errors roughly (~5% on the peak, larger on
  rising steps). The registered predictions themselves were blind.
- **The true prospective test is the next co-simulation experiment.**
  Its boundary registers A125's bands (`register_band`, calibrated on
  all 43 rows) next to D63's point predictions.
- Rows within one experiment share a design, so they are correlated.
  Coverage on 34 rows has a sampling sd of ~7 points or more.

## 2. Criteria

1. **Primary:** the peak with S at nominal 80%, pooled over the 34 test
   rows: coverage **≥ 70%**.
2. **D63's weak domain made quantitative:** with M calibrated on all 43
   rows, the 80% peak band is **wider for rising line steps** than for
   the other rows.
3. **Unit tests pass** (the guarantee on exchangeable data).

## 3. Predictions (not criteria)

- **Hand band ±10% on the peak:** coverage ~85%.
- **S at 80%:** a final half-width of ~7-10% of the prediction. That is
  narrower than ±10% at a stated level, or wider if the rising rows
  dominate the tail.
- **ACI:** coverage at least as close to 80% as S's, since the designs
  drift (1 MHz timed → floor → 2.5 MHz).
- **The Vo extreme and the recovery:**
  - Vo extreme: bands of a few mV.
  - Recovery: wide (log band ~×1.5-2). A118 showed D63 under-predicting
    it.

## 4. Decision rule

- **If criterion 1 holds:** from the next co-simulation experiment on,
  each boundary registers A125's band (M at 80%, calibrated on every
  registered row so far) next to D63's point prediction. The hand ±10%
  is retired.
- **If not:** the hand band stays, with A125's result recorded.
