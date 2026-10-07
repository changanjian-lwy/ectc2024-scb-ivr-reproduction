# A166 - an interlock-safe lead per board (BOUNDARY)
Method: mixed (EPC2067 gate model, D79; plant cosim/gate.py; frozen RTL controller; cfg + bridge driver option)
Track A, package layer. Written and committed before the runs, while A164 / A165 finished.
Decision it changes: the form of the high-side turn-on lead in the drive spec.
- A fixed 8 ns lead works in A164 / A165's rows so far (0 shoot-throughs).
- But it removes the controller's implicit interlock. With dt_pred >= 0, the high side was never commanded before
  the low side's turn-off command. A165's pre runs stopped on a physical shoot-through (phase 4, 146-153 us): the
  slow corner at +-10 % with an 8 ns lead, and at +-20 % with a 12 ns lead. Phase 4's dt_pred fell toward 0 after the
  handover, and the lead exceeded the gate delay.
Cheaper check done first: none; the rule follows from dt_pred >= 0 and the measured delays.
Budget: 13 runs incl. four modules, ~5 h with A165.

## 1. What and why
- Rule: lead = the board's shortest high-side turn-on delay (command to channel start) - 1 ns. The delay is taken from
  the board's calibration start-up (A164 cosim_cal, gate_stats delay_on min). With dt_pred >= 0 the channel cannot
  start before the low side's turn-off command + 1 ns, whatever the learning does. A controller would measure the
  delay with its switch-node comparator (command to node fall).
- Leads (leads.json): nominal 1.31 ns (L x 0.7 / 1.3: 1.27), ff 0.47, hot 1.06, slow corner (3.6 ohm) 6.06 ns.
- The valley-timing limit becomes delay <= ~5.5 ns + lead on phase 4:
  - nominal: 6.8 ns, against 6.1 ns on the line step;
  - slow corner: 11.6 ns, against 9.2-9.7 ns steady (up to 16.6 ns on line-step hard turn-ons).
- Everything else as A165: 50 pH, 3.0 / 0.3 ohm +-20 %, per-board start-up trim (A164 trims.json), the lead as a
  pulse shift. Rows: nom l_p48_1us, s_p62, slew4, L07_l_p48_1us, L13_l_p48_1us; ff l_p48_1us, l_m80_10us; ss
  l_p48_1us, s_p62, l_m80_10us, slew4; hot l_p48_1us; four modules (nominal).

## 2. Criteria (A164's, a164_analyze.judge; each row; four modules 1-3)
1. Whole-run max V_DS <= 40.0 V.
2. Physical start-up peak (t < 300 us) <= 200 A, and Vo(143.5 us) within 1.035 +- 0.02 V.
3. Post-step:
   - physical peak <= 200 A;
   - command-time peak <= min(A152 ref + 5, 200) A;
   - 0 NEW oracle events;
   - late fires <= ref + 2;
   - 0 overlaps (physical shoot-throughs), COMPLETED.
4. Vo: |extreme| <= |ref| + 4 mV; if |extreme| > 11 mV, back within 1 % <= ref + 2 us.

## 3. Predictions (not criteria)
- 0 shoot-throughs on every row: the point of the rule.
- Nominal, hot, ff: as A165. Late fires 0 on the line steps; nominal with no lead had 48 (A164 control).
- L x 0.7: criterion 2 misses on mode S's ~202 A, as in A164 / A165. The handover is lower than A164's 218.6 A.
- Slow corner: late fires in the handover and after rising line steps, more than A164's 65 / ~160 because the lead
  is 6 instead of 8 ns. NEW spikes after the steps, peaks <= 185 A, V_DS <= 32 V.

## 4. Decision rule
- 0 shoot-throughs and A165's passes kept: the spec's lead becomes "the board's shortest turn-on delay - 1 ns".
- The slow corner's transient late fires stay a documented limit of the frozen controller, with no peak or voltage
  consequence. Removing them needs a faster gate at that corner (a +-10 % turn-on resistance) or an interlock in
  hardware that is not tested here.
- Shoot-throughs: the rule's 1 ns margin is not enough. Name the margin from the measured overlap.
