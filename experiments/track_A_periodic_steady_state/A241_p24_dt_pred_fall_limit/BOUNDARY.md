# A241 - a fall limit on the slotted phases' turn-on delay (item 10) (BOUNDARY)
Method: RTL + cosim (cfg-gated option; code and cfgs committed before the runs).
Track A. Looked at beforehand: A240's records (every row, per phase), A237's and A229's re-applications, and a screen
of all 288 V7-era records for the shortest predictive turn-on delay.
Decision it changes: whether item 10 (repeated load steps above 200 A) closes in the final configuration with a
limit on how fast dt_pred may fall.
Cheaper check done first: the records (below). D63 has no dt_pred block (A143), so there is no cheaper model.
Budget: stage 1 19 runs (~3.5 h at 10 jobs), stage 2 28 runs (~3 h; the two four-module rows set the wall time).

## 1. What and why
- **Mechanism** (records; plant V7, final configuration): every load re-application drives a slotted phase's dt_pred
  to 0-4 ns (A237 cw5_N75 phase 2: 15.8 -> 0.0 ns within 6 us at Ton 450-830 LSB; A240 N75 100 kHz phase 2 1.0 ns).
  A late report lowers dt_pred by half the error, so it can fall several ns in one report. It climbs back only one
  dt_step (0.28 ns) per early report, so it needs 25-30 us.
- **Why the repetition matters:** a load that returns within that time finds the phase turning on early. Within a run
  the phases whose delay collapses carry the peaks (N75 100 kHz: phase 2 / 4 at 1.0 / 1.8 ns peak 210.3 / 163.7 A;
  phases 1 / 3 at 11.6 / 6.4 ns peak 115.0 / 154.5 A). A collapse alone does not decide it: 76 of 288 V7 records
  reach < 2 ns, and the single re-applications pass.
- **Option** (A241): bridge cfg "dt_fall_ns" -> scb_phase cfg_dt_fall. A report that is neither early nor flat sets
  dt_pred to at least dt_pred - cfg_dt_fall; rises are unchanged.
  - Off: bit-identical (unit 119 / 119, regression quick and full PASS on fresh outputs, before this boundary).
  - Arm f: dt_fall_ns = the row's dt_step_ns (0.282843 ns, 9 LSB): dt_pred moves at most one step per report either
    way. Over A240's 5 us light half at 100 kHz that allows about 3-6 ns.
- **Basis:**
  - A143 named a dt_pred fall limit as an open candidate (not tested).
  - Chen et al., TPEL 2022 (vol. 37, no. 8): a bang-bang dead-time controller, i.e. one fixed step per decision; GaN
    buck, 10 MHz, dead time down to 0.4 ns. Abstract only; the step rule was not checked in the text.
  - No source limits a predictive ZVS turn-on delay for a series-capacitor converter's slotted phases under repeated
    load steps: that rule is ours.
- **Risk:** item 3 (A236) runs the other way. After a falling line step dt_pred climbs to 28 ns and has to come back
  down when the valley returns. A slower fall keeps the high side's body diode conducting for longer, and that is
  item 3's spike. Stage 2 includes those rows.
- **Stage 1 rows:** A240's 18 rows (N0, N75 at 25 C; S75 at 125 C; 10 kHz-1 MHz) with arm f, against A240's records.
- **Stage 2 rows:** A236's 25 rows (falling, rising, item 2, load, re-applications, skipping, four modules) and A237's
  cw5_N0, cw5_N75 and c30_S75h, each with arm f against its reference record. It runs only if stage 1 meets the rule
  in Section 4.
- **Identity:** o_cw5_N75 is A237's cfg unchanged, compared bit for bit with A237's run_cw5_N75.
- **Not tested:** other fall limits than one step, other temperatures for the load rows, the accelerator load on four
  modules.

## 2. Criteria
- g0: unit 119 / 119, regression quick and full PASS, run_o_cw5_N75 = A237's run_cw5_N75 (sections, edge lists,
  late fires, overlaps, peaks).
- Stage 1, every row, arm f:
  - g1: A240's q1 (whole run: peak <= 200 A, V_DS <= 40 V, no overlap or shoot-through).
  - g2: A240's q4 (peak after 300 us <= the board's single re-application + 10 A).
  - g3: A240's q2 and q5 (above 1.05 V for under 25 us; within 1 % over the last 20 us).
  - g4: Vo's minimum after 300 us no more than 5 mV below A240's on the same row.
- Stage 2, arm f against each reference:
  - g5: A236's e2 (limits; item 2's rows <= reference + 2 A; four modules rail 1 <= 13.5 V).
  - g6: A236's e3 (post-event peak <= reference + 2 A, or + 10 A on re-applications including A237's; NEW oracle
    events after the event <= the reference's; |Vo extreme| <= |reference| + 1 mV except on re-applications).
  - g7: A236's e4 (skipping rows: A229's run test, true valleys within +-1 A).

## 3. Predictions (not criteria)
- The slotted phases' shortest delay in the trains stays >= 6 ns (A240: 1.0-4.8 ns on the failing rows).
- N75 at 100 / 200 kHz <= 180 A; N0 at 60 / 100 kHz <= 175 A.
- 1 MHz is uncertain (185-225 A): the delay there sits low for the whole train (S75 medians 3.6-4.8 ns), and a rate
  limit does not move a persistent level.
- N0's 30-60 kHz dips within +-5 mV of A240 (phase 1's edge, not dt_pred). The 10 kHz late fires unchanged (T33).
- Stage 2:
  - re-applications 0-12 A lower (cw5_N75 171.1 -> about 160 A);
  - falling rows: the post-step peaks within +-2 A, but item 3's rows (f_N75_k4, r_N13_lm48) may gain NEW events;
  - skipping rows within 0.2 A.

## 4. Decision rule
- **Stage 1 g1 passes at 10-200 kHz:** stage 2 runs.
  - If g1 misses only at 1 MHz, 1 MHz is stated as a limit, with the caveat that the steps act at Co with no package
    capacitance.
  - If g1 misses at 100-200 kHz, the option is not adopted and stage 2 does not run; the miss is traced.
- **All of g0-g7 pass:** dt_fall_ns = dt_step_ns joins the final configuration (one module, and four modules by the m4
  rows). Item 10 closes for the frequencies that pass.
- **A stage 2 miss:** it is traced before any adoption (e.g. item 3: a faster fall after an early run, or a
  combination with A236's hold).
