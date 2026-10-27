# scb_ivr.cosim - changelog

History lives here and in the experiments' BOUNDARY/RESULTS, not in the
code. Each entry names its source and the gate that showed it changes no
result.

## 2026-10-28 (A258) - a ceiling on the limit's count (bridge)

**Source:** A256's count has no ceiling. While the limit is suspended, every pulse it would have cut counts +1, so a
125 % overload drives the counts to 159-201 in 120 us (replay on A254's records). After the overload ends, the limit
stays off for about as many clean pulses (80-100 us), and a 1 MHz train in that window is unprotected (A246: 244.6 A
gate-level).

Bridge cfg "ocp" gains "n_cap" (absent = no ceiling): a count stops at n_cap, so the limit acts again n_cap clean
pulses after any overload ends.

**Gate:** "n_cap" absent leaves ocp_count as A256's: tests 726 (test_cosim_ocp: the ceiling bounds the count and
re-arms after n_cap clean pulses; no ceiling by default). cosim_regression --quick and --full PASS.

**Adopted (A258's registered rule, 2026-10-28; t0-t3 pass):** n_cap 6 joins the final configuration. After 90 us at
125 % the limit re-arms 2.9 / 3.9 us after the release (without the ceiling 84.5 / 81.6 us), and a 1 MHz train 10 us
later holds 198.0 / 187.3 A on N75 / S75h (without 276.9 / 209.3 A). A256's suspending rows are equal up to the earlier
re-arm.

## 2026-10-27 (A256) - the peak current limit suspends itself after a run of limited pulses (bridge)

**Source:** A254. At 110 / 125 A the limit takes item 10's 1 MHz peaks under 200 A. But under a 125 % load on N0 it
cut almost every pulse, and the series capacitors collapsed (rails 3.8 / 26.6 / 3.6 / 14.0 V, Vo 757 mV, 241.5 A).
- A per-phase limit that keeps setting the on-time is peak current control, which flying-capacitor converters cannot
  balance (Abdelhamid et al., TPEL 2019, abstract).
- Commercial controllers count limit events and then shut down or hiccup: TI TPS546D24A (up/down count, default 3),
  Renesas ISL68222 / 68233 (6 consecutive), TI TPS54A20 (an SCB: 3 sequential, hiccup with a Ct pre-charge).
- The +62.5 A step is a specified row, so it must stay regulated. Here the count instead hands the overload to the
  loop. That action is ours, no source.

Bridge cfg "ocp" gains "n_susp" (0 = never):
- per phase, an up/down count: +1 for a limited pulse, -1 for a clean one (floor 0);
- a count of n_susp suspends the limit on every phase;
- while it is suspended, a crossing only sets a probe at its would-be turn-off time. The pulse counts +1 if the
  controller's turn-off comes after that time. A pending turn-off is dropped before the plant steps;
- when every count is back at 0, the limit acts again;
- record "ocp_susp" (t_s, phase, on).

**Gate:** "n_susp" absent or 0: ocp_count returns at once, so runs are A254's bit for bit. tests 724 (test_cosim_ocp:
the count suspends and re-arms, off by default, a suspended turn-off is only counted). cosim_regression --quick and
--full PASS. A254's p_S75h_10k to 160 us (5 fires in the handover, count <= 1) is the same with and without n_susp 6.

**Adopted** (user decision 2026-10-27, A256 RESULTS 4). The final configuration now carries ocp {i_a 110 / 125 / 140 A
on 2.2 / 2.933 / 3.813 nH, t_ns 1.0, n_susp 6}.

## 2026-10-26 (A253) - a cycle-by-cycle peak current limit in the driver's path (bridge)

**Source:** item 10's open part. On A240's 1 MHz train, a slotted phase starts its on-time with a positive valley
(+40 A) while the loop's Ton is still the full load's, so it peaks at 232 A (N75; 3 of 5073 turn-offs over 200 A).
A251 / A252: the turn-on delay does not remove it. Multiphase controllers limit each phase's current cycle by cycle:
- a valley limit that delays the next pulse (TI TPS53647, MPS MP2888A);
- a pulse-by-pulse peak limit (Infineon XDPE, Renesas ISL68233).

Here the current falls at only Vo / L, and adjacent phases may not overlap in an SCB, so the limit is a peak limit. It
acts in the driver's path, outside the controller.

Bridge cfg "ocp" {"i_a", "t_ns" 0}:
- while a high side is on, the first window end that finds its current >= i_a schedules a turn-off at the crossing
  (linear between window ends, ocp_cross) + t_ns + t_drv;
- the turn-off is dropped if the on-time ended first;
- the controller's own turn-off of that pulse is then skipped;
- record "ocp_fires".

**Gate:** "ocp" absent: no code path runs. A dropped turn-off changes no state, so a run in which the limit never
acts is the same bit for bit. cosim_regression --quick and --full PASS on fresh outputs. tests 717 (three new in
test_cosim_ocp: ocp_cross).

**Fix (same day):** with "ocp" set, start() read the constructor's argument first_high, out of scope (NameError at
the first run; the regression has no "ocp" case). The module now keeps it as self.first_high. Two new tests build a
module with "ocp" and call start() (master: phase 1 high; slave: all low); they fail before the fix. test_cosim_ocp
skips without cocotb (CI has none; its import had turned CI red). Smoke runs to 160 us: a 60 A limit acts 401 times
(turn-offs <= 122 A, no late fire or overlap); A253's own cfg (130 A) does not act and equals A246's record edge for
edge.

**Fix 2 (after A253's runs, its o1):** a stale limit turn-off (the on-time had ended) was dropped only after the plant
had stepped to its time. That split the integrator's step, so rows where the limit never acted still left their
reference at float level (currents differ from the first crossing on; p_N75_100k at 148.94 us). The smoke check above
had compared edge times and phases only. run_window now drops it before the step; apply() no longer checks. Two new
tests: a stale turn-off leaves the steps alone, a live one acts. tests 721, cosim_regression --quick and --full PASS.

## 2026-10-26 (A251) - the slotted phases keep their learnt delay after the start-up (RTL + bridge)

**Source:** A249: a fixed delay per board removes the N0 100 kHz lock, but at the start-up the learner's per-period
adaptation kept the ladder near balance while Vin ramped (A250: D63 does not carry that phase). A251 lets the learner
run through the start-up and then holds what it learnt. scb_ctrl cfg_dt_hold_n (16 bits): a counter of phase 1's
turn-ons in mode P (reset outside mode P); from cfg_dt_hold_n on, phases 2..N get cfg_dt_fix's gate (phase 1 gets 0,
in a slave too), so their dt_pred stays at its value. scb_multi regenerated. Bridge cfg "dt_hold_periods" (0-65535;
absent = 0 = off).
**Gate:** dt_hold_periods absent: cfg_dt_hold_n 0, the counter stays at 0 and the gate is cfg_dt_fix alone; unit tests
144 / 144 (three new: dt_hold_keeps_the_learnt_value, dt_hold_skips_phase1, dt_hold_off), cosim_regression --quick
and --full PASS on fresh outputs.

## 2026-10-26 (A249) - a fixed turn-on delay for the slotted phases (RTL + bridge)

**Source:** A247 / A248: the soft turn-on windows nest, so one delay per board serves every negative low-side turn-off
current; the learner drifts to either end of the window, because a full swing clamps the node and its valley is flat.
A249 tests a fixed delay in the closed loop. scb_ctrl cfg_dt_fix, wired to phases 2..N (phase 1 gets 0, in a slave
too); scb_phase input cfg_dt_fix: no report changes dt_pred, which stays at dt_init. scb_multi regenerated. Bridge cfg
"dt_fix_ns" (N - 1 delays for phases 2..N, in place of dt_init_ns there; absent = off).
**Gate:** dt_fix_ns absent: cfg_dt_fix 0, dt_init as before; unit tests 141 / 141 (four new: dt_fix_keeps_dt_init,
dt_fix_skips_phase1, dt_fix_off, slave_dt_fix_skips_phase1), cosim_regression --quick and --full PASS on fresh outputs.

## 2026-10-25 (A246) - a held report lifts a delay far below the other phases' (RTL + bridge)

**Source:** A244's remaining item-10 lock (N0 at 100 kHz, record A244 `run_w_p_N0_100k.json`): in a light half the
slotted phase 4's valleys reach -40..-70 A, its node finishes the swing before the gate turns on, and its reversed
reports lower dt_pred 0.3-1.1 ns each, 13.3 -> 7.7 ns (phases 2-3 stay at 16-17 ns). In the next full-load half its
low-side turn-off current is positive, A236 / A242 hold every report, and the phase turns on early with positive
current each period (170-182 A). With positive current the node cannot swing, so a delay shorter than the other phases'
only gives the phase more volt-seconds. In A244's 47 records a held report on phases 2-4 with dt_pred more than 3 ns
below both other slotted phases occurs 210 / 538 times on N0 100 kHz / N75 1 MHz, 1-11 times on seven rows, never on
37. scb_ctrl cfg_hold_floor / cfg_floor_band: phases 2..N get dt_floor = the other phases 2..N's smallest dt_pred
minus the band (floor 0; 0 when off); scb_phase input dt_floor: a report with m_pos that leaves dt_pred (early or
late, held by A236 / A242 while either hold is on, or flat: with positive current the node often shows no dip) raises
dt_pred to it when below. scb_multi regenerated. Bridge cfg "hold_floor_ns" (the band; absent = off). No source for
the rule.
**Gate:** hold_floor_ns absent: dt_floor 0, the held branches as before; unit tests 137 / 137 (five new:
hold_floor_raises_a_held_report, hold_floor_lifts_a_flat_report_with_m_pos, hold_floor_leaves_reports_not_held,
hold_floor_needs_the_holds, hold_floor_off), cosim_regression --quick and --full PASS on fresh outputs.

## 2026-10-25 (A245) - a turn-on delay that keeps finding the swing finished is lowered (RTL + bridge)

**Source:** A245's pilot of the Ton trims below (S75 at 125 C into 30 %, records in release records-a245): the trims
move the low rail back, but the low rail's phase holds a long delay until the rail is nearly back, then drops it in a
few periods, and the trims left over swing the ladder the other way (Vo +-1 %). In every unbalanced start-up record
(A230 S75 / S75h at 30 %, A239 at 5 A) the low rail's phase turns on with V_DS <= 0 at the command on 69-946
consecutive reports (the node had finished its swing and the switch conducts in reverse); in A244's 47 records
phases 2-4 do so at most 6 times in a row and phase 1 at most 35. Its valley report is then on target: the minimum
of a node that creeps towards the reverse-conduction voltage is always the last sample. TI's Predictive Gate Drive (SLUA281,
2003) and Sun et al. (Microelectronics 54(4), 2024, GaN) shorten the delay while reverse conduction is detected.
scb_phase m_rev / cfg_rev_n and a per-phase count of m_rev reports in a row (8 bits, saturating): from the
cfg_rev_n-th such report, each lowers dt_pred by cfg_dt_step (floor 0), before the early / flat / late rules; any
other report restarts the count. scb_ctrl passes m_rev to every phase and cfg_rev_n to phases 2..N (phase 1 gets 0,
in a slave too: it never locked, and its runs reach 35 / 30 in A244's falling-line rows on one / four modules, phases
2-4 at most 6); scb_multi regenerated.
Bridge cfg "rev_n" (0-255, absent = 0); m_rev = V_DS <= 0 at the turn-on command.
**Gate:** rev_n absent: cfg_rev_n 0, the count changes nothing; unit tests 132 / 132 (five new:
rev_lowers_from_the_nth_report, rev_counts_per_phase, rev_skips_phase1, rev_off, slave_rev_skips_phase1),
cosim_regression --quick and --full PASS on fresh outputs.

## 2026-10-25 (A245) - ladder balance by Ton trims (RTL + bridge)

**Source:** A239's item 6c: a start-up into a light load leaves the series-capacitor ladder off balance (S75 into 30 %:
4.6-5.2 V at 300 us), and light-load operation does not restore it; releases from full load stay balanced. In every
unbalanced record the low rail's phase has a long turn-on delay (S75h 30 %: 18.7 against 11.4-12.6 ns), so it gets
more volt-seconds. Wei, Ramadass and Ma (JSSC 2021) rebalance a flying capacitor by sensing the switch node against
Vin / 4 and trimming the on-times. scb_ctrl cfg_bal / cfg_bal_step / cfg_bal_max, inputs b_valid / b_hi / b_lo, output
bal: per-phase Ton trims on phases 2..N in 1/16 LSB (a phase's own rail report moves it, phase 1's moves the others the
other way), clamped, 0 outside mode P (scb_multi regenerated). Bridge cfg "bal" {"band_v", "step_q4", "max_ns"}: at
each low-side turn-off the phase's rail against Vin / 4 +- band; record "bal_final_ns".
**Gate:** cfg "bal" absent: cfg_bal 0, Ton as before and no report pulses; unit tests 127 / 127 (four new:
bal_trims_slotted_phases, bal_fractional_steps, bal_off, bal_held_in_mode_s), cosim_regression --quick and --full
PASS on fresh outputs.

## 2026-10-24 (A244) - the holds wait after the handover (RTL + bridge)

**Source:** A243: with A236's and A242's holds both on, every row's holds before its disturbance act only 0.07-2.58 us
after mode P's entry, and there they only move the ladder (C1 0.2-0.5 V lower; an item-2 step 20 us later +2..+5.6 A).
scb_ctrl cfg_hold_wait (8 bits; scb_multi regenerated): a counter of phase 1's turn-ons in mode P (cleared outside
it, saturating at cfg_hold_wait) gates cfg_early_hold and cfg_late_hold to the phases. Bridge cfg "hold_wait" (0-255,
absent = 0).
**Gate:** hold_wait absent: cfg_hold_wait 0 and the gate always open, so A243's arm b is unchanged; unit tests
123 / 123 (two new: hold_wait_counts_phase1_turn_ons, hold_wait_starts_at_mode_p), cosim_regression --quick and
--full PASS on fresh outputs.

## 2026-10-23 (A242) - hold the turn-on delay on a late report without reversal (RTL + bridge)

**Source:** A241's records: 54 % of dt_pred's falls over 0.5 ns on A240's and A237's re-application rows (63 % of
the total fall) come from reports whose low-side turn-off current had not reversed. The node cannot swing there; the
dip the valley monitor finds is the edge's ring, read as a late valley. scb_phase cfg_late_hold (scb_ctrl passes it;
scb_multi regenerated): a late report with m_pos leaves dt_pred; early reports as before (A236's cfg_early_hold
unchanged). Bridge cfg "late_hold_a" sets A236's m_pos comparator (threshold in A; with "early_hold_a" also set the
two must be equal) and cfg_late_hold; turn-on records carry "lo_pos" whenever the comparator is set.
**Gate:** late_hold_a absent: cfg_late_hold 0 and m_pos as before; unit tests 121 / 121 (two new: err_high_late_hold,
err_high_late_hold_off), cosim_regression --quick and --full PASS on fresh outputs.

## 2026-10-23 (A241) - a fall limit on the turn-on delay (RTL + bridge)

**Source:** A240 (item 10): every load re-application drives a slotted phase's dt_pred to 0-4 ns, and it climbs
back at one dt_step per early report (25-30 us); a repeated load meets it there and the swing builds (A143's open
candidate). scb_phase cfg_dt_fall (TW bits; scb_ctrl passes it to every phase; scb_multi regenerated): a report that
is neither early nor flat sets dt_pred to at least dt_pred - cfg_dt_fall (floor 0), on the error-based and the m_tv
path alike; rises are not limited. Bridge cfg "dt_fall_ns" (absent or 0 = no limit).
**Gate:** cfg_dt_fall 0 leaves the update unchanged: unit tests 119 / 119 (two new: err_high_fall_limit,
tv_fall_limit), cosim_regression --quick and --full PASS on fresh outputs.

## 2026-10-22 (A240) - a periodic load current (plant + bridge)

**Source:** every load step so far was one or two instantaneous events; a processor
load repeats its steps at a finite slew (P24 Fig. 6's 1 kW processor). CircuitParams
pulse_t0 ... pulse_tr, CircuitParams.pulse_at and the C kernel's pulse_at: a trapezoid
current added in load_at from pulse_t0 (high, down over pulse_tr, low, up over the
period's last pulse_tr; pulse_hi from pulse_t1 on). Bridge cfg "load_pulse" {t_us,
t_stop_us, i_lo_a, i_hi_a, f_khz, duty, slew_a_us}; with modules > 1 the currents and
the slew are shared alike.
**Gate:** load_pulse absent: pulse_t0 = inf, load_at's arithmetic as before
(cosim_regression --quick and --full PASS on fresh outputs); test_cosim_plants: the
Python and C plants step bit for bit alike through every part of the trapezoid.

## 2026-10-16 (A238) - a sink mode at the lower Ton limit (RTL + bridge)

**Source:** A237: below the lower Ton limit a module pauses and cannot sink, so a
release to a true no load stays high (item 6b). Dell US 9467052 B2 enters FCCM on an
overshoot; with P24's held valley the equivalent is a deeper valley target.
scb_ctrl cfg_sink / cfg_sink_hi / cfg_sink_lo, output sink: set by a Vo sample above
vref + sink_hi with the loop's Ton at its lower limit (mode P), cleared by a sample at
or below vref + sink_lo; while set no round is skipped. Bridge cfg "sink" {hi_mv,
lo_mv, i_a}: every use of the target is i_a while sink is set; record "sink_log".
**Gate:** cfg "sink" absent: cfg_sink 0, sink stays low, skip_c as before
(cosim_regression --quick and --full PASS on fresh outputs); tb 117 / 117 (six new).
**Result:** not adopted (latches on N75, A238 RESULTS); the option stays, off by default.

## 2026-10-16 (A237) - the resistive load can disconnect (bridge)

**Source:** every light-load row since A216 kept the 4 mOhm load and added a current
step, so a "10 %" or "no load" row still had 250 A/V and sank current above 1 V.
cfg "t_load_off_us": r_load disconnects at that time (plant.load_on false), leaving
the load steps alone - a release to a constant-current load.
**Gate:** t_load_off_us absent: load_on as before (cosim_regression --quick and
--full PASS on fresh outputs).

## 2026-10-16 (A236) - hold the turn-on delay when the valley did not reverse (RTL, bridge)

**Source:** A235 run_r_N13_lm48 / A232 run_f_N75_k4_b: after a -4.8 V / 1 us step a
slotted phase turns its low side off at +1..+5 A for 25-30 us; each hard turn-on
reports "early" and dt_pred climbs 0.28 ns per period past cfg_rs_high (K3), then
the restored valley meets a delay ~8 ns too long (NEW spike). cfg "early_hold_a":
m_pos per valley report = the current at the actual low-side turn-off above this
value; scb_phase cfg_early_hold leaves dt_pred on an early report with m_pos.
**Gate:** early_hold_a absent: cfg_early_hold 0, m_pos 0, no record field added
(tb 111 / 111 with two new tests; cosim_regression --quick and --full bit for bit;
A236 e0 reruns A232's f_N75_k4_b).
**Fix (A236 amendment):** the first commit read early_hold in configure() before
start() set it (every run crashed at t = 0) and the regression passed on stale
outputs. early_hold now set in ModuleSim.__init__; run.py removes an existing output
before its run (a cocotb process exits 0 when its test fails; success = the output
exists). Regression quick and full then PASS on fresh outputs.

## 2026-10-16 (A230) - the handover request with a slope lead (bridge)

**Source:** A214 / A225: a start-up into 30 % of the load reaches 1.0510-1.0528 V
(limit 1.05 V) because Vo still rises at 8-14 mV/us when the 1.045 V request fires
and the current turns round only about 0.7 us after mode P's entry. cfg
"hand_lead_us": the sequencer compares Vo + lead x (Vo's change since the previous
sample / the time between them) with hand_vo_v - a comparator behind a lead network.
**Gate:** hand_lead_us absent: the old comparison bit for bit (the slope term is
0.0; A230's full-load rows bit for bit their base arm; cosim_regression --quick and
--full).

## 2026-10-15 (A229) - the derivative term held within a band above the limit (RTL, bridge)

**Source:** A228: with the hold at the limit the derivative term still moves
the 10 % skipping rows' upper valley end by 1.8-2.3 A (d0 within 0.6 A over
four release instants); inside a burst the PI output sits up to about 2 ns
above the limit and the term kicks Ton there. scb_ctrl cfg_kd_band (cfg
"kd_band_ns"): with cfg_kd_hold, d_term = 0 while the PI output is at most
the limit + the band. One unit test.
**Gate:** kd_band absent: the old cosim bit for bit (unit tests 109,
cosim_regression --quick and --full; A229 BOUNDARY j1).

## 2026-10-15 (A227) - the derivative term held at the lower Ton limit (RTL, bridge)

**Source:** A224's N0 10 % skipping row: the derivative term lifted Ton off
its 4 ns limit between pauses (up to 4.91 ns, A221 4.41 ns) and the true
valleys missed the band by 0.4 A. scb_ctrl cfg_kd_hold (cfg "kd_hold"):
d_term = 0 at a sample whose PI output is at or below the lower limit.
One unit test.
**Gate:** kd_hold absent: the old cosim bit for bit (unit tests 108,
cosim_regression --quick and --full; A227 BOUNDARY j1).

## 2026-10-15 (A224) - a derivative term in the voltage loop (RTL, bridge)

**Source:** A223's records: after a large load re-application Vo rings with
about 3 us (the timed low-side edge lets the current integrate Ton's excess,
and the P term around it is undamped). scb_ctrl cfg_kd / cfg_kd_db (cfg
"kd_ns_per_v", "kd_db"): d_term = -kd x (the ADC code's change since the
last sample), held like p_term, zero while the change is below the dead band.
One unit test.
**Gate:** kd absent: the old cosim bit for bit (unit tests 107,
cosim_regression --quick and --full; A224 BOUNDARY j1).

## 2026-10-14 (A223) - phase 1's relative cap only while Vin rises (RTL, bridge)

**Source:** A216's large load re-applications (problem 9): at constant Vin
scb_vff's relative cap is 1.25 x ton's low-pass, so a step that raises the
loop's Ton faster than the low-pass follows holds phase 1 alone (rail 1 to
16.3 V, 249.8 A). scb_vff input rgth (scb_ctrl cfg_vff_rgth, cfg vff
"rel_gate", Vin codes): the cap acts only at samples where rail - rss is >=
rgth; elsewhere no cap and tlp restarts from ton. Two unit tests.
**Gate:** rel_gate absent: the old cosim bit for bit (unit tests 106,
cosim_regression --quick and --full; A223 BOUNDARY j1).

## 2026-10-14 (A221) - the inductor's core loss (plant V7) and a zero-current pause keeps the slots' period

**Source:** A220's records and development runs. (1) V6 has no resistance in an
idle phase (circuit R 0, an off switch has none): an inductor's ring against
the switches' capacitance never decays, and the phases resume from different
points of it. circuit.py gets r_core, a resistor across each inductor (x_k to
out, always in the circuit): the parallel model of a magnetic core's loss, D76
(cfg circuit "r_core"; bridge CIRCUIT_KEYS). (2) A220's zero-current turn-off
made the pause's skipped instant early, so the slots' period was measured short
and the first two rounds after a resume had short slots: with cfg_zcd the pause
no longer updates t_per (scb_ctrl). One unit test, three plant tests.
**Gate:** r_core and zcd absent: the old cosim bit for bit (unit tests 104,
cosim_regression --quick and --full; A221 BOUNDARY j1).

## 2026-10-14 (A220) - a pause starts at zero current (RTL, bridge)

**Source:** A217's records. The pause began with every low side turned off at
its valley (a negative current), so each idle node swung to its rail and rang
with about 11 V (6-7 A in the inductor; 0.54 mOhm the only damping); at a
resume each phase started from a different point of that ring, which set its
first valley (s3 missed). With cfg skip "zcd_a" (needs "async") the pause's
last low-side intervals end at zero current: scb_phase input zcd (phase 1:
the timed edge gives way to the front end, no trim, no dlo; a slotted phase
arms its front end in LOW and is held at its report, its slot not taken, off
anyway half a tk_per after the slot); scb_ctrl input cfg_zcd and zpend (phase
k's high side turned off with skip_q high), phases 2..N's reports on A133's
fa_valid / fa_tlo. The bridge's front-end threshold is zcd_a while skip1 is
high (phase 1) and for phases 2..N's latches (turn-off only, no turn-on); the
record gains zcd_fires / zcd_log. scb_multi regenerated; two unit tests.
**Gate:** zcd_a absent: the old cosim bit for bit (unit tests,
cosim_regression --quick and --full; A220 BOUNDARY j1).

## 2026-10-14 (A217) - the resume's low-side interval ends at the target (RTL output, bridge)

**Source:** A216. A resume's low-side interval of phase 1 ended about 8 ns
after its comparator crossed the target (front end and driver), 2.7-4 A too
deep; phases 2-4 take that interval's length, and the error started a decaying
two-period alternation of the valleys in every burst (s3 missed). scb_phase
gets the output res_lo (phase 1: in that interval), scb_ctrl res1. The bridge
raises the front end's threshold by cfg skip "res_ofs_a" while res1 is high
(latch_thr; the kernel path now takes latch_thr's value, which is the old one
whenever neither res1 nor the floor applies). scb_multi regenerated.
**Gate:** offset absent or 0 and skip absent: the old cosim bit for bit (unit
tests, cosim_regression --quick and --full; A217 BOUNDARY j1).

## 2026-10-14 (A216) - skipped rounds below the lower Ton limit (RTL, bridge, plant)

**Source:** A207 / A208 / A210: below about 30 % of its load a module's Ton sits
at its lower limit and Vo runs away upward. scb_ctrl gets cfg_skip, cfg_skip_hi,
cfg_skip_lo and the outputs skip1 (to the front end), smp (a tick: the ADC
samples) and idle. With the loop's Ton at its limit and the last Vo sample
above vref + hi (+ lo once skipping), skip_q (latched at phase 1's low-side
turn-on) withholds phase 1's next turn-on; the skipped instant is the slots'
reference, so phases 2..N turn their low sides off and stay off. scb_phase gets
hold, tk_skip, tk_per, res_time and sk_pulse, tk_pulse, res_pulse, t_lon_q: a
held phase 1 ticks every period and resumes with its low side, ended by the
front end at the current target (no trim, dlo untouched); held slotted phases
turn their low sides on at the resume's instant plus their slots. With
cfg_ton_lat the condition's three comparisons are read from registers loaded
with the phases' Ton. scb_multi is regenerated (the slaves do not follow a
master's pause yet). Bridge: cfg "skip" {"hi_mv", "lo_mv"}; a tick adds a
record to "sections" (key "tick") and samples Vo and Vin (the record's code is
now one method, section()); the front end makes no turn-on while skip1 is
high; the record adds "skip_ticks". Plant: cfg "load_step2", a second load
event (CircuitParams i_step2 / t_step2, the kernel's run_t and load_at).
**Gate:** "skip" and "load_step2" absent are the old cosim bit for bit (unit
tests 100 of 100 with five new ones, cosim_regression --quick and --full; A216
BOUNDARY i1), and a run that never reaches the limit is the same with skip
configured (i2).

## 2026-10-14 (A215 results) - the bridge refuses ton_lat > 30

**Source:** A215 RESULTS 0. The divider's completion, 32 clocks after a
sample, is a source event and restarts the count; from ton_lat 31 the first
load after a sample is pre-empted and the registers load only on periods
longer than 32 + ton_lat clocks (the 30 % rows at ton_lat 32 never load).
bridge.py raises ValueError outside [0, 30]. Gate: cosim_regression --quick
(4 of 4 bit for bit).

## 2026-10-14 (A215) - the port expression and the Ton path's registers (RTL unfrozen by the user)

**Source:** A209. (1) scb_ctrl's `.lo_add(IS_FIRST ? lo_add : {TW{1'b0}})` mixes a
signed wire and an unsigned constant and stops yosys's front end; the constant
is now `$signed({TW{1'b0}})`. (2) The path from the loop's accumulator through
scb_vff into the phases is 12 times the clock in sky130. scb_ctrl gets
cfg_ton_lat (6 bits): when not 0, the phases read ton_ph / lo_add from
registers (ton_ph_r, lo_add_r) that load cfg_ton_lat clocks after the last
event that changes a source of the arithmetic (lat_ev: the loop's sample,
scb_vff's new output upd, the handover, a change of ext_ton). scb_vff gets upd
(the sample's clock, the clock after it, the divider's last step). scb_multi is
regenerated. The bridge's cfg "ton_lat" sets cfg_ton_lat; absent = 0.
**Gate:** cfg_ton_lat = 0 is the old controller bit for bit (unit tests 95 of
95 with six new ones, cosim_regression --quick and --full; A215 BOUNDARY c1).

## 2026-10-14 (A208) - the loop's lower Ton limit as its own cfg value (bridge)

**Source:** A207. The bridge set cfg_ton_min to half of cfg ton_ns. ton_ns is
the loop's reset value and grew to 44.48 ns for the handover (A185), so the
limit rose to 22.25 ns and a module stopped regulating below about 70 % of
its load. cfg "ton_min_ns" sets cfg_ton_min directly. The RTL is unchanged
(cfg_ton_min is an existing input). cfg_ton_max stays at 2 ton_ns.
**Gate:** absent = 0.5 ton_ns as before: regression quick 4 / 4 and A207's
14 us smoke record bit for bit, also with the key set to the default's value
(A208 BOUNDARY i1, i2).

## 2026-10-10 (A186) - handover requested on Vo (bridge, sequencer)

**Source:** A184 / A185. At a 200 ns mode-S period the locked trim drifts up to
+95 mV hot, and a handover fixed at 144 us starts mode P from that state. cfg
"hand_vo_v": the bridge raises hand_req once a phase-1 Vo sample (the ADC's
instant) reaches it, or at t_hand, whichever is first. One latch is shared by
the modules of a multi-module run, so they all get the request in the same
window. The record adds "t_hand_req_s". The RTL is unchanged (hand_req is an
input; in hardware a comparator / supervisor drives it).
**Gate:** absent = t_hand only, bit for bit (cosim_regression --full and A183's
N13 start-up rerun, A186 BOUNDARY).

## 2026-10-09 (A184) - mode S's own Ton (user-authorised RTL change)

**Source:** A183. A 200 ns mode-S period balances the series-capacitor ladder,
but its start-up trim is 0.55-1.1x the loop's steady Ton, and ton_ns also set
the loop's reset value, scb_vff's C10 seed (tpre) and the 0.5x / 2x clamps.
scb_ctrl gets cfg_ton_s: ton_now outside mode P is cfg_ton_s. ton_acc still
resets to cfg_ton. scb_vff gets tseed (scb_ctrl's old ton_now expression with
cfg_ton), and tpre follows it instead of ton. scb_multi is regenerated. The
bridge's cfg "ton_s_ns" sets cfg_ton_s; absent = ton_ns. The testbench mirrors
cfg_ton into cfg_ton_s unless a test sets it.
**Gate:** cfg_ton_s = cfg_ton is the old controller bit for bit (ton_seed ==
ton_now). Unit tests 89/89, 1 of them new (mode_s_own_ton). pytest 693 passed.
cosim_regression --full and an A183 start-up rerun are identical (A184
BOUNDARY).

## 2026-10-05 (A145) - finite switching edges

**Source:** A144's overshoot came from instantaneous edges. cfg "edge"
{"didt_a_ns", "didt_on_a_ns"} -> CircuitParams edge_didt_off / edge_didt_on:
a switch in an edge is open and its channel current is a right-hand-side
source (Sim.edge_inc); turn-off with forward current ramps down, a hard
turn-on (V_DS > 0) ramps up until V_DS <= 0. FastPlant holds the ramps
(set_gate, _advance); KernelSim sends edge steps to FastSim.step;
KernelPlant2 steps in Python while a ramp is active; ReferencePlant
refuses edges. Sections add "edge_energy_j", the record "edge_params" and
"edge_stats". plant_kernel.c unchanged.
**Gate:** edges off = A144 bit for bit (A145 harness, id_ runs, regression);
Fast / Kernel / Kernel2 identical with edges on.

## 2026-10-05 (A141) - the floor's late report

**Source:** A140's duplicate phase-1 turn-on, traced to the RTL. A floor
(A118, or C06's slave floor) that fires in the window before the clocked
turn-off (timed edge or slot) reports two windows later (synchroniser),
after that turn-off was committed. scb_phase took the report only in LOW,
so it was ignored: the front end's turn-on reached the power stage first,
while Ton counted from the later clocked turn-on (+0-6 ns on, +20-38 A).

**Changes:**
- **`rtl/scb_phase.v`:** input `cfg_floor_late`. With it, a floor report
  in UP earlier than t_lo sets t_on = a_tlo + dt_pred and enters HIGH (the
  pending turn-on dropped); in HIGH, a floor turn-on earlier than t_on
  moves t_on to it. t_lo keeps the clocked edge: it is the slots' reference
  and the slaves' ext_ref, and must change once per cycle (A141's first
  version also moved t_lo; the slaves then saw two references in one
  master cycle and fired their slots a cycle early, 357 A on four modules).
- **`rtl/scb_ctrl.v`:** the input, passed to every phase.
- **`rtl/scb_multi.v`:** regenerated.
- **`bridge.py`:** cfg `floor_late` (default 0).
- **`tb/`:** 5 tests (4 in test_scb_ctrl, 1 in test_scb_slave); 85 pass.

**Gate:** off by default; A141 criterion 1 (an A140 record and a C10
record replayed bit for bit).

## 2026-10-03 (A118) - the floor: phase 1's front end armed in timed mode

**Source:** D63's design map and A120's search. The timed turn-off fails
on load decreases and falling input steps, where phase 1's valley passes
the zero-voltage threshold. A comparator floor below the target stops
that, and keeps the timed edge everywhere else.

**Changes:**
- **`rtl/scb_phase.v`:**
  - input `cfg_lo_floor`;
  - with it, phase 1's front end stays armed in timed mode
    (`arm = ... && (!lo_timed || cfg_lo_floor)`);
  - a front-end report that arrives before the timed edge is the
    turn-off, as with cfg_async (t_lo, t_on = a_tlo + dt_pred, HIGH), and
    is not current-bound, so there is no trim update.
- **`rtl/scb_ctrl.v`:** the input, passed to phase 1 only.
- **`rtl/scb_multi.v`:** regenerated.
- **`plant.py`:** `KernelPlant2.integrate_to` takes a chain of latches,
  each armed after the one before it fires. A single latch is the same
  code path as before.
- **`bridge.py`:** cfg `lo_floor` (default 0) and `lo_floor_a` (A,
  default 2).
  - While phase 1 is timed, the front end's threshold is i_target + trim
    − lo_floor_a.
  - The crossing measurement of i_target is chained before it.
  - A floor turn-off is not bound (no residual report).

**Gates:**
- RTL unit tests 56 of 56 (new: `lo_floor_arms_in_timed_mode`,
  `lo_floor_report_before_the_timed_edge_is_the_turn_off`,
  `lo_floor_timed_edge_first`);
- synthesis `check -assert` clean. Same flow before and after: SLAVE 0,
  41 963 → 41 998 cells; SLAVE 1, 36 887 → 36 948;
- the Python tests;
- `--full` regression PASS (the default is the previous behaviour);
- **identity on the front-end paths the regression cases predate:** A115
  n10 (comparator learning, then timed) and A116 c60_n0 (the front end
  throughout), rerun to 1700 µs. All 1478 sections are identical to the
  archived runs.

## 2026-10-03 (A115) - the input ramp as a configuration value

**Source:** A115 (P24's 1 MHz design point). The start-up ramp must
grow with √(L Cs), D60's margin over Roberts' first ladder resonance.

**Change:**
- **`bridge.py`:** cfg key `t_ramp_us` overrides the init run's input
  ramp (`t_ramp`), as `t_load_us` / `t_hand_us` do.

**Gates:**
- Absent the key, `make_params` builds the same parameters: the loop
  only adds keys present in cfg.
- A 20 µs start check of A115's `cfg_n12p5`: Vin 2.66 V at 19 µs,
  48 V × 19 / 343.05.

## 2026-10-03 (review) - recovery time, the output join, per-cycle gaps, an acceptance gate

**Source:** an external review of the multi-module level. All five
points were checked and found true. The results corrections are in
`reports/MULTI_MODULE_SUMMARY_2026-10-02.md` Section 7 and the C02 /
C03 / C04 / A108 errata.

**Changes:**
- **`matrix.step_stats`:** a trace still outside its band at its last
  sample has not recovered: `back_within_1pct_us` and
  `ladder_back_below_1pct_us` are inf.
  - Before, a trace stuck at 0.98 V reported 29.9 µs.
  - Every archived value is unchanged, since every step run recovered.
- **`matrix.gaps_per_cycle`** (new): every consecutive pair of low-side
  turn-offs against the local master period / (M N).
  - `lsoff_after` gives mean positions, which hid the cycle-by-cycle
    error: 0.58 ns max in C03 n0, against 0.05 ns of the means.
- **`plant.join_nodes`** (new), used by `cosim_multi`: the joined output
  voltage is the Co-weighted mean, or the plain mean when the Co are
  equal. That is the previous expression, so the result is
  bit-identical. Before, unequal `co` in `module_circuit` broke charge
  conservation.
- **`scripts/acceptance.py`** (new): the gate over the registered
  criteria of C01-C04, A108 and A109.
  - Each criterion is PASS, DOCUMENTED (listed with the RESULTS section
    explaining it) or FAIL.
  - Missing runs, rows absent from a summary, and listed exceptions that
    now pass fail the gate.
  - `--reanalyse` reruns the experiments' scripts.
  - **Now:** all ACCEPTED, 43 documented, 0 unexplained.
- **Profiling:** `COSIM_PROFILE` already dumped for the M-module system
  (2026-10-02 speed entry).

**Gates:**
- the whole test suite, 612 passed, 1 skipped, including:
  - `test_step_stats_not_recovered_is_inf`;
  - `test_gaps_per_cycle_c03_n0`;
  - `JoinNodes` (equal Co gives the plain mean; unequal Co conserves
    charge);
  - `tests/test_acceptance.py` (fail, documented, missing, outdated);
- C02 m4_n0 to 100 µs identical to the run before the change;
- `acceptance.py C04 --reanalyse` regenerates C04's summary identically.

## 2026-10-03 (speed) - every core: more jobs by default, plant threads in M-module runs; no change in results

**Asked by the user:** use more cores while running.

**Measured on the M5** (4 performance + 6 efficiency cores, 16 GB):

| batch | 4 jobs (before) | more jobs |
|---|---|---|
| 10 one-module runs, 150 µs | 81 s | **49 s** (10 jobs) |
| 8 four-module runs, 100 µs | 143 s | **111 s** (8 jobs); 3 jobs × 4 threads 157 s; 5 jobs × 2 threads 142 s |

For batches, more processes beat threads. Threads help when fewer runs
than cores are going.

**Changes:**
- **`run.py`:** `--jobs` defaults to every core (`os.cpu_count()`).
  - Each child gets `COSIM_THREADS = cores // (runs at once)`. An
    explicit COSIM_THREADS wins.
- **`bridge.py` `cosim_multi`:** with COSIM_THREADS > 1, the M plants'
  window integration runs in a thread pool (at most M threads). The C
  kernel releases the GIL.
  - The window step touches only its own module's plant, monitors and
    records, never the simulator, and every module still runs before
    the stop check.
  - Default COSIM_THREADS 1 when the bridge runs outside run.py.
- **`scripts/cosim_regression.py`:** `--jobs` defaults to every core.
- **Memory:** 252 MB per run at most (sampled), so 10 at once use
  ~2.5 GB.

**Gates (identical in every record except `wall_s` and `provenance`):**

| run | how | wall (archived → now) |
|---|---|---|
| C02 m4_n0 | alone, 4 plant threads | 400 → 144 s |
| C03 ls_p10 and l_p48_1us | together, 4 threads each | 353 → 203 s; 429 → 230 s |
| `--full` regression | default jobs | PASS, 69 s |

## 2026-10-02 (speed) - fewer signal writes and reads, a partial-step cache, -O3 -mcpu=native; no change in results

**Source:** a cProfile of 100 µs runs (`COSIM_PROFILE`, now also dumped
for the M-module system).
- **Four modules:** 81 s; the C kernel 45 s, signal writes 9.6 s
  (2.5 M), reads 8.5 s (1.95 M), Python partial steps 7.2 s.
- **One module:** 23 s; the kernel 11.9 s.

**Changes:**
- **`bridge.py` `Ctl.set`:** a write of the integer value last written
  to the same input is skipped. Only the bridge drives these inputs,
  and the reset is written directly.
- **`bridge.py` `MultiCtl`:**
  - writes combine in the shared cache and reach the DUT at
    `flush_writes()`, once per signal and phase, skipped when unchanged.
    `cosim_multi` flushes before every await that follows writes: after
    configuration, after start, after the windows' integration, after
    the sampling.
  - reads in a read-only phase come from a per-phase cache, cleared at
    each read-only phase. Every read happens in `read_rising`, the
    master's t_ref / t_lo1 reads, and `result`, all in read-only
    phases.
- **`plant.py` `KernelSim.step`:**
  - a step shorter than p.h (a gate edge or a window end inside the
    grid) keeps its factorisation and kernel entry in a bounded LRU
    cache (4096 entries) instead of rebuilding them. They are the same
    values; 95% hit rate.
- **`plant.py` `CFLAGS`:** `-O3 -mcpu=native` (was `-O2`), keeping
  `-ffp-contract=off -fno-fast-math`, so no fused or reassociated
  floating-point operations.

**Gates:**
- `tests/test_cosim_plants.py`, wrapper and matrix tests: 17 passed, 1
  skipped;
- `--full` regression PASS;
- full-length reruns identical in every record except `wall_s` and
  `provenance`, four at a time as before:

| run | wall before → after |
|---|---|
| C02 m4_n0 (four modules, 500 µs) | 400 → 287 s |
| C03 l_p48_1us (four modules, line step, 600 µs) | 429 → 322 s |
| A105 i2_s_p62 (one module, 600 µs) | 110 → 94 s |
| A109 s1_m48_10us (one module, `slot_trim`) | 135 → 86 s |

**What remains:** ~85% of a run is now the C kernel's fixed 10 ps
steps. Going further means a different integrator, which changes
results and so would be a new plant, not a speed change.

## 2026-10-02 (A109) - a valley trim for the slotted phases

Source: A108 RESULTS 0.3. The slotted phases' turn-offs had no
correction from their own current, so a lagging ladder left their
valleys positive. C01 found the same gap for slave modules.

- **`rtl/scb_phase.v`:**
  - inputs `cfg_slot_trim` and `cfg_st_smax`; output `sofs`, a signed
    offset added to a slotted phase's slot in mode P;
  - each residual-current report (r_valid) at a slot turn-off moves it
    later (r_below 0) or earlier, by a step that doubles while decisions
    agree (up to cfg_st_smax), as A100;
  - |sofs| ≤ 1024 LSB;
  - a master's phase 1 is not affected.
- **`rtl/scb_ctrl.v`:** the inputs passed to every phase; output
  `slot_ofs`.
- **`rtl/scb_multi.v`:** regenerated.
- **`bridge.py`:** cfg keys `slot_trim` (default 0) and `st_smax`.
  - With `slot_trim`, the residual-current sign is reported at every
    low-side turn-off.
  - `slot_ofs_final_lsb` is recorded.
- **Gates:**
  - RTL unit tests 53 of 53 (new: `slot_trim_adaptive_step`,
    `slot_trim_moves_the_slot`, `slot_trim_not_phase1`,
    `slot_trim_not_in_mode_s`);
  - synthesis `check -assert` clean: SLAVE 0, 47 914 cells; SLAVE 1,
    42 072;
  - wrapper and matrix tests;
  - `--full` regression PASS;
  - with the default, A105 i2_s_p62 and C02 m4_n0 rerun: every record
    identical except `wall_s` and `provenance`.

## 2026-10-02 (C02, track C) - slots referenced to phase 1's low-side turn-off; shared interleave statistics

Source: C01 RESULTS Section 2. Phase 1 of every module sat one valley
delay (9.44 ns) early, so the 16-phase interleave was not uniform.

- **`rtl/scb_ctrl.v`:**
  - input `cfg_slot_lo`: in mode P with following slots, the slots of
    phases 2..N are t_lo1 + (k − 1) T/N instead of t_ref + (k − 1) T/N.
    Configured slots stay on t_ref.
  - output `t_lo1`: phase 1's last low-side turn-off.
  - A phase still learns of a new cycle from t_ref, so the slot must
    lie after it: T/N − dt_pred > ~2 windows.
- **`rtl/scb_phase.v`:** output `t_lo_q` (its t_lo).
- **`rtl/scb_multi.v`:** regenerated.
- **`bridge.py`:** cfg key `slot_lo` (default 0). With it, the slaves'
  slot base and reference id are the master's t_lo1.
- **`matrix.py`:** `phase_waveform`, `ref_turnons`, `lsoff_after` and
  `output_ripple`, C01's interleave statistics as shared functions. C01's
  own script stays as the record.
- **Gates:**
  - RTL unit tests 49 of 49 (new: `follow_slots_from_phase1_low_off`,
    `slot_lo_keeps_configured_slots_at_t_ref`);
  - synthesis `check -assert` clean: SLAVE = 0, 46 443 cells; SLAVE = 1,
    40 127;
  - `--full` regression PASS;
  - `tests/test_cosim_matrix.py`: the shared interleave statistics equal
    C01's (ripple in four placements, low-side turn-off times);
  - with the default (`slot_lo` 0), A105 i2_s_p62 (one module, to
    600 µs) and C01 m4_n0 (four modules, to 500 µs) rerun: every record
    identical except `wall_s` and `provenance`.

## 2026-10-02 (C2, C3, track C) - multi-module: slave modules and the M-module system

- **`rtl/scb_ctrl.v`:**
  - inputs `cfg_ext_ton` and `ext_ton`: in mode P, Ton is ext_ton (the
    master's, broadcast);
  - parameter `SLAVE` (default 0) with inputs `ext_slot` and `ext_ref`:
    a slave's phase 1 is a slotted phase like phases 2..N, its low-side
    turn-off at ext_slot once per reference ext_ref. It resets LOW, and
    phase 1's front end and timed turn-off are off for it.
- **`rtl/gen_multi.py` → `rtl/scb_multi.v` (generated):** M instances,
  0 the master and 1..M-1 slaves. Every port except clk and rst is M
  times as wide.
- **`run.py`:** cfg `modules` > 1 builds `scb_multi` with M.
- **`bridge.py`:**
  - `MultiCtl`: module m's slice of the wrapper's signals; combined
    writes through a shared cache.
  - `cosim_multi`: M `ModuleSim`s, each the single-module plant with its
    own Co and load, so the system has M Co and the load / M.
    - Output nodes joined after every window by charge conservation; the
      largest and mean differences are recorded.
    - The master's Ton is broadcast.
    - Slave m's phase-1 slot is t_ref + m T / (M N) after each master
      turn-on (T: the master's last period, or the mean of its last two).
  - cfg keys `modules`, `module_circuit` (per-module circuit values); a
    load step's i_a is the system's.
  - The new inputs are set to 0 for a single module.
- **Gates:**
  - RTL unit tests 47 of 47 (new: `external_ton`);
  - synthesis `check -assert` clean: SLAVE = 0, 46 566 cells (A104
    46 468); SLAVE = 1, 40 447;
  - `tests/test_cosim_wrapper.py`: the wrapper regenerates identically;
  - M = 1: `--full` regression and the four feature-rich reruns (C1's)
    identical;
  - M = 2 smoke run (A105 I2 to 120 µs): no overlap; both modules in
    mode P at 72 µs; Vo 1.0000 V; equal currents; join difference ≤ 50 µV.

## 2026-10-02 (C1, track C) - the bridge per module, for multi-module runs

- **`bridge.py`:** restructured with no change in behaviour.
  - One module's plant, controller-side analog functions, measurements
    and records are a `ModuleSim`, with the window steps `read_rising`,
    `write_falling`, `run_window` and `sample`.
  - The controller's signals go through `Ctl` (with one module, the DUT).
  - `load_cfg` and `make_params` are shared.
  - Every operation keeps its order.
- **Gates:**
  - `--full` regression PASS;
  - A105 i2_s_p62 (timed turn-off, PI, load step), A106 pi100_p48_1us
    (line step), A102 e125_5v (branch enable) and A107 cs8p7_n0 (cfg
    `circuit`) rerun to their ends: every record identical except
    `wall_s` and `provenance`.

## 2026-10-02 (A107) - circuit values as scenario inputs; the shared standard matrix

- **`bridge.py`:** cfg key `circuit` {name: value, SI}.
  - Any of `CIRCUIT_KEYS` (vin, L, R, c_high, c_low, cs, co, r_load,
    i_load, g_on) replaces the init run's value.
  - Other names are refused. Structural values (n, load kind) stay out.
  - One mechanism for every circuit-value scenario, instead of a key per
    value.
- **`matrix.py` (new):** the standard matrix as one definition: rows,
  configurations from a step-free base, `window_stats`, `step_stats`.
  - It replaces copies in experiment folders. A105's `matrix_stats.py`
    stays as the record.
- **Gates:**
  - `--full` regression PASS;
  - `circuit: {cs: 3e-6}` (the default) gives sections and steps
    identical to no override (A105 i2_n0 to 30 µs);
  - `tests/test_cosim_matrix.py`: the module regenerates A105's and
    A106's configurations exactly, and its statistics equal A105's and
    A106's.

## 2026-10-02 (A106) - input (line) step

- **`circuit.py`:** `vin_step`, `t_vstep`, `t_vslew`. `vin_at` adds
  vin_step × min((t − t_vstep)/t_vslew, 1) from t_vstep (at once if the
  slew is 0); nothing without a step.
- **`plant_kernel.c`, `plant.py`:** the same in the C `vin_at`; the run
  struct and `_Run` gain the three fields at the end.
- **`bridge.py`:** cfg key `line_step` {"t_us", "dv", "slew_us"}.
- **Gates:**
  - `--full` regression PASS;
  - `tests/test_cosim_plants.py` `CosimPlantLineStep`: −4.8 V over 10 ns
    inside the lockstep window. Fast, Kernel and Kernel2 (loop and
    monitors) are bit-identical with Reference.

## 2026-10-02 (A104) - proportional term in the voltage loop

- **`rtl/scb_ctrl.v`:** input `cfg_kp` (parameter KPW = 24, FRAC = 16
  fractional bits).
  - At each ADC sample in mode P with the loop on, p_term = kp × e is
    held.
  - Ton = round(ton_acc + p_term), clamped to [ton_min, ton_max].
  - With cfg_kp = 0, Ton is A79's round(ton_acc).
- **`bridge.py`:** cfg key `kp_ns_per_v` (default 0), in the same units as
  `ki_ns_per_v`.
- **Gates:**
  - RTL unit tests 46 of 46 (2 new: `voltage_loop_proportional`,
    `voltage_loop_pi`);
  - synthesis `check -assert` clean, 46 468 cells (A100: 43 924);
  - `--full` regression PASS.

## 2026-10-02 (A103) - start-up sequence timing

- **`bridge.py`:** cfg keys `t_load_us` and `t_hand_us` override the init
  run's load connection and handover request times (default: the init
  run's, 88.61 µs each).
- **Gate:** `--full` regression PASS.
- **RTL and plant unchanged.**

## 2026-10-02 (A102) - branch enable time and per-branch precharge

- **`plant.py`:** `aux_armed` (default all True). A disarmed branch
  ignores its low side's edges, so its switch stays open; once armed it
  starts at its next low-side turn-off. Python-side only (`_aux_gate`),
  shared by all four plants; the C kernel is unchanged.
- **`bridge.py`:** cfg `aux` keys `t_en_us` (default 0: armed from the
  start, as A101) and `vm0_v` as one value or one per branch. With
  `t_en_us` > 0 the branches start disarmed and open, and are armed at
  the first window at or after `t_en_us`. `aux_params` records `vm0_v`
  as a list per branch, `t_en_us` and `t_armed_s`.
- **Gates:**
  - `--full` regression PASS (format additions as before);
  - `tests/test_cosim_plants.py`: `CosimPlantAuxEnable` (disarmed for
    150 ns, then armed; per-branch precharges): FastPlant and KernelPlant
    bit-identical with ReferencePlant, and no branch current while
    disarmed;
  - A101's `dz_vz0` and `p125` rerun to 100 µs: every section equal to
    the archived runs.
- **RTL unchanged.**

## 2026-10-02 (A101) - auxiliary commutation branches

- **`circuit.py`:** `aux_phases`, `aux_l`, `aux_r`, `aux_c`, `aux_vm0`.
  - Per listed phase, a node m_k with Cm to ground (after "out") and a
    branch current (after the phase currents) through Lr from m_k into
    x_k while its bidirectional switch conducts.
  - The switch states follow the 2N switches in `conducting`. An open
    branch is uncoupled, with di/dt = 0.
  - Without branches every matrix is as before.
- **`plant.py`, `plant_kernel.c`:** the same in all four plants.
  - The switch is commanded with its phase's low side complemented.
  - It opens at the step where its current reaches or crosses zero after
    the open-command (current set to 0, Euler restart).
  - Per branch: int i² dt and the current extremes.
  - The peak phase current counts the phase currents only.
  - Monitors' `vmin_zero`: the high side's minimum stops at its first
    V_DS ≤ 0.
  - The C run struct gains its fields at the end.
- **`bridge.py`:**
  - cfg key `aux`;
  - Cm voltages and branch records in the sections;
  - `highoffs_last` (phase and branch currents at every high-side
    turn-off) in every run, a format addition.
- **Gates:**
  - `--full` regression PASS (`highoffs_last` listed as a format
    addition);
  - `tests/test_cosim_plants.py`: 3 new tests with branches on every
    phase. ReferencePlant, FastPlant, KernelPlant and KernelPlant2 are
    bit-identical, including the zero-current openings.
- **RTL unchanged.**
- **Later the same day:** `valley_zero` defaults to 0. With 1, the
  turn-off currents of phases 2-4 became unstable in A101 (z075); with
  the plain valley measurement the same design is stable (dz_vz0). All
  A101 configurations set the key explicitly.

## 2026-10-01 (night, A100) - adaptive dlo step and Ton feedforward

- **`rtl/scb_phase.v`, `rtl/scb_ctrl.v`:**
  - `cfg_lo_adm` / `cfg_lo_smax`: dlo's step doubles while consecutive
    decisions agree, up to the cap, and returns to 1 when they differ
    (Jayant's adaptive delta modulation).
  - `cfg_lo_ff` / `cfg_lo_kff`: dlo moves by kff times every change of
    ton.
  - With both at 0, dlo's update is A99's ±1 with a floor at 0.
- **`bridge.py`:** cfg keys `lo_adm`, `lo_smax`, `lo_ff`, `lo_kff`.
- **`tb/`:** 2 new tests. **44 of 44 pass.**
- **Gates:**
  - `--full` regression PASS;
  - A99 n0 replayed bit-identically;
  - synthesis 0 problems, 43 924 cells.
- **A100's result:** ADM32 (`lo_adm` 1, `lo_smax` 32) tracks ±25 and
  ±62.5 A steps within 1.7 A.
- **Recommended, not yet in the preset**, pending the trade-off review
  (`reports/TRADEOFF_SCORECARD.md`).

## 2026-10-01 (night, A100) - load step and record length

- **`circuit.py`, `plant_kernel.c`, `plant.py`:** a load current step
  (`i_step` from `t_step` on), on top of the load, in the source term.
  - No step: a + 0.0, so nothing changes.
  - The C run struct gains two doubles at its end, so no other field
    moves.
- **`bridge.py`:** cfg keys `load_step` {"t_us", "i_a"} and
  `records_last` (default 1000).
- **Gates:**
  - `--full` regression PASS;
  - `tests/test_cosim_plants.py` passed.

## 2026-10-01 (later still) - timed phase-1 turn-off (A99)

- **`rtl/scb_phase.v` (phase 1), new `cfg_lo_pred`.**
  - Each comparator-decided mode-P turn-off sets `dlo` to its on-low
    interval.
  - After `cfg_lo_learn` of them (`lo_timed`), the turn-off is a timed
    edge at t_lon + dlo, followed by the predictive turn-on, and the
    asynchronous front end is no longer armed.
  - dlo then steps +1 LSB when the crossing report is early or below
    `cfg_lo_tgt`, else −1.
- **`rtl/scb_ctrl.v`:** the ports; `dlo1` and `lo_timed1` are outputs.
- **`bridge.py`:** cfg keys `lo_pred`, `lo_learn`, `lo_tgt_ps`.
  - In timed mode it measures phase 1's crossing of i_target with the C
    loop's latch test, used as a measurement only.
  - It reports actual turn-off − crossing (or early) at the turn-off.
  - Output fields are added only when `lo_pred` is set.
- **`tb/`:** 3 new tests (learning then timed; the ±1 update; no arming
  when timed). **42 of 42 pass.**
- **Gates:**
  - `--full` regression PASS;
  - `tests/test_cosim_plants.py` passed;
  - synthesis: 0 problems, 41 605 cells.
- **A99's result:** the timed mode lowers the jitter response of phases
  2-4 by 30-38% and removes the trim's limit cycle.
- **Not adopted yet** (load steps untested). The preset is unchanged.

## 2026-10-01 (late night) - jitter on one side's edges only (A98)

- **`bridge.py`:** `driver.jitter_edges` = `"high"` or `"low"` restricts the
  Gaussian edge jitter to that side's gate edges.
  - Absent or `"all"`: every edge, and the same random sequence as before.
- **Gate:** `scripts/cosim_regression.py --full` PASS (A92 j100 exercises
  the jitter path).
- **The preset is unchanged.** A98's gain-1/4 runs lowered the turn-ons
  before the valley but raised the reverse-conduction loss by more than the
  hard-on loss they saved.

## 2026-10-01 (night) - slots from the two-period average (A97); the preset adopts them

- **`rtl/scb_ctrl.v`:** new input `cfg_slot_avg`.
  - It keeps the period before last (t_per2) and a flag that three phase-1
    turn-ons have been seen.
  - With `cfg_slot_follow` as well, phase k's slot is
    t_ref + (k-1)(T_meas + T_prev)/(2N).
  - With the bit at 0, A93's expression is unchanged.
- **`bridge.py`:** cfg key `slot_avg` (absent = 0).
- **`run.py`:** the provenance's `cfg_path` is project-relative when the
  configuration is inside the project, so published records carry no home
  directory. This is a format change only; `--quick` still passes.
- **`tb/`:**
  - the fixture drives the new input (0 by default);
  - `_phase1_cycle` can hold the current comparator for a different
    period;
  - 3 new tests; **39 of 39 pass**, with A93's 36 unchanged.
- **Gates:**
  - `scripts/cosim_regression.py --full` with the new RTL: A89 r2, A92
    j100, A92 m3p and A93 m3n_both are bit-identical (61-64 s each);
  - `tests/test_cosim_plants.py`: 3 passed;
  - synthesis: 0 problems.
- **`presets/p24_5pct_adopted.json`:**
  - now has `slot_follow`, `slot_avg`, `slot_guard` = 1 and
    `plant_impl` `kernel2` (bit-identical to the `kernel` it named);
  - **A97 adopted these slots**
    (`experiments/track_A_periodic_steady_state/A97_verilog_averaged_period_slots/RESULTS.md`
    Section 7);
  - the preset equals A97's `cfg_n0_avg_guard.json` except for `out` and
    `note`;
  - A92's adopted configuration remains in A92's folder.

## 2026-10-01 (evening) - process check (`scripts/cosim_trace_compare.py`)

**What it checks.** That the trajectory, not only the result, is the same
before and after the clean-up. It uses the opt-in `COSIM_TRACE` in
`bridge.py`.
- A92 n0 runs twice: once with the archived A92 bridge and plant (copied
  verbatim into tmp, with the same checkpoint lines), and once with
  `kernel2`.
- At every checkpoint both runs update a running BLAKE2b hash of t, the
  full state y, the diode flags and the Euler counter. The checkpoints are
  the plant integrated to each gate edge and to each 4 ns window end.

**Result: 125 259 checkpoints, all identical.** Final digest
82f7bab1ecfd3afb3bafee693dcc7e4f in both runs. Both outputs are also
bit-identical to the archived run.

**Wall time, each run alone:** 1444.7 s with the archived code, 54.7 s
with `kernel2` (26 times faster).

## 2026-10-01 (evening) - benchmark against the archived runs (`scripts/cosim_benchmark.py`)

**`--batch`.** A92's 9 configurations, default plant, 4 at a time:
- 147 s in total, 61-67 s per full run (16 s for the 96 us diagnostic);
- all 9 are bit-identical to the archived runs;
- for comparison, the archived batch took 4353-4452 s per run with 8-10
  runs at once.

**`--plants`.** A92 n0, the adopted design, full length. The first four
ran at once, one core each; kernel2 ran alone.

| implementation | wall time | result against the archived run |
|---|---:|---|
| archived A92 bridge and plant (the code before the clean-up) | 1998 s | bit-identical |
| `reference` (same plant code, shared bridge) | 1983 s | bit-identical |
| `fast` | 1151 s | bit-identical |
| `kernel` | 423 s | bit-identical |
| `kernel2` (default) | **53 s** | bit-identical |

All five give Ton 17.750 ns, period 232.2025 ns, Vo 1.000183 V, dither
0.7066 A, P_rev 0 W, settling 116.86 us after the handover, peak 186.19 A
and 26.80 V. Each runs 38 906 796 steps and records 1756 sections.

## 2026-10-01 (later) - the step loop and the Newton fallback in C (A96)

- **`plant_kernel.c` gains:**
  - the full-Newton fallback (dgemm and dgesv with numpy's arguments);
  - `pk_run`, the whole step loop with the bridge's per-step monitors.
- **`plant.py` gains:**
  - `KernelPlant2`, the plant whose `integrate_to` runs `pk_run`;
  - `Monitors`, the shared monitor arrays and their Python update.
- **`bridge.py`:**
  - the monitor state moves to `Monitors`, for every plant;
  - the latch actions move into `latch_fire()`;
  - a `kernel2` plant choice;
  - optional profiling (`COSIM_PROFILE`).
- **Gates:**
  - A96's step-level equivalence: 519 395 steps, every field and monitor
    identical;
  - `--quick` regression with `kernel` (the bridge refactor on the Python
    path), with `kernel2`, and with the new default: PASS;
  - **`--full` with `kernel2`:** A89 r2, A92 j100, A92 m3p and A93
    m3n_both are bit-identical, **122-128 s each**, 4 at a time;
  - **`--full` with `kernel`** (the Python-monitor path, and the C
    fallback inside `pk_step`): bit-identical, 618-622 s each;
  - `tests/test_cosim_plants.py`: a KernelPlant2 loop-and-monitors test
    is added (3 tests).
- **The default plant is now `kernel2`.**

## 2026-10-01 - the package is created (code clean-up)

| piece | taken from | how it was checked |
|---|---|---|
| `rtl/` | A93's `rtl/` (A77 → A80 → A81 → A89 → A92 → A93) | Code identical to A93's below the rewritten header comments. 36/36 unit tests. Replays (below). |
| `tb/test_scb_ctrl.py` | A93's tests | Test code identical; docstring rewritten. 36/36 pass. |
| `circuit.py` | A88's `a88_transient.py`: `Params` (trimmed to the fields the co-simulation uses, as `CircuitParams`), `topology`, `EPC2067Coss`, `fit_fig8`, `Sim` | Every function body is AST-identical to A88's; `import csv` moved to the top of the module. |
| `plant.py` | `ReferencePlant`: the bridges' `Plant` (A89-A93); `FastSim` / `FastPlant`: A94's `fast_plant.py`; `KernelSim` / `KernelPlant`: A95's `kernel_plant.py` | Every method body is AST-identical to its source. The kernel library is now built content-addressed into `tmp/cosim_kernel/`. |
| `plant_kernel.c` | A95 | Code identical; header rewritten. |
| `bridge.py` | A94's bridge | The loop is unchanged. Added: plant selection (`plant_impl`, default `kernel`); `init_run` falls back to project-relative; output path, stop time and provenance from `run.py`; gzip when the output name ends in `.gz`. |
| `run.py` | new | Runs each configuration in its own process, at most `--jobs` (default 4) at a time. |
| `presets/p24_5pct_adopted.json` | A92 n0's configuration | The adopted design. `init_run` is project-relative and the output compressed. |

**Gates (2026-10-01):**
- `scripts/cosim_regression.py --full` with the kernel plant: A89 r2,
  A92 j100, A92 m3p and A93 m3n_both, full length (388.61 us), are
  **bit-identical**.
  - That covers every section, the final registers, the step count, the
    peaks, and every recorded turn-on, low-side turn-off, low-side
    turn-on and edge.
  - Format additions only: `provenance`; for A89 r2 also the fields that
    bridges newer than A89's write.
  - 542-552 s each, 4 at a time.
- `tests/test_cosim_plants.py`: FastPlant and KernelPlant against
  ReferencePlant, 3000 steps each.

### Lineage of the controller options (summary)

| experiment | option |
|---|---|
| A77 | predictive valley turn-on, comparator trim, restarts, fixed slots |
| A80 | mode S start-up, handover, voltage loop |
| A81 | asynchronous phase-1 front end (`cfg_async`) |
| A89 | timed low side (`cfg_low_pred`, dtl corrector); leading-edge blanking (`cfg_blank`) |
| A92 | error-based correctors (`cfg_err_low`, `cfg_err_high`, targets, gain) |
| A93 | period-following slots (`cfg_slot_follow`), missed-slot guard (`cfg_slot_guard`). Not adopted: they raise the dither. |
| A97 | slots from the two-period average (`cfg_slot_avg`). Adopted, with follow and guard: the dither returns to A92's and the m3n starvation stays removed. |

### Lineage of the plant (summary)

| experiment | step |
|---|---|
| A71-A73 | the N-phase zero-start circuit |
| A86 | datasheet Coss(V) |
| A87 | reverse drop |
| A94 | FastPlant: Python overhead removed, bit-identical, 1.66 times faster |
| A95 | C kernel, bit-identical, 3.17 times faster than the original |

## A128 (extension ml_design_assist): Vin feed-forward, opt-in

- New `rtl/scb_vff.v`, instantiated in `scb_ctrl.v`; `scb_multi.v` was
  regenerated.
- The bridge samples Vin with Vo's ADC sample (cfg "vff": c, k, sh2,
  sh20, vin_lsb_v).
- With "vff" absent, every phase gets ton_now bit for bit.
  - `cosim_regression.py --full` passes.
  - Unit tests: 59/59, 3 of them new.
- Spec: `extensions/ml_design_assist/experiments/A128_cosim_vin_feedforward/SPEC_RTL.md`.


## A205: replay snapshots, opt-in

- cfg "snap_us" [t0, t1]: the bridge records the full plant state and every
  gate voltage at phase 1's high-side turn-off commands inside the window
  (record "snaps"). With "debug_edges_us" it is the input of an open-loop
  replay in LTspice (`scripts/p24_replay.py`).
- Read-only (`Module.snapshot`); absent, the record has no new key.
- With it the record also lists every interlock hold (`gate_holds_last`:
  hold start, switch, release), kept by gate.py in `hold_log`.
  - `cosim_regression.py --quick` passes.
  - A run with and without "snap_us" has equal sections (A205 BOUNDARY).


## A206: zero-voltage turn-on as an edge, switch resistances (plant V6), opt-in

- cfg gate "zvs_edge" 1 (`gate.py`): a turn-on commanded at V_DS <= 0 is an
  active edge from the command. The device's third-quadrant channel carries
  the reverse current while the gate charges; a turn-on edge then ends at
  |V_DS| <= v_hand with the gate above its channel start. Under an
  interlock, such a turn-on waits while its complement conducts.
  A conducting switch commanded off at reverse current is an edge too: its
  channel conducts until the gate has discharged (below 0.1 V), then the
  Vf + R fit takes over. For the interlock it conducts only while its gate
  is above the channel start.
- cfg gate "miller" 1: an idle off gate follows its charge balance with its
  drain's movement (`GateEdges._follow`), after Python steps and at commands.
- cfg gate "r_on_ls": the low sides' own turn-on resistance.
- cfg "r_sw_mohm" [high, low] (`CircuitParams.r_sw`, `Sim.g_sw`): the
  resistance of a conducting switch position, in place of g_on.
- Why: A205 found the plant 12.6 W and 3.5-6.8 A per period away from
  LTspice with EPC's model. The harness
  (`A206_p24_low_side_zvs_turn_on/a206_edge.py`) is within 3-8 % of LTspice
  on one low-side turn-on at 3.0 / 1.0 / 0.3 ohm with the three parts on.
  The reverse-current turn-off came in A206's second round: with only the
  turn-on, mode S ended 1.6-1.8 A per period away from LTspice; the harness
  is within 2 % of LTspice on that turn-off (12.73 against 12.50 nVs).
- With all four absent every step is as before.
  - `cosim_regression.py --quick` passes.
  - A205's N0 record: 751 sections and 7 snapshots to 160 us, bit for bit
    (checked again after the second round's change).
  - Unit tests: `tests/test_cosim_gate_zvs.py` (7; 5 need the vendor library).
