# A216 - skipped rounds: one module regulates below its lower Ton limit (BOUNDARY)
Method: RTL (scb_phase, scb_ctrl) + bridge (ticks, front-end inhibit, a second load event in the plant) + cosim.
Track A. Written and committed before the V6 runs. Looked at beforehand, on the ideal plant (A143's cfg, ideal
switches, no gate model; development runs, not records): the function itself and the numbers quoted in Section 3.
Decision it changes: whether the final configuration takes cfg "skip", which moves the specification's minimum load
from 30 % of a module to no load, and whether a raised lower limit is a way to light-load efficiency on slow boards
(A211) or that needs whole modules shed.
Cheaper check done first: unit tests (100 of 100) and thirteen ideal-plant runs of 420 us (2.5 min each).
Budget: 11 runs, 5.7 run-equivalents of 900 us, about 1.5 h at 10 jobs.

## 1. What and why
- A207 / A208 / A210: below about 30 % of its load a module's Ton sits at its lower limit and the output runs away
  upward (1.09 V at 10 % on N0, 1.56 V at no load with the old limit). The valley is held at -15.6 A, so the
  current a module delivers cannot fall below what one pulse per period gives.
- The remedy leaves pulses out. With cfg_skip, when the loop's Ton is at its lower limit and the last Vo sample is
  above vref + hi, phase 1's next turn-on is withheld; phases 2-4 turn their low sides off at their slots and stay
  off too, so every phase ends its last pulse at its valley and the module idles with all eight switches off.
  Phase 1 then asks for an ADC sample once per period. At the first sample at or below vref + lo it turns its low
  side on; its current comparator ends that interval at the target (as before lo_learn), and the next cycle is a
  normal one from the valley. Phases 2-4 turn their low sides on at the same instant plus their slots, so each gets
  the interval phase 1's comparator measured. No pulse starts from zero current, and no high side turns on hard.
- The condition is read from the registers of A215 when cfg_ton_lat is set (three comparison bits loaded with the
  phases' Ton), so the Ton arithmetic still reaches no phase register within a clock.
- Bridge: a tick samples the ADC and adds a record to "sections" (key "tick"); the front end makes no turn-on when
  the controller skips it; cfg "load_step2" adds a second load event (plant kernel), so a release and a
  re-application fit in one run. All absent = bit for bit.
- Rows (final configuration, plant V6, lower limit 4.0 ns, ton_lat 16, skip hi 5 mV / lo 1 mV): the load released
  at 300 us to 20, 10 and 0 % on N0; to 10 % on N75, S75 at 25 C and S75 at 125 C; N0 released to 5 %, then
  +62.5 A (the specification's load step) at 380 us.
- Information rows: +237.5 A back from 5 % with skipping and +200 A back from 20 % without (larger than any load
  step run so far); S75 at 30 % with the lower limit raised to 20.78 ns (its 60 % register), so that it runs large
  pulses and skips; A215's +62.5 A row with skip configured (the limit is never reached there).
- Not tested: four modules (the slaves do not follow a master's pause yet), start-up into a light load, line steps
  while skipping, other thresholds.

## 2. Criteria
1. i1: with "skip" and "load_step2" absent the cosim is the old one: unit tests all pass, regression quick and full.
2. i2: A215's m16_n_s_p62 with skip configured gives the same sections, edge log and gate records as without it.
3. s1 (all seven rows): COMPLETED, 0 shoot-throughs, 0 overlaps, 0 forced edges, whole-run peak <= 200 A,
   V_DS <= 40 V.
4. s2 (seven rows): Vo within 1 V +- 10 mV over the last 20 us.
5. s3 (seven rows): over the last 20 us every low-side turn-off current inside the board's band of A208 / A210
   ([-20, -12] A on N0 and N75, [-22, -8] A on S75) and no late fire.
6. s4 (the +62.5 A row): after the step Vo stays within 1 V +- 50 mV.

## 3. Predictions (not criteria)
- Ideal plant, N0: no load ends at 1.002-1.005 V with every round skipped; 5 % runs 62 % of its rounds, Vo
  1.000-1.006 V; +62.5 A out of skipping: peak 57-63 A, dip 12-16 mV, back at 1.000 V. On V6 the nominal board
  regulates at 20 % without skipping (A208: 4.53 ns), so that row skips only in the transient; 10 %, 0 % and 5 %
  skip steadily. s1 and s2 pass on all seven rows; Vo's mean sits 2-4 mV above 1 V while skipping.
- s3: phase 1 inside the band (its comparator ends the resume interval). Phases 2-4 miss it by up to 4 A on some
  resumes: an idle node rings (L against the switches' output capacitance), and the resume catches each phase at a
  different point of that ring (ideal plant: -23.8..-13.4 A). So s3 is expected to miss on phases 2-4 of the
  skipping rows; the slow board's rows are open (A210: at 4.0 ns its high sides do not finish turning on).
- The release itself (r3 of A208, not a criterion here): the overshoot is the inductors' energy and stays as it
  was (ideal plant: 1.057 V with and without skipping at 10 %).
- Large re-applications: over 200 A with and without skipping (ideal plant, +225 A from 10 % without skipping:
  235 A; +237.5 A from 5 % with: 246 A). The loop's upper Ton limit is twice its seed and bounds nothing.
- The raised limit: Vo's band at the end wider than +- 10 mV (ideal plant: 13 mV peak to peak at a 16 ns limit,
  27 mV at 24 ns), loss below A211's 17.57 W by 20-40 %.

## 4. Decision rule
- i1 or i2 fails: stop and fix.
- s1, s2 and s4 pass on N0 and N75: the final configuration takes skip (hi 5 mV, lo 1 mV) and the specification's
  minimum load becomes "none" for those boards, with s3's figures stated as measured. A slow-board row failing
  s1 or s2 keeps that board's minimum at 30 % and names why.
- s3 misses by more than 5 A, or s1 fails anywhere: skipping is not adopted as it is; the resume is reworked.
- The raised limit: adopted for slow boards only if s2 holds with it. Otherwise light-load efficiency on slow
  boards is left to shedding whole modules, which needs the slaves to follow a pause (the next step).
- The large re-application rows decide nothing here; they set the size of the next problem (an upper Ton limit of
  its own, or a peak limit).
