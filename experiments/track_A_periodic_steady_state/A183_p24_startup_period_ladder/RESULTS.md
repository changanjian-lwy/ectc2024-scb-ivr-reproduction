# A183 - the open-loop start-up period against the series-capacitor ladder split (RESULTS)
Boundary: 0804c0d (extra pairs 6b50ef6; stage-2 code and trims bbd5410, cfgs b637784). Records: release records-a183
(16 screen start-ups, 18 trim start-ups, 10 stage-2 runs, logs). Analysis: a183_analyze.py -> a183_screen.json,
a183_pick.json, a183_summary.json. All runs from committed code, plant V5, t_il 1.0 ns, RTL unchanged.

## 0. Verdict
- **FAIL as registered on c5 at one run** (S75 at 125 C: 2.59 A over 250-300 us against the 25 C record listed in
  the BOUNDARY). The t0 = 400 ns records were still settling in that window: at 400-495 us every full run is within
  1.4 A of its own t0 = 400 record (S75 25 C 0.15 A, N0 0.00 A, S75 125 C against A181's 125 C run 1.38 A). c1-c4
  pass on all 10 runs.
- **Mechanism confirmed.** In mode S, valleys are not regulated. When they straddle the turn-on thresholds, some
  phases turn on hard and lose on-time on slow gates while others get ZVS, and the ladder splits. At t0 200 ns every
  valley is positive (+24..+45 A), every turn-on is hard, and every board's ladder max/min is 1.006-1.028 (S75 at
  400 ns: 1.80).
- **A181's failure is removed at t0 200 ns.** S75 at 25 C: start-up 135.7 A (was 202.1), handover 151.0 A (was
  278.4), post-step 190.3-192.1 A at three positions. At 125 C with the 25 C trim locked: 144.6 / 143.8 / 194.0 A.
  The six other boards: start-up 116.5-139.9 A, handover 139.5-177.2 A, before the step <= 151.4 A. V_DS <= 33.8 V,
  0 shoot-throughs and overlaps, all COMPLETED.
- **Not adopted.** The start-up trim ton_ns also sets three things in mode P: the loop integrator's reset value,
  scb_vff's seed (C10 tpre = mode S's Ton) and the 0.5x / 2x Ton clamps. At 200 ns the trim is 0.55-1.1x the loop's
  steady Ton:
  - N13: steady 43.3 ns = 1.83x its 23.645 ns trim, against a 2x clamp (at 400 ns: 1.06x). A -8 V step needs
    ~1.2x, so the clamp binds (calculation, not run).
  - Handover Vo dips to 0.954 / 0.969 / 0.969 V on N13 / N0 / F0 (at 400 ns: 0.984-0.999) while Ton climbs
    1.55-1.84x.
  - The locked trim moves S75's Vo(143.5 us) by +95 mV hot (1.034 -> 1.129 V; +37 mV at 400 ns). That is inside
    0.99-1.17 V but 41 mV from its top: every turn-on is hard, so the gates' temperature acts on every phase.
- **Stage 1:** 200 passes (worst 168.1 A). 300 passes (196.0 A; phase 4 alone ZVS, ladder 1.52-1.84). 250 fails S2
  at its lower bracket run (Vo 0.965 V -> 211 A). 500 fails (phase 1 alone hard; start-up 238-242 A). Below Vo
  ~0.92 V every t0 runs away at the handover (305-379 A, A163's cliff).
- **Trims at 200 ns:** nominal boards 23.645-23.679 ns at L x 0.7-1.3 (L-independent once every turn-on is hard,
  as the volt-second balance says), S0 35.795 ns, S75 35.451 ns, F0 21.334 ns.

## 1. Criteria
| run | c1 start / hand (A) | c2 post (A) | c3 V_DS, shoot | c4 Vo(143.5) | c5 dev 250-300 us |
|---|---|---|---|---|---|
| S75 25 C p0 / p1 / p2 | PASS 135.7 / 151.0 | PASS 191.0 / 190.3 / 192.1 | PASS <= 31.3 V, 0 | - | PASS 1.46 |
| S75 125 C p0 | PASS 144.6 / 143.8 | PASS 194.0 | PASS 31.3 V, 0 | PASS 1.129 | **FAIL 2.59** |
| N0 25 C p0 | PASS 124.7 / 159.2 | PASS 184.7 | PASS 33.8 V, 0 | - | PASS 0.07 |
| S0 / N75 / N07 / N13 / F0 (to 300 us) | PASS <= 139.9 / <= 177.2 | - | PASS <= 33.2 V, 0 | - | PASS <= 1.57 |

## 2. Predictions
- Mean mode-S valleys: predicted +31 / +20 / +10 / -34 A at 200 / 250 / 300 / 500 ns; measured +23..+37,
  +15..+28, (+22, +20, +16, -19), (+7, -43, -48, -50). The 500 ns "all ZVS" was wrong. Phase 1's node carries the
  most capacitance (2 + 3 devices plus the next phase's 2), so it is the last phase to reach ZVS, as phase 4 is the
  first.
- Expected t0* 200 or 250: 200. Stage-2 risk named in the BOUNDARY (the seed and the clamps): confirmed.

## 3. Limits
- One row (+4.8 V / 1 us) on S75 and N0. Five boards only to 300 us. Four modules not run (stage 3 not reached).
- The N13 clamp binding is a calculation (1.2 x 43.3 = 52 ns > 47.3 ns), not a run.
- c5's window assumed settling by 250 us (true for N0, not for the S75 references, which settle by ~400 us).

## 4. Decision (BOUNDARY Section 4)
No branch applies literally: c5 fails on S75 itself, through its window. t0 200 ns is not adopted and FINAL_SPEC is
unchanged. The fix works on its own. Adopting it needs mode S's Ton separated from the loop's integrator seed,
vff seed and clamps. That is either one RTL register (a mode-S Ton; default = ton_ns, bit-identical) or, without an
RTL change, clamps set by config while the two seeds stay at the start-up trim. The choice is the user's.
