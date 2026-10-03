# A120 - a deep-learning surrogate of D63 (RESULTS)

Extension `ml_design_assist`.

**Boundary:** `BOUNDARY.md`, committed (3be1d7d) before any training.

**Records:**
- `a120_dataset.npz` (8000 D63 runs, seed 1);
- `a120_mlp.npz` (the network and its scalers);
- `a120_summary.json` (`run_a120.py`);
- `a120_explore.json` (`explore_a120.py`, after the registered checks).

**Model:** an MLP (11 → 64 → 64 → 5, tanh), numpy, Adam; early stopping
at epoch 332.

## 0. Verdict

1. **Every registered target is met.**

   | target | registered | result |
   |---|---|---|
   | peak, held-out D63 test (800) | MAE ≤ 5 A, R² ≥ 0.97 | **2.04 A, 0.985** |
   | Vo extreme | R² ≥ 0.90 | 0.948 (MAE 4.0 mV) |
   | phase-1 crossing depth | MAE ≤ 2 A | 0.68 A (R² 0.994) |
   | ln(1 + time back) | R² ≥ 0.80 | 0.927 |
   | speed | ≥ 1000× D63 | **11 087×** (0.59 µs against 6.5 ms per transient) |
   | co-simulation, 25 non-runaway 1 MHz transients | MLP's peak MAE ≤ D63's + 5 A | **MLP 8.7 A, D63 9.2 A** |
   | design verdict, 200 random designs | agree ≥ 90% | **98.5%**; all 3 disagreements within 10 A of 200 A |

   - **22 of 8000 samples diverged in D63** (0.3%). They were kept out of
     the regression.
   - **Where D63 diverges in two co-simulated rows** (3 µF comparator,
     fast steps), the MLP gives 249 and 197 A. The co-simulation gave 282
     and 208 A. That is interpolation from neighbouring designs, not a
     property the network learned; it is noted, not claimed.
2. **The surrogate makes the design space searchable** (exploration,
   after the registered checks).
   - **Search:** 100 000 random designs × 8 standard transients in 3 s.
     - The transients: ±62.5 A; ±4.8 V over 1, 5 and 20 µs.
     - Feasible means every peak ≤ 200 A and phase 1 inside D63's
       refitted crossing rule.
   - **With the 1 µs line steps, 0.24% are feasible:** 239 with the
     floor rule, 1 timed, none with the comparator. They have Cs
     3-4 µF, pct 5-8% and fc 48-80 kHz.
   - **With the bus slew ≥ 5 µs, 21%:**

     | rule | Cs 3-5 µF | 5-8 | 8-12 | 12-20 |
     |---|---|---|---|---|
     | floor | 94% | 69% | 42% | 12% |
     | timed | 14% | 13% | 6% | 1% |
     | comparator | 0% | 0% | 0% | 0% |

     - Floor by pct: 63% (5-8%), 60% (8-11%), 44% (11-15%).
     - Timed: only at 5-8% (28%).
     - The comparator fails the rising line steps everywhere (A116,
       A117).
3. **Optimising on a surrogate selects its errors.**
   - **The 15 designs with the surrogate's largest margin:** MLP 195.4 A
     worst peak against D63 202.1 A. Only 3 of 15 are D63-feasible.
   - **15 borderline designs:** 6 of 15 feasible.
   - **Why:** picking the minimum of predictions picks the ones the
     network underestimates. Its 2 A test error becomes a ~7 A bias at
     the optimum.
   - **Rule for every later use:** a surrogate's choice is re-checked by
     D63, and then by the co-simulation.

## 1. What it means for the design (feeds `reports/TRADEOFF_SCORECARD.md` and A118)

- **The 1 µs line step is the binding constraint at 1 MHz.** Even the
  best designs sit at ~200 A (D63: 194-206 A).
- **With a bus slew ≥ 5 µs** (typical with the bulk capacitance a 48 V
  bus has):
  - the floor rule with Cs ≲ 8 µF is feasible in most of its range,
    including the 10% target;
  - the comparator never is;
  - the timed rule only at low pct.
- **Cs 3 µF's handover oscillates in the co-simulation** (A117, not seen
  by D63). So the candidate for A118 is the floor rule at Cs ~5-8 µF,
  pct 10%, fc 60-75 kHz, floor ~2 A.

## 2. Limits

- **A model of D63, not of the converter:** its error against the
  co-simulation is D63's (peaks ~10%), and D63's blind spots carry over.
- **1 MHz, 7.333 nH only;** inside the sampled ranges.
- **The crossing rule in the feasibility check** is D63's refit, not yet
  tested on new runs.
