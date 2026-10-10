# A189 - the adopted start-up below 25 C (RESULTS)
Boundary: 5495576. Records: release records-a189 (12 start-ups to 200 us, log). Analysis: a189_analyze.py ->
a189_summary.json. Code cfe581f, plant V5, t_il 1.0 ns. Below 25 C the EPC model's linear temperature factors are
extrapolated.

## 0. Verdict
- **FAIL as registered: the adopted start-up does not hold below 25 C on slow boards.**
  - At -40 C both slow boards fall below A163's cliff: mode-S Vo(143.5) 0.955 / 0.957 V, handover 264.2 / 277.9 A.
  - At 0 C the slow L x 0.75 board hands over at 1.006 V but peaks 211.1 A; slow L0 reaches 198.0 A.
  - Nominal, ff and L x 1.3 boards pass at 0 and -40 C: entry Vo >= 1.015 V, handover <= 194.4 A.
- **Two causes.**
  1. Mode S's Vo follows the gates' temperature on every phase (all turn-ons hard). Slow boards fall ~1.2 mV/K
     below 25 C: 1.034 -> 1.005 -> 0.955 V at 25 / 0 / -40 C. Nominal boards fall ~0.26 mV/K, ff ~0.12 mV/K.
  2. The bumpless seed assumes the 25 C entry Vo. ton_ns = T_ss + (kp + ki)(Vo_cal - 1 V) builds in the kp step
     that a 1.0345 V entry produces. At 0 C the entry is 1.006 V, so that step is ~11 ns smaller and the first
     loop Ton lands ~11 ns above steady state. Handover 211.1 A at Vo 1.006 V, above the cliff.
- **The 400 ns start-up also fails cold on the slow L0 board:** -40 C entry 0.996 V, ladder max/min 1.73, handover
  242.2 A. Nominal L0 passes (1.023 V, 151.6 A). So no tested start-up holds the slow corner at -40 C.
- Predictions: slow boards ~0.97 V at -40 C (measured 0.955-0.957: the drift is steeper cold, 1.2 vs 0.95 mV/K);
  nominal >= 1.02 V (1.015-1.017); the 400 ns S0 ~1.010 V (0.996 V, and it failed through its ladder split). The
  0 C slow L x 0.75 failure above the cliff was not predicted.

## 1. Criteria
| board | 0 C: entry Vo / start / hand (A) | -40 C: entry Vo / start / hand (A) |
|---|---|---|
| S75 | 1.006 / 132.9 / **211.1** | **0.956** / 128.0 / **264.2** |
| S0 | 1.007 / 121.1 / 198.0 | **0.958** / 116.7 / **277.9** |
| N0 | 1.026 / 124.3 / 170.8 | 1.015 / 123.4 / 193.1 |
| F0 | 1.029 / 124.8 / 194.4 | 1.024 / 124.4 / 168.9 |
| N13 | 1.027 / 116.1 / 152.2 | 1.016 / 115.3 / 160.4 |
| 400 ns N0 / S0 | - | 1.023 / 161.3 / 151.6; 0.996 / 163.2 / **242.2** |
c3 passes everywhere (V_DS <= 38.2 V, 0 shoot-throughs).

## 2. Limits
Start-ups to 200 us only; device model extrapolated below 25 C; four modules not run.

## 3. Decision (BOUNDARY Section 4)
The adopted spec is stated for 25-125 C. The candidate fix is a temperature-compensated mode-S trim: ton_s(T) =
ton_s(25 C) + dVo(T) / 0.0535 V/ns, with dVo per device corner from a characterised table. It brings the entry Vo
back to ~1.035 V, where the bumpless seed holds. A190 tests it on boards the table was not taken from.
