# A186 - the handover requested on Vo (BOUNDARY)
Method: mixed (cosim, plant V5, RTL e1cf0a7 (cfg_ton_s); bridge option "hand_vo_v": the sequencer raises hand_req
once a phase-1 Vo sample (the ADC's instant) reaches it, or at t_hand, whichever is first, for every module at once.
cfg: A185's cfgs + hand_vo_v 1.03 V.)
Track A, package layer. Written and committed before the runs (with the bridge code).
Decision it changes: whether the start-up spec (t0 200 ns + mode-S trim + bumpless seed) also holds hot when the
handover follows Vo rather than the clock. FINAL_SPEC's start-up row would then cover 25 and 125 C, and the
start-up overshoot would drop from 126-129 mV (slow boards hot, A184) to the request level.
Cheaper check done first: A184 / A185 records. With the handover at 144 us the hot slow boards enter at Vo 1.126-1.130 V,
kp x (Vo - 1 V) = 45-48 ns puts Ton on the 0.5x clamp for > 5 us, and Vo undershoots to 0.975-0.978 V. At 25 C the
trimmed boards reach 1.030 V within the last ~2 us before 144 us, so the request changes little there. Gates on the
bridge code (352828c): cosim_regression --full PASS; A183's N13 start-up rerun identical in every field. One smoke run
(S75 125 C to 170 us): request at 129.6 us at Vin 45.4 V; Vo maximum 1.033 V (A185: 1.129 V); minimum after entry
0.996 V (A185: 0.977 V). Peak 187.5 A at 148 us on phase 1, near the end of the 20 us lead ramp, with the loop's Ton
at 38.5 ns against 30.7 ns steady. Budget: 12 runs, --jobs 6, ~2.5 h.

## 1. What and why
- The locked mode-S trim drifts +15..+95 mV at 125 C at 200 ns (every turn-on hard, gate speed acts on every
  phase). With a fixed 144 us handover, mode P starts from that drifted state, so the hot boards dip and overshoot
  the 50 mV start-up limit of VRD 11.1 (A103). Requesting the handover at Vo 1.03 V makes the entry state the same at
  every temperature; the hot slow boards enter during the input ramp (~44 V).
- This is a sequencer change, not an RTL change. In hardware it is a comparator on the sampled Vo driving hand_req
  (an external supervisor, or one compare on the controller's ADC code if it moves into the RTL).
- Runs: A185's 11 (every 25 C board, four modules, N0 / S0 / S75 at 125 C) + F0 at 125 C. S75 25 C, N0 25 C and S75
  125 C are full runs (+4.8 V / 1 us at 500 us).
- Not tested: below 25 C (a cold board whose mode-S Vo never reaches 1.03 V falls back to 144 us at its own Vo);
  other rows; four modules at the corners.

## 2. Criteria (a184_analyze definitions; every module)
 g0 Sections up to A186's mode-P entry equal A185's run of the same condition (mode S unchanged until the request).
 c1 start-up / handover <= 200 A;  c2 post-step <= 200 A (full runs; S75 125 C: A181 / A184 show 202.8 / 206.7 A at
    step phases 0.81 / 0.86, a mode-P item, so a miss there is read against that, not against the handover);
 c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs / overlaps;  c4 Vo(143.5 us) in 0.99-1.17 V;
 c5 450-495 us per-phase peaks within +-2 A of the t0 = 400 record (F0 125 C: none);
 c6 handover Vo minimum >= the t0 = 400 record's - 5 mV, at 25 and 125 C;
 c7 Vo <= 1.05 V over 0-300 us (start-up overshoot <= 50 mV).
Diagnostic: request and entry times, Vin at entry, the loop's Ton after entry.

## 3. Predictions (not criteria)
- Requests: 25 C boards at 142-144 us; N0 / F0 hot ~135-141 us; S0 / S75 hot ~125 us at Vin ~43.5-44 V.
- c7 passes everywhere (maxima <= 1.04 V). Hot minima >= 0.99 V. Handover peaks <= 190 A (the smoke run's 187.5 A
  on S75 125 C is the closest). 25 C results within +-3 A / +-3 mV of A185, so c6 at 25 C misses on N0 / F0 / four
  modules as in A185 (the period jump).

## 4. Decision rule
- c1-c7 pass (c2 at S75 125 C read as above): start-up spec = t0 200 ns + per-board mode-S trim (cfg_ton_s) + bumpless
  seed (ton_ns) + Vo-requested handover at 1.03 V, at 25 and 125 C. Update FINAL_SPEC, docs, acceptance gate.
- c6 / c7 fail hot only: adopt for 25 C (A185's spec), hot named open with the mechanism.
- Anything fails at 25 C: the Vo request harms the 25 C start-up; not adopted.
