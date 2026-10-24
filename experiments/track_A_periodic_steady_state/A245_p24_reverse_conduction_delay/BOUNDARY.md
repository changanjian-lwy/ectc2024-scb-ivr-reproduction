# A245 - a turn-on delay that keeps finding the swing finished (item 6c) (BOUNDARY)
Method: RTL + cosim (cfg-gated option; code 6d215ad and cfgs committed before the runs).
Track A. Looked at beforehand: the start-up records of A230 / A231 / A239, A244's 47 records, and two pilots on the
three locked S75 rows (records in release records-a245, from 6822a94 / 2c7fe25 / 1105d61, provenance clean).
Decision it changes: whether rev_n 16 joins the final configuration and closes item 6c (a start-up into a light load
leaves the ladder off balance).
Cheaper check done first: the records (counts below); no cheaper model has the dt_pred learner or the gate delay.
Budget: 45 runs in one queue at 10 jobs (four modules and the 5 A rows first), about 6 h.

## 1. What and why
- **Item 6c (plant V7):** S75 into 30 % ends 4.6 / 5.2 V off balance at 300 us at 25 / 125 C (A230
  `run_u_S75_30_base.json`, `run_u_S75h_30_base.json`; rails 16.3 / 16.5 / 7.4 / 7.8 and 13.6 / 13.7 / 6.8 / 14.0 V).
  A230's lead arm, the same start handed over 0.6 us earlier, locks on S75 at 25 C and not at 125 C: the end state
  depends on history.
- **Trace:** in every locked record the low rail's phase turns on with V_DS <= 0 at the command on every period (S75h
  207 / 207 in the last 40 us; balanced records 0). The node has finished its swing and the switch conducts in
  reverse, so the phase gets more volt-seconds and its rail stays low. Its valley report is on target (error 0.1 ns,
  target 0.094 ns): the minimum of a node creeping towards the reverse-conduction voltage is always the last sample,
  so the learner holds the long delay (S75h phase 3 18.6 ns against 11.4-12.6 ns).
- **Pilot 1, Ton trims (cfg "bal", after Wei, Ramadass, Ma, JSSC 2021: switch node against Vin / 4, trailing-edge
  trims; tri-state double step-down, 24 / 12 V to 1 V, 3 W, 180 nm BCD).** The trims raise the low rail, but its phase
  keeps the long delay until the rail is nearly back, then drops it in a few periods; the trims left over swing the
  ladder the other way (step 4 / 16: rails 9.0-17.8 V at 300 us, Vo 0.990-1.011 V). Not taken further; the option stays
  in the code, off.
- **Option (A245):** scb_phase m_rev / cfg_rev_n (bridge "rev_n"). From the rev_n-th report in a row with V_DS <= 0
  at the command, each such report lowers that phase's dt_pred by one step (0.28 ns); any other report restarts the
  count. Phase 1 of every module is left out: it never locked, and its runs reach 35 / 30 in A244's falling-line rows
  on one / four modules. Off (absent = 0): unit 132 / 132, regression quick and full PASS.
- **Basis:** shortening the delay while reverse conduction is detected is TI's Predictive Gate Drive (Mappus, SLUA281,
  2003: body-diode conduction sensed, one 4 ns step per cycle; silicon synchronous buck, 5 V to 0.9 / 1.8 V, 250 /
  500 kHz) and Sun, Wu, Sun, Zhen, Zhang (Microelectronics 54(4), 2024: GaN buck, 12 V to 1 V, the switch node's
  negative voltage sensed). Ours, no source: its use at the zero-voltage turn-on of an SCB's phases, the count in a
  row, and leaving phase 1 out.
- **Threshold 16 (pilot 2, the three locked S75 rows):** every threshold balances them (end 0.10-0.12 V, in band by
  152-173 us). Vo's minimum after mode P's entry: rev_n 64 0.9837-0.9868 V, 32 0.9893-0.9933 V, 16 0.9941-0.9961 V. The
  lock's own release dips Vo the same way: A230's S75h lead row releases at 164 us and reaches 0.9827 V 3 us later.
  An earlier act meets a smaller imbalance. In A244's 47 records phases 2-4 reach at most 6 in a row.
- **Rows:** stage 1, 20 start-ups (A230 / A231 / A239 cfgs, two arms): f = final configuration (A244's holds), r = f +
  rev_n 16. S75 / S75h into 30 % (base and lead), N0 / N0h / N75 / N75h into 5 A, N0 10 / 20 / 30 %, N0h 30 %, N75
  20 / 30 %, N75h 30 %, full load on N0 / N0h / N75h / S75 / S75h. Stage 2, identity: A244's w cfgs + rev_n 16 for
  p_N0_10k / 100k / 30k (phases 2-4: 6 in a row), r_F0_lm80 (phase 1: 35), m4_l_m80_10us (four modules, phase 1: 30).
- **Not tested:** a true no load (item 6b, below the 2 % minimum: the module pauses); four modules starting into a
  light load; F0 / N13 start-ups; other thresholds outside the pilot; disturbances after the start-up with rev_n
  acting (A244's rows never reach 16).

## 2. Criteria (arm r against arm f, per row)
- g0: unit 132 / 132; regression quick and full PASS; stage 2's five runs equal A244's run_w_ bit for bit (sections,
  edge lists, late fires, overlaps, peaks).
- g1 (the fix): at the run's end every rail within 1.0 V of Vin / 4, and no phase 2-4 with 16 or more reports in a row
  with V_DS <= 0 in the last 40 us.
- g2 (limits, whole run): peak <= 200 A, V_DS <= 40 V, no overlap or shoot-through. Oracle NEW events (a142_oracles):
  outside the release window no more than arm f's; inside it only spikes. Release window: from the rule's first act to
  1 us after the ladder last leaves 1 V.
- g3: Vo after mode P's entry within [min(0.99 V, arm f's minimum), max(1.05 V, arm f's maximum)].
- g4: a row where arm r never reaches 16 in a row on phases 2-4 equals arm f bit for bit.
- Reported, not criteria: time into the 1 V band, late fires, hard turn-ons, edge and reverse-conduction loss over the
  last 50 us.

## 3. Predictions (not criteria)
- S75 / S75h at 30 % (4 rows): in band by 150-170 us, end <= 0.2 V, Vo minimum 0.994-0.996 V at 105-110 us, peaks
  <= 125 A; edge loss 3-6 W lower at the end (pilot: 17.7 / 22.2 / 19.8 -> 14.7 / 16.1 / 16.2 W); 0-4 NEW spikes,
  all in the window; late fires up (phases 3-4 join phase 2's 60-110).
- Nominal 10-30 % (7 rows): the rule acts (old records: 63-132 in a row); end within 0.6 V as arm f; Vo within 2 mV
  of arm f. Uncertain: these ladders recovered by themselves, and an earlier release may dip Vo.
- 5 A (4 rows): the rule acts; end <= 1 V (A239 without holds: 1.0-2.6 V). Uncertain (skipping).
- Full load (5 rows): at most 2 in a row, so equal to arm f bit for bit. Stage 2: bit for bit.

## 4. Decision rule
- **g0 or g4 fails:** the option is wired wrong. Not adopted; traced.
- **All pass:** rev_n 16 joins the final configuration (one and four modules; four modules checked for identity
  only). Item 6c closes for start-ups into >= 5 A on N0 / N75 (25 / 125 C) and into 30 % on S75 (25 / 125 C).
- **A g1 miss:** not adopted for that range; traced.
- **g2 / g3 misses only inside the release window**, with Vo >= 0.9827 V (the natural release on the same board) and
  peaks <= 200 A: put to the user with the evidence. **Any other miss:** not adopted; traced.
