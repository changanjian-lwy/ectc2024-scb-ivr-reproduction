# A137 - restart the feed-forward's low-passes at mode P's entry (BOUNDARY)
Track A, single module, A136's adopted cap. Written and committed before the runs. Looked at beforehand: A136's records.
Decision it changes: whether cfg vff "seed" joins the adopted setting (rel_q8 320, rel_lp 1), removing A136's start-up
regression. Cheaper check done first: the formula and two unit tests (D63 has no mode-S handover of the feed-forward).
Budget: 18 runs + 1 identity, two batches, ~15 min.

## 1. What and why
- A136: in operation the new cap is right at L x 0.7-1.3, but the handover got worse: m3n's late fires 107-173 at
  L x >= 1.0 (A129 5), start-up peaks 185-218 A (g125 184 A), none of it inside the recorded window (from 220-442 us).
- Mechanism (formula): Vin ramps 0 -> 48 V in 137 us; scb_vff samples it in mode S too, so at the 144 us handover lp20
  trails Vin by ~10 V. The cap's rail model (rail 1 = Vin - 3/4 lp20 - Vo) then reads ~19 V while mode S has kept the
  ladder near 12 V, and the relative cap holds phase 1 near half its Ton for tens of us.
- Fix: cfg vff "seed" 1 (scb_vff: the first Vin sample after en rises restarts lp2, lp20, tlp and the prediction from
  itself, as the very first sample does; a rise without a sample waits for the next one). At mode P's entry the cap
  then reads rail = rss, i.e. 1.25 ton (the absolute cap would read k / (Vin/4 - Vo) = 48 ns), and acts only on what
  Vin does in mode P. seed 0 is A136's path; scb_ctrl cfg_vff_seed, bridge, scb_multi regenerated; unit tests 78
  (2 new: a ramp with the feed-forward off, then en rises - seed 1 leaves 133 LSB, seed 0 caps phase 1).
- Rows: m3n, m1n (the handover's worst), n0, l_p48_1us, l_p48_5us, s_p62 at L x 0.7 / 1.0 / 1.3 (arm s = A136's q +
  seed 1; steps at 1000 us). References: A136's q runs, A129's g125 (L0, absolute cap).
- Not tested: the matrix's other rows, the four-module design (C08 runs A136's version; rerun if this is adopted).

## 2. Criteria (A136's statistics, a135_analyze.stats)
1. Identity: A136's q100_m3n rerun (seed absent) bit-identical; unit tests 78/78.
2. Handover: m3n and m1n late fires <= 100 at every L and below A136's same row; every run's start-up peak (whole run
   when before the step) <= A136's same row, and <= 200 A at L0.
3. Operating mode unchanged: post-step peaks within 7 A of A136's same rows; no lock (A135's rule) on any run.

## 3. Predictions
- m3n late fires near A129's (5) at L0 and far below A136's elsewhere; start-up peaks back near g125's 184 A at L0.
- Step rows within the 2-7 A noise floor of A136's.

## 4. Decision rule
- 1-3 pass: the adopted setting becomes vff rel_q8 320, rel_lp 1, seed 1; C08's rows are rerun with it (C09).
- 2 fails: the handover regression has another cause; trace a handover (debug_edges_us over 140-300 us) before any
  further change; A136's setting stays adopted for the operating mode with the regression open.
- 3 fails: seed changes more than the start-up; not adopted.
