# A179 - the interlock release time at the slow corner, with step-position scatter (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, threshold-form driver interlock; frozen RTL controller;
cfg only)
Track A, package layer, plant V5. Written and committed before the runs. Looked at beforehand: A173 / A174 / A177
records (late fires split at the step, below) and A173's steady state at 300-990 us.
Decision it changes: FINAL_SPEC_COVERAGE's interlock row says "the slow corner wants < 1.4 ns". This experiment
either confirms 1.4 ns (the per-board comparator reference) or replaces it by a number. Cheaper check done first:
the record split below. Budget: 22 runs, --jobs 10, ~3 h (four modules ~2.6 h, single ~1 h).

## 1. What and why
- A177 judged 1.4 ns against one 0.5 ns run per row. Its misses (NEW +1 / +5, Vo 2.6 mV) are near the scatter
  between neighbouring runs, and nothing measured that scatter at the slow corner.
- Late fires split at the step (A173 0.5 / A177 1.4 / A174 8.3 ns):

  | row | before the step (all at 160-300 us) | after the step |
  |---|---|---|
  | ss s_p62 (load step) | 72 / 83 / 104 | 0 / 0 / 0 |
  | ss l_m80_10us (-8 V / 10 us) | 72 / 83 / 104 | 9 / 47 / 50 |
  | four modules ss l_p48_1us | 385 / 367 / 438 | 418 / 425 / 1170 |

  The release time moves the start-up settling count on every row; only -8 V moves after the step, and 9 -> 47
  may be the 0.5 ns run's step position.
- Runs (make_cfgs.py): A173's cfgs with only the step time, the run end and t_il changed. Step at 500 us + k T / 3,
  k = 0, 1, 2 (four modules: 500 us and + T / 2), end = step + 400 us (as A173). T = 0.5048 / 0.5069 us.
  R1 = ss l_m80_10us at t_il 0.5 / 0.8 / 1.0 / 1.4 ns; R2 = ss s_p62 and M4 = four modules ss l_p48_1us at
  0.5 / 1.4 ns.
- Why 500 us: A173's records settle by then (single: Cs within 5 mV and period within 0.12 % of 990 us; four
  modules: Cs within 2 mV from 450 us on), and no late fire falls between 300 us and the step. The 1000 us step
  was a lo_learn-1024 leftover. The ff corner is not settled at 400-500 us (0.6 mV ADC limit cycle) and is not run.
- No old cfg, record or summary is changed. Records: release records-a179.

## 2. Criteria
Late fires are counted before and after the step (late_log sections). W(x) = worst value over the new positions.
1. Window identity: every 0.5 ns run's sections before its step equal A173's run of the same row, and every 1.4 ns
   run's equal A177's (vo, vcs, late; exact).
2. Window check: the old-window run (A173 0.5 ns, A177 1.4 ns) lies inside the new positions' range widened by
   A174's tolerances (post peak +-3 A, NEW +-2, |Vo extreme| +-2 mV, post-step late [min / 1.5 - 5, 1.5 max + 5]).
3. Release-time decision, per row and t_il, against the 0.5 ns runs of the same row (new positions only):
   COMPLETED, 0 shoot-throughs / overlaps, V_DS <= 40 V, post peak <= 200 A at every position, and
   W(post peak) <= W0 + 3 A; W(post-step late) <= 1.5 W0 + 5; W(NEW) <= W0 + 2; W(|Vo extreme|) <= W0 + 2 mV;
   pre-step late <= 1.5 x the 0.5 ns value + 5.
   The release-time number = the largest t_il passing criterion 3 on R1, with R2 and M4 passing at 1.4 ns or at
   that number.

## 3. Predictions (not criteria)
- Criterion 1 holds exactly; criterion 2 holds.
- R1 at 0.5 ns reaches >= 30 post-step late fires at one position or more (A173's 9 a low draw), ~50 %.
- 1.4 ns passes criterion 3 on R2 (no post-step late) and on M4; on R1 ~55 %, else 1.0 ns.
- Pre-step late at 0.8 / 1.0 ns between 72 and 83.

## 4. Decision rule
- Criterion 1 fails: the cfg change did more than move the step; stop and diagnose, nothing reported from those runs.
- Criterion 2 fails on a metric: the shortened window shifts it; criterion 3 is then reported per window and later
  runs keep the 1000 us step.
- 1.4 ns passes on R1, R2, M4: the spec reads "release <= 1.4 ns at the slow corner" (the per-board comparator
  reference meets it); A177's misses become step-position scatter (post hoc note in A177, its verdict unchanged).
- 1.4 ns fails on R1: the spec reads "<= X ns", X = the largest of 1.0 / 0.8 ns passing R1. If R2 failed at
  1.4 ns, stage 2 runs R2 at X (three positions). Nothing passes: "< 0.8 ns" (adaptive dead-time driver).
- M4 fails at 1.4 ns while the single rows pass: four modules set the bound; named open.
- Criterion 2 holds: later V5 runs on settled corners may step at 500 us.
