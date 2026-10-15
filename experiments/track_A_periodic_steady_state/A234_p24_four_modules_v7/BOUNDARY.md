# A234 - four modules on plant V7 with the final controller (BOUNDARY)
Method: cosim (cfg only; code as at 63d7c8b).
Track A. Written and committed before the runs. Looked at beforehand: a 20 us smoke run of arm b (tmp, timing only:
173 s, four modules COMPLETED).
Decision it changes: whether the final configuration's controller (A229's damped loop, A231's handover lead) and plant
V7 can be stated for four modules. Four modules last ran on V5 (A172 / A173 / A192); C12 + lo_learn 4 (C13) is the
four-module design of record. Nothing since V6 (low sides 0.3 ohm, trims, r_core, ton_lat 16, ton_min 4.0, the damped
loop, the lead) has run on four modules.
Cheaper check done first: none fits - D63 has no multi-module block; the smoke run only checks that the cfg runs.
Budget: 6 runs to 500-510 us, about 1.5-2.5 h at 6 parallel jobs.

## 1. What and why
- Four N0 modules (nominal L0, 25 C) on one output with a common Ton and the slave floor (C12's arrangement), each with
  the one-module final configuration's plant and controller settings (a230 make_cfgs.adopted("N0")), without skipping:
  the slaves do not follow a pause (A216), and full-load rows do not reach the lower Ton limit.
- Arms: d0 = before A229 (no gate, no derivative term, no lead); b = the final configuration.
- Rows (system totals, as C12): +4.8 V / 1 us, +250 A (62.5 A per module) and -8 V / 10 us at 400 us (A143's lo_learn
  4 makes phase 1 timed at ~145 us, so 400 us is settled; C12 used 800 us from lo_learn 1024).
- Not tested: device or inductance spread between modules (C14 / D66), other boards and temperatures, the falling
  -4.8 V / 1 us, load release, skipping.

## 2. Criteria (arm b)
- f1: every module completes; whole-run peak <= 200 A, V_DS <= 40 V, no overlap or shoot-through on any module; Vo
  within 1 % over the last 20 us; no NEW oracle event from the event on.
- f2: post-event peak <= d0's + 5 A and |Vo extreme after the event| <= |d0's| + 2 mV (A152's four-module tolerance).
- f3: every module's phase-1 rail in mode P before the event <= 13.5 V (C10's lock gate).
- d0 is information: if d0 misses f1, the problem is plant V7 on four modules, not the controller.

## 3. Predictions (not criteria)
- Start-up <= 165 A, handover <= 185 A in both arms (one-module V7: 148.3 A at the handover on N0).
- +4.8 V / 1 us post 180-190 A, +250 A 180-185 A, -8 V / 10 us 165-175 A; b within 3 A of d0; rail 1 <= 12.9 V.

## 4. Decision rule
- f1-f3 pass: the four-module design of record becomes the one-module final configuration without skipping, on V7,
  for these rows; the coverage table's four-module column moves to V7 for them.
- d0 passes, b misses: the controller additions stay one-module; four modules keep d0's settings on V7.
- d0 misses f1: the V7 four-module problem is traced first.
