# A177 - the per-board interlock reference on the slow-corner rows (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, threshold-form driver interlock; frozen RTL controller;
cfg only)
Track A, package layer. Written and committed before the runs. Looked at beforehand: A173 (t_il 1.4 ns on ss
+4.8 V / 1 us passes; late 210 vs 194), A174 (the fixed 1.0 V reference, 8.3 ns, fails criterion 4 on ss s_p62,
l_m80_10us, slew4 and four modules ss).
Decision it changes: the summary and D79 now recommend a per-board comparator reference (V_th - 0.2 V, ~1.4 ns
release at every corner by A173's estimate). That rests on one row. This experiment checks it on the four rows
where the fixed form failed. Cheaper check done first: the delay estimate (A173). Budget: 4 runs (four modules
~4.5 h, single ~2 h), --jobs 4 next to A178.

## 1. What and why
- A173's cfgs of ss s_p62, ss l_m80_10us, ss slew4 and four modules ss l_p48_1us with t_il 1.4 ns.
- Not tested: the per-board form at nom / ff / hot. Its release there (0.95-1.02 ns) is within the 1.0 ns that
  A171 ran on L x 0.7, and those corners hold rarely or never.

## 2. Criteria (A174's criterion 4, a174_analyze.judge_fr, against A173's t_il 0.5 ns run of the same row)
Post-step peak within ±3 A; late <= 1.5 x A173 + 5; NEW <= A173 + 2; |Vo extreme| within ±2 mV; V_DS <= 40 V;
0 shoot-throughs, COMPLETED.

## 3. Predictions (not criteria)
- All four pass. Late +0-20 % over A173 (ss +4.8 V / 1 us was +8 %); four modules 800-950.

## 4. Decision rule
- All pass: the per-board reference is checked on every slow-corner row the final plant ran; D79 / the summary
  keep it as the spec's interlock form.
- Any miss: the interlock needs a release faster than ~1.4 ns at the slow corner on that row (an adaptive
  dead-time driver, 0.03-1 ns); named open.
