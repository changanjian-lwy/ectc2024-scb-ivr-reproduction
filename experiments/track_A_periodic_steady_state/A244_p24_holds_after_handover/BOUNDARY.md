# A244 - the holds act only after the handover (items 10 and 3) (BOUNDARY)
Method: RTL + cosim (cfg-gated option; code and cfgs committed before the runs).
Track A. Looked at beforehand: A243's records (46 rows and the 28-run control) and its RESULTS.
Decision it changes: whether the final configuration ignores dt_pred reports from periods without reversal, which would
close item 10 (repeated load steps, 10-200 kHz) and item 3 (the climb after a falling step).
Cheaper check done first: A243's records (below); no cheaper model has a dt_pred block.
Budget: 47 runs in one queue at 10 jobs (A243's misses, item 3 and four modules first), about 6 h. If needed, a control
of 2 runs per missed row on arm w, and 2 on arm r where A243 has none (Section 4).

## 1. What and why
- **A243 (both holds, early_hold_a and late_hold_a 0.0):** fixed items 10 and 3 where the holds act after a
  disturbance (every 10-200 kHz row <= 159.6 A; no K3 / NEW on the falling rows). It was not adopted: the control's
  c1 missed on a_S75h_d20 and the three release rows.
- **The trace:** on every one of A243's 46 rows the holds before the disturbance act only 0.07-2.58 us after mode
  P's entry (3 per module on N0 / N75, 6-8 on S75 / N13), and the run parts from its reference there.
  - At the handover they leave C1 0.2-0.5 V lower. The item-2 step 20 us later meets rail 1 at 12.29 against
    11.97 V, which gives +2..+5.6 A at three positions.
  - The release rows' NEW counts follow that state. u_N0 at k 4 has no hold after the release and still 14 NEW
    against 8.
- **Option** (A244): scb_ctrl cfg_hold_wait (bridge "hold_wait"), a count of phase 1's turn-ons in mode P (cleared
  outside it). Both holds reach the phases only once the count reaches it.
  - Off (absent = 0): A243's behaviour. Holds off: bit-identical (unit 123 / 123, regression quick and full PASS on
    fresh outputs, before this boundary).
  - Arm w: holds 0.0 and hold_wait 32 (12.5-16.4 us at the settled periods 0.39-0.51 us; 5x the last handover hold).
    A shorter wait than item 2's 40 us hold-off is chosen on purpose: the holds then act on the item-2 steps at 20 us
    (and from about 13.5 us into a_S75h_d2's transient), so those rows still test them.
- **Basis:** as A242 / A243 (Zhang et al., TPEL 2023: zero voltage needs a reverse current; Chiang & Chen, TPEL
  2009). The rule to ignore such reports, and the wait, are ours; no source.
- **Rows:** A243's 46 against the same references, plus identity o_cw5_N75 (A243's cfg_b_cw5_N75 unchanged).
- **Not tested:** waits other than 32; start-ups below full load (item 6c's rows); four modules under the accelerator
  load; thresholds other than 0 A.

## 2. Criteria (A243's g1-g7 on arm w; g0 and g8 new)
- g0: unit 123 / 123; regression quick and full PASS; run_o_cw5_N75 = A243's run_b_cw5_N75 (sections, edge lists,
  late fires, overlaps, peaks).
- g8: every run equals its reference before its disturbance (sections: t, Vo, Vin, flying capacitors, Ton; high-off,
  low-off and turn-on lists: t, phase, current; every module). This is what the wait is for.
- Stage 1 (A240's 18 rows):
  - g1: A240's q1 (peak <= 200 A whole run, V_DS <= 40 V, no overlap or shoot-through).
  - g2: A240's q4 (peak after 300 us <= the board's single re-application + 10 A).
  - g3: A240's q2 and q5.
  - g4: Vo's minimum after 300 us no more than 5 mV below A240's.
- Stage 2 (A236's 25 rows and A237's 3):
  - g5: A236's e2, the limits (item 2's rows <= reference + 2 A).
  - g6: A236's e3, peak, NEW and Vo against the reference.
  - g7: A236's e4, the skipping rows.

## 3. Predictions (not criteria)
- g8 holds on all 47 runs; o_cw5_N75 is bit for bit.
- Stage 1 as A243: every 10-200 kHz row <= 165 A, N0's overshoot <= 1.0515 V; 1 MHz open (N75 230-260 A).
- Stage 2: the falling rows without K3 / NEW, f_N75_k0 / k2 / k4 within +-3 A of A243's; re-applications 10-22 A below
  their references; four modules within 2 A and 1 mV of A243's.
- Risks: a_S75h_d20 and a_S75_d20 (holds after the step on phase 1) within +2 A of the reference, uncertain;
  a_S75h_d2 (holds begin in its transient) may move by up to 3 A; release rows' NEW counts within +-2 of the
  reference (the holds act 0-2 times after the release, as in A243).

## 4. Decision rule
- **g0 or g8 fails:** the wait does not do what it is for. Not adopted; traced.
- **All of g0-g8 pass** (g1 / g2 at 1 MHz excepted): early_hold_a 0, late_hold_a 0 and hold_wait 32 join the final
  configuration (one and four modules). Items 10 (10-200 kHz) and 3 close; 1 MHz stays a limit with its mechanism.
- **A g5 / g6 miss:** each missed row is run at k 2 and 4 of T / 6 on arm w. Arm r is A243's existing run_cr_ records
  (same cfgs; the code with the options off is unchanged); a row A243 did not move is moved with A243's
  make_ctrl_cfgs rule. A243's c1 is used: arm w's worst over k 0 / 2 / 4 against arm r's worst, with +2 A, or + 10 A
  on re-applications; NEW at most arm r's most; |Vo| + 1 mV.
  - Every miss passes c1: adoption is put to the user with the evidence.
  - Otherwise: not adopted, and traced.
