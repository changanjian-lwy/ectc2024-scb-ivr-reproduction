# A249 - one fixed turn-on delay per board in the closed loop (an oracle test of A247 / A248) (BOUNDARY)
Method: RTL + cosim (cfg-gated option; code b3093a2, values and cfgs committed before the runs).
Track A. Looked at beforehand: the learner's settled dt_pred in A246's records (per board, phases 2 / 3 / 4) and the
plant harness's command-to-turn-on map (a249_values.py); no run of the option.
Decision it changes: whether the learner's per-period adaptation of phases 2-4 is needed on the rows where it locked
or cost. If a fixed delay per board does as well, step 3 designs how a controller finds that value (slow calibration)
in place of A236-A246's rules.
Cheaper check done first: A247 / A248, open loop on 1.27 M recorded turn-ons. The closed loop depends on the gate's
command-to-turn-on behaviour (two regimes, 2.6-3.0 ns or 8-10 ns), which D63 lacks; that is a question for the
physical model (memory choose-math-vs-physical-model). Budget: 18 runs at 10 jobs, about 2.5 h.

## 1. What and why
- A247 / A248: the plant's soft windows nest, so one delay per board, phase group and rail keeps V_DS <= 2 V for 99.5 %
  of the currents that have a window. The learner drifts to either end, because a full swing clamps the node and the
  valley is flat. Where it is more than 2 ns off that delay, the delay gives a median 0.05 V against the recorded 2.87 V
  (open loop).
- Option (b3093a2): bridge "dt_fix_ns" -> RTL cfg_dt_fix. Phases 2..4 start at the given dt_pred and no report changes
  it; phase 1 learns as before. Off: unit 141 / 141, regression quick and full PASS.
- Arms (a249_values.json), dt_pred (ns) for phases 2 / 3 / 4:
  - s, the learner's own settled value (median of A246's arm-h ends):
    - N0: 17.344 / 17.312 / 15.812;
    - N75: 16.031 / 16.031 / 15.313;
    - S75h: 11.875 / 11.875 / 11.062.
  - o, A248's choice at 12 V mapped to a command through the plant harness (i_off -17 A):
    - N0: 16.6 / 16.6 / 15.5;
    - N75: 15.2 / 15.2 / 14.8;
    - S75h: 11.6 / 11.6 / 11.1.
- Rows (references: the final configuration's records):
  - stage 1 (A240's train): p_N0_100k at k 0 / 2 / 4 of T / 6 (the lock), p_N0_60k, p_N75_100k, p_S75h_100k (A246's
    cost);
  - stage 2: a_S75h_d20 (item 2's re-application), f_N75_k4 (item 3's falling line);
  - start-up: u_S75h_30 (item 6c). Its reference is A245's run_r (rev_n 16, before the floor; the floor was never run
    on start-ups).
- Not tested: four modules, other start-ups, F0 / N13 boards, rails outside 10-14 V at the fixed value, a controller
  that finds the value itself.

## 2. Criteria (each arm)
- c0: the run's phases 2-4 dt_pred at its end equals its dt_fix_ns within one LSB (31.25 ps).
- c1: N0 at 100 kHz at k 0 / 2 / 4: the peak after 300 us is <= 171.5 A (A240's q4, as A246's g10).
- c2: every other row is no worse than its final-configuration record.
  - Stage 1: peak after 300 us <= +2 A, and Vo's minimum >= -1 mV.
  - Stage 2: post-event peak <= +2 A (+10 A on a_S75h_d20, inside item 2's hold-off), NEW <= the reference's, and
    |Vo extreme| <= +1 mV.
  - Start-up: every rail within 1.0 V of Vin / 4 at the end, and Vo after mode P >= min(0.99 V, the reference's
    minimum).
- Reported: hard turn-ons of phases 2-4 (V_DS > 6 V at the actual turn-on, from 20 us after mode P, as A245), late
  fires, V_DS maxima.

## 3. Predictions (not criteria)
- c1 holds in both arms at 145-160 A (A246: 150.9 / 156.4 / 156.3 A).
- p_S75h_100k: Vo's minimum within 1 mV of A246's record, which also has no collapsed phase.
- u_S75h_30: in band at the end (<= 0.3 V). A fixed delay cannot lengthen into A245's lock.
- Hard turn-ons are fewer than the reference on the N0 100 kHz rows.
- Risk: the start-up and handover, where dt_pred used to learn from dt_init 16.4 ns at low rails. A fixed value
  chosen at 12 V may give hard turn-ons early in mode P.

## 4. Decision rule
- **c0 fails:** the option is wired wrong; trace it.
- **c1 and c2 pass in arm s:** a fixed delay per board suffices on these rows. Step 3 registers how a controller
  finds the value. It also widens the rows: four modules, start-ups on every board, items 2 / 3.
- **c1 passes, c2 misses on a row:** name what the per-period adaptation bought on that row (rail, current), before
  step 3.
- **c1 fails:** the lock is not only the learner; trace it.
- Arm o against arm s is reported (centring in the window); it does not decide.
