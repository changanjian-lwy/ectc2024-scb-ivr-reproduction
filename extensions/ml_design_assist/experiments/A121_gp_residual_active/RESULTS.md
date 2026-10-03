# A121 - a Gaussian process on the residual co-simulation − D63, and active learning (RESULTS)

Extension `ml_design_assist`.

**Boundary:** `BOUNDARY.md` and `a121_predictions_a118.json`, committed
(d7b5632) while A118's runs had produced no output.

**Records:** `a121_summary.json` (`run_a121.py evaluate`).

## 0. Verdict

1. **Every registered criterion is met.**

   | criterion | registered | result |
   |---|---|---|
   | leave-one-out, A115-A117 (25) | D63 + GP MAE ≤ 0.8 × D63's | **6.8 against 9.2 A (0.74)** |
   | leave-one-out coverage, ±1.645 sd | ≥ 75% | **88%** |
   | prospective, A118's 12 non-runaway step rows | not worse than D63 | **9.7 against 10.5 A** |
   | prospective coverage | ≥ 75% | **92%** (11 of 12) |
   | the floor rows less certain than training | median sd > 7.9 A | **13.1 A** |

   **The miss outside ±1.645 sd** is f15_l_p48_5us: 241 A against
   216.8 ± 14.3. That is the timed design's rising step at 15 µF, D63's
   known weak domain.
2. **The correction is modest where it matters.**
   - **Prospectively** the GP improves D63 by 8%, against 26% in
     leave-one-out. The floor rows were new, and the GP fell back toward
     its prior, as it should.
   - **Its real value is the error bar.**
     - It flagged the floor rows as uncertain (13 against 8 A).
     - Its intervals held in 11 of 12 runs.
     - So a D63 prediction can be given a calibrated ±1.645 sd band
       (~±22 A here) before a co-simulation.
3. **Active learning reduces to space-filling with this little data.**
   - **Refitted on 37 transients,** the length scales are short:
     - pct: 0.6 sd (~1.5 percentage points);
     - ln Cs: 0.9 sd;
     - the turn-off rule: 0.1-0.2.
   - So every candidate away from the observed points (pct 10%, Cs 6 /
     15 µF) sits at the prior sd (13.2 A). The 8 proposed runs are a
     spread over pct 8-12%, Cs 4-10 µF and the slews.
   - **The lesson for the next runs:** D63's error changes over a short
     range of pct and Cs. A design moved by ~1.5 points of negative
     current, or by Cs, needs its own co-simulation check.

## 1. Proposed next co-simulation runs (floor rule; `a121_summary.json`)

All at the prior sd 13.2 A:
- pct 8.0, Cs 9.5 µF, floor 1.6 A: +4.8 V / 1.4 µs;
- pct 12.0, Cs 8.4 µF, floor 1.3 A: −4.8 V / 2.2 µs;
- pct 8.0, Cs 4.3 µF, floor 3.6 A: +4.8 V / 3.5 µs;
- pct 8.0, Cs 8.4 µF, floor 3.8 A: −4.8 V / 1.7 µs;
- pct 12.0, Cs 9.8 µF, floor 2.4 A: +4.8 V / 1.4 µs;
- pct 12.0, Cs 4.1 µF, floor 2.4 A: +62.5 A;
- pct 12.0, Cs 4.2 µF, floor 1.5 A: +4.8 V / 1.5 µs;
- pct 8.0, Cs 9.4 µF, floor 1.0 A: +4.8 V / 9.4 µs.

**Not run yet.** They map the candidate's neighbourhood (the standard
matrix comes first).

## 2. Limits

- 37 points in 10 inputs: the GP's view is local.
- The baseline is D63, so the GP models D63's error, not the converter.
