# A221 - the inductor's core loss in the plant (V7), and a pause that keeps the slots' period (RESULTS)
Boundary: 9ff8330 (branch a221-core, merged into main with 677c4f5). Records: release records-a221 (8 cosim
records, logs). Analysis: a221_analyze.py -> a221_summary.json. Runs from 9ff8330, cosim_sources_modified False.
Plant V7 = V6 + r_core across each inductor (2.90 ohm at L0, 2.17 ohm at 0.75 L0; rc2 rows twice that); skipping
rows: skip hi 5 / lo 1 mV, res_ofs_a and zcd_a = 8 ns x Vo / L, ton_lat 16, one module.

## 0. Verdict
- **Skipping now meets its own criteria on both nominal boards at 10 %, but is not adopted yet: k1 misses by
  0.14 mV** (decision rule: skipping is not judged on V7 until V7 passes its check).
- **The miss is the open-loop start-up's calibration, not normal operation**: on N0 Vo at 143.5 us (mode S, before
  the handover) is 1.0308 V on V7 against 1.0329 V on V6, so the maximum before 300 us falls by 2.14 mV (tolerance
  2 mV; record cosim/run_k_n_s_p62.json against A215's run_m16_n_s_p62.json). The core resistor draws current
  in mode S and the mode-S trim was calibrated on V6 (A206). Everything else on the two check rows is inside k1:
  post-step peaks 181.23 / 192.85 A (V6 181.91 / 195.17), handover 148.1 / 176.9 A (V6 148.9 / 181.1), A212's and
  A206's criteria pass. Next: re-trim mode S for V7 as A206 did for V6, then the adoption.
- **The resume is fixed on V7**: N0 10 % true valleys -16.8..-13.5 A, N75 10 % -16.7..-14.4 A (band -20..-12; A220
  -21.2..-5.0 and -23.4..-9.3 A); every phase resumes within 0.22 / 0.31 A of zero (A220 on V6 up to 4.8 A). With
  half the damping (rc2, about D76's extrapolation to the ring) -16.0..-13.3 and -16.9..-13.8 A, within 0.33 / 0.52 A.
  The slots after a resume are the period's quarters again (the fix; A220's were short).
- **No load misses s3t by 1.2 A**: -21.2..-15.6 A over the last 60 us (phase 3; the last 20 us are one pause, so the
  resume current is not measured there). The +62.5 A row passes s1, s2, s4 and s3t.
- **N0's ladder settles by 750 us**: within 0.49 V of Vin / 4 at the end (A220 at 450 us: 1.56 V between rails 4
  and 1).
- **Core loss in the books (estimate from the edge log, dead times left out)**: N0 full load 15.5 W per module
  (D76's small-signal 7.5 W, its kappa 1-4 range 7.5-30 W), S75 125 C 29.4 W; at 10 % 8.0 W (N0) and 8.0 W (N75)
  next to 2.5 / 3.1 W of semiconductor loss. At short pulses the model's f^2 grows faster than HBS1's f^1.5 above
  8 MHz, so the light-load figures are upper estimates.

## 1. Criteria
| row | j1 / k1 | s1 | s2 | s3t (true valleys, A) | z1r (resume, A) | s4 | A220's z1 (info) |
|---|---|---|---|---|---|---|---|
| k N0 +62.5 A | **k1 miss** (Vo -2.14 mV) | - | - | - | - | - | - |
| k S75 125 C k 5 | k1 pass | - | - | - | - | - | - |
| N0 10 % | - | pass | pass | pass (-16.8 .. -13.5) | pass (0.22) | - | 0.85 A |
| N75 10 % | - | pass | pass | pass (-16.7 .. -14.4) | pass (0.31) | - | 0.84 A |
| N0 no load | - | pass | pass | **miss** (-21.2 .. -15.6, 60 us) | not measured | - | 0.53 A |
| N0 5 %, +62.5 A | - | pass | pass | pass (-17.0 .. -15.2) | not measured | pass | - |
| N0 10 %, rc2 | - | pass | pass | pass (-16.0 .. -13.3) | pass (0.33) | - | 1.63 A |
| N75 10 %, rc2 | - | pass | pass | pass (-16.9 .. -13.8) | pass (0.52) | - | 1.61 A |
- j1: unit tests 104 of 104, regression quick and full bit for bit, the three r_core tests.
- "not measured": no resume in the 20 us edge log; the analysis scores it false.

## 2. Predictions
- Held: z1r on every measured row, also at rc2; s3t on N75 at both r_core and on N0 10 % at 750 us; the ladder by
  750 us; N0 no load missing by up to 3 A (1.2); the check rows' inductor peaks (-0.7 / -2.3 A) and N0's core books
  (15.5 W against 14-15).
- Missed: "Vo the same within 1 mV" (N0's start-up -2.1 mV: the trim, not foreseen); S75's core books (29.4 W against
  17-20 W); the semiconductor loss at 10 % (N75 3.06 W, not A220's 2.5 W plus nothing).

## 3. Limits
- r_core is HBS1's small-signal loss fitted at 8 MHz; the ring's 20-25 MHz lie beyond the data (rc2 brackets it).
  Temperature, kappa > 1 and the copper's resistance (D72) are not in.
- The plant's peaks are inductor currents; a switch at turn-off also carries the core resistor's current, (rail -
  Vo) / r_core = 3.8 A on N0, 5.0 A on 0.75 L0 boards, which turn-off energy would see.
- One step position; four modules and the slow board's skipping (it does not skip) not run.
