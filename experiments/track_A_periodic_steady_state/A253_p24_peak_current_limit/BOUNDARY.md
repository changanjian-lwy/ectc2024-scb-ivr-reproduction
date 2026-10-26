# A253 - a cycle-by-cycle peak current limit for item 10's 1 MHz train (BOUNDARY)
Method: cosim. The bridge option is at 0915877: cfg "ocp", a comparator in the driver's path. Regression quick + full
PASS, tests 717. Track A. Written and committed before the runs.
Looked at beforehand:
- A246's records: at N75 1 MHz only 3 of 5073 turn-offs exceed 200 A, all on phase 4, all 30-260 ns after the load
  fell. Phase 4 starts its on-time at +40 A with the full load's Ton (36 ns), and peaks at 232 A (gate record
  244.6 A).
- The 66 reference rows: 6 reached 175 A, all on L 2.2 nH.
- Literature (agent, 2026-10-26; datasheets read in full, IEEE papers as abstracts):
  - multiphase constant-on-time controllers limit each phase cycle by cycle: a valley limit that delays the next
    pulse (TI TPS53647 / TPS53681, MPS MP2888A, which passes the pulse to the next phase after a timeout), or a
    pulse-by-pulse peak limit (Infineon XDPE192C4C, Renesas ISL68233);
  - no source compensates the limit's latency; TI TPS54340B documents a 60 ns delay's overshoot;
  - a peak comparator that sets the on-time unbalances a flying-capacitor ladder (Abdelhamid et al., TPEL 2020);
  - adjacent SCB phases must not overlap (Naradhipa and Li, COMPEL 2023);
  - repetitive-load sweeps run up to 1 MHz (Infineon AN074317; Renesas ISL68127 report), with Vo bands as the pass
    criteria and no peak-current criterion.

Decision it changes: whether the final configuration adds the limit, which would close item 10 at 1 MHz.
Cheaper checks first:
- D63 does not carry the train: a per-period map gives 146.7 A against 244.6 A;
- A252 tests the delay.

Budget: 8 runs, about 2.5 h.

## 1. What and why
- A valley limit is the commercial COT norm. Here the current falls at Vo / L (0.45 A/ns), so phase 4 would wait about
  45 ns, into the next slot, and adjacent phases may not overlap. A peak limit only shortens an on-time.
- Limit: i_a 130 A on L 2.2 nH and 145 A on 2.933 nH; t_ns 1.0, plus t_drv 10 ns.
  - A crossing turns the switch off about 12 ns later, about 60 / 45 A higher.
  - The gate record adds about 12 A, so the cap is about 190-200 A. That level is our own, from the latency; no source
    gives it.
  - In normal periods the on-time ends before the limit's turn-off, which is then dropped.
- Rows (references: A246 run_h_, the final configuration):
  - act: p_N75_1000k, p_S75h_1000k, a_S75h_d2, a_S75h_d20, a_S75_d20, k_S75h;
  - identity: p_N75_100k, p_N0_100k. The comparator crosses its level in every full-load period there, and no
    on-time runs 12 ns past it.
- The other 58 reference rows stay under 175 A, where the limit cannot act. A dropped turn-off changes no state, so
  those rows are equal to their references by construction; the identity rows check that.

## 2. Criteria
- o1: identity rows: equal to the reference (A246's same) and no fires.
- o2: p_N75_1000k and p_S75h_1000k: A240's q1 and q2 (whole-run peak <= 200 A, V_DS, time above).
- o3: stage-2 rows: whole-run peak <= 200 A, NEW <= the reference's, post-event peak <= max(reference, 200 A) + 2 A,
  and |Vo extreme| <= the reference's + 2 mV.
- o4: the 1 MHz rows: A240's q3, and Vo's minimum >= the reference's - 2 mV.

## 3. Predictions (not criteria)
- The limit fires on 4 rows (N75 / S75h 1 MHz, a_S75h_d2, a_S75h_d20), fewer than 20 times each; k_S75h and
  a_S75_d20 are equal to their references.
- The peaks are 190-200 A; Vo's minimum moves by less than 2 mV.
- Risk: a truncated pulse leaves its phase's series capacitor short of charge, which may ring (Abdelhamid 2020) or
  push the next pulse higher.

## 4. Decision rule
- **o1 fails:** wiring; trace it.
- **o2-o4 pass:** the user decides adoption (AskUserQuestion). Item 10 would close at 1 MHz.
- **o2 fails with fires:** the cap estimate is wrong. Measure the overshoot, then re-register the level.
- **o3 / o4 fail:** name each row's cost; the user decides.
