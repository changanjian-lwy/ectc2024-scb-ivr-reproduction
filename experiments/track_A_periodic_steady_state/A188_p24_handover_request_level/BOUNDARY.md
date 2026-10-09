# A188 - the Vo handover request at 1.045 V, above the 25 C start-up (BOUNDARY)
Method: mixed (cosim, plant V5, code cfe581f; cfg: A186's with hand_vo_v 1.045 V)
Track A, package layer. Written and committed before the runs.
Decision it changes: the start-up spec's handover rule. A186 requested the handover at 1.03 V. That removed the hot
overshoot (1.129 -> 1.033 V) and the hot dips, but at 25 C it handed over while Vo was still rising (N13: +5.3 mV/us,
valleys 57 / 52 / 44 / 41 A against 41-45 A at 144 us). N13's minimum fell from 1.000 V (A185) to 0.982 V.
A request above the 25 C start-up and below the hot drift keeps A185 at 25 C and A186's fix hot.
Cheaper check done first: A185's records. Every 25 C run (and four modules) stays at or below 1.0358 V before its 144
us entry, so the latch never sets at 1.045 V and those runs are A185's bit for bit. One check run (S0, the highest)
shows it. Hot pre-entry maxima: N0 1.049, S0 1.127, S75 1.130 V (they trigger); F0 1.038 V (does not). Budget: 5
runs, ~1.5 h.

## 1. What and why
- At 25 C the trimmed boards settle at ~1.033 V, and handing over there (144 us, A185) is the cleaner entry. Hot,
  the locked mode-S trim drifts to 1.05-1.13 V, and the request at 1.045 V cuts that short during the input ramp.
- Runs: S75 125 C full (+4.8 V / 1 us at 500 us), S0 / N0 / F0 125 C to 500 us, S0 25 C to 150 us (identity check).
  The 25 C results are A185's (records-a185); the S75 125 C post-step positions are A187's question.
- Not tested: below 25 C; other rows; four modules hot.

## 2. Criteria
 g0 S0 25 C: no request before 144 us, sections up to 150 us equal A185's.
 Hot runs: c1 start-up / handover <= 200 A; c2 post-step <= 200 A (S75); c3 V_DS <= 40 V, COMPLETED, 0
 shoot-throughs / overlaps; c4 Vo at mode-P entry in 0.99-1.17 V (A163's cliff guard, now applied at the entry,
 since an early request puts 143.5 us inside mode P); c5 450-495 us per-phase peaks within +-3 A of the t0 = 400
 record (A186's S75 25 C settled 2.34 A away; A143 records the floor's history-dependent 2-4.5 A valley spread);
 c6 handover Vo minimum >= the t0 = 400 record's - 5 mV (F0: none); c7 Vo <= 1.05 V over 0-300 us.

## 3. Predictions (not criteria)
- g0 holds. Requests: S0 / S75 at ~131-132 us (Vin ~46 V); N0 at ~142-144 us or not at all; F0 none (144 us).
- c7: maxima <= 1.048 V (the request level plus a few mV). c6: S0 / S75 >= 0.99 V, N0 / F0 as in A185 / A184 (1.000 /
  0.999 V). Handover peaks <= 190 A.

## 4. Decision rule
- g0 and the hot runs pass: the start-up spec is t0 200 ns + per-board mode-S trim (cfg_ton_s) + bumpless seed (ton_ns)
  + handover at Vo >= 1.045 V or 144 us. Evidence: 25 C = A185 (c6 misses on the L0 boards by 1-4 mV, the period
  jump; worst handover minimum 0.989 V against the 400 ns design's 0.961 V), 125 C = A188. FINAL_SPEC, docs and the
  gate are updated.
- A hot run fails c1 / c3 / c4 / c7: the request level is wrong for that board; named, not adopted hot.
- g0 fails: code / cfg defect.
