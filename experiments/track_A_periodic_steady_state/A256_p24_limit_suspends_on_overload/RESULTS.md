# A256 - the peak limit suspends itself after a run of limited pulses (RESULTS)
Boundary: ae301d3 (bridge f9369fe). Plant V7, one module except m4_s_p250 (four). Records: cosim/run_s_*.json, 11 runs
from ae301d3 (cosim_sources_modified False; release records-a256). Analysis: a256_analyze.py -> a256_summary.json.
Figure: a256_figure.py -> a256_limit_suspends.png.

## 0. Verdict
- **The suspension removes the ladder collapse on every overload row.** n_susp 6 suspends 2.0-2.9 us after the first
  fire. After that, each row runs as the final configuration (limit 110 A, +62.5 A step = 125 % load):

  | row | fires | suspended | peak (final config) | ladder dev (final config) | Vo extreme (final config) |
  |---|---|---|---|---|---|
  | k_N0 | 10 | 517.35 us | 181.3 (181.2) A | 0.40 (0.40) V | -12.8 (-12.8) mV |
  | m4_s_p250 | 28 | 416.60 us | 181.4 (181.3) A | 0.40 (0.40) V | -12.9 (-12.9) mV |
  | o125_N75 | 23 | 511.58 us | 182.1 (182.0) A | 0.36 (0.35) V | -10.0 (-10.0) mV |
  | o125_S75h | 26 | 505.50 us | 185.4 (185.6) A | 0.34 (0.35) V | -11.8 (-11.5) mV |

  With the limit alone (A254 / A255), the same rows had Vo 757 / 731 / 637 mV and ladders off by 12-14 V.
- **The 1 MHz rows keep A254's result (s1, s4):** N75 193.2 A and S75h 182.7 A, below 200 A. The three identity rows equal
  A254's records; the count stays at most 2 there.
- **s2 fails as registered, on o125_S75h's NEW clause only.**
  - The suspension's hand-back makes 2 spike hits on phase 2: 174.6 A at 505.92 us and 172.8 A at 506.76 us. They are
    14.0 / 12.1 A above both neighbours, 5.9-6.8 us after the step. A142's K4 window ends 1 us after the step, so the
    oracle counts them as NEW.
  - Mechanism (sections' ton_lsb): while the limit cuts, the loop's Ton rises 34-38 LSB above the final configuration's
    (1.1 ns; 505.8 us: 1242 vs 1208). So the first uncut pulse of each phase is +11-14 A. The rows then alternate for
    3-4 periods and settle; Ton is back at 506.6 us.
  - The kick's excess on the other rows: N75 8.3 A, k_S75h 4.6 A, N0 0.5-2.9 A. All stay below their rows' peaks and
    200 A.
- **s3 fails as registered, on a_S75h_d20's ladder by 7 mV.** It reaches 3.525 V against 3.518 V (final configuration
  3.318 + 0.2) at a single section, 154.53 us. That is 1.1 us after the +4.8 V / 1 us step and before the count reaches 6
  (159.2 us). The cause is the limit's two phase-1 cuts; A254's arm l has the same 3.525 V. The row's peak falls 6.8 A,
  from 207.8 to 201.0 A.
- **On the item-2 rows the suspension hands the limit's gain back.** Their counts reach 6, so the limit suspends for
  19.5-31.6 us, and their peaks return to the final configuration's:
  - a_S75h_d2: 211.8 A; final configuration 211.2 A, limit alone 200.8 A;
  - a_S75h_d20: 201.0 A; final configuration 207.8 A, limit alone 197.1 A.

  Item 2 stays as it was, as predicted.
- Cost summary:
  - with n_susp 6 the limit fixes the 1 MHz rows;
  - it keeps every 125 % row as the final configuration, plus one hand-back kick (at most +14 A, below the row's peak);
  - it adds 0.2 V for one section on one item-2 row.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| s0 | tests 724, regression quick + full | pass (tmp/logs/a256_tests / _reg_quick / _reg_full.log) |
| s1 | identity rows equal A254 | pass, 3/3 |
| s2 | overload rows vs final configuration (A253 o3 + ladder) | **fail**: 3/4; o125_S75h NEW 2 vs 0 (hand-back spikes); peak, Vo and ladder pass |
| s3 | item-2 and line rows, same test | **fail**: 3/4; a_S75h_d20 ladder 3.525 vs 3.518 V (one section, from the limit, not the suspension) |
| s4 | 1 MHz rows: A240 q1 + q2 | pass: 193.2 / 182.7 A |

## 2. Predictions
- Held:
  - suspended 2.0-2.9 us after the first fire, before the ladder moves;
  - k_N0 at 181.3 A with rails within 0.40 V;
  - s1 and s4 as predicted.
- Partly held: the item-2 rows are within 2 A of the final configuration, except a_S75h_d20 at -6.8 A.
- Not predicted: the hand-back kick.

## 3. Limits
- n_susp 6 only, at 125 % load. No real fault was run: a short circuit needs a total over-current trip with hiccup and
  pre-charged restart (TPS54A20), which this plant does not model.
- The suspension stays on for as long as the overload lasts (the four 125 % rows end suspended). Re-arming was seen on
  the four item-2 and line rows, 19.5-31.6 us after suspension, with no fire after it. A re-arm under a load that is
  still high was not run.

## 4. Decision
- **ADOPTED by user decision on 2026-10-27, with the costs above recorded.** The final configuration is now A244 cfg_w +
  rev_n 16 + hold_floor_ns 3.0 + ocp {i_a 110 / 125 / 140 A on 2.2 / 2.933 / 3.813 nH (A254's level), t_ns 1.0,
  n_susp 6}. Item 10 is closed at 1 MHz.
- Stated limits:
  - plant V7;
  - tested at 110 A on 2.2 nH and 125 A on 2.933 nH; the 140 A level on 3.813 nH (N13) is A254's formula, run afterwards by A257
    (it holds);
  - one module, plus m4_s_p250 on four modules;
  - 125 % load only;
  - no fault path modelled;
  - the hand-back kick (at most +14 A) and a_S75h_d20's single section +0.2 V are recorded costs. The oracle's classes
    are unchanged, so they still count as NEW / misses.
