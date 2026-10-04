# A132 - negative-current target self-tuning (RESULTS)
Boundary: 4a9e706. Records: cosim/run_*.json (64, code 4a9e706, sources unmodified), identity reruns in tmp/;
a132_summary.json (a132_analyze.py). Every run: A129's g125 design (A124 + gated Vin feed-forward), 48 V, 250 W,
corner = (k_C Coss scale, k_L), steps at 800 µs (c0.7_l1.3: 1600 µs); "on" = cfg dep (V_set 3.9 V, wsh 5, smax 4).
## 0. Verdict
- **The loop works where the plant is quasi-steady.** c1.3_l0.7 (C +30%, L −30%): dep +22.5 codes (D57: 22.7), depth
  21.3 A, phase-1 V_on 5.78 → 3.87 V, efficiency 89.47 → 89.83% (+0.36 points, predicted +0.37). Nominal n0 and matrix:
  V_on within 0.06 V, peaks within 0.5 A, dep ±2 codes. No step moved it for 55-73 µs (every transient window discarded).
- **Not adopted as built.** At c1.3_l0.7 the deeper target costs +5.3 A of steady peak (145.0 → 150.3 A) and +11-12 A
  on the +4.8 V rows: 196/194 → 207/206 A (> 200 A; the off arm passes). dep was unchanged at the peak, so this is the
  static depth, not line tracking - the loop's own failure under the decision rule.
- **The worst-margin corner could not test the loop.** c0.7_l1.3 (C −30%, L +30%) settles into a ladder limit cycle
  that does not depend on the depth: rails 13.6 / 11.5 / 11.5 / 11.4 V from 1200 µs on, phases 2-4 valleys −24 A with
  V_DS −0.4 to −1.2 V (valley gone), Vo ±6 mV, 167-1000 late fires per run, +4.8 V peaks 251/252 A. On = off bit for
  bit: no window is quasi-steady, as designed. Pilots: L +30% alone starts the same way, C −30% alone does not, so
  **the adopted design does not tolerate L +30%** (new open item, independent of A132).
- Nominal "inert" misses are mostly the criterion's: after a line step the loop re-tunes to the new rail (V_on 3.9 V
  instead of 5.0 / 2.1 V; the criterion compared it with the off arm's operating point). +4.8 V / 1 µs: 181.5 →
  186.8 A with dep 0 at the peak, inside A129's 2-7 A peak noise floor. j100 / s_p62: dep 5 / 3 codes.
- D57 scaling holds in cosim: c1.3_l0.7 off V_on 5.78 / 5.42 V (predicted 5.81 / 5.07), on depth 21.3 A (21.3).
## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | identity (A129 l_p48_1us, n0) | pass: sections, turn-ons, low-offs, high-offs identical |
| 2 | convergence | 2/3: nom +0.5 codes, c1.3_l0.7 +22.5 (V_on 3.87 V); c0.7_l1.3 0 (never quasi-steady) |
| 3 | valley kept | 2/3: c0.7_l1.3 phases 2-4 V_on −0.36 / −1.15 / −0.30 V (limit cycle, on = off) |
| 4 | matrix, on | 14/24: nom 8/8; c1.3_l0.7 6/8 (m1n 202.5, m3n 211.7 A are mode-S start-up peaks before the loop can act; steady 150 A); c0.7_l1.3 0/8 (late fires > 100) |
| 5 | step rows, on | 12/21: nom 7/7; c1.3_l0.7 5/7 (+4.8 V rows 207 / 206 A); c0.7_l1.3 0/7 (late fires 167-847, A124's runaway rule) |
| 6 | inert at nominal | 9/16: 5 line rows (re-tuned operating point), s_p62 (dep 3), j100 (dep 5) |
| 7 | efficiency | 2/2: c1.3_l0.7 +0.36 points; c0.7_l1.3 0.00 (loop idle) |
## 2. Limits
- One module, uniform Coss scale, two extreme corners; the loop's margin side (shallower target) is untested in cosim
  because c0.7_l1.3 is dominated by the L +30% limit cycle.
- Efficiency: D62 middle with copper at the nominal L; start-up peaks at c1.3_l0.7 come from mode S (L −30%).
- Criterion 6 was written for a fixed operating point; it should have excluded the post-line-step state.
