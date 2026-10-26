# A250 - the turn-on delay as a ladder lever: the start-up ladder in D63 with the clamp block (BOUNDARY)
Method: math (D63 with an A250 block, cfg-gated, default off: 20 / 20 D63 tests unchanged). Track A.
Written and committed before the replays. Looked at beforehand:
- A249's records (a249_trace): the fixed arm's start-up ladder and phases 2-4's delays and V_DS;
- D63's code: the clamp ramps the current, but its charge never reaches the ladder, and the delay t_tr is also the
  swing's valley time.
Decision it changes: how step 3 times phases 2-4's turn-on.
- If the clamp is the lever, the turn-on must bound the clamp: an event (V_DS comparator) or a clamp-aware schedule.
  A fixed value is not enough.
- If not, the start-up ladder needs its own path (literature).
Cheaper check first: this is it (D63, seconds per replay), before any RTL or cosim. Budget: < 1 h.

## 1. What and why
- A249: with phases 2-4 at a fixed delay, the 75 A start-up on S75h (u_S75h_30, 30 % load, r_load 13.3 mOhm) sends rail
  1 to 17.7 V while Vin ramps (deviation 6.4 V at 137 us). The learner's run stays within 1 V from about 130 us.
  - Fixed arm: phases 2-4 turn on 13.4-14.1 ns after t_lo, deferred by the driver interlock, on a node already clamped
    (V_DS -1.5 to -2.1 V), with valleys of -48 to -60 A.
  - Learner: it collapses to 3.6-3.8 ns (V_DS 1.6-3.8 V).
- Hypothesis: while the node is clamped (the high side reverse-conducting), the inductor sees the rail as if the high
  side were on. A clamp lengthens the phase's effective on-time, so its rail falls (in an SCB, rail_k D_k ~ Vo).
  - A lower rail lowers I_th, so the crossing is deeper, the node reaches the rail sooner, and the clamp at a fixed
    delay is longer. That is positive feedback.
  - Bounding the clamp breaks it.
- D63 block (A250; p24_valley_map.Design):
  - t_val: the node's own valley time, apart from the turn-on t_tr;
  - t_sw0: the swing starts after the low side's turn-off (1.65 ns, A248);
  - clamp_q: the clamp's reverse charge through the high side enters the ladder;
  - t_evt: a crossing phase turns on that long after the node reaches the rail (a V_DS comparator), with t_tr as the
    backstop.
- Replays (a250_d63.py), each from the record's state at mode P's entry (95.6 us), with the record's Vin ramp, to
  300 us:
  - rec_s: each phase's delay as the fixed arm recorded it (A249 run_s_u_S75h_30), per 1 us;
  - rec_l: as the learner's run recorded it (A245 run_r_u_S75h_30);
  - c11 / c135: phases 2-4 constant at 11.0 / 13.5 ns (steady / deferred);
  - evt1 / evt2: t_evt 1 / 2 ns, backstop 13.5 ns;
  - each with clamp_q on; rec_s and rec_l also with it off.
- Board: S75h, L 2.2 nH. D57 thresholds over 3-20 V (25 C Coss); t_val = A124's D57 valley times scaled by
  sqrt(L).
- Not tested: other boards and loads, the first load release (reported only, if cheap), the driver's deferral (it
  enters only through the recorded delays).

## 2. Criteria (deviation = max |rail - Vin / 4|)
- k1: rec_s (clamp_q on) reproduces the fixed arm. Its peak deviation is within +-40 % of 6.4 V, peaks within 15 us
  of 137 us, and is >= 3 V at 140 us.
- k2: rec_l (clamp_q on) reproduces the learner: <= 1.5 V at 140 us (record 0.29 V).
- k3: an event turn-on (evt1 or evt2) is <= 1.5 V at 140 us, with a peak no higher than rec_l's.

## 3. Predictions (not criteria)
- rec_s with clamp_q off still diverges, but less (the effective-duty part is in the current already).
- c135 behaves like rec_s; c11 lies between rec_s and rec_l.
- In rec_s, the per-period clamp time of phases 2-4 grows while rail 1 rises (the feedback).

## 4. Decision rule
- **k1 and k2 pass:** D63 carries the start-up ladder, and the clamp is the lever. Step 3 picks the turn-on law in
  D63, then RTL + cosim. With k3 the law is an event-bounded clamp; without it, look for a ladder-balance path.
- **k1 fails:** D63 misses the start-up ladder (not the clamp, or a missing block). Trace it, or test the lever
  directly in cosim (a per-phase delay offset during the start-up).
- **k1 passes, k2 fails:** the learner's benefit is something D63 lacks. Trace it.
