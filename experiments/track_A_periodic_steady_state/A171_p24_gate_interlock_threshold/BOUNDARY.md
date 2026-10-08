# A171 - the driver interlock in threshold form (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, D79; plant cosim/gate.py, interlock "threshold" (0c60feb);
frozen RTL controller; cfg only)
Track A, package layer. Written and committed before the runs.
Looked at beforehand: A170's first three rows (S50 ff, hot pass; nom misses) and A169 (all).
- A170's gate form holds a turn-on's gate at 0 V until the complement stops. That serialises the low side's
  turn-off (<= 2.9 + 1.8 ns) and the high side's whole gate delay.
- After the +4.8 V step on the nominal board, the 90th-percentile command-to-channel delay rose from 4.3 to 9.4 ns
  (max 6.1 -> 14.9 ns). Result: post-step 187.6 A (ref 181.7), 7 late fires, Vo 12.6 mV / 45.5 us back.
- Without an interlock (A169) the same row passes, because the high side's delay already kept its channel after the
  low side's turn-off there.
- By A170's decision rule the gate form is not enough.
Decision it changes: whether a driver interlock can make the lead safe without the controller change. The
alternative is the bounded signed dt_pred in the frozen RTL, which goes to the user.
- The threshold form only blocks what an interlock must block, a channel starting while its complement conducts. A
  driver can do this by comparing its own gate to a threshold reference and the complement's gate to its threshold
  (t_il covers the comparators and logic; the workspace's adaptive dead-time driver ICs reach 0.03-1 ns).
Cheaper check done first: A170's S50 L x 0.7 cfg in threshold form to 165 us. 0 shoot-throughs; 8 holds <= 1.57 ns;
late 4 (gate form 31); phase-4 dt_pred 11.3 ns (gate form 1.5, A169 2.5). The gate form is unchanged by the code
change (A170 S50 ff reproduced to 165 us).
Budget: 8 runs to 1400 us (~3 h shared).

## 1. What and why
- A170's eight cfgs with gate "interlock" "threshold":
  - S50 (50 pH, 3.0 ohm, A164's trims): nom l_p48_1us, nom L07_l_p48_1us, ff l_p48_1us, hot l_p48_1us, ss l_p48_1us;
  - S50t1: L x 0.7 with t_il 1.0 ns;
  - Q60 / Q75 L x 0.7 (A168's configurations and trims).
- All switches are gate-driven.
- Reference: the same row at 50 pH with ideal low sides and no interlock (A167 / A164), as in A168-A170. A170's run
  of the same name is shown alongside.

## 2. Criteria (A168's, a168_analyze.judge)
1. Whole-run max V_DS <= 40.0 V.
2. Vo(143.5 us) within 1.035 +- 0.02 V; physical start-up and handover peaks <= 200 A (<= ref + 3 A where the
   reference is above 197 A).
3. Post-step:
   - physical peak <= 200 A and <= ref + 5 A;
   - 0 overlaps, 0 shoot-throughs, COMPLETED;
   - late fires <= 1.5 x ref + 5;
   - NEW 0 where the reference has none, else <= 1.5 x ref + 5.
4. Vo: |extreme| <= |ref| + 2 mV; where |extreme| > 11 mV, back within 1 % <= ref + 2 us.

## 3. Predictions (not criteria)
- 0 shoot-throughs and COMPLETED everywhere.
- S50 nom / ff / hot as A169 within +-2 A and +-3 late fires (holds rare, <= 2 ns).
- S50 L x 0.7: handover <= 197 A, post-step within ref + 5 A, late <= 11.
- S50 ss: late fires as A167 (260 +- 40), peaks as A167 +- 3 A.
- t_il 1.0 ns: as 0.5 ns within 2 A.
- Q60 / Q75: no shoot-through. Criterion 2 misses on mode S's start-up peak (213.6 / 217.9 A, A168).

## 4. Decision rule
- S50 passes (late fires excepted where they have no peak, V_DS or Vo consequence): the package spec adds a driver
  interlock in threshold form (a turn-on's channel waits until the complement's gate is below threshold;
  <= 0.5-1 ns). The lead keeps A167's form, the open interlock item closes without an RTL change, and A169's
  plant (all eight switches gate-driven) becomes the reference plant.
- S50 misses a peak, V_DS or Vo criterion: the bounded signed dt_pred in the RTL goes to the user as the remaining
  route.
- Q60 / Q75 feed A168's loop-bound conclusion only.
