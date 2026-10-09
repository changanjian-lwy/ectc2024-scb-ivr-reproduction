# A185 - A184 with a bumpless loop seed (RESULTS)
Boundary: 0c447a5. Records: release records-a185 (11 runs, log). Analysis: a185_analyze.py -> a185_summary.json. All runs
from committed code (e1cf0a7), plant V5, t_il 1.0 ns.

## 0. Verdict
- **FAIL as registered on c6 at 3 of 8 25 C runs** (N0 0.991 V, F0 0.993 V, four modules 0.989 V, against references
  0.998-0.999 V less 5 mV), each by 1-4 mV. g0 (mode S = A184 bit for bit) and c1-c5 pass everywhere: start-up
  <= 144.6 A, handover <= 173.2 A, post-step <= 193.8 A, V_DS <= 33.6 V, mode P within 1.42 A of the t0 = 400 records.
- **The seed does what the formula says.** The loop's first Ton lands on its steady value (N0 32.4 vs 32.3 ns, N13
  43.2 vs 43.3, N75 23.3 vs 23.2). Handover minima move up:
  - N13: 0.971 -> 1.000 V; N0: 0.984 -> 0.991 V; F0: 0.987 -> 0.993 V; four modules: 0.982 -> 0.989 V;
  - N0 at 125 C: 0.989 -> 1.000 V.
  - S75, S0, N75, N07 stay at 0.996-1.000 V.
- **What remains at L0 is the period jump, not the seed.** Mode S runs at 200 ns, and mode P's own period at L0 is
  ~520 ns. Phases 2-4 take their slots first from the configured k t0 / 4 (50 ns steps), then from period estimates
  that climb 200 -> 370 -> 458 -> 521 ns. Over those periods phase 4's valley swings to -71 A (N0; N13 -69, N75 -43),
  so the output charge falls short for ~2 us. At L x 0.75-0.7 the jump is smaller (200 -> 363 ns) and the dip
  vanishes.
- **Worst case across boards improves.** At 25 C the lowest handover minimum is 0.989 V (four modules); at 400 ns it
  was 0.961 V (S75), 0.983 V (S0) and 0.984 V (N13). The miss is only against the per-board "no worse" criterion on
  the L0 nominal / ff boards (0.998-0.999 V before).
- **Hot (diagnostic):** S75 0.977 V, S0 0.991 V (reference 0.991 V). Mode-S Vo is still 1.126-1.129 V at entry, so kp
  clamps Ton. A seed calibrated at 25 C cannot fix this (A186: Vo-requested handover). S75 125 C post-step 193.8 A
  (step phase moved).

## 1. Criteria (25 C; hot c6 diagnostic)
| run | g0 | c1 start / hand | c2 post | c3 V_DS | c4 | c5 dev | c6 Vo min (ref) |
|---|---|---|---|---|---|---|---|
| S75 / S0 / N75 / N07 / N13 | = | <= 139.9 / <= 164.6 | S75 191.9 | <= 33.1 | 1.032-1.035 | <= 1.42 | 1.000 / 0.996 / 1.000 / 1.000 / 1.000 |
| N0 | = | 124.7 / 165.4 | 182.8 | 33.6 | 1.033 | 0.35 | **0.991** (0.999) |
| F0 | = | 125.0 / 166.4 | - | 32.3 | 1.033 | 0.09 | **0.993** (0.998) |
| four modules | = | 124.7 / <= 173.2 | - | <= 30.5 | 1.033 | <= 0.46 | **0.989** (0.998) |
| N0 / S0 / S75 125 C | = | <= 144.6 / <= 147.4 | S75 193.8 | <= 31.8 | 1.048-1.129 | <= 0.30 | 1.000 / 0.991 / 0.977 (diag.) |

## 2. Predictions
- First Ton within +-1 ns of T_ss: right (+0.1 ns).
- 25 C minima >= 0.995 V everywhere: wrong at L0 (0.989-0.993). The prediction treated the dip as the seed's
  alone; the L0 period jump (200 -> ~520 ns) is a second cause.
- Hot minima as in A184: right for S75 (0.977 vs 0.975). S0 improved (0.978 -> 0.991) and N0 more (0.989 -> 1.000):
  their 25 C seeds happen to sit nearer their hot steady Ton.

## 3. Limits
- The seed is in-sample: T_ss and Vo_entry come from the same board's 25 C run (A184).
- One row (+4.8 V / 1 us) on S75 / N0. Four modules only nominal.

## 4. Decision (BOUNDARY Section 4)
c6 still fails at 25 C on the L0 boards, so this is not adopted on its own. The seed is kept (it removes the seed
part of the dip: N13, N0 hot). The remaining 25 C dip is the mode-S to mode-P period jump. The hot dip is the
mode-S drift, which A186 tests with a Vo-requested handover. The period jump would need the configured slots to
follow mode P's period at entry, not t0. That is the same coupling as cfg_ton (cfg_slot = k t0 / N), and it is
named, not run.
