# A170 - a driver interlock for the high-side lead (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, D79; plant cosim/gate.py with the new interlock option;
frozen RTL controller; cfg only)
Track A, package layer. Written and committed before the runs.
Looked at beforehand: A168 and A169 while running. The L x 0.7 row shot through 8-9 us after the handover in A168 Q60
(60 pH / 3.5 ohm), A168 Q75 (75 pH / 4.0 ohm) and A169 (50 pH / 3.0 ohm, the adopted spec with gate-driven low sides).
- Phase 4's valley went to -43..-73 A (A167: -27..-38 A). The node then swings within ~2 ns of the low side's
  turn-off, and the high side (3-6 ns delay) cannot reach it.
- The error-based dt_pred fell to 0.4-2.5 ns while the ramped lead had grown to 3.2-3.6 ns, so the high-side command
  came before the low side's turn-off. This is A164's mechanism: a fixed lead removes the dt_pred >= 0 interlock.
  A167's spec passed only with ideal low sides.
Decision it changes: whether the package spec must name a driver interlock. The interlock holds a high-side gate until
the low side stops conducting (and the reverse). That is standard in integrated GaN drivers: adaptive dead times of
0.03-1 ns, workspace papers on dual-edge / double-sided adaptive dead-time driver ICs. It would also mean the 8 ns lead
is safe by construction, without touching the frozen RTL.
Cheaper check done first: 165 us smoke runs with the interlock (8d83e29) on A168 Q60 L07 and A169 L07: 0
shoot-throughs; high side held up to 9.5 ns; phase-4 late fires 29-31 by 165 us. Interlock off is unchanged (P60's
start-up equals 168163a's record to 150 us).
Budget: 8 runs to 1400 us (~3-4 h shared with A168 / A169).

## 1. What and why
- cfg gate "interlock" 1, "t_il_ns" 0.5: a turn-on commanded while its complement conducts is held until the
  complement's channel stops (gate-driven: its turn-off edge ended; otherwise its command), then starts 0.5 ns later.
  The delay is still counted from the original command, and the controller sees the physical turn-on as before.
- Every switch is gate-driven (A169).
- Rows:
  - S50 (adopted spec, A164's trims): nom l_p48_1us, nom L07_l_p48_1us, ff l_p48_1us, hot l_p48_1us, ss l_p48_1us;
  - S50t1: nom L07_l_p48_1us with t_il 1.0 ns;
  - Q60 / Q75 (A168's configurations and trims): nom L07_l_p48_1us.
- Reference: the same row at 50 pH with ideal low sides and no interlock (A167, else A164), as in A168 / A169.
  A169's run of the same row is shown alongside.

## 2. Criteria (A168's, a168_analyze.judge; each row against its reference)
1. Whole-run max V_DS <= 40.0 V.
2. Vo(143.5 us) within 1.035 +- 0.02 V; physical start-up and handover peaks <= 200 A (<= ref + 3 A where the
   reference is above 197 A).
3. Post-step:
   - physical peak <= 200 A and <= ref + 5 A;
   - 0 overlaps, 0 shoot-throughs, COMPLETED;
   - late fires <= 1.5 x ref + 5;
   - NEW oracle events 0 where the reference has none, else <= 1.5 x ref + 5.
4. Vo: |extreme| <= |ref| + 2 mV; where |extreme| > 11 mV, back within 1 % <= ref + 2 us.

## 3. Predictions (not criteria)
- 0 shoot-throughs and COMPLETED on every row (by construction).
- L x 0.7 rows (S50, S50t1, Q60, Q75): criterion 3's late fires miss (30-150; phase 4 stays held until dt_pred
  recovers). Peaks <= 200 A after the handover at S50; Q60 / Q75 keep mode S's start-up peak (213.6 / 217.9 A),
  so criterion 2 misses there.
- Other S50 rows as A169 within +-3 A and +-5 late fires; holds only around the handover and the steps.
- t_il 1.0 vs 0.5 ns: late fires +10-30 %, peaks within 2 A.

## 4. Decision rule
- S50 passes, or misses only on late fires with no peak, V_DS or Vo consequence: the spec adds "driver interlock
  (gate held until the complement stops conducting, <= ~0.5-1 ns)". The lead keeps A167's form, now safe by
  construction, and the interlock open item closes without an RTL change.
- S50 misses a peak or Vo criterion: the interlock alone is not enough. The bounded signed dt_pred in the RTL is
  needed, which changes the frozen controller and goes to the user first.
- Q60 / Q75: they only say whether the interlock removes the larger loops' shoot-through. The loop bound itself is
  A168's result.
