# A193 - the slow boards' 9.5 ns lead below 25 C, +4.8 V / 1 us (RESULTS)
Boundary: d96b6a2. Records: release records-a193 (9 runs, logs). Analysis: a193_analyze.py -> a193_summary.json.
Code cfe581f, plant V5, t_il 1.0 ns, A188 start-up with A190's cold trims, board S75 (slow devices, L x 0.75).

## 0. Verdict
- **All 9 runs pass c1-c3 and c7. The 9.5 ns lead passes at -40 and 0 C at all three step positions, so by the
  decision rule the slow boards' lead holds over -40..125 C on this row (tested points).**
- Post-step peaks (step positions p0 / p1 / p2):
  - 9.5 ns, -40 C: 191.1 / 191.2 / 195.0 A.
  - 9.5 ns, 0 C: 194.5 / 194.7 / 197.8 A.
  - 8 ns, -40 C: 197.4 / 191.9 / 189.4 A.
- **Worst S75 peak with 9.5 ns over -40 / 0 / 25 / 125 C: 197.8 A (0 C, p2). The margin is 2.2 A.** (25 C:
  197.1 A, A192; 125 C: 196.9 A, A191.)
- At -40 C the lead does not raise the worst case (195.0 against 197.4 A). Position by position it moves the peak
  by -6.3 / -0.7 / +5.6 A, so the step position matters as much as the lead.
- Start-up 135.5-135.7 A, handover 150.7-154.9 A, V_DS <= 33.8 V, 0 shoot-throughs, Vo <= 1.0345 V over 0-300 us.
- Diagnostic, no criterion: cold runs have more one-period spikes (10-22 A above the neighbouring periods, never
  above 187.8 A).
  - Count per run: -40 C 158-185 with 9.5 ns and 207-282 with 8 ns; 0 C 58-79; 25 C 37-44 (A192).
  - 61-62 of them at -40 C fall at 170-300 us, after the 144 us handover, with either lead (22 at 0 C).
  - With 8 ns at -40 C the spikes continue past 700 us (18-66 events), so those runs are not settled
    at their end. With 9.5 ns 0-10 remain.
  - Post-step late fires at -40 C: 109-153 with 9.5 ns, 194-210 with 8 ns.
- Vo dips: 9.5 ns -10.7..-11.9 mV at -40 C and -13.2..-14.5 mV at 0 C; 8 ns -8.3..-10.1 mV at -40 C.

## 1. Criteria
| run | c1 start / hand | c2 post-step (p0 / p1 / p2) | c3 V_DS | c7 Vo max | late / NEW |
|---|---|---|---|---|---|
| -40 C, 9.5 ns | 135.5 / 154.9 | 191.1 / 191.2 / 195.0 | <= 32.9 V | 1.0337 | 109-153 / 158-185 |
| 0 C, 9.5 ns | 135.7 / 150.7 | 194.5 / 194.7 / 197.8 | <= 33.8 V | 1.0345 | 91-106 / 58-79 |
| -40 C, 8 ns | 135.5 / 153.0 | 197.4 / 191.9 / 189.4 | <= 31.7 V | 1.0337 | 194-210 / 207-282 |
25 C at the same positions: 9.5 ns 196.1 / 195.8 / 197.1 A (A192), 8 ns 192.5 / 191.5 / 192.7 A (A184).

## 2. Predictions
- Held: c1, c3 and c7 pass. Post-step bands: 9.5 ns 191.1-195.0 A (registered 191-203), 8 ns 189.4-197.4 A
  (registered 188-200). The open question, whether 9.5 ns clears 200 A at -40 C, is answered yes at these positions.

## 3. Limits
- One board (S75), one row, three step positions per temperature. With a 2.2 A margin and a peak this sensitive to
  position, more positions could exceed 200 A.
- The device model is extrapolated below 25 C (A190).
- Not run cold: other rows, S0 / S80 / four modules, nominal boards after a step.
- The -40 C spike trains (after the handover, and to the end of the 8 ns runs) are not traced.
