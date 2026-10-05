# C13 - random-stimulus test of the four-module design (BOUNDARY)
Method: RTL (cosim of random stimuli; A142's event oracles on every module, no model fitted)
Track C (four modules). Written and committed before any run. Looked at beforehand: A143 RESULTS, A142 generator / oracles / BOUNDARY.
Decision it changes: freeze the four-module design (C12 + lo_learn 4) as final and close the multi-module level, or open a C14 RTL fix.
Cheaper check done first: none (A142 on one module found its defect only by random draws; D63 has no arbitration).
Budget: 30 four-module runs + I0, 32.4 ms simulated, ~70 min at --jobs 10.

## 1. What and why
- Design under test: A143 `cfg_g5_l_p48_1us_k4` = C12 four-module design + lo_learn 4 (adopted; one module frozen).
- Generator `make_cfgs.py` = A142's (numpy default_rng(13), `c13_inputs.json`): L x U(0.7,1.3), Cs x U(0.7,1.3), driver mismatch
  U(+-3.4) ns, low-edge jitter U(0,100) ps; strata L 12 (line step), B 6 (line + load), D 6 (load), S 6 (one step at U(145,900) us:
  mode-P comparator phase, the ~1.5 us window after the handover). L/B/D steps at U(1000,1010) us (lo_learn 4: timed from ~146 us).
  Line dv U(+-1,+-8) V, slew log-U(1,50) us; load U(+-10,+-62.5) A; t_end = last event end + 150 us. records_last 16000.
  I0 = the template verbatim (A143's run_g5_l_p48_1us_k4).
- Oracles: `a142_oracles.check` on all four modules (duplicates floor-first / race K1 / other, order, alternation, spikes, non-predictive
  turn-ons; known K1-K4), plus rails.
- Not tested: >4 modules, start-up before mode P + 20 us, peaks against a spec (A139 owns the single-module map).

## 2. Criteria (all 30 runs)
1. Floor-first duplicate turn-ons: 0 (every module).
2. Record overlaps 0; alternation hits 0.
3. NEW hits 0 (duplicate other than K1 / floor-first, order outside K2, spike outside K4, non-predictive turn-on outside K3).
4. Settling: COMPLETED from unmodified sources; |Vo_end - 1| <= 1 %; ladder deviation at the end <= 0.03.
5. I0 replays A143's record bit for bit (turn-on, high-off lists, ipk, all modules).
6. Handover rails (C10.rails limits): every module's rail 1 <= 13.5 V, <= 5 us above 13.3 V, mode P before min(242 us, first step).

## 3. Predictions (not criteria)
- K1 in 5-20 % of runs. Post-disturbance peak <= 200 A in >= 85 % of L/B/D (single-module A139 map; four modules had +-2 A of it).
- S rows near 145 us: no prediction; late fires only transient.

## 4. Decision rule
- 1-6 pass: four-module design frozen, multi-module level closed (CURRENT_STATUS, scorecard, scb-map).
- 1-3 / 6 fail: trace the event window on the failing draw (Opus); arbitration defect -> C14 fix with the draws as regression rows;
  plant transient with every edge in its window -> new known class, design frozen.
- 4 fails: lock / settling diagnosis (A134 method). 5 fails: toolchain changed - stop.
