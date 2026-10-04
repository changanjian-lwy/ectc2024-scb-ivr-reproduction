# C08 - the four-module final design with A136's phase-1 cap (BOUNDARY)
Track C. Written and committed before any C08 run. Looked at beforehand: A134-A136 RESULTS, C06's records.
Decision it changes: whether the four-module final design takes the same phase-1 cap as the single module (one adopted
version per component), and whether it holds an L spread the absolute cap locks on.
Cheaper check done first: the single module (A136) - at L0 the two caps agree within 1 %, so C06's rows should repeat.
Budget: 20 four-module runs, two batches at 10 jobs, ~40 min.

## 1. What and why
- A134: A128's absolute phase-1 cap locks the ladder when the steady Ton a load needs crosses it (single module:
  s_p62 at L x 1.1). A136 replaces it with the cap on Ton's low-pass (vff rel_q8 320, rel_lp 1): the same value at
  L0, scaled by the loop elsewhere, idle in steady state. Every module of C05/C06 carries scb_vff, so the final design
  must change with it.
- Rows: C06's 18 (A124's seven step rows, n0, A129's matrix, slave L +5 / +10 %) with the new cap in every module,
  C06's timing (steps at 800 us; the master goes timed at 662 us). Plus s_p62 with every module's L x 1.2 and the step
  at 1000 us, with the absolute cap (l12a) and with the new one (l12q).
- Analysis: C06's per-row statistics and criteria (c06_analyze.analyse), with two changes registered here: the
  whole-run peak criterion takes the peak after the start-up (t >= 600 us; A135/A136 raised start-up peaks to
  191-218 A on one module), and C06's C05-identity criterion is dropped.
- Not tested: L spread between modules with the new cap beyond C06's slave rows; Cs / Coss corners.
- A136's start-up regression (handover late fires, start-up peaks) is being fixed in parallel (A137: restart the
  feed-forward's low-passes at mode P). C08 runs A136's version; if A137 is adopted, C08's rows are rerun with it
  for the start-up part, and C08's late-fire totals (which include the start-up) are read with that in mind.

## 2. Criteria
1. Hard constraints on every one of the 18 rows: no overlap, peak after the start-up <= 200 A, locked, post-step peak
   <= 200 A. Every other C06 criterion (as modified above) passes wherever it passed in C06: no new failure. C06's own
   misses (late fires on m1n, m3n and the line rows; step_10pct / back_2us on three line rows; ls_on_ref on j30 / j100)
   are reported against C06's values.
2. Every stepped row's post-step peak within 7 A of C06's same row.
3. l12a locks (any module: ladder deviation more than 0.5 points above C06's s_p62 module, or Vo outside 1 %), l12q
   does not.

## 3. Predictions
- 18 rows within a few A of C06 (A136 at L0: -2.1 / +1.9 A on the rising rows against the absolute cap).
- l12a locks as A134's single module did at L x 1.1-1.2; l12q holds.

## 4. Decision rule
- 1-3 pass: the final design (C06 + A136's cap) is the adopted multi-module version; MULTI_MODULE_SUMMARY notes it.
- 1 or 2 fails on some row: the row's mechanism is traced before any adoption; the single-module adoption stands.
- 3 fails (l12a does not lock): the multi-module design is less exposed than the single module; reported, no change.
