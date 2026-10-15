# Final package specification: configuration and what it was checked on

Written 2026-10-08 after an external review of D70-D79 / A163-A172. It found that the summary's "every corner, four
modules" ran on two plant versions. This file fixes the final configuration, lists which plant version each result
comes from, and says what may be claimed.

## 1. The final configuration (frozen)

| part | setting | source |
|---|---|---|
| controller | frozen RTL: one module A143 (lo_learn 4) on A129 g125 + vff {rel_q8 320, rel_lp 1, seed 2} + floor_late; four modules C12 + lo_learn 4 (C13). One register added by user decision on 2026-10-09: cfg_ton_s, mode S's own Ton (A184; scb_vff's C10 seed and the loop's reset value keep cfg_ton; equal values = the old controller bit for bit). **Since 2026-10-14 the RTL is open again (user decision). A215: the phases read their Ton from registers loaded 16 clocks after the last change of the Ton arithmetic's inputs (cfg ton_lat 16: 68 ns from the sampling instant to the phases); checked on nine V6 rows, every other row ran with 0. Tested bound 17 clocks: at 32 two binding rows cross 200 A and the 30 % rows starve (the bridge refuses ton_lat > 30)** **Skipped rounds below the lower Ton limit on nominal boards (A216-A222, plant V7): cfg skip {hi 5 mV, lo 1 mV, res_ofs_a and zcd_a = 8 ns × Vo / L}: a module pauses with every low side turned off at zero current, resumes with its low sides, phase 1 ending its interval at the target; the slots keep their period across a pause** **A damped loop for large load steps (A223-A229, plant V7, adopted 2026-10-16): scb_vff's relative cap on phase 1 acts only while Vin rises by ≥ 0.5 V (vff rel_gate 25 codes), and the loop gets a derivative term on the Vo sample's change (kd 355 ns/V, dead band 2 codes, held to the next sample), which is 0 while the PI output is within 4 ns above the lower Ton limit (kd_hold 1, kd_band_ns 4.0) so it stays out of the skipping bursts. Run on one module only (A223-A229's rows); the other columns of Section 3 and four modules ran without it** | A143, C13, A184, A215, A216, A217, A220, A221, A223, A224, A228, A229 |
| loop | 50 pH, ideal parallel damper at ring Q 7 | A168, A157 |
| devices | EPC2067, EPC's model (vendor library at run time), 2 + 3 per phase; spread corners ff (V_th −0.3 V, driver ×0.8), ss (V_th +1.0 V, Q_G ×1.29, driver ×1.2), hot (125 °C) | D79, A163 |
| drive | high sides: 3.0 Ω turn-on / 0.3 Ω turn-off per device, ±20 %; R_G 0.3 Ω; every switch gate-driven. **Low sides, since A206 (plant V6): their own turn-on resistance, 0.3 Ω times the board's drive factor (0.36 Ω on slow boards); turn-off 0.3 Ω as before.** They turn on at zero voltage and gain nothing from a slow gate: with 3.0 Ω the semiconductor loss is 29.6 W per module against 20.2 W, and the handover reaches 206.4 A with switches at the datasheet maximum. Up to A205 every switch had 3.0 Ω, and every V5 result in this file was run that way | A164, A169, A205, A206 |
| controller-side lead | high-side turn-on earlier by 8 ns, or by 9.5 ns on slow boards (the corner read from the 25 °C trim), ramped in over 20 µs after the handover. The 9.5 ns lead closes the slow corner's 125 °C post-step miss (A191). On its other rows it costs 3-5 A of peak and 3-5 mV of dip at 25 °C on +4.8 V / 1 µs (S75 ≤ 197.1 A, A192). Below 25 °C the same row holds: S75 ≤ 195.0 A at −40 °C and ≤ 197.8 A at 0 °C (A193, three step positions each; margin 2.2 A) | A167, A191, A192, A193 |
| start-up | **since 2026-10-10 (A188):** mode S at t0 = 200 ns, so every turn-on is hard and the series-capacitor ladder stays balanced (A183; at 400 ns slow boards split to 15.6 / 14.8 / 8.9 / 8.7 V). Per-board trim of mode S's Ton (cfg_ton_s) to Vo(143.5 µs) = 1.035 V: nominal 23.65-23.68 ns at L × 0.7-1.3, slow 35.45-35.80, ff 21.33 ns. The loop's seed is ton_ns = T_ss + (kp + ki)(Vo_entry − 1 V), from one closed-loop measurement (A185). The handover is requested at Vo ≥ 1.045 V or at 144 µs, whichever comes first: a sequencer comparator on the sampled Vo (A188; at 25 °C it never fires). Trims and seed are set once at 25 °C. Above 25 °C they stay locked (A188). Below 25 °C the mode-S trim follows a per-corner table, the corner read from the 25 °C trim: slow +0.531 / +1.441 ns, nominal +0.113 / +0.313 ns at 0 / -40 °C (A190, held on hold-out boards; device model extrapolated below 25 °C). Without the table slow boards fail cold (A189: -40 °C entry 0.956 V, 278 A; 0 °C 211 A). Checked at -40, 0, 25 and 125 °C. Superseded: t0 400 ns with ton = ton0 + (1.035 − Vo)/0.026 (A164-A181). **On plant V6 with 0.3 Ω low sides the 25 °C trims move: nominal L0 −0.279 ns, nominal 0.75 L0 −0.261 ns, slow 0.75 L0 +0.289 ns (A206; the cold table stays on top). Checked on these three boards (slow also at 0 and 125 °C): Vo before the handover within 3.1 mV of V5's, Vo ≤ 1.0476 V, handover ≤ 182.0 A**. **On plant V7 (A222) the 25 °C trims move again by +1 / +2 / +3 steps of 31.25 ps: N0 23.4375 ns, N75 23.46875 ns, S75 35.84375 ns; Vo before the handover then within 1.0 mV of V6's on all three boards, S75 at 125 °C within 0.2 mV (maximum 1.0474 V)** | A183-A190, A206, A222 |
| calibrated vs adaptive | factory, once per board: the mode-S trim and the loop seed (one closed-loop measurement of T_ss). Adapting at run time: valley timing (dt_pred, dlo), low-side dead time (dtl), negative-current trim, the Vin feed-forward's filters. Fixed: drive resistors, lead (per corner class, set once), t_il | A143, A164, A192 |
| driver interlock | threshold form: a channel about to start while its complement conducts waits at that gate level, then starts t_il = 0.5 ns after the complement stops (modelled ideally). The release time is a timing spec, not a safety one: no delay up to 8.3 ns changed a peak or V_DS. At the slow corner it should release within 1.0 ns (A179: after the −8 V ramp the late fires rise at 1.4 ns at 2 of 4 step positions); a per-board comparator reference (V_th − 0.2 V, ~1.4 ns) is just above that, a fixed 1.0 V reference (8.3 ns) far above. This settles the ramp's late fires only: at 1.0 ns the load step's spike count still fails its registered tolerance (scatter, open), and a real comparator's offset, noise and early release are not modelled | A171, A173, A174, A177, A179 |
| load range | **Minimum load per module: 30 % (75 A), with the loop's lower Ton limit set to ton_min_ns = 4.0 ns (A208, A210; plant V6).** 30 % is the lowest row that works on every board tested: nominal L0 and 0.75 L0 at 25 °C, slow 0.75 L0 at 0 / 25 / 125 °C. Nominal L0 regulates to 20 %; nominal 0.75 L0 reaches the limit near 26 %; the slow board regulates at 20 % but its high sides are then turned off before they have finished turning on (not counted). Below a board's floor Vo rises (1.06-1.09 V with 10-20 % of the load): there is no light-load mode and no way to shed a module. The limit is a bridge cfg value; cfg_ton_min is an existing RTL input. **Before A208 it was half the loop seed (22.25 ns) and the floor about 70 % (A207); every earlier row ran at 75 % or more and never reached it, so those rows are unchanged.** Semiconductor efficiency in the plant's books at light load: nominal L0 93.7-95.0 % from 60 to 20 %; nominal 0.75 L0 92.0 % at 30 %; slow 0.75 L0 79.7-82.6 % at 30 % (15.8-19.1 W, of it 9-12 W in high-side edges at 5.5-5.8 MHz): the frequency rises as the load falls **Since A221 / A222 (plant V7, skipping): no minimum on nominal boards.** N0 and N75 at 10 % regulate with every valley inside −20..−12 A (−16.8..−13.5 / −16.7..−14.4 A) and 2.5 / 3.1 W of semiconductor loss plus about 8 W booked in r_core (a damping resistor, not the design's core loss, D83 Section 3); N0 with no load regulates at 1.0017-1.0049 V with valleys down to −21.2 A (1.2 A outside the band). The slow board does not reach the lower limit at 10 % (Ton 5.4-7.1 ns, 8.25 MHz, 13.7 W) and keeps a 30 % minimum: its light-load loss is a shedding question | A207, A208, A210, A216, A221, A222 |
| plant | **V7 since A222 (2026-10-14):** V6 + a resistor r_core across each inductor, a damping resistor fitted at 8 MHz to D76's toroid data (2.90 Ω at L0, 2.17 Ω at 0.75 L0; with [10]'s embedded HBS1 data the same fit gives 2.62-2.85 Ω at L0, D83 Section 3). It damps an idle phase's ring, which V6 (no resistance in an idle phase) kept forever. Its books carry 15.5 W per module at full load on N0, 29.4 W on S75 at 125 °C; that is a damping resistor's loss, not the design's core loss and not an efficiency figure (the design's core loss at 2.5 MHz, 25 °C, with HBS1 units: 34.5-44.1 W per module at kappa 1, 106-136 W at [10] Table V kappa, D83 Section 0). V7 stays unchanged (D83 Section 3). On the two rows compared it moved the post-step peaks by −0.6 / −2.3 A | A221, A222 |
| reference cfgs | `experiments/track_A_periodic_steady_state/A172_p24_final_gate_plant/cosim/cfg_nom_L07_l_p48_1us.json` (one module), `cfg_m4_nom_l_p48_1us.json` (four) | A172 |

## 2. Plant versions

| | plant | experiments |
|---|---|---|
| V0 | ideal switches, no package | A124-A143, C05-C14 |
| V1 | loop + current-ramp edges | A144-A162 |
| V2 | gate model on the high sides; low sides ideal; no interlock | A163-A168 |
| V3 | every switch gate-driven; no interlock | A169 |
| V4 | every switch gate-driven; gate-form interlock | A170 |
| **V5** | **every switch gate-driven; threshold-form interlock (final up to A205)** | **A171 (S50 rows), A172, A173-A198, A205** |
| **V6** | **V5 + a turn-on at V_DS ≤ 0 and a turn-off at reverse current are gate edges (the channel conducts in reverse while the gate moves), an off gate follows its drain, the on-resistance sits in the switches (lumped R = 0); low sides with their own turn-on resistance** | **A206 (settled N0, start-up on three boards, twelve binding rows)** |
| **V7** | **V6 + a damping resistor r_core across each inductor (D76 fit; not the design's core loss, D83); final since A222** | **A221, A222 (skipping rows, two check rows, three start-ups)** |

A V2 result does not count as a V5 check. V2 and V5 differ in the low sides' turn-off delay (≤ 2.9 + 1.8 ns), and
that delay is what made the lead shoot through (A169).

A V6 result does not count as a V7 check either: V7 adds the core's loss and damps idle rings; on the rows compared (A221, A222) the post-step peaks moved by −0.6 / −2.3 A and mode S needed a trim of 1-3 steps. Every row of Section 3 not named under A221 / A222 is a V6 (or earlier) result.

A V5 result does not count as a V6 check either. V5 misses 12.6 of 27.4 W of semiconductor loss and ends a settled
period 3.5-6.8 A away from LTspice (A205); V6 is within 0.7 A and 0.7 % (A206, nominal devices, 25 °C). V6 has run
only the rows of Section 3a. Every other row of Section 3 is a V5 result with 3.0 Ω on the low sides.

## 3. Coverage of the final plant

Cell = physical post-step peak (A), A168's criteria (a168_analyze.judge) against the same row on V2. ✓ pass,
✗ miss (what). "—" = not run on V5. Every V5 run: 0 shoot-throughs, 0 overlaps, COMPLETED, V_DS ≤ 38.4 V.

| stimulus | nom | ff | hot | ss | L × 0.7 | L × 1.3 | four modules |
|---|---|---|---|---|---|---|---|
| +4.8 V / 1 µs | 182.5 ✓ (A171) | 181.8 ✓ (A171) | 179.3 ✓ (A171) | 178.7 ✓ (A171) | 199.7 (A172); 199.5-201.5 over 5 step phases (A174) ✗ at one; L × 0.75 / 0.8: ≤ 198.3 / ≤ 194.7 ✓ over 5 phases (A178) | 188.7 ✓ (A173) | nom 184.2 ✓ (A172); ss 181.4 ✗ 8 NEW spikes (A173); ±5 % L spread 196.5 ✓ (A173) |
| +4.8 V / 2, 3, 5, 10 µs | 182.9, 181.8, 182.3, 183.7 ✓ (A175) | — | — | — | — | — | — |
| +4.8 V / 4 µs | 182.5 ✓ (A173) | — | — | 180.2 ✗ Vo −13.5 mV, 17 µs | — | — | — |
| −4.8 V / 1 µs | 172.4 ✗ 3 restarts + 6 NEW spikes (A175) | — | — | — | — | — | — |
| −8 V / 10 µs | 166.7 ✓ (A173) | 181.5-183.0 over 5 step phases ✗ Vo +0.1-1.3 mV over, a spike at 2 of 5 (A173 / A174) | — | 169.4 ✗ Vo +0.9 mV | — | — | — |
| +62.5 A load step | 181.4 ✓ (A173) | 181.2 ✓ | 181.4 ✓ | 184.3 ✓ | 182.2 ✓ | 179.8 ✓ (A175) | nom 181.6 ✓ (A173) |

At nominal devices the final plant has run all 13 rows of A152's matrix: 12 pass, −4.8 V / 1 µs misses on oracle
events only.

Start-up / handover peaks (open loop, per-board trim): nom 162.1 / 149.7, ff 161.6 / 146.4, hot 161.8 / 150.3,
ss 188.8 / 188.8, L × 0.7 200.2 / 190.2 (limit ref + 3 = 205.5), L × 1.3 146.5 / 137.2, four modules nom 162.1 /
149.7, ss 193.0 / 193.0, ±5 % 169.1 / 161.9 A (400 ns start-up).

With the A188 start-up: at 25 °C (A185, seven boards and four nominal modules) start-up 116.5-139.9 A and handover
148.8-173.2 A. At 125 °C (A188; S75, S0, N0, F0) start-up ≤ 139.0 A and handover ≤ 184.4 A. Vo ≤ 1.048 V throughout;
S80 at 125 °C (A197): handover 182.0 A and Vo 1.0486 V, 1.4 mV under the 1.05 V limit
(400 ns: 57-71 mV overshoot on hot slow boards). Handover minima 0.989-1.000 V; the 400 ns design ranged from 0.961 V
(S75) to 0.999 V, and the L0 nominal / ff / four-module boards lose 5-9 mV against it (the 200 → ~520 ns period jump,
A185). Slow devices with L × 0.75 at 25 °C: start-up 135.7 A, handover 161.8 A, post-step ≤ 192.7 A at three
positions (A184 / A185; 400 ns: 202.1 / 278.4 A).

Interlock delay (A173 / A174), against the 0.5 ns runs:
- fixed 1.0 V reference = t_il 8.3 ns at ss: peaks within ±0.7 A and V_DS no higher on every row. Late fires
  +26 % (+4.8 V / 1 µs), +44 % (load step), +57 % (4 µs ramp), +90 % (−8 V ramp); the load step gets 4 more NEW
  spikes. It misses A174's tolerance on 3 of 4 single rows. Four modules at ss: late fires ×2.0 (1608), NEW
  spikes 82 against 8, Vo −13.7 against −9.9 mV;
- per-board reference = 1.4 ns at ss (A173 / A177): passes +4.8 V / 1 µs and the 4 µs ramp. Small misses elsewhere:
  late fires +60 % on the −8 V ramp, NEW +3 on the load step, NEW +5 on four modules. It keeps four modules at 792
  late fires (0.5 ns: 803; fixed: 1608). Late fires grow monotonically with the delay; NEW and Vo scatter between
  neighbouring runs;
- A179, three step positions per row and delay (step at 500 µs, exact against the old runs before the step): after
  the −8 V ramp the late fires are 12-21 at 0.5 ns, 9-21 at 0.8, 12-32 at 1.0 and 12-51 at 1.4 ns (51 and A177's 47
  at 2 of 4 positions; limit 36.5) → release ≤ 1.0 ns. The load step has no late fires after the step at any delay;
  its one-period 10-18 A spikes number 16-19 at 0.5 ns and 7-27 at 1.0 / 1.4 ns without a trend (open, peaks
  unchanged). Four modules pass at 1.4 ns: A177's NEW 13 vs 8 is position scatter (0.5 ns alone gives 5-22). The
  late fires that rise with the delay before the step (72 / 79 / 77 / 83 at 0.5 / 0.8 / 1.0 / 1.4 ns) fall in the
  start-up settling at 160-300 µs;
- ff at 1.0 ns (its fixed-reference value) and L × 0.7 at 2.0 ns: same as 0.5 ns.

Step position (A174, 4 more phases per row): L × 0.7 +4.8 V / 1 µs 199.7, 199.9, 199.8, 199.5, 201.5 A. At the
201.5 A phase Vo stays outside 1 % for 37.9 µs. ff −8 V / 10 µs: 181.5-183.0 A, Vo 30.6-31.8 mV at every phase,
the spike at 2 of 5.

Random stimuli on V5 (A194, 2026-10-12, one module, final configuration): 36 draws over boards N0 / N75 / N13 / F0 /
S0 / S75 / S80, −40 / 0 / 25 / 125 °C, rising line steps of 1-4.8 V over 1-40 µs, falling 1-8 V, load steps of
±20-62.5 A; 14 of them 37-145 µs after the handover, 22 at 500 µs. All 36 pass: COMPLETED, 0 shoot-throughs, peak
≤ 184.6 A, V_DS ≤ 33.9 V, Vo within 13.1 mV of 1 V, back inside 1 % within 10.3 µs. The handover reaches 184.5 A
(S75) and 182.0 A (S80) at 125 °C and at most 166.4 A elsewhere. The draws did not reach the first 37 µs after the
handover (the lead ramp) or a rising step ≥ 4 V on S75 / S80; the worst known case stays the designed row (197.8 A,
A193). 36 of 36 bounds the miss rate under this distribution at about 8 % (95 %).

The worst row right after the handover (A198, 2026-10-12, one module, final configuration): +4.8 V / 1 µs placed 2 /
10 / 20 / 40 / 80 µs after mode P's entry. N0 at 25 °C: 193.7 / 183.5 / 179.0 / 179.9 / 178.5 A, all pass. S75 at
25 °C: 195.5 / 197.6 / **206.1** / 195.3 / 192.4 A. S75 at 125 °C: **202.8 / 214.4 / 217.3** / 186.7 / 187.2 A.
V_DS ≤ 33.6 V, 0 shoot-throughs, Vo within 18.1 mV everywhere. **The row needs a hold-off of 40 µs after the
handover** (first tested instant from which all three boards pass; the boundary lies between 20 and 40 µs).

Only on earlier plants: the corners ff / hot / ss on the registered ramps and −4.8 V rows (V2, A164 for some; A194's
draws touch them at random amplitudes and slews); random stimuli on four modules (V0, C13); the inductor spread
beyond ±5 % (V0, C14).

The misses are regulation or oracle events, none on voltage. Current misses:
- L × 0.7 at one step phase (201.5 A, A174);
- slow devices at 125 °C after +4.8 V / 1 µs with L × 0.75 or 0.8 exceeded 200 A with the 8 ns lead: 204.5 /
  207.2 A and 217.1 / 201.5 A at 2 of 6 step positions each (A187; valley-timing limit, phases 3-4 lose their valley
  for ~25 µs). Fixed by the 9.5 ns lead on slow boards: 194.6-196.3 / 190.8-194.8 A at all six with the final configuration
  (A197). A191, where the lead was chosen, ran A186's 1.03 V handover request: 194.1-196.9 / 190.6-192.8 A. The lead's
  cost on the other slow rows is the 25 °C margin: S75 +4.8 V / 1 µs 195.8-197.1 A (A192, three positions). Cold,
  the same row gives 191.1-195.0 A at −40 °C and 194.5-197.8 A at 0 °C (A193). The worst tested S75 point over
  −40..125 °C is 197.8 A, a 2.2 A margin.
- A181's slow L × 0.75 start-up miss (202-207 A open loop, a 278 A handover) is fixed by the A188 start-up.
- +4.8 V / 1 µs within the first 40 µs after the handover on slow boards with L × 0.75: up to 217.3 A at 125 °C and
  206.1 A at 25 °C (A198). Not fixed: stated as a hold-off (Section 5). **On V7 (A225, with A224's candidate gate +
  kd): 211.2 / 210.3 / 207.8 A at 2 / 10 / 20 µs after the entry on S75 at 125 °C; S75 at 25 °C 199.6 / 197.0 /
  190.3 A and N0 at 2 µs 182.8 A pass (records `A225_p24_startup_items_recheck/cosim/run_a_*.json`). The hold-off
  stays for slow boards; controller item 2 stays open.**
The rest:
- falling steps (nom −4.8 V / 1 µs, ff −8 V / 10 µs): A148's valley loss on phases 2-4 turns into K3 restarts and
  10-20 A spikes, which V2 does not show (A176 supports the lead plus the gate-driven low sides as the cause; one
  step position per variant, so "none" on a variant is one sample);
- slow corner: Vo dips 3-5 mV deeper than V2 after line ramps (the low sides' turn-off delay plus holds);
- four modules ss: 10-16 A spikes, four of them A160's K4-window artefact.

## 3a. Plant V6 (A206, 2026-10-13)

One module, final configuration, low sides at 0.3 Ω (× 1.2 on slow boards), switches at the datasheet maximum times
the vendor model's temperature factor, new start-up trims. Stimulus: +4.8 V / 1 µs at 500 µs + k T / 6. Cell = largest
post-step peak (A); V5 = the same row's record, read to the same time.

| board | step positions k | V6 | V5 | margin on V6 |
|---|---|---|---|---|
| nominal L0, 25 °C | 0 | 179.0 | 182.8 | 21.0 A |
| nominal 0.75 L0, 25 °C | 0, 2, 4 | 189.0-196.2 | 198.5 (k 0 only) | 3.8 A |
| slow 0.75 L0, 25 °C | 0, 2, 4 | 194.9-195.8 | 195.9-197.1 | 4.2 A |
| slow 0.75 L0, 0 °C | 0, 2, 4 | 195.0-195.4 | 194.5-197.8 | 4.6 A |
| slow 0.75 L0, 125 °C | 1, 5 | 196.1-197.6 | 195.4-196.3 | 2.4 A |

Every V6 run (29, start-up included): 0 shoot-throughs, 0 forced edges, V_DS ≤ 33.7 V, Vo ≤ 1.0476 V in start-up and
within 13.6 mV of 1 V from 20 µs after the handover. One miss: 3.0 Ω on the low sides with switches at the datasheet
maximum, handover 206.4 A (not the chosen value). Settled N0, semiconductor loss per module in the plant's books:
20.15 W (high-side edges 2.44, low-side edges 1.41, dead-time reverse conduction 0.66, conduction 15.65), which is
92.5 % as P_out / (P_out + loss) at 250 W; V5 booked 15.75 W (94.1 %). With typical switches 17.32 W, LTspice 17.36 W.
**Nominal L0 board, the other rows (A212, 2026-10-14; V6, low sides 0.3 Ω, ton_min_ns 4.0 ns, one step position):**
+4.8 V over 2 / 3 / 4 / 5 / 10 µs 184.1 / 184.0 / 182.9 / 183.4 / 183.8 A (V5 182.9 / 181.8 / 182.5 / 182.3 / 183.7);
−4.8 V / 1 µs 171.7 A with 3 K3 restarts and 3 NEW oracle events (V5 172.4 A, 3 restarts and 6 NEW spikes);
−8 V / 10 µs 169.5 A (V5 166.7; the Ton register dips to 20.4 ns, below the old limit); +62.5 A 181.5 A (V5 181.4);
the −62.5 A release 146.6 A (A207). All pass: V_DS ≤ 33.3 V, Vo within 26.5 mV, no late fire after a stimulus.

Not on V6: the device corners' own rows, L × 0.7 / 0.8 / 1.3, fast devices, −40 °C, steps near the handover, four
modules. Those columns of Section 3 remain V5 results with 3.0 Ω on the low sides.

## 4. Not covered by the final plant

- **Light load (A207, 2026-10-14).** No run before A207 had less than 75 % of the load on a module. With part of the
  250 A released (plant V6, nominal L0 board, 25 °C, one module) the 75 % row regulates (Ton register 24.09 ns,
  2.42 MHz, 12.4 W of semiconductor loss); at 60 / 55 / 50 / 45 / 40 / 30 / 10 % the register sits at its 22.25 ns
  limit from 1.4-2.8 µs after the release and Vo ends at 1.09 / 1.14 / 1.19 / 1.23 / 1.28 / 1.37 / 1.56 V (figure
  `A207_p24_load_range/a207_vo.png`, records run_f60 .. run_f10 in release records-a207). The limit is reached at
  about 174 A. How high Vo goes depends on the load model (4 mΩ plus a current fed back); that it leaves regulation
  does not. Four modules all on therefore cover 697-1000 A only. Shedding whole modules, as LSCB (Tong et al., VLSI
  2026) sheds phases, would cover 174-1000 A with gaps at 250-349 A and 500-523 A (a composition, not a run; the
  frozen controller cannot shed a module). Not fixed. Other boards, temperatures, slow load changes and a start-up
  into a light load are not run.
- **Light load after A208 / A210 (2026-10-14).** With ton_min_ns = 4.0 ns the nominal L0 board works at 60, 50, 40, 30
  and 20 % (register 18.8 / 15.3 / 11.7 / 8.3 / 4.5 ns; 2.8-5.2 MHz; 8.7 / 6.7 / 5.3 / 4.2 / 3.4 W) and delivers 46.6 A
  at the limit; nominal 0.75 L0 works at 40 and 30 % and delivers 65 A at the limit; slow 0.75 L0 works at 30 % at 0,
  25 and 125 °C. **Not covered: anything below 30 %; the slow board's 20 % row, where no high-side turn-on completes
  (a regime the plant has not been compared with LTspice in); the release itself when it is 200 A or more in zero
  time (52.6 mV overshoot, then down to 0.9635 V with the 4.0 ns limit); slow load changes; a start-up into a light
  load; fast devices; four modules.** The gate-drive loss, which grows with the frequency, is not in the books.
- **The RTL as a circuit (A209, 2026-10-14; synthesis estimate, yosys + ABC, no layout).** As written the RTL does
  not pass a synthesis front end: one port expression in scb_ctrl.v (A148) mixes a signed wire with an unsigned
  constant; with that constant written signed every module synthesizes with 0 problems. One module's controller is
  125 821 generic cells (A100: 43 924), 55 % of it scb_vff. Longest path against the 4 ns clock: 47.0 ns in sky130 (a
  130 nm open library standing in for a 130-180 nm BCD node) and 10.5 ns at 45 nm, from the loop's accumulator through
  scb_vff into phase 1's edge logic; that path's source changes once per period and would take a register stage. The
  per-clock logic of one phase alone is 10 ns in sky130 and 2.4 ns at 45 nm. Estimates good to a factor (plain
  mapping, no wires). The 31.25 ps edge placement, comparators, TDCs and ADC remain model assumptions.
- **Loss against load, and what shedding modules would save (A211, 2026-10-14; plant V6, 25 °C, one module,
  ton_min_ns 4.0 ns; figure `A211_p24_loss_against_load/a211_curves.png`).** Semiconductor loss per module in the
  plant's books at 100 / 75 / 60 / 50 / 40 / 30 % of the load: nominal L0 20.2 / 12.4 / 8.7 / 6.7 / 5.3 / 4.2 W
  (92.5-95.0 %); nominal 0.75 L0 22.3 / 14.2 / 10.5 / 8.3 / 6.9 / 6.5 W (91.8-93.8 %); slow 0.75 L0 31.9 / 24.4 /
  20.9 / 20.7 / 19.9 / 17.6 W (88.7 % at full load, 81.0 % at 30 %). The slow board's edges cost 13.5 W at full
  load (D80's thermal note carried 3.9 W from V5 and is not rerun), and its frequency rises from 2.6 to 5.6 MHz
  as the load falls. At 50 and 40 % the slow board regulates but its valleys alternate between −17 and −7 A (the
  two-cycle orbit, wider than at full load). Composed for four equal modules: running two instead of four would
  save 19 / 31 / 41 % of the loss at 50 / 40 / 30 % of the system's load on slow boards, 7-21 % on nominal ones,
  and would reach down to 7.5 %. **Not covered: shedding itself. No module leaves or re-enters in any run; the
  frozen controller cannot do it.** 0 and 125 °C on these rows, the gate drive's loss and the inductors' are not in.
- **Start-up into less than the full load (A214, 2026-10-14; plant V6, the load resistance set from t = 0).** Every
  earlier start ran into the full load. Nominal L0 with 75 and 50 % of the load, and slow 0.75 L0 with 50 % at 25 and
  125 °C, start cleanly: Vo ≤ 1.0492 V, peaks ≤ 161.5 A, V_DS ≤ 30.6 V. The handover is requested by Vo (1.045 V)
  at 109-137 µs instead of 144 µs, while Vin is still at 38-48 V, and mode P takes over. **Nominal L0 with 30 %
  reaches 1.0528 V, 2.8 mV over the limit (record `A214_p24_startup_light_load/cosim/run_u_N0_25_30.json` in
  release records-a214). Tested start-up range: 50-100 % of the load.** Slow boards at 30 %, 0 °C, a load that
  switches on during the start, and four modules are not run. **On V7 (A225, run with A224's candidate gate + kd):**
  nominal L0 into 30 % reaches 1.0510 V, 1.0 mV over, 0.7 µs after mode P's entry, where gate and kd already act
  (the final configuration without them was not run on this row); slow 0.75 L0 into 30 % at 25 / 125 °C passes
  (1.0483 / 1.0491 V, peaks ≤ 115.0 A). Records `A225_p24_startup_items_recheck/cosim/run_u_*_30.json`, release
  records-a225. Controller item 6 (the loop's seed is set for the full load) stays open.
- **The Ton path's registers (A215, 2026-10-14; plant V6, ton_lat 16).** A212's four N0 rows, A206's three binding
  rows and the 30 % rows of A208 / A210 pass their own criteria: post-step peaks -6.3 .. +1.1 A against the
  ton_lat 0 records (binding row 196.95 A, S75 25 C k 4), Vo before 300 µs unchanged, N0's handover 148.9 A instead
  of 162.0 A. In synthesis (A209's flow and estimate, not sign-off) no path from the Ton arithmetic reaches a phase
  register within a clock; at 45 nm the phase logic fits the 4 ns clock (3.08 ns), and the one path still over it is
  ton_acc -> scb_vff's divider numerator (5.14 ns), a multi-cycle path in operation (read from the RTL). At sky130
  the phase logic needs about 16 ns; a 16 ns clock with a 9-bit fine delay regulated on one row (+62.5 A, 181.45 A).
- **Light load by skipping rounds (A216-A222, 2026-10-14; one module, 25 °C).** Below its lower Ton limit a module
  pauses and resumes. On V6 it regulated down to no load (Vo within 1 V + 2-4 mV on average, +62.5 A out of a pause
  at 58.7 A) but the valleys after each resume left the band by up to 20 A: V6 has no resistance in an idle phase,
  so the pause's ring never decayed and set each phase's first valley (A217, A220), and A220's zero-current pause
  measured a short period for the slots (fixed in A221). On V7 (core loss, which damps the ring) N0 and N75 at 10 %
  keep every valley in −20..−12 A, every phase resumes within 0.3 A of zero, also with half the damping; N0 with no
  load reaches −21.2 A (records `A221_p24_core_loss_and_pause/cosim/run_z_N0_25_0.json`, release records-a221).
  **That figure had the V6 trim. With A222's V7 trim the final configuration reaches −22.8 A at no load, 2.8 A
  below the band (A226, record `A226_p24_noload_valley_reference/cosim/run_z_N0_0_d0.json`, release records-a226),
  and N0 at 10 % keeps −16.2..−13.6 A (A227, `run_z_N0_10_d0.json`, release records-a227).**
  N0's ladder, unbalanced by a large release (3.7 V between rails 4 and 1, also without skipping), settles with
  about 125 µs. Not covered: four modules (the slaves do not follow a pause), the slow board (it does not skip),
  temperatures other than 25 °C, line steps while paused, the copper's resistance (D72).
- **Large load re-applications (controller item 9; closed 2026-10-16 by A223-A229, plant V7, one module).** Found in
  A216 (V6): +200 A from 20 % reached 249.8 A and +237.5 A from 5 % 235.4 A (records
  `A216_p24_skipped_rounds/cosim/run_w_N0_25_20_up_ns.json`, `run_w_N0_25_5_up.json`). Two mechanisms: phase 1's Ton
  held by scb_vff's relative cap (rail 1 to 16.3 V; A223 gates the cap to rising Vin), and a ring of about 2.9 µs that
  the loop's P term and Co form around the current that integrates Ton's excess while phase 1's low-side learner moves
  at most 2 ns per period (figure `A223_p24_cap_on_rising_vin/a223_w20.png`; A224's derivative term damps it). The
  derivative term first moved the 10 % skipping rows' upper valley end by 1.4-2.8 A (A228, four release instants each;
  the final configuration agrees within 0.6 A), so it is held within 4 ns above the lower Ton limit (A229). With the
  adopted controller: N0 from 0 / 5 / 20 % to full load 153.9 / 159.8 / 149.3 A, N75 from 5 % 159.6 A (without: 223.6
  / 248.3 / 214.0 / 232.1 A, A223), S75 at 125 °C +175 A from 30 % 153.7 A after the step; the 10 % skipping rows keep
  every valley in −20..−12 A (8 of 8 runs), no load −21.3..−21.7 A as before (records
  `A229_p24_kd_band/cosim/run_*_b.json`, release records-a229). Margin of the derivative gain: S75 at 125 °C hands over
  at 178.9 / 187.0 / 276.6 A with kd 355 / 440 / 530 (A224). Not run with the damped loop: four modules, the device
  corners, L × 0.7 / 1.3, other temperatures for the re-applications.
- **The plant against a second simulator (A205, 2026-10-13).** LTspice with EPC's model on all 20 switches, started
  from the plant's state and given the plant's gate commands for two periods (23 replays, nominal devices, 25 °C,
  one module: mode S, settled, and +4.8 V / 1 µs on N0 and N75). It reproduces the plant's largest peaks within
  0.17 A (182.7 / 182.8 A, 198.35 / 198.52 A), hard switching within 0.024 ns and 0.14 V, and every switch's largest
  V_DS within 1.5 V (≤ 32.3 V). It does **not** reproduce a settled period: the currents end 3.5-6.8 A lower and
  **12.6 W of semiconductor loss per module are missing from the plant** (27.4 W against 14.8 W). The plant makes a
  low side conduct the instant it is commanded on at zero voltage; through the specified 3.0 Ω its gate needs about
  10 ns, and until then the device conducts in reverse at up to 2.8 V (about 10 W, 3.3 A per turn-on). With 0.3 Ω
  on the low sides in LTspice the gap is 4.0 W. At fixed commands phase 1's next peak is 1.1-2.7 A higher in LTspice
  (N75: 200.5-201.3 A against 197.8-198.5 A). Every efficiency figure and every margin below about 3 A in this file
  predates this and is stated for the plant as it was. Slow / fast devices, other temperatures, four modules and a
  closed loop on the LTspice circuit are not done.
- **Plant V6 against LTspice (A206, 2026-10-13).** The two effects are in the plant (cfg-gated; off = V5 bit for
  bit). Same method, 26 replays, nominal devices, 25 °C, one module: one period later the currents are within 0.68 A
  settled, 0.41 A in mode S and 1.05 A after N0's step, and the settled loss books within 0.7 % at 3.0, 1.0 and
  0.3 Ω. **Stated error: 0.75 L0 at the step's peak**, where LTspice ends 1.52-1.57 A lower and single peaks are up to
  2.3 A lower (the plant is the higher one). Cause: a high side commanded on whose node swings past the rail before
  its gate reaches threshold conducts at 2.2 V in the plant and at 0.43 V in LTspice. Not fixed. Four modules and a
  closed loop in LTspice are not done.
- **The binding row against LTspice (A213, 2026-10-14).** The slow 0.75 L0 board at 125 °C, +4.8 V / 1 µs, the row
  with the smallest margin on V6 (197.57 A). LTspice with the vendor model at 125 °C, its threshold + 1.0 and its
  gate capacitances × 1.29, replayed from the three snapshots before and at the peak, gives 196.79 / 196.98 /
  197.38 A: 0.2-0.8 A below the plant. The settled loss books agree within 0.5 % (39.9 W per module at this
  corner), V_DS within 1.2 V. V6's one-period error is larger here than at nominal, on the conservative side:
  currents 1.3-2.0 A lower in LTspice settled and at the step, up to 3.0 A around the peak (not traced). **Not
  covered: other step positions and boards at this corner, 0 °C, and any slow device that is not the typical
  model with these three changes.**
- **The interlock is an idealised function.** It senses the complement's channel exactly and holds the gate at its
  own channel start. Where it acted (L × 0.7, slow corner), zero shoot-throughs are imposed by the rule, not
  shown. Where it never acted (0 holds: nom / ff / hot one module, four modules nominal), they do not depend on it.
  A173 / A174 set t_il to realisable forms (above). A comparator reference above a device's channel-off level
  would release early; the spec excludes it, and it is not modelled.
- **Each limit was found with the others at nominal, except the combinations of A181 and A183-A188** (slow devices,
  L × 0.75 / 0.8, t_il 1.0 ns, trims locked at 25 °C, 25 / 125 °C). With the A188 start-up and the 8 ns lead they pass at 25 °C and fail
  the 200 A budget after the step at 125 °C (A187); with the slow boards' 9.5 ns lead they pass at both (A192 at 25 °C; A197 at 125 °C; A191 at 125 °C ran the 1.03 V handover request of A186), and S75 passes +4.8 V / 1 µs at −40 and 0 °C (A193). Other combinations (ff with a
  small L, slow devices between 0.75 and 1.0 L0, four modules) are not run. Step positions are offsets in absolute
  time; A181 reads their phase after phase 1's low-side turn-off instead of imposing it.
- Devices inside a board are identical (mismatch only in LTspice single edges, D79 4.7). Four-module boards
  share one corner.
- The damper is an ideal Q 7 resistor; the driver is an ideal source behind a resistor.
- 50 pH is the bound **for this drive and this controller** (A168). It is not a package limit in general.
- **Slow-device boards run on a two-cycle orbit in steady state (A195, found 2026-10-11 in 22 existing records).**
  The valley and the peak alternate from one cycle to the next: valley by 3.7-7.2 A, peak by 4.0-7.9 A, on V2 and V5,
  with the 8 and the 9.5 ns lead, on S0 / S75 / S80, at −40 / 0 / 25 / 125 °C. Nominal and fast boards: ≤ 0.9 A.
  Every slow-corner peak and margin above includes it; no earlier report named it. Cause: the high-side turn-on
  corrector hunts when the gate delay is 8-11 ns (nominal 2.8 ns). Corrector registers dt_step 0.0625 ns with
  err_shift 2 cut it to 0.3-0.85 A on S0 and 0.84-1.40 A on S75 and lower S75's worst post-step peak to 194.4 /
  194.7 A at 0 / 25 °C (reference 197.8 / 197.1 A), but raise its handover to 177.5-177.7 A (reference 150.7-154.0 A),
  and the 125 °C handover is already 184.5 A (A194). **Not adopted (A196, fails as registered).** The handover and the steady
  state want different corrector settings; a setting that changes after the handover is not run.
  **On V7 the orbit is gone (A225, 2026-10-15; S75 at 25 °C, run with A224's candidate gate + kd):** mean |valley
  change| per period 0.04 A at 100 % and 0.04-0.25 A at 50 % (V6, A211: 4.2-5.1 and 5.1-7.7 A), and with half the
  core's damping 0.27-0.38 / 0.05-0.10 A (records `A225_p24_startup_items_recheck/cosim/run_s_S75_*.json`, release
  records-a225). The orbit belonged to plants V2-V6, which had no damping in an idle inductor; controller item 5 is
  closed on V7. The slow-corner margins above that were measured on V2-V6 include it. Seen on the way and not
  traced: at 50 % phases 3 and 4 settle at −33.9 / −33.1 A against −15.6 A on phases 1-2.

## 5. How to state the results

- "The final plant passed the listed rows (Section 3)", not "every corner" or "every test".
- Inductance tolerance (A174 / A178, +4.8 V / 1 µs, five step phases per board): 0.75 L0 ≤ 198.3 A, 0.8 L0 ≤
  194.7 A, 0.7 L0 199.5-201.5 A (nominal devices, t_il 0.5 ns, each board trimmed). State "at 0.75 and 0.8 L0
  every tested phase stays ≤ 200 A with nominal devices; 0.7 L0 reaches 201.5 A" - not "every L ≥ 0.75 L0": the
  peak is not monotone in L (L0 182.5 A, 1.3 L0 188.7 A). Slow devices, with the A188 start-up: 0.75 L0 holds at
  25 °C (three step positions, ≤ 192.7 A). At 125 °C, with the 8 ns lead, neither 0.75 nor 0.8 L0
  holds after +4.8 V / 1 µs (2 of 6 positions each, up to 207.2 / 217.1 A, A187). With the slow boards' 9.5 ns lead
  both hold at all six positions (≤ 196.3 / 194.8 A with the adopted 1.045 V handover request, A197; ≤ 196.9 / 192.8 A
  in A191, which ran the 1.03 V request). At 25 °C, 0.75 L0 then reaches 197.1 A (A192, three
  positions); slow L0 with 9.5 ns gives 181.4 / 182.7 A at 25 / 125 °C (one position each). Below 25 °C, 0.75 L0 holds at
  −40 °C (≤ 195.0 A) and 0 °C (≤ 197.8 A) on the same row (A193; device model extrapolated). Tested points only: the
  smallest margin is 2.2 A at three positions per temperature. 0.8 L0 at and below 25 °C, 0.85-0.95 L0, and other
  rows or boards cold are not run.
  The 0.7 board's open-loop start-up is 200.2 A (registered limit ref + 3 A = 205.5 A).
- Line steps after start-up: "+4.8 V / 1 µs is covered from 40 µs after the handover on the tested boards (S75 at 25
  and 125 °C, N0 at 25 °C); within the first 40 µs slow boards reach up to 217.3 A" - not "from start-up on". The
  hold-off is counted from mode P's entry (131.4 µs on hot slow boards, 144.0 µs otherwise). It is a condition on
  the input bus: no step of this size until 40 µs after the handover, about 185 µs after enable. No run has a line
  step during the open-loop start-up either. Load steps in the same window are not run; a power-good signal
  released 40 µs after the handover would exclude them (the load, not the bus, is what power-good gates).
- Slow-corner currents: "slow-device boards alternate by 4-7 A from one cycle to the next in steady state; the
  stated peaks include it" - not "the slow corner's steady peak is 150 A" without it. The steady valley of a slow
  board is a pair (S75, 25 °C, 9.5 ns: −12.9 / −17.3 A), not one number; A192's "deeper valleys with the 9.5 ns
  lead" is that pair's mean moving.
- The interlock: "closes in the model with an idealised threshold interlock. Its release time is a timing spec: any
  delay up to 8.3 ns keeps peaks and voltages; at the slow corner it should release within 1.0 ns, which a
  per-board comparator reference (~1.4 ns) just misses and a fixed reference misses by far (A174, A177, A179)".
- Two layers. Engineering: peak current, V_DS, Vo extreme and recovery, loss. Diagnostic: late fires, oracle NEW
  events, restarts. The interlock's 1.0 ns is a diagnostic target: in A179 peaks (169-171 / 183-185 A), V_DS
  (≤ 32.9 V) and Vo extremes (within ~2 mV) do not separate 0.5-1.4 ns; up to 8.3 ns peaks and V_DS held and
  four-module Vo was −13.7 against −9.9 mV (A174).
- After A205: "the plant's peaks, hard-switching edges and V_DS maxima agree with LTspice (vendor model, nominal
  devices, 25 °C) within 0.2 A, 0.03 ns and 1.5 V on the replayed windows" may be said. "The efficiency is 90 %" may
  not: the plant omits the low sides' reverse conduction at turn-on, about −4 points with 3.0 Ω on the low sides and
  about −1.3 points with 0.3 Ω (open-loop estimate from one period). "The slow corner holds 200 A with a 2.2 A
  margin" may not be said without "in the plant; LTspice's next peak is up to 2.7 A higher at fixed commands".
- After A206: "on plant V6, which agrees with LTspice within 0.7 A per period and 0.7 % of loss at nominal devices
  and 25 °C, the twelve binding rows stay ≤ 197.6 A with 0.3 Ω on the low sides" may be said. The smallest margin
  is then "2.4 A on the slow board at 125 °C; LTspice, replayed from the plant's state at that corner, is 0.2-0.8 A
  lower (A213; two periods at fixed commands, one step position)". Semiconductor efficiency: "92.5 %
  in the plant's books at nominal devices, 25 °C, switches at the datasheet maximum (20.2 W per 250 W module)"; it
  leaves out the inductors, the loop's damper, the capacitors and the gate drive. A V5 efficiency figure may not be
  quoted without its version.
- Converter efficiency with the inductor array (D83, 2026-10-15, corrects D72 / D76): at 2.5 MHz, 25 °C, 250 W per module, no package, with real IND048-HBS1 units,
  84.0 % without core loss, 73.2-75.3 % with core loss at kappa 1, 57.7-62.0 % at [10] Table V kappa. The earlier 86.6-87.7 % (D72), 84.4-85.4 % and 78.4-79.3 % (D76)
  and 90.6 % (A124 / D62) rested on inductor units that [10] does not have as HBS1 and on a core loss one third too low; they may not be quoted.
- The drive specification "3.0 Ω ± 20 % on / ≤ 0.3 Ω off per device" was derived for hard high-side turn-ons. For
  the low sides, which turn on at zero voltage, it is not a specification but an oversight: they need their own,
  small turn-on resistance (A205). A206 set it to 0.3 Ω: the low sides' hard turn-ons are at most 77 per run, all
  but one or two in start-up and handover, with low-side V_DS ≤ 19.6 V. Fast devices (0.24 Ω) are not run.
- After A207 / A208 / A210: every statement about a module holds "between 30 and 100 % of its load, with the lower Ton
  limit at 4.0 ns" (tested on N0, N75 and S75; rows run before A208 used the old limit and stayed at 75 % or more).
  "Regulates down to 20 %" may be said for the nominal L0 board only. "Efficient at light load" may be said for
  nominal devices (92.0-95.0 % at 30 %), not for slow ones (about 80 % at 30 %). Below 30 % the output is not
  regulated on every board.
- After A209: "the controller is RTL that simulates" may be said; "synthesizable" may not without the one-token fix,
  and "meets its 4 ns clock" may not: the estimate is 2.6 times too slow at 45 nm and 12 times in a 130 nm library
  as written, and the per-clock phase logic alone fits only at 45 nm.
- Efficiency: η = P_out / (P_out + P_loss). A loss increase divided by 250 W is a share of the output, not
  efficiency points: the gate-level edges add 1.7 / 3.9 W per module (nominal / slow corner), −0.4..−0.5 /
  −1.0..−1.2 points depending on the baseline (D80, corrected 2026-10-09).
- Acceptance: "ACCEPTED" means every registered criterion passes or is a documented exception; it includes
  experiments that FAIL as registered (A163, A179, ...). It is not a count of successful designs.
- Edge power: per module 2.26 / 2.45 / 2.86 / 4.57 W at ff / nom / hot / ss (A171), 4.18 W at L × 0.7 (A172),
  2.44-2.46 W on four modules (steady window; A172's 2.87 W included the step). D62's ideal-edge terms were
  0.94 W. The thermal result with these losses: D80.

## 6. Second external review (2026-10-09): experiment design

| # | point | verdict | action |
|---|---|---|---|
| 1 | each corner re-trimmed (125 °C too): shows "works after re-calibration", not "a board trimmed once still starts hot" | correct; estimated impact small (nominal board: hot trim 0.33 ns shorter → Vo(143.5 µs) +8.5 mV, away from the cliff); slow corner + hot never run | row "start-up" and "calibrated vs adaptive" in Section 1; A181: the locked 25 °C trim holds at 125 °C on L0 boards |
| 2 | relative criteria (late ≤ 1.5 ref + 5, NEW ≤ ref + 2, Vo ± 2 mV) are regression checks, not hardware requirements | correct in principle; the 1.0 ns was already called a timing (not safety) spec, but it reads like a requirement | Section 5 "Two layers": 1.0 ns is a diagnostic target; engineering metrics do not separate 0.5-1.4 ns |
| 3 | A176 ran one step position per variant; "none" may be phase luck | correct; A176's own limits said so, its verdict and later docs said "only together" | reworded to "supports" (Section 3, D79, summary, status) |
| 4 | separately found limits do not combine; discrete points are not a range | correct; our data show the peak is not monotone in L (L0 182.5, 1.3 L0 188.7 A) | Section 5 states tested points; A181 ran one combination (slow + L × 0.75 + locked trim + hot): it fails the 200 A budget, so the inductance tolerance is per device corner |
| 5 | an ideal interlock cannot release early, so its safety is preset by the model | correct; already stated in Section 4 ("imposed by the rule, not shown"; early release "not modelled") | none; a comparator model with offset / noise / mismatch would be new work |
| 6 | A180's step-2 rule tied the windowed clamp to the always-on clamp's loss | partly: A180 RESULTS already reads the rule as not authorising step 2; criterion 5 stood in for the windowed clamp's ideal trigger | A180 unchanged (FAIL stays). Run as A182: a 0.75 V detector with <= 0.3 us delay keeps the ideal trigger's benefit at twice the clamp current (289 vs 146 A); 1.0 us or 1.5 V loses it (0/4 as registered; extension lscb_ladder closed) |

Run as A181 (2026-10-09 evening): the locked 25 °C trim holds hot at L0; slow devices with L × 0.75 exceed 200 A
at start-up (202-207 A), at the 25 °C handover (278 A) and once after the step at 125 °C (202.8 A). Then A183-A188
(10-09 / 10, after the user's "solve what is found"):
- the start-up miss came from mode S's ladder split, fixed by the start-up above;
- the 125 °C post-step miss is mode P's valley-timing limit at this corner (A187), closed by the slow boards' 9.5 ns
  lead (A191-A193: 125, 25, 0 and −40 °C). The RTL limit itself (no predictive turn-on before t_lo + ~1 clock) stays.

## 7. Third external review (2026-10-09): the mathematical model

Details, numbers and the scripts: `symbolic_derivations/03_P24_native/D81_P24_MATH_MODEL_ACCEPTANCE.md`.

| # | point | verdict | action |
|---|---|---|---|
| 1 | stability eigenvalues taken from a reused (possibly stale) Jacobian | correct (D45-D51 used Newton's chord matrix); recomputed at all 36 orbits: largest modulus moves ≤ 8.1e-4, all < 1 (worst 0.9959). Step size matters more: 1e-6-1e-7 adds up to 4e-3 of integrator noise | `section_jacobian` (central, 1e-4, event-order flag) in the solver and gate; D45-D51 notes |
| 2 | lookups and event times leave their range silently; R = 0 | correct; the old code clamped I_th (8-17 V), and gave negative periods once a level was passed (only in runs that had already diverged). Rail < 8 V on falling steps: real thresholds move peaks ≤ 0.56 A, no outcome class changes. R = 0 raised, it did not return a wrong number | flags in every D63 record, `inf` for unreachable levels, R = 0 limit; D63 "≤ 4.7 A" → ≤ 5.5 A |
| 3 | "steady state" by a fixed warm-up, root finding without acceptance | correct; 139 of 142 simulate() warm-ups are periodic (fixed point or 2 / 4-period quantised cycle), 3 drift within 0.09 mV / 0.35 A (unchanged on 10-10 with the control memory dlo / t_hist / step compared too); A134 / A135's L × 1.3 absolute cap locks before its step | `steady_check`, `metrics()["warm_settled"]`; `steady_ton` bracket + residual |
| 4 | reduced models cannot certify the final system | correct; the counterexamples were already in the repo (A142, A143 oscillations D60 / D63 cannot represent) | D60 scope note; final stability only from co-simulation of the named plant version |
| 5 | calibrated models counted as independent evidence | correct in principle; D58 / D63 / D68 already named their fits, but no overview existed | evidence-class table (D81 Section 4) |
| 6 | order-of-magnitude estimates written as proofs | correct for D71's "negligible" | reworded with its assumptions |

