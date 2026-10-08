# A167 - A164's lead, ramped in after the handover (BOUNDARY)
Method: mixed (EPC2067 gate model, D79; plant cosim/gate.py; frozen RTL controller; cfg + bridge driver option)
Track A, package layer. Written and committed before the runs.
Looked at beforehand: A164 (all), A165 (all), and A166's first 7 rows.
- L x 0.7 after +4.8 V / 1 us, physical peak by lead form (3.0 ohm):
  | A164: 8 ns, turn-on only | A165: 8 ns, pulse shift | A166: 1.27 ns per board |
  |---|---|---|
  | 192.1 A | 211.0 A | 207.8 A, 65 late fires |
- A164's only cost at L x 0.7 is the handover step: 218.6 A at the handover.
Decision it changes: the form of the lead in the spec. The question is whether A164's 8 ns turn-on lead can be enabled
gradually after the handover (a register the controller writes once mode P runs). That would keep its post-step
behaviour and remove the handover step.
Cheaper check done first: A164's handover check (L0: 140.7 A without the lead, 150.6 A with it, A164 pre).
Budget: 5 runs, ~2-3 h shared with A166.

## 1. What and why
- Bridge driver "lead_ramp_us" 20: the lead grows linearly from 0 to 8 ns over 20 us (~40 periods) after mode P
  starts. dt_pred and the voltage loop follow it.
- Everything else is A164's cfg of the same row: same trims, corners and references.
- Rows:
  - nom L07_l_p48_1us: the handover and the post-step;
  - nom l_p48_1us: no regression;
  - ss l_p48_1us and s_p62: the slow corner's handover;
  - hot l_p48_1us: the pre-run shoot-through corner.

## 2. Criteria (A164's, a164_analyze.judge; each row)
1. Whole-run max V_DS <= 40.0 V.
2. Physical start-up peak (t < 300 us) <= 200 A, and Vo(143.5 us) within 1.035 +- 0.02 V.
3. Post-step:
   - physical peak <= 200 A;
   - command-time peak <= min(A152 ref + 5, 200) A;
   - 0 NEW oracle events;
   - late fires <= ref + 2;
   - 0 overlaps, COMPLETED.
4. Vo: |extreme| <= |ref| + 4 mV; if |extreme| > 11 mV, back within 1 % <= ref + 2 us.

## 3. Predictions (not criteria)
- L x 0.7:
  - handover <= 195 A (A166's small lead: 191.5 A);
  - post-step ~192 A as A164;
  - criterion 2 still misses on mode S's 202.5 A (the frozen design's open-loop start).
- nom l_p48_1us: as A164, within +-1 A.
- Slow corner: handover late fires as A164 or more (little lead during the ramp); after 300 us as A164.
- 0 shoot-throughs.

## 4. Decision rule
- L x 0.7's handover <= 200 A with the post-step as A164, and no regression elsewhere: the spec's lead becomes an 8 ns
  turn-on lead enabled over ~20 us after the handover.
- Otherwise: A164's form stays, with the L x 0.7 handover named as its limit.
