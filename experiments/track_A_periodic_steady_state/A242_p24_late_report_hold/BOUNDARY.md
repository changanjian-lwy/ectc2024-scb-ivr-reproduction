# A242 - hold the turn-on delay on a late report without reversal (item 10) (BOUNDARY)
Method: RTL + cosim (cfg-gated option; code and cfgs committed before the runs).
Track A. Looked at beforehand: A241's records (stage 1 complete, stage 2 15 of 28 rows), A240's and A237's records
report by report.
Decision it changes: whether item 10 (repeated load steps above 200 A) closes in the final configuration without
A241's costs on falling and item 2 rows.
Cheaper check done first: the records (below). D63 has no dt_pred block, so there is no cheaper model.
Budget: 47 runs in one queue at 10 jobs (stage 1 first, then the four-module rows, then the rest); stage 1 in about
3 h, all in about 6 h. Stage 2 is stopped if stage 1 fails the rule in Section 4.

## 1. What and why
- **A241 (one step per report):** fixed the repetition at 10-200 kHz (every row <= 161.1 A; A240 up to 210.3 A).
  But it made the delay ratchet up wherever the valley stays positive. Early reports add a step, a late report can
  take back only one, so the delay reaches the 28.3 ns restart: f_N75_k0 got 6 restarts and 6 spikes (166.1 against
  156.2 A), and item 2's rows got 216.3 / 218.5 A against 211.2 / 207.8 A.
- **What collapses the delay** (A240's 18 rows and A237's three re-applications, 94,931 reports):
  - 54 % of the falls over 0.5 ns, 63 % of the total fall (5969 of about 9450 ns), come from reports whose low-side
    turn-off current had not reversed (>= 0 A). For example: N75 100 kHz phase 2 -2.6 ns at +47 A; cw5_N75 -4.4 ns
    at +3 A; N0 100 kHz phase 4 -1.2 ns at +43 A.
  - 20 % come from valleys below -30 A, where the node does swing fast.
- **Why those reports mislead:** without a reversed current the node cannot swing to the rail. The bridge's monitor
  takes the high side's V_DS minimum after the low-side turn-off. If there is a dip (the edge's ring) and the voltage
  is not still falling at the edge, the report is "late", with the error from that dip, and dt_pred drops by half of
  it.
- **Option** (A242): bridge cfg "late_hold_a" -> A236's m_pos comparator (the low-side turn-off current above this
  value) and scb_phase cfg_late_hold: a late report with m_pos leaves dt_pred. Early reports are unchanged, so A236's
  hold is not part of the arm.
  - Off: bit-identical (unit 121 / 121, regression quick and full PASS on fresh outputs, before this boundary).
  - Arm l: late_hold_a 0.0 (A236's threshold: the current's sign).
- **Basis:**
  - Zhang et al., TPEL 2023: zero voltage needs a reverse current to discharge the node (GS66516T, double-pulse and
    305 kHz TCM; cited in A236).
  - Chiang & Chen, TPEL 2009: the turn-on is split by whether zero voltage can be reached (5 -> 3.3 V buck IC, about
    3.6 MHz).
  - No source ignores a dead-time learner's report on the current's sign: that rule is ours.
- **Rows:** A241's, with arm l.
  - Stage 1: A240's 18 rows against A240's records.
  - Stage 2: A236's 25 rows and A237's cw5_N0, cw5_N75 and c30_S75h, against their references.
  - Identity: o_cw5_N75 (A237's cfg unchanged, bit for bit with A237's run_cw5_N75).
- **Not tested:** thresholds other than 0 A; the deep-valley falls (20 %), which the hold leaves; four modules under
  the accelerator load.

## 2. Criteria (A241's, on arm l)
- g0: unit 121 / 121, regression quick and full PASS, run_o_cw5_N75 = A237's run_cw5_N75 (sections, edge lists,
  late fires, overlaps, peaks).
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
- Stage 1:
  - N75 at 100 / 200 kHz and N0 at 60 / 100 kHz <= 185 A, but above A241's 148-161 A, because the deep-valley falls
    remain.
  - The slotted phases' shortest delay >= 4 ns.
  - Vo's maximum within +2 mV of A240 (A241: +4-6 mV).
  - The 10 kHz late fires mostly gone (A241: 496 -> 11 on N0).
  - 1 MHz 215-245 A (the ladder beat, not the delay).
- Stage 2:
  - Falling, rising and item 2 rows within +-2 A of the reference, with no new K3 or NEW events: early reports are
    handled as in the reference.
  - Re-applications 0-15 A lower (cw5_N75 171.1 -> 155-165 A).
  - Skipping rows within 0.2 A.

## 4. Decision rule
- **Stage 1 g1 fails at 100-200 kHz:** the hold is not enough alone. Stage 2 is stopped and the remaining falls are
  traced.
- **All of g0-g7 pass** (g1 / g2 at 1 MHz excepted, as A241): late_hold_a 0 joins the final configuration (one
  module, and four modules by the m4 rows). Item 10 closes at 10-200 kHz, and 1 MHz is stated as a limit with its
  mechanism (the load beating against the slots on the ladder; no package capacitance).
- **A stage 2 miss:** it is traced before any adoption.
