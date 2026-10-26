# A251 - the learner through the start-up, then its delay held (BOUNDARY)
Method: RTL + cosim (option 1172a40: cfg dt_hold_periods -> scb_ctrl cfg_dt_hold_n; unit 144 / 144, regression quick +
full PASS). Track A. Written and committed before the runs.
Looked at beforehand: A249 / A250. Also A246's 1 MHz records: before their peaks, phases 2-4's learner collapses to
2-4 ns with valleys of -93 to -161 A.
Decision it changes: whether the final configuration becomes "learner until HOLD_N phase-1 turn-ons in mode P, then
hold". That retires the learner (and its six rules) from operation after the start-up.
Cheaper checks done first:
- A249: a fixed delay in the closed loop;
- A250: D63 cannot carry the start-up, so the start-up keeps the validated learner.

Budget: 90 runs at 10 jobs, about 10 h. The decision rows are queued first (about 2 h); the rest is stopped if they fail.

## 1. What and why
- A249: with phases 2-4 at a fixed delay (the learner's own settled value), the N0 100 kHz lock is gone.
  - S75h's hard turn-ons go to 0.
  - Two transients lost what the learner's collapse did by accident: the train's first release (Vo minimum 2.5 mV
    lower) and the start-up ladder (rail 1 to 17.7 V while Vin ramps).
- Arm z = the final configuration + dt_hold_periods 256. From the 256th phase-1 turn-on in mode P (about 70-130 us
  after the entry), phases 2-4 keep their dt_pred; phase 1 learns as before.
  - The hold falls before the A240 train (300 us) on every board: mode P at 133-144 us, periods 0.28-0.65 us.
  - On the start-ups (mode P about 96 us) it falls after the ladder has come within 1 V in the final configuration.
- Rows:
  - A246's 46 (stage 1: A240's train at 10 k-1 MHz on N0 / N75 / S75h; stage 2: items 2 / 3, line and load steps,
    four modules, light loads, skips), with references A246's run_h_ (the final configuration);
  - A246's 4 position rows (N0 / S75h 100 kHz at k 2 / 4);
  - A245's 20 start-ups, in arm h (the final configuration: A245's cfg_r_ + hold_floor_ns 3.0, never run on
    start-ups) and in arm z.
- Not tested:
  - a re-learn after the hold (temperature drift, a new Vin level);
  - HOLD_N other than 256;
  - the hold value's spread;
  - restarts out of mode P (the counter resets and the learner restarts).

## 2. Criteria
- g0: unit 144 / 144, regression quick + full PASS (logs tmp/logs/a251_*.log).
- z1: N0 100 kHz at k 0 / 2 / 4: the peak after 300 us is <= 171.5 A (A240's q4; A246's g10).
- z2: every row is no worse than the final configuration.
  - Stage 1: peak after 300 us <= +2 A, and Vo's minimum >= -1 mV.
  - Stage 2: A246's g9 against A246's run_h_ (post-event peak +2 A, or +10 A on the wide rows; NEW <=; |Vo extreme|
    +1 mV; on skip rows the valley range within 1 A).
  - Start-ups: A245's g1-g3 hold in arm z where they hold in arm h, peak <= +2 A, and the end deviation <= max(arm h
    + 0.2 V, 1.0 V).
- z3: before the hold (its instant minus 0.5 us), arm z's turn-ons equal its reference's on every row (wiring).
- z4 (closes item 10's open part if it holds): p_N75_1000k and p_S75h_1000k meet A240's q1 and q2 (peak <= 200 A,
  V_DS, time above).
- Reported: arm h on the start-ups against A245's g1-g3 (the floor on start-ups); hard turn-ons; late fires.

## 3. Predictions (not criteria)
- z1 holds, at 149-161 A (A249).
- z2 misses on p_S75h_100k: the first release is about 2.5 mV lower (A249). The other stage-1 rows pass.
- Stage-2 rows whose events come before the hold are identical to the reference.
- z4: N75 1 MHz under 200 A with a probability of about 0.5; S75h 1 MHz (211 A) more likely.
- Arm h passes A245's g1-g3 on every start-up: the floor needs a held report with m_pos, which the start-ups rarely
  give.

## 4. Decision rule
- **g0 or z3 fails:** wiring; trace it before anything else.
- **z1 fails:** the held value is not the settled one (held mid-excursion); trace it.
- **z1 and z2 pass:** the user decides adoption (AskUserQuestion). With z4, item 10 closes at 1 MHz too.
- **z1 passes, z2 misses on rows:** name each row's cost. The user decides adoption with the trade: no learner in
  operation and no lock, against those costs.
- The queue's first 10 runs decide early: if z1 or z3 fails on them, the rest is stopped.
