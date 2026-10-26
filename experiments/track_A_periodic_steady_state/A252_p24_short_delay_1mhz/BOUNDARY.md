# A252 - a short held delay on the 1 MHz train (an oracle for item 10's open part) (BOUNDARY)
Method: cosim, cfg only (A249's dt_fix_ns). Track A. Written and committed before the runs.
Looked at beforehand:
- A246's 1 MHz records: S75h's learner sits collapsed through the train (dt_pred median 4.2-4.4 ns; 211.1 A);
  N75's stays at 13-15 ns (244.6 A);
- A251: holding about 11-12 ns gives S75h 224.4 A and N75 246.9 A;
- T37: N75 1 MHz gave 237.5-289.0 A in every arm of A241-A246.

Decision it changes: whether the turn-on delay can close item 10 at 1 MHz (then a deliberate short-delay mode for
trains), or not (then a cycle-by-cycle current limit, the standard protection of constant-on-time regulators).
Cheaper check first: none. D63 misses the delay's gate behaviour (A250). Budget: 3 runs on the 3 cores A251's
start-ups leave free, about 2 h.

## 1. What and why
- A251 found the learner's collapse lowers the S75h 1 MHz peak by 13 A against a held 11-12 ns. A shorter delay lowers
  the slotted phases' effective duty.
- Arms (phases 2-4 held from reset):
  - s4: S75h at the learner's own train median (4.41 / 4.34 / 4.16 ns);
  - n5 / n9: N75 at 5 / 9 ns.
- Not tested: a delay that switches between steady state and the train; other trains; the cost in steady state
  (hard turn-ons before the train).

## 2. Criteria
- k1 (per arm): A240's q1 and q2 on the row (whole-run peak <= 200 A, V_DS, time above).

## 3. Predictions (not criteria)
- s4: within 5 A of 211.1 A (the same delays as the learner's), so k1 misses.
- n5 / n9: 230-250 A, k1 misses. T37 puts N75's 1 MHz in the ladder, not the delay.

## 4. Decision rule
- **k1 passes on N75:** the delay can close 1 MHz. Design a train-time short-delay mode.
- **k1 misses on N75:** item 10's 1 MHz part is not a delay question. The next step is a cycle-by-cycle current limit
  (first in D63, then RTL).
