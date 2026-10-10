# A192 - the 9.5 ns lead on the slow corner's other rows (RESULTS)
Boundary: 31a4be0. Records: release records-a192 (14 runs, logs). Analysis: a192_analyze.py -> a192_summary.json.
Code cfe581f, plant V5, t_il 1.0 ns, the A188 start-up, driver hs_on_lead_ns 9.5. Gate: 60 pass, 0 fail.

## 0. Verdict
- **All 14 runs pass c1-c3, c7 and c10, so the lead is adopted (BOUNDARY Section 4).** Slow boards (25 C trim in the
  slow class) use 9.5 ns, all others 8 ns. With A191, slow devices hold 200 A after +4.8 V / 1 us at 125 C with
  L x 0.75 (194.1-196.9 A) and L x 0.8 (190.6-192.8 A), at six step positions each.
- Safety and start-up: start-up <= 135.7 A, handover 154.0-172.1 A, V_DS <= 34.9 V, 0 shoot-throughs, Vo <= 1.0475 V
  over 0-300 us, every run COMPLETED.
- **Where it helps:**
  - -8 V / 10 us: the post-step late fires fall to 0 / 7 / 21 (A179 at 8 ns: 12 / 32 / 22).
  - +4.8 V / 1 us: S75 25 C 45-92 late fires (A184: 163-170); four modules 148 (A179 / A173: 417-487).
- **What it costs: at 25 C on +4.8 V / 1 us the peaks rise a few A and the dips deepen.**
  - S75 25 C, step positions p0-p2: 196.1 / 195.8 / 197.1 A against A184's 192.5 / 191.5 / 192.7 and A185 / A186's
    191.9 / 192.4 (p0). The Vo extreme moves from -9.5..-13.1 to -13.8..-17.5 mV. The return to within 1 % takes
    21-37 us instead of 0-19.
  - Four modules: 185.2 A against 180.0-183.2 A, and -15.7 against -9.9..-12.9 mV.
  - Mechanism (S75 p0 against A184 p0): the steady valleys are 1.3 A deeper (-15.8 / -14.5 A). In the first 30 us
    after the step the deepest valleys on phases 2-4 reach -72 / -91 / -88 A, against -49 / -76 / -67 A. The lead
    turns on earlier than the gate delay at 25 C needs. That is the same chain as A187: the valleys draw charge back,
    Vo dips, and the loop raises Ton.
- **Worst S75 peak over 25 and 125 C:** 197.1 A with the lead, against 207.2 A without it (A187). The 25 C margin
  narrows, but the lead-8 spread at 25 C already reached 198.7 A (A181 p0, the 400 ns start-up). A temperature-
  scheduled lead (8 ns cold, 9.5 hot) would not lower the worst case below that, so it is not run.

## 1. Criteria (every module)
| row (k = step positions) | c1 start / hand | c2 post-step | c3 V_DS | c7 / c10 | late / NEW (8 ns ref) |
|---|---|---|---|---|---|
| S0 25 C -8 V / 10 us, k 0-2 | 123.6 / 164.1 | 169.3-170.2 (169.4-170.0) | 28.1 | 0 / 7 / 21 <= 36.5 | 0/7/21 / 0/0/0 (12/32/22 / 1/5/1) |
| S0 25 C +62.5 A load, k 0-2 | 123.6 / 164.1 | 182.7-183.8 (183.8-184.5) | 28.1 | pass | 0 / 22/23/5 (0 / 13/21/24) |
| S0 25 C +4.8 / -4.8 V 1 us | 123.6 / 164.1 | 181.4 / 177.3 | 30.9 / 28.1 | pass | 26/0 / 2/0 |
| S0 125 C +4.8 V 1 us, -8 V 10 us | 126.5 / 172.1 | 182.7 / 166.8 | 30.9 / 27.9 | pass, c10 0 | 3/0 / 0/4 |
| S75 25 C +4.8 V 1 us, k 0-2 | 135.7 / 154.0 | 195.8-197.1 (191.5-192.7) | <= 34.9 | pass | 45-92 / 37-44 (163-170 / 58-85) |
| four modules 25 C +4.8 V 1 us | 123.6 / 158.8 | 185.2 (180.0-183.2) | 32.1 | pass | 148 / 4 (417-487 / 5-22) |
The references are lead-8 runs at the same row and position. A179 (t_il 1.0 ns) covers -8 V and the load step;
A184 covers S75. The four-module references are A179 t_il 0.5 / 1.4 ns and A173, all with the 400 ns start-up.

## 2. Predictions
- Held: c1-c3, c7 and c10 everywhere; the -8 V late fires fall below A179 at every position.
- Held as a range: load-step NEW 5-23 is within A179's 7-27, though p0 is above its own position (22 against 13).
- Vo extremes within +-1 mV of A179: held on the load step (<= 0.2 mV). On -8 V the difference is 0.1 mV at p0.
  p1 is the same magnitude with the opposite sign, and p2 is 1.6 mV smaller.
- No prediction was registered for the S75 / four-module +4.8 V costs. They are reported above, not hidden by the
  pass.

## 3. Limits
- 25 and 125 C only. The cold slow boards (A190's table) were not run with 9.5 ns.
- Slow L x 0.8 is tested on +4.8 V / 1 us at 125 C only (A191). Nominal and ff boards keep 8 ns, not retested.
- Three step positions per row at 25 C. On +4.8 V the S75 margin is 2.9 A at the worst tested position.
