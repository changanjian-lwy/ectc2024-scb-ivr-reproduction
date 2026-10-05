# C14 - D66's sharing cost checked in co-simulation (RESULTS)
Boundary: 545472e. Records: release records-c14 (13 runs, 296 MB). Summary: c14_summary.json (c14_analyze.py).
All runs from committed code (cosim_sources_modified False).

## 0. Verdict
- **D66 holds in steady state:** heavy-module share +7.3 / +7.7 / +14.9 % and steady peak 155.8 / 156.4 / 168.4 A
  for w5 / o10 / w10, all inside D66's bands (at their low end for the share).
- **D66's transient is 2-7 A pessimistic:** post-step peaks 194.4 / 195.4 / 207.9 A against 199-201 / 201-202 /
  210-214 A. Its +45 A increment came from C10 (lo_learn 1024, l_m48_1us 189 A); the frozen design's nominal
  increment is 40.7 A (worst nominal row l_p48_1us 184.7 A; l_m48_1us 182.1 A).
- **Spec:** one module at -10 % (195.4 A) and ±5 % worst case (194.4 A, 5.6 A margin) stay <= 200 A; ±10 % worst
  case reaches 207.9 A. Interpolated, the 200 A crossing is near ±7 % worst case. The summary's "about ±5 %" stands
  (conservative by ~2 points).
- The heavy module (module 2) carries every peak; the others stay at 164-178 A. Controller intact on all 13 runs
  (0 overlaps, 0 new duplicates). Vo is back within 1 % in 3.6-11.7 us on every row but o10 l_p48_1us (40.1 us,
  18 late fires, mostly phase 4; nominal 2): ~35 us after a +4.8 V step the series-capacitor ladder rebalances
  (rail 1 16.9 V at the step, nominal too) and Vo makes a second, positive bump - nominal +6.1 mV, w5 +7.9 mV,
  o10 +12.9 mV (over 1 %). w10 stays inside 1 %, so the bump is not monotone in the spread (one row each).

## 1. Criteria
| # | criterion | w5 | o10 | w10 |
|---|---|---|---|---|
| 1 | integrity (COMPLETED, 0 overlaps, no NEW/FF, Vo back) | PASS | PASS | PASS |
| 2 | n0 share in D66 band ± 1.5 points | +7.3 % PASS | +7.7 % PASS | +14.9 % PASS |
| 3 | n0 steady peak in D66 band ± 4 A | 155.8 A PASS | 156.4 A PASS | 168.4 A PASS |
| 4 | max post-step peak within ± 7 A of D66 | 194.4 A PASS (-4.6..-6.6) | 195.4 A PASS (-5.6..-6.6) | 207.9 A PASS (-2.1..-6.1) |
| 5 | largest spread with every row <= 200 A | yes | yes | no (s_p62 207.9, l_p48_1us 207.8) |

Predictions: D66's numbers (held, transient at the low side); peak on l_m48_1us -> only for o10 (w5: l_p48_1us,
w10: s_p62); module 2 carries it -> held; "none of the spreads stays <= 200 A" -> wrong (w5 and o10 do).

## 2. Limits
- One heavy slave (module 2); a heavy master, ±20 %, and Cs / R spread together with L are not run.
- The ±7 % crossing is a linear interpolation between two spreads, not a measured point.
- Peaks carry A129's step-position noise (2-7 A).
