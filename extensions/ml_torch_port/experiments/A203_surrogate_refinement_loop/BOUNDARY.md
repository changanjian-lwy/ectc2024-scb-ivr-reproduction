# A203 - the surrogate search closed with D63: a refinement loop, scored against D63's own search (BOUNDARY)
Method: mixed - ML (A202's gradient search through A120's MLP surrogate; the surrogate fine-tuned in PyTorch on new
D63 runs, an active-learning loop) and math (D63, the valley map, on 100 000 random designs as the reference)
Extension ml_torch_port. Written and committed before the loop and the reference ran. Seen before writing: A202's
results (the surrogate's optimum is 198.8-200.1 A in D63, optimistic by 8.6 A; the best of the 42 designs D63
checked there is 190.1 A), D63's speed (8.3 ms per transient), and timing-only smoke runs (2 short rounds; 400
designs).
Decision it changes: whether a surrogate-based design search can be trusted once it is closed with D63 runs - the
method to recommend for later surrogate-based design work - and what it costs against searching D63 directly.
No design value changes (A120's 1 MHz design space, superseded by A124).
Cheaper check done first: A202 (one-shot search and its D63 re-check).
Budget: reference 800 000 D63 transients, ~110 CPU-min, ~25 min on 8 processes; loop 10 rounds, ~3 min.

## 1. What and why
- **Problem found in A202.** An optimiser moves to where the surrogate errs in its favour: at the corner of the
  box the surrogate was 8.6 A optimistic, and D63's best checked design was ranked 5.7 A worse than that corner.
- **Method.** Ten rounds. In each: A202's two gradient searches (margin and front, unchanged) on the current
  surrogate; 16 new designs are picked (the 8 smallest surrogate worst peaks, then 8 spread along the surrogate's
  front; a design within a rounding grid of one already run is skipped); D63 runs them on the 8 standard
  transients; their rows are added to A120's training rows with weight 10; the surrogate is fine-tuned from its
  current weights (Adam, 100 epochs, lr 5e-4, A120's L2 1e-5 and scalers, ml_nn's loss).
- **Reference.** D63 on the 100 000 random designs A120 and A202 searched on the surrogate (seed 2024): D63's
  feasible set and its best worst peak. Random search in D63 at the loop's cost is drawn from that table: 1000
  random subsets of 160 designs (the loop's own D63 runs) and of 1160 (plus A120's 8000 transients).
- **Not tested.** Other loop settings (picks per round, weight, epochs), retraining from scratch, uncertainty-based
  acquisition, more rounds; the front as a criterion (reported only); co-simulation; the 2.5 MHz design. D63's
  true optimum over the box is not known: the reference is the best of 100 000 random designs.

## 2. Criteria
1. **Reaches the reference.** After 10 rounds (160 D63 designs) the loop's best D63-feasible worst peak is <= the
   reference's best + 1.5 A.
2. **Beats random search in D63 at equal cost.** The loop's best is lower than the best of 160 random D63 designs
   in >= 95 % of the 1000 subsets, and lower than the best of 1160 in >= 90 % (a subset without a feasible design
   counts for the loop).
3. **The surrogate stops being optimistic at its optimum.** Over rounds 8-10, the mean of (D63 worst peak -
   surrogate worst peak) on each round's 8 margin picks is within +-4 A (A202: +8.6 A).
4. **No damage elsewhere.** A120's held-out test MAE of the peak stays <= 2.5 A after the last round (2.04 A before).

## 3. Predictions (not criteria)
- Reference: 150-400 of the 100 000 feasible in D63, nearly all with the floor rule; best worst peak 187-190 A.
- A120's surrogate against D63 on the 100 000: of the designs it calls feasible, under half are (precision < 0.5).
- The loop is within 1.5 A of the reference by round 3-5 and ends 0-2 A below it.
- Random D63 search with 160 designs finds a feasible design in about a third of the subsets.
- Margin optimism falls from about +8 A in round 1 to within +-2 A by round 5; the test MAE stays within 0.3 A.

## 4. Decision rule
- Criteria 1 and 2 pass: closing the search with D63 runs is the method to use for surrogate-based design; a
  one-shot surrogate search is not.
- Criterion 1 fails: the loop as specified does not converge; its settings are not tuned under this number, the
  failure is reported and the record shows which rounds stalled.
- Criterion 3 says whether the fine-tuned surrogate itself can be trusted at its optimum (pass) or the loop works
  only because D63 judges every pick (fail).
- Criterion 4 fails: the fine-tuned surrogate is a local model and is not used for statements over the whole box.
