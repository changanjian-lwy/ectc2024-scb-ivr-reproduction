# A202 - design search by gradients through A120's surrogate, against random search and D63 (BOUNDARY)
Method: ML (deep learning: backpropagation to the inputs of A120's MLP surrogate; multi-start Adam on a
box-constrained design, a smoothed Chebyshev scalarisation for two objectives) checked against exhaustive random
search on the same surrogate and against the math model D63
Extension ml_torch_port. Written and committed before the searches ran. Seen before writing: A120's results and its
exploration (240 of 100 000 random designs feasible on the surrogate, 239 of them with the floor rule; D63 found
only 3 of the surrogate's 15 best designs and 6 of its 15 borderline designs feasible), the targets' scales and test
errors (peak MAE 2.04 A, Vo extreme 4.0 mV), and a timing-only smoke run (short searches, no objective printed).
Decision it changes: the search method for any later surrogate-based design work (random search, or gradients
through the surrogate), and whether a surrogate's optimum may be quoted without a D63 re-check. No design value
changes: A120's design space is the 1 MHz one, superseded by the 2.5 MHz design (D64, A124).
Cheaper check done first: A120's own exploration (random search, 3 s). The port of the surrogate is checked inside
this experiment (criterion 1).
Budget: about 2 min (100 000 x 8 surrogate predictions, 2400 optimiser steps, ~400 D63 transients at 6.5 ms).

## 1. What and why
- **Problem.** A120 searched its surrogate by drawing 100 000 random designs. With PyTorch the surrogate's gradient
  with respect to its inputs is available, so a design can be improved directly ("inverse design": from the wanted
  response back to the design). Two things are not known: whether that finds what the exhaustive search finds,
  and whether designs pushed to the surrogate's optimum hold in the model the surrogate was trained on.
- **Design and objectives.** Design = (pct 5-15, Cs 3-20 uF, fc 20-80 kHz, rule cmp / timed / floor, floor 1-5 A),
  A120's sampling box. On the 8 standard transients (+-62.5 A; +-4.8 V over 1, 5, 20 us): f1 = the worst peak (A),
  f2 = the worst |Vo extreme| (mV). Feasible = A120's rule (every peak <= 200 A, phase 1 inside D63's refitted rule).
- **Method.** Per rule, Adam (lr 0.05, 400 steps) on a sigmoid-boxed design from random starts, with smooth
  maxima over the transients (temperature 2 A / 2 mV) and a smooth penalty for the phase-1 rule.
  - Margin: minimise f1, 64 starts per rule.
  - Front: a smoothed Chebyshev scalarisation of (f1, f2) at 21 weights x 16 starts per rule.
  - Every final design is then judged with the hard objectives and A120's verdict on the surrogate.
- **References.** The same surrogate on A120's 100 000 random designs (its seed, 2024): the best feasible f1 and
  the non-dominated set. D63 on the designs both searches return (12 best margins and up to 12 front designs each).
- **Not tested.** Co-simulation; a refinement loop (optimise, run D63, retrain); other optimisers or
  scalarisations; more than two objectives; the 2.5 MHz design.

## 2. Criteria
1. **Port.** The surrogate in PyTorch gives numpy's outputs within 1e-9 on 800 rows; autograd's input gradient is
   within 1e-6 relative of central differences (step 1e-5).
2. **Margin.** The gradient search's best feasible f1 is <= the random search's best feasible f1 + 0.5 A.
3. **Front.** The hypervolume of the gradient designs' feasible non-dominated set below (200 A, 100 mV) is >= 0.98 x
   that of the 100 000 random designs.
4. **In D63.** Of the gradient search's 12 best-margin designs, >= 80 % are feasible in D63 and the mean of
   (D63's worst peak - the surrogate's) is <= 4 A (twice the test MAE).

## 3. Predictions (not criteria)
- Criterion 1: 1e-12 and ~1e-8. Criteria 2 and 3: pass; the gradient's best f1 is 1-5 A below the random search's
  (it runs into the box's corner: pct 5, Cs 3 uF, fc 80 kHz, floor rule), hypervolume ratio 1.00-1.10.
- Criterion 4: fails. <= 4 of 12 feasible in D63, the surrogate optimistic by 5-15 A; worse than the random
  search's 12 best, because the optimiser moves to where the surrogate errs in its favour.
- Cost: 480 000 design evaluations for the gradient searches against 100 000 for the random search: no saving in a
  box of four variables.

## 4. Decision rule
- Criterion 1 fails: stop; the port is wrong.
- Criteria 2 and 3 pass: gradient search through the surrogate is a valid search here, without an advantage in four
  variables (evaluations are free and it needs more of them); random search stays the default at this size, and
  gradients are the tool for design spaces too large to sample. Either fails: multi-start scalarised gradient
  search misses part of the feasible set and is not used alone.
- Criterion 4 passes: a surrogate optimum may be quoted with the surrogate's test error. Fails: a surrogate
  optimum is never quoted without a D63 re-check, and the remedy is a refinement loop, which is not run here.
