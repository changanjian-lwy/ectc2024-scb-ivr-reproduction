# A243 - leave the turn-on delay on every report without reversal (items 10 and 3) (BOUNDARY)
Method: cosim, cfg only (A236's early_hold_a and A242's late_hold_a together; no code change since A242's 7f64828).
Track A. Looked at beforehand: A242's records (all 47 rows) and A236's results.
Decision it changes: whether the final configuration ignores dt_pred reports from periods whose current did not
reverse. That would close item 10 (repeated load steps) and item 3 (the climb after a falling step) together.
Cheaper check done first: the records (below). No cheaper model has a dt_pred block.
Budget: 46 runs in one queue at 10 jobs (stage 1 first, then the four-module rows), about 5.5 h. No identity row,
because there is no code change.

## 1. What and why
- **A242 (hold on late reports with m_pos):**
  - Fixed the repetition: every 10-200 kHz row <= 159.7 A. N0's overshoot 1.0513 V for <= 0.92 us (A241 1.0538 V);
    the 10 kHz late fires 496 -> 12.
  - Made item 3 worse. f_N75_k2: 173.7 against 153.7 A, with a K3 and a NEW. f_N75_k4 +9.4 A; f_N75_k0 +2.3 A.
- **The trace** (f_N75_k2, phase 3): after the falling step the low-side turn-off current stays at +7..+11 A, so every
  report is early with m_pos. dt_pred climbs 0.28 ns per period (24.7 -> 28.1 ns), the restart fires, and when the
  valley returns (-19, -22 A) the delay is about 8 ns too long: a 174 A spike.
  - In the reference the same no-reversal periods also gave "late" reports (the ring) that offset the climb, and
    dt_pred stayed at 15.3-15.9 ns.
  - Neither kind of report measures a swing, because the node cannot swing without a reversed current.
  - A236 held the early ones: item 3's events went, but item 10 was untouched. A242 held the late ones: item 10 went,
    and item 3 climbed unopposed.
- **Arm b:** early_hold_a 0.0 and late_hold_a 0.0. Any report with m_pos leaves dt_pred; reports with a reversed
  current work as before.
- **A236's costs with the early hold alone (to watch here):**
  - four modules, -8 V / 10 us: undershoot 3.0 mV deeper and peak +2.6 A;
  - a_S75h_d2: three spikes 10-12 A above their neighbours (peak unchanged).
- **Basis:** as A242 (Zhang et al., TPEL 2023: zero voltage needs a reverse current; Chiang & Chen, TPEL 2009). The
  rule to ignore such reports is ours.
- **Rows:** A241's / A242's 46 (stage 1: A240's 18; stage 2: A236's 25 and A237's three), against the same references.
- **Not tested:** thresholds other than 0 A; four modules under the accelerator load.

## 2. Criteria (A242's g1-g7; g0 replaced)
- g0: no change under src/ between A242's code (7f64828) and every run's commit, and A242's g0.
- Stage 1, every row:
  - g1: A240's q1 (whole run: peak <= 200 A, V_DS <= 40 V, no overlap or shoot-through).
  - g2: A240's q4 (peak after 300 us <= the board's single re-application + 10 A).
  - g3: A240's q2 and q5.
  - g4: Vo's minimum after 300 us no more than 5 mV below A240's on the same row.
- Stage 2, against each reference:
  - g5: A236's e2 (limits; item 2's rows <= reference + 2 A; four modules rail 1 <= 13.5 V).
  - g6: A236's e3 (post-event peak <= reference + 2 A, or + 10 A on re-applications including A237's; NEW events
    <= the reference's; |Vo extreme| <= |reference| + 1 mV except on re-applications).
  - g7: A236's e4 (skipping rows: A229's run test, true valleys within +-1 A).

## 3. Predictions (not criteria)
- Stage 1 as A242: every 10-200 kHz row <= 165 A, Vo within +2 mV of A240, 1 MHz open.
- Stage 2:
  - The falling rows have no K3 and no NEW (as A236). f_N75_k2 / k4 / k0 within +-2 A of the reference or lower.
  - Re-applications lower by 0-20 A, but their NEW counts may rise by up to 4 (A242: +3 / +4 on w5_N0 / w20_N0).
  - Item 2's rows may miss by up to 3 A or by NEW events (A236, A242).
  - The four-module -8 V row may miss g6's Vo clause (A236: 3 mV).
  - The skipping rows within 0.2 A.

## 4. Decision rule
- **All of g0-g7 pass** (g1 / g2 at 1 MHz excepted): early_hold_a 0 and late_hold_a 0 join the final configuration
  (one and four modules). Items 10 (10-200 kHz) and 3 close; 1 MHz stays a limit.
- **A miss:** traced. Misses that are only step-position scatter (A129: moving a step by under one period moves its
  peak 2-7 A) are shown against that scatter with a run that moves the step. Adoption is then put to the user with
  the evidence, not taken here.
- **Stage 1 g1 fails at 100-200 kHz:** stage 2 is stopped.
