# A176 - what turns the falling-step valley loss into restarts on the final plant (BOUNDARY)
Method: mixed (EPC2067 gate model; frozen RTL controller; cfg only - a diagnostic)
Track A, package layer. Written and committed before the runs. Looked at beforehand: A173 ff l_m80_10us, A174's
step positions of it, A175 nom l_m48_1us, A163 / A164 (V2) on the same rows.
- After a falling line step, phases 2-4 lose their valley (A148). On the final plant this produces K3 restarts and
  10-20 A spikes: -4.8 V / 1 us (A175: 3 restarts, 6 spikes) and ff -8 V / 10 us (A173 / A174: 1 spike at 2 of 5
  step positions).
- V2 shows none of it: A163 (high-side gates, 2.5 ohm, no lead) on -4.8 V / 1 us, and A164 (high-side gates,
  3.0 ohm, fixed 8 ns lead) on ff -8 V / 10 us.
Decision it changes: how the summary states this open item. Either the lead (a controller-side choice that could be
made direction-aware) or the low sides' gates / interlock (device physics) is the cause.
Cheaper check done first: the valley records (A175 RESULTS); a single edge cannot show a 30 us transient.
Budget: 4 single runs on the cores A174 leaves free, ~1.5 h.

## 1. What and why
- v2lead: ideal low sides, no interlock, A167's ramped 8 ns lead (V2 as adopted in A167);
- v5nolead: the final plant without the lead (A164's lead0 form).
- Rows: nom l_m48_1us (A175's cfg), ff l_m80_10us (A173's cfg). Same trims.

## 2. Criteria (attribution; counts by a142_oracles: K3 restarts + NEW spikes after the step)
1. Events with the lead and ideal low sides (v2lead) on both rows -> the lead is sufficient.
2. Events on v5nolead on both rows -> the low sides' gates / interlock are sufficient.
3. Events only on the full final plant -> the combination.
A row counts as "events" with >= 1 K3 restart or NEW spike after the step. Peaks, V_DS and Vo are reported.

## 3. Predictions (not criteria)
- v2lead: none on either row (A164 had none on ff with the fixed lead).
- v5nolead: none on -4.8 V, but late fires after rising steps are not in these rows. So: outcome 3, the combination
  (the lead brings the turn-on forward while the gate-driven low side still conducts after a lost valley).

## 4. Decision rule
- 1: the open item is named as a lead effect; the summary proposes a direction-aware lead (not run: RTL frozen).
- 2: named as device behaviour of gate-driven low sides at a lost valley; no drive-side fix proposed.
- 3: named as the lead's interaction with the low sides' turn-off delay (A169's mechanism without a shoot-through).
