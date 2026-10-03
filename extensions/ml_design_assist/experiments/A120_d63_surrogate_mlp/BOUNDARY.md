# A120 - a deep-learning surrogate of D63 (BOUNDARY)

Extension `ml_design_assist`. **Written before any training.**

## 1. What and why

**What:** a multilayer perceptron (MLP) that maps a 1 MHz design and a
disturbance to D63's outcome. D63 is the cycle-by-cycle valley map,
validated against 37 co-simulated transients.

**Why:**
- D63 takes ~0.1 s per transient.
- A design check needs ~8 transients.
- A search over the design space needs ~10⁵ checks, which the surrogate
  answers in milliseconds.
- A121 and A122 build on it.

**Inputs (11):**
- pct (5-15%);
- ln Cs (3-20 µF);
- fc (20-80 kHz);
- the turn-off rule (comparator, timed, floor; one-hot), floor_a
  (1-5 A);
- load or line;
- di (±62.5 A);
- dv (±4.8 V);
- ln slew (1-50 µs).

**Targets (5, after the step):**
- the peak (A);
- Vo's extreme (mV);
- phase 1's crossing depth (A);
- ln(1 + its periods);
- ln(1 + the time back within 1%, µs, capped at 400).

**Data:**
- 8000 random samples (seed 1), `ml_d63_data.sample`, each run through
  D63; split 6400 / 800 / 800 (train / validation / test).
- Diverged runs (the map unbounded) are kept out of the regression and
  counted.

**Network:**
- 11 → 64 → 64 → 5, tanh, standardised inputs and targets;
- Adam (lr 2·10⁻³), batch 128, L2 10⁻⁵;
- early stopping on validation (patience 40, at most 600 epochs).

## 2. Registered targets

1. **On the held-out test set (D63):**
   - peak: mean absolute error ≤ 5 A and R² ≥ 0.97;
   - Vo extreme: R² ≥ 0.90;
   - phase-1 crossing depth: mean absolute error ≤ 2 A;
   - ln(1 + back): R² ≥ 0.80.
2. **Speed:** at least 1000× faster per query than D63 (batched).
3. **Against the co-simulation:**
   - the 1 MHz transients co-simulated in A115-A117, excluding runaways;
   - the peak after the step;
   - the MLP's mean absolute error ≤ D63's own + 5 A. The surrogate adds
     little to the model error.
4. **A design check:**
   - feasible = every one of 8 standard transients (±62.5 A; ±4.8 V over
     1, 5 and 20 µs) peaks ≤ 200 A, with phase 1 inside D63's refitted
     rule (crossing ≤ 12 A or < 25 periods), and no divergence;
   - on 200 random designs, the MLP's verdict agrees with D63's in
     ≥ 90%.

**What would falsify it as a tool:**
- target 1 or 4 missed;
- the MLP disagreeing with D63 in the transitions that matter. The
  near-200 A edge is reported separately.

## 3. What it is not

- **Not a model of the converter:** it is a model of D63. Its error
  against the co-simulation is at least D63's (peaks ~10%, outcome rule
  refitted).
- **Not valid outside the sampled ranges,** nor at other frequencies or
  L.
