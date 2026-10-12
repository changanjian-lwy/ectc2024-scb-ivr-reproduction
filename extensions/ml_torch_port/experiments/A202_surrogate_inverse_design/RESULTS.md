# A202 - design search by gradients through A120's surrogate, against random search and D63 (RESULTS)
Boundary: 5a3072c. Run from 6b8e719 (the first run, from 5a3072c, stopped while writing the summary: a numpy bool
in the JSON; nothing was printed or read from it; the fix changes types only). Record: a202_summary.json
(a202_inverse.py). torch 2.14.1, float64, CPU. Post hoc items are marked.

## 0. Verdict
- **3 of 4 criteria pass; the one that fails is the finding.** Gradient search through the surrogate is a valid and
  somewhat better search, but the surrogate's optimum is not D63's.
- **The port is exact.** Outputs within 3.6e-15 of numpy; autograd's input gradient within 9.3e-10 of central
  differences.
- **On the surrogate, gradients find more than random draws.**
  - Smallest worst peak: 191.05 A, at the corner of the box (floor rule, pct 5.0, Cs 3.0 uF, fc 80 kHz, floor
    1.0 A). The 100 000 random designs reach 193.67 A.
  - Front of (worst peak, worst |Vo extreme|): hypervolume 298.5 with 13 points against 232.6 with 6.
  - 454 of the 1200 final gradient designs are feasible; 240 of the 100 000 random ones (0.24 %).
- **Post hoc, at equal cost the advantage is smaller.** The gradient searches used 480 000 design evaluations.
  480 000 random designs (seed 2025) reach 192.86 A and hypervolume 280.6: the gradient is ahead by 1.8 A and 6 %.
  In four variables it saves no evaluations.
- **In D63 the surrogate's optimum does not hold.**
  - The 12 best-margin gradient designs are one design (the corner). D63 puts it at 198.8-200.1 A against the
    surrogate's 191.1 A: optimistic by 8.6 A, four times the test MAE (2.04 A). 9 of the 12 count as feasible
    only because they land 0.3-1.2 A under the limit.
  - The random search's 12 best: optimistic by 7.4 A, 2 of 12 feasible in D63.
- **Away from the corner the surrogate errs the other way.** On the gradient front it is pessimistic by up to
  7.6 A. D63's best of the 42 designs checked is 190.1 A (pct 5.84, Cs 3.06 uF, fc 79.8 kHz, floor 3.3 A), which
  the surrogate puts at 196.8 A. Near the feasible corner the surrogate's error (+-7-9 A) exceeds the differences
  the search optimises (2-6 A).
- **Decision (BOUNDARY Section 4).** Gradient search is valid here and not needed at this size; random search
  stays the default for a few variables. A surrogate optimum is never quoted without a D63 re-check. The limit is
  the surrogate's accuracy at the edge of its training box, not the search; the remedy is a refinement loop
  (optimise, run D63, retrain), not run. No design value changes (1 MHz design space, superseded by A124).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | port: outputs within 1e-9, input gradient within 1e-6 of central differences | PASS: 3.6e-15, 9.3e-10 |
| 2 | gradient's best feasible worst peak <= random's + 0.5 A | PASS: 191.05 A against 193.67 A |
| 3 | hypervolume below (200 A, 100 mV) >= 0.98 x random's | PASS: 298.5 against 232.6, ratio 1.283 |
| 4 | gradient's 12 best margins: >= 80 % feasible in D63, surrogate optimistic by <= 4 A | FAIL: 9 of 12 (75 %), +8.6 A |

D63 on the returned designs (D63 - surrogate, mean):

| group | feasible in D63 | worst peak | worst \|Vo extreme\| |
|---|---|---|---|
| random search, 12 best margins | 2 of 12 | +7.4 A | -8.3 mV |
| random search, front | 3 of 6 | +3.8 A | +1.5 mV |
| gradient, 12 best margins (one design) | 9 of 12 | +8.6 A | -6.3 mV |
| gradient, front | 11 of 12 | -1.4 A | -0.5 mV |

Post hoc: the D63 hypervolume of the checked feasible front designs is 484 (gradient, 11 points) against 114
(random, 3 points); the two sets differ in size.

Predictions:
- Criterion 1 at 1e-12 and ~1e-8: held (the gradient closer than predicted).
- Criterion 2, 1-5 A below at the box's corner: held (2.6 A; the corner as predicted).
- Criterion 3, ratio 1.00-1.10: wrong against the 100 000 (1.28); 1.06 at equal cost (post hoc).
- Criterion 4 fails with <= 4 of 12 feasible, worse than the random search's best: the failure and the optimism
  (5-15 A predicted, 8.6 A found) held; the count was wrong (9 of 12 against the random search's 2 of 12). The
  gradient's extra margin on the surrogate absorbs most of the optimism.
- Cost 480 000 against 100 000 evaluations, no saving: held.

## 2. Limits
- **One design, not twelve.** The gradient's best-margin group is the same corner design reached from different
  starts; its "75 % feasible" is one design sitting on the 200 A limit.
- **D63 was run on 42 designs only.** Its own optimum over the box was not searched; 190.1 A is the best of those
  checked.
- **Scope.** D63, not co-simulation; the 1 MHz design space; one optimiser setting and one scalarisation. The
  equal-cost random search and the D63 hypervolume are post hoc.
