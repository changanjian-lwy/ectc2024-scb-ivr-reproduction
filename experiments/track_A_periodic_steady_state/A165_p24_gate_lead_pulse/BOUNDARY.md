# A165 - A164's drive spec with the lead as a pulse shift (BOUNDARY)
Method: mixed (EPC2067 gate model, D79; plant cosim/gate.py; frozen RTL controller; cfg + bridge driver option)
Track A, package layer. Written and committed before the matrix runs, while A164 finished.
Looked at beforehand:
- A164's first 9 rows. Nominal and ff pass, except ff -8 V / 10 us (Vo +28.5 mV, 0.6 mV over) and L x 0.7.
- L x 0.7: mode S 202.5 A physical (A152's ramps 205.6 A), then 218.6 A 2.4 us into mode P.
- The pre runs (a165_pre.py, 190 us).
Decision it changes: how the 8 ns lead is specified. Option one is a faster turn-on path in the driver (A164: the pulse
gets wider by the lead). Option two is a signed dt_pred in the controller (A165: the pulse, its turn-off and the next
low-side turn-on all move).
Cheaper check done first: the pre runs (handover to 190 us; table below).
Budget: 15 rows + four modules, ~5 h at 10 jobs.

## 1. What and why
- In A164 the turn-on-only lead widens every predictive pulse by 8 ns. Mode S has no predictive turn-ons, so the
  handover is an 8 ns on-time step. That step adds 10 A at L0 (140.7 -> 150.6 A) and breaks 200 A at L x 0.7 (218.6 A).
- A controller with a signed dt_pred would move the whole pulse instead. The bridge does this with driver lead_mode
  "pulse": the lead-moved predictive turn-on moves its pulse's turn-off and the low side's following turn-on too.
  The low side's turn-off is current-decided and stays.
- Pre runs (190 us), handover peak, pulse / turn-on-only lead:
  | run | pulse | turn-on-only |
  |---|---|---|
  | nominal L0 | 137.9 A | 150.6 A |
  | L x 0.7 | 189.6 A | 218.6 A |
  | slow corner 3.6 ohm | 172.2 A | 181.6 A |
  | slow corner 4.55 ohm (+-30 %) | 178.4 A | 228 A |
- Rows: A164's matrix without its two no-lead controls. Same cfgs, trims (A164 trims.json), corners and references,
  with lead_mode "pulse". late_log on.

## 2. Criteria (A164's, a164_analyze.judge; each row; four modules 1-3)
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
- L x 0.7: handover ~190 A. Criterion 2 still misses on mode S's 202.5 A: the frozen design's open-loop start at
  L x 0.7 (A137, A152 physical 205.6 A), which the trim cannot remove without dropping Vo toward the 0.99 V cliff.
- Every other row: as A164 within +-2 A / +-0.5 V. Handover peaks 5-50 A lower where A164's lead step showed.
- Edge power: as A164.
- The slow corner's late fires: as A164 (the lead's turn-on timing is the same).
- ff -8 V / 10 us: Vo extreme as A164 (+28.5 mV, not a lead effect).

## 4. Decision rule
- A165 passes where A164 missed and is no worse elsewhere: specify the lead as a signed dt_pred (pulse shift).
  The spec is then A164's: 50 pH, 3.0 / 0.3 ohm +-20 %, 8 ns lead, per-board trim.
- Otherwise: A164's turn-on-only lead stays, and the L x 0.7 handover is named as its limit.
- Either way, the L x 0.7 mode-S peak (~202 A physical) is the frozen design's known start-up limit, not the drive's.
