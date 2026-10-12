# A203 - the surrogate search closed with D63: a refinement loop, scored against D63's own search (RESULTS)
Boundary: c196329. Loop run from c196329. Records: a203_loop.json and a203_surrogate_final.npz (a203_loop.py),
a203_reference.json (a203_d63_reference.py; the per-transient table d63_100k.npz is in release records-a203),
a203_summary.json (a203_analyze.py). Post hoc items are marked.

## 0. Verdict
- **4 of 4 criteria pass.** Closed with D63, the search finds in 160 D63 designs what 100 000 random D63 designs
  find. The reference also shows that A120's surrogate had the feasible region wrong.
- **The loop reaches the reference.** Best D63-feasible worst peak 189.88 A (floor rule, pct 8.75, Cs 3.01 uF,
  fc 79.9 kHz, floor 4.95 A; round 5) against 190.33 A, the best of the 100 000 (pct 5.91, floor 3.78 A). It is
  within 1.5 A from round 3. The 0.45 A difference is inside D63's own roughness (A202: +-0.7 A between
  neighbouring designs), so "matches", not "beats". No design of the 100 000 is at or below 189.88 A; five are
  below 191 A.
- **Against random search in D63 at equal cost.** 160 random D63 designs: median best 196.3 A; 1160 (adding the
  8000 transients behind A120's surrogate): 193.3 A. The loop is better in 1000 of 1000 subsets of either size.
  106 of the loop's 160 designs are feasible in D63 (66 %) against 1.53 % of random designs.
- **The surrogate's optimism at its optimum is gone.** Per round: +9.0, +10.0, +2.1, +2.3, +1.3, +6.9, +2.1, -5.0,
  -2.8, -3.4 A; the last three average -3.7 A (limit +-4 A): it now errs on the safe side, narrowly inside the limit.
  The held-out test MAE went from 2.04 to 1.68 A.
- **But the loop did not make the surrogate right, it made the search right.** The best design was a front pick
  that the surrogate of round 5 put at 198.8 A; D63 found 189.88 A. The surrogate learned that region only after
  D63 had run it. Over the whole box the fine-tuned surrogate is still a poor judge of feasibility (below).
- **New: A120's surrogate had the feasible set wrong in size and shape.** D63 finds 1530 feasible designs among the
  100 000 (1.53 %); the surrogate said 240, of which 95 are (precision 0.40, recall 0.06). On D63's feasible
  designs its worst peak is 7.6 A too high on average - pessimistic there, while optimistic by 8.6 A at its own
  optimum (A202).
  - Floor rule: 1336 feasible, pct 5.4-14.6 (median 9.0), Cs 3.0-7.95 uF. The surrogate's set had pct 5.0-8.3.
  - Timed rule: 194 feasible (pct 5.4-6.2, Cs 3.0-6.1 uF) with a worst |Vo extreme| of 20-31 mV against 48-103 mV
    for the floor rule. The surrogate found one. Comparator rule: none.
  - After the loop: 1954 called feasible, 381 are (precision 0.19, recall 0.25), MAE on D63's feasible 5.0 A.
- **Post hoc, the two-objective front.** In D63 the timed rule dominates the trade-off: 191.8 A with 21 mV. The
  loop's feasible picks reach 76 % of the reference front's hypervolume (555 against 726; 160 random designs:
  median 164) and have the floor branch, but only one timed design (199.6 A).
- **Decision (BOUNDARY Section 4).** A surrogate search closed with D63 runs is the method for surrogate-based
  design; a one-shot surrogate search is not. A surrogate's feasible set is not quoted without D63: A120's
  exploration gets a dated note. No design value changes (1 MHz design space).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | loop's best <= reference best + 1.5 A after 160 D63 designs | PASS: 189.88 A against 190.33 A; within 1.5 A from round 3 |
| 2 | better than 160 random D63 designs in >= 95 % of subsets, than 1160 in >= 90 % | PASS: 100 % and 100 % |
| 3 | margin optimism over rounds 8-10 within +-4 A | PASS: -5.0 / -2.8 / -3.4 A, mean -3.7 A |
| 4 | A120's test MAE of the peak <= 2.5 A after the loop | PASS: 1.68 A (2.04 A before) |

| round | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| D63-feasible picks of 16 | 9 | 1 | 9 | 5 | 9 | 14 | 13 | 15 | 16 | 15 |
| best so far, A | 194.3 | 194.3 | 191.5 | 191.5 | 189.9 | 189.9 | 189.9 | 189.9 | 189.9 | 189.9 |
| margin optimism, A | +9.0 | +10.0 | +2.1 | +2.3 | +1.3 | +6.9 | +2.1 | -5.0 | -2.8 | -3.4 |

Predictions:
- Reference 150-400 feasible, nearly all floor, best 187-190 A: wrong on the count (1530, 194 of them timed); the
  best is 190.33 A. I had taken the surrogate's 0.24 % as D63's share.
- A120's surrogate precision below 0.5: held (0.40). Its recall of 0.06 was not anticipated.
- Within 1.5 A by round 3-5, ending 0-2 A below the reference: held (round 3; 0.45 A).
- 160 random D63 designs find a feasible one in about a third of the subsets: wrong (91 %), for the same reason.
- Optimism within +-2 A by round 5: held at round 5 (+1.3 A), then it swung (+6.9, -5.0). Test MAE within 0.3 A:
  it improved by 0.36 A.

## 2. Limits
- **The reference is a random search, not D63's optimum.** Both bests sit at box bounds (Cs 3 uF, fc 80 kHz), so the
  true optimum of the box may be lower still.
- **One run of the loop, one setting.** Picks per round, weight, epochs and learning rate were fixed beforehand and
  not varied; the best design came from the front half of the picks, so a margin-only loop might not have found it.
- **Cost accounting.** The loop starts from A120's surrogate (8000 D63 transients). D63 itself is cheap (8 ms per
  transient), so here the reference was affordable (33 min on 8 processes); the method matters where it is not.
- **Scope.** D63, not co-simulation; the 1 MHz design space; the 8 standard transients.
