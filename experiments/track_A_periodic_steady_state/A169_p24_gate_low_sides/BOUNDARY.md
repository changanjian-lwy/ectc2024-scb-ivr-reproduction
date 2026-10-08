# A169 - the adopted drive with gate-driven low sides (BOUNDARY)
Method: mixed (EPC2067 gate model, D79, now on all eight switches; plant cosim/gate.py; frozen RTL controller; cfg only)
Track A, package layer. Written and committed before the runs.
Decision it changes: whether the package spec needs a low-side clause beyond "sink <= 0.3 ohm". In particular, whether
the 8 ns high-side lead must shrink once the low side's turn-off takes real time. It also removes D79's stated limit
("the plant's low sides keep instantaneous edges").
Cheaper check done first: the low side's turn-off delay from the device model (gate discharge through 0.3 ohm x corner
+ R_G until the channel needs 0.2 V to carry the valley current, 3 devices):
- 15.6 A: nom 1.71, ff 1.79, ss 1.35, hot 1.82 ns. The spread is ~0.5 ns, against a valley 9.5-11 ns after the
  low-side command (A163) and the 8 ns lead.
- So the valley moves ~1.7 ns later everywhere, and dt_pred should absorb it. The cosim's value is the closed loop and
  the physical interlock: since fab6366 a shoot-through is counted against the complement's physical conduction (a
  gate-driven turn-off still pending or active counts), in both directions.
Budget: 5 runs to 1400 us (~2 h at 5 jobs, low-side edges add plant steps).

## 1. What and why
- cfg gate "switches" "all": the low sides use the same resistors and corner as the high sides. Their turn-on is ZVS
  (V_DS <= 0: conducting at once); their turn-off with forward (valley) current follows the gate.
- Everything else is A167's spec: 50 pH, 3.0 / 0.3 ohm +-20 %, 8 ns lead ramped over 20 us, A164's per-board trims
  (not recalibrated: criterion 2 checks them).
- Rows: nom l_p48_1us, nom L07_l_p48_1us, ff l_p48_1us (shortest high-side delay, so the lead is most ahead), hot
  l_p48_1us (A164's pre-run shoot-through corner), ss l_p48_1us (late fires).
- Reference: the same row with ideal low sides (A167, else A164 for ff).
- Not modelled: the low side's turn-on delay under reverse conduction (dead-time loss), Miller turn-on by dv/dt (D79
  Section 4.6, LTspice only).

## 2. Criteria (A168's, a168_analyze.judge; each row against its reference)
1. Whole-run max V_DS <= 40.0 V.
2. Vo(143.5 us) within 1.035 +- 0.02 V; physical start-up and handover peaks <= 200 A (<= ref + 3 A where the
   reference is above 197 A).
3. Post-step:
   - physical peak <= 200 A and <= ref + 5 A;
   - 0 overlaps, 0 shoot-throughs (physical, both directions), COMPLETED;
   - late fires <= 1.5 x ref + 5;
   - NEW oracle events 0 where the reference has none, else <= 1.5 x ref + 5.
4. Vo: |extreme| <= |ref| + 2 mV; where |extreme| > 11 mV, back within 1 % <= ref + 2 us.

## 3. Predictions (not criteria)
- Low-side turn-off delay (gate stats delay_off_ls) 1.2-2.0 ns; active turn-off <= 2 ns.
- Peaks within +-3 A of the reference, V_DS within +-0.5 V, Vo(143.5) within +-5 mV.
- Late fires equal or fewer (the valley moves later, which widens dt_pred's room); 0 shoot-throughs.

## 4. Decision rule
- All rows pass: the spec stands with physical low sides. The low-side clause stays "sink <= 0.3 ohm, gate loop
  <= 1 nH", and D79's limit is lifted for the closed loop.
- A shoot-through or a timing miss caused by the low-side delay: the lead is bounded by the low side's turn-off
  (lead <= valley time - low-side delay), stated in the spec, and the rows are rerun with that bound.
- A trim miss only (criterion 2): recalibrate with low-side gates and rerun that row (the trim is a measurement on
  the board, so it would include them).
