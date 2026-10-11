# A195 - the slow corner's two-cycle orbit: what sustains it (RESULTS)
Boundary: d38a4d2. Records: release records-a195 (5 runs, logs). Analysis: a195_analyze.py -> a195_summary.json
(the 22 earlier records: a195_records.json). Code d38a4d2, plant V5, t_il 1.0 ns, the A188 start-up, lead 9.5 ns,
25 C, no event before 330 us. Window 290-330 us. cosim_sources_modified False on all five.

## 0. Verdict
- **The orbit is the high-side turn-on corrector hunting, and a register setting removes it on S0.** With the early
  step at 0.0625 ns (from 0.2828) and the late gain at 1/4 (err_shift 2, from 1), the valley's mean cycle-to-cycle
  change on board S0 is 0.28-0.85 A per phase (reference 4.1-4.8 A; nominal boards <= 0.9 A). c1 and c2 pass.
- **Neither register does it alone.** Step only: 1.8-2.1 A on S0 and 1.1-1.4 A on S75 (reference 5.3-6.2 A).
  Gain only: 3.2-4.8 A. Target 375 ps: 4.4-5.3 A, slightly worse.
- **The registered reading was wrong in one point.** Section 4 took the measured map slope near -1.1 as a property
  the corrector cannot change. The plant does amplify the corrector's step (a 0.28 ns step is worth about 1.4 A by
  itself, the orbit is 4-5 A), but the loop that closes the orbit runs through the corrector's late branch, and
  halving that gain together with the step opens it. Predictions held for step4 on S0, shift2 and tgt4.
- **What the setting gives in steady state is small: the largest steady peak falls by 0.9 A** (148.5 against
  149.4 A on S0). The valleys' range falls from 6.0-6.7 to 2.0-2.4 A, but their mean is 1.1-1.2 A deeper
  (-15.0..-16.5 A), which takes back part of the gain.
- **Outside the criteria, the run before the window changes** (whole run to 330 us, S0):
  - Handover peak 170.1 A against 164.1 A (+6.0 A), and Vo's maximum after the handover +12.5 against +8.9 mV. The
    gain alone does the same (171.2 A, +12.9 mV), so this is the slower late correction.
  - Late fires up to 330 us: 0 against 9. With the step alone they rise: 47 on S0, 110 against 43 on S75.
- **Not measured here:** the setting on S75 (only the step alone ran there), any temperature other than 25 C, and
  any line or load event. Whether the orbit explains the 3-5 A dependence of the slow boards' post-step peak on the
  step position is still a hypothesis.

## 1. Criteria (S0 unless stated; reference = A192's final-cfg record of the same board, same window)
| run | registers | valley change, phases 1-4 (A) | c1 <= 1.0 A | c2 | hand / after (A) | late to 330 us |
|---|---|---|---|---|---|---|
| reference S0 | step 0.2828 ns, shift 1, target 94 ps | 4.31 / 4.80 / 4.77 / 4.11 | - | - | 164.1 / 149.4 | 9 |
| step4 | step 0.0625 ns | 1.87 / 2.11 / 2.09 / 1.84 | no | pass | 161.4 / 148.8 | 47 |
| shift2 | shift 2 | 3.44 / 4.21 / 4.78 / 3.25 | no | pass | 171.2 / 157.6 | 2 |
| tgt4 | target 375 ps | 4.69 / 5.29 / 5.18 / 4.38 | no | pass | 165.1 / 150.3 | 4 |
| **step4_shift2** | step 0.0625 ns, shift 2 | **0.29 / 0.40 / 0.28 / 0.85** | **yes** | pass | 170.1 / 149.1 | 0 |
| reference S75 | as S0 | 5.34 / 5.96 / 5.76 / 6.20 | - | - | 154.0 / 151.9 | 43 |
| S75 step4 | step 0.0625 ns | 1.13 / 1.32 / 1.29 / 1.37 | no | pass | 152.1 / 150.8 | 110 |
c2 in the window: COMPLETED, 0 shoot-throughs, mean Vo within 0.09 mV of the reference, mean valleys -14.3..-17.0 A
(limit: 1.5 A from -15.6 A; the largest distance is 1.35 A, shift2's phase 3), 0 late fires.

## 2. Decision (BOUNDARY Section 5)
- A variant passes c1 and c2 on S0, so the first branch applies: **a follow-up with its own number (A196) runs
  step4_shift2 on the slow rows and on a rising step before anything is adopted.** The binding row comes first:
  S75, +4.8 V / 1 us, 0 and 25 C (worst 197.8 A, A193), because the steady gain alone (0.9 A) does not justify a
  per-class setting and the handover moves the other way.
- A192's open point (why the 9.5 ns lead "deepens the valleys") is closed by BOUNDARY Section 1: the mean of an
  alternating pair moved.

## 3. Limits
- **The analysis script's c2 had a fault, corrected after the runs.** It tested the shoot-through list with `not`,
  and a list of eight zeros is not empty, so c2 printed False for every run. The criterion as written in the
  BOUNDARY ("0 shoot-throughs") is what the corrected line tests; no threshold changed.
- One board at one temperature for the passing variant, 40 us of steady state (78-79 cycles per phase).
- The window's criteria missed the handover: the +6.0 A there was found by a whole-run check added afterwards
  (`whole()` in the analysis script). A196 registers whole-run peaks as a criterion.
