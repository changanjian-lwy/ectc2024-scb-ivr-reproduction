# A164 - the gate drive over the datasheet spread: 3.0 ohm +-20 %, high-side turn-on lead, per-board start-up trim (BOUNDARY)
Method: mixed (EPC2067 gate model, D79; plant cosim/gate.py; frozen RTL controller; cfg + bridge driver option)
Track A, package layer. Written and committed before the calibration and matrix runs. Looked at beforehand: A163's
records, its 15 start-up diagnostics, single edges (scripts/p24_gate_edges.edge_plant) and the pre-registration runs
(a164_pre.py: 300 us of l_p48_1us per corner, lead 0 / 4 / 8 / 9.5 ns; a164_pre.json; cosim_cal_r35/).
- At 3.5 ohm +-30 % the slow corner (4.55 ohm) has 9-20 ns turn-on delays and up to 32 ns turn-on transitions.
  - Without a lead it fires late every period.
  - With 8 / 9.5 ns the steady state holds (phase-4 dt_pred 4.3 / 6.6 ns, peaks <= 156 A), but the handover reaches
    228 / 216 A.
  - Any resistor fast enough for that corner breaks the fast corner's 40 V at -30 %. So the driver tolerance goes to
    +-20 %: the turn-on resistance is mostly the external resistor (1 %), and the driver's pull-up (+-40 %) is a
    fraction of it.
- Pre run at 3.6 ohm (= 3.0 x 1.2) and lead 8 on the slow corner: handover 181.6 A, steady <= 159 A, dt_pred
  8.7-10.0 ns; late fires 0 / 2 / 25 / 47 by 300 us.
Decision it changes: the package drive spec (A163's 2.5 ohm resistor drive failed the spread).
Cheaper check done first: single edges and the pre runs.
Budget: 6 calibration runs (150 us) and 18 matrix runs + four modules, ~5 h at 10 jobs.

## 1. What and why
- A163 broke on three mechanisms, each with one change here:
  1. The open-loop start-up on-time moves with the device. Fix: a per-board start-up trim. Each board (device corner x
     inductor corner) gets one start-up run to 150 us at a first-guess ton; then
     ton = ton0 + (1.035 - Vo(143.5 us)) / 0.026 V/ns. One shot, as a production test would do it.
  2. The valley timing: the gate delay must fit before the valley, minus one 4 ns clock. Fix: predictive high-side
     turn-ons reach the plant 8 ns earlier than the other edges (bridge driver "hs_on_lead_ns", as if dt_pred could go
     8 ns below zero). Start-up, restart and ZVS turn-ons are unchanged. A turn-on is a shoot-through only when its
     channel starts while the low side conducts ("overlaps", the run stops).
  3. The driver at -30 % overshoots. Fix: r_on 3.0 ohm per device (r_off 0.3) with a +-20 % tolerance. Single edge,
     fast corner (2.4 ohm, threshold -0.3 V): 37.0 V (2.5 ohm at -30 %: 40.9 V).
- The corners are datasheet-consistent (A163 RESULTS; tests/test_p24_gate_model.py):
  - nom;
  - ff: threshold -0.3 V and the driver x 0.8;
  - ss: threshold +1.0 V, charge x 1.29 and the driver x 1.2;
  - hot: 125 C.
- Rows (A152's matrix, 50 pH Q 7, low sides on A152's ramps):
  - nom: l_p48_1us, s_p62, l_m80_10us, slew4, L07_l_p48_1us, L13_l_p48_1us and four modules (l_p48_1us);
  - ff: l_p48_1us, s_p62, l_m80_10us;
  - ss: l_p48_1us, s_p62, l_m80_10us, slew4;
  - hot: l_p48_1us, s_p62;
  - controls without the lead (nom): l_p48_1us, l_m80_10us.
- Every run logs late fires per section (late_log).
- References: A152's S50 run of the same row. Peaks are compared with matched definitions: command-time against
  command-time, physical against the 200 A budget.

## 2. Criteria (each row; four modules 1-3; a164_analyze.py)
1. Whole-run max V_DS <= 40.0 V.
2. Physical start-up peak (t < 300 us) <= 200 A, and Vo(143.5 us) within 1.035 +- 0.02 V.
3. Post-step:
   - physical peak <= 200 A;
   - command-time peak <= min(ref + 5, 200) A;
   - 0 NEW oracle events;
   - late fires <= ref + 2;
   - 0 overlaps, COMPLETED.
4. Vo: |extreme| <= |ref| + 4 mV; if |extreme| > 11 mV, back within 1 % <= ref + 2 us.

## 3. Predictions (not criteria)
- Trims: nom ~39.6 ns, L x 0.7 ~34.3, L x 1.3 ~41.0, ff ~37.9, hot ~39.3, ss ~48.2 ns.
- Whole-run V_DS: nom <= 35.5 V, ff <= 38.6 V (single edge 37.0 V + the cosim's 1.6 V), ss <= 33 V.
- Steady phase-4 dt_pred: nom ~14.5 ns, ss ~8.7 ns. Late fires: nom 0-2; ss mostly in the handover (pre run 74 by
  300 us), so ss may miss criterion 3 on late fires without other consequence.
- Edge power per module: nom ~2.6 W, ff ~2.2 W, ss ~4.5 W, hot ~2.5 W.
- Start-up physical peaks <= 175 A at L0 (ss handover ~182 A), <= 195 A at L x 0.7.
- Controls without the lead: steady state holds (phase-4 dt_pred ~6.7 ns at 3.0 ohm). Line steps may give a few late
  fires (A163: 0-5 at 2.5 ohm, 7-24 at 3.5 ohm).

## 4. Decision rule
- All pass: the drive spec becomes:
  - 50 pH, r_on 3.0 / r_off 0.3 ohm per device (turn-on resistance +-20 %);
  - a predictive high-side turn-on lead of 8 ns (a shorter driver path, or a signed dt_pred in the controller);
  - a per-board start-up trim to Vo(143.5 us) = 1.035 V.
  Then Mihai's question 1, the summary's loop bound and the scorecard T20 are rewritten from A163 / A164.
- ff fails V_DS: r_on 3.5 ohm with +-10 % (A165).
- ss fails timing: the lead is not enough; name the slow-corner delay as the binding spec (device screening or a
  controller-side lead).
- The trim fails (Vo outside the band or start-up > 200 A at L x 0.7): the start-up needs a closed loop, which is a
  controller change outside the frozen design. State it.
