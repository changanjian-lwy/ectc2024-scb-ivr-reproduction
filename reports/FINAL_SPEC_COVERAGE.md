# Final package specification: configuration and what it was checked on

Written 2026-10-08 after an external review of D70-D79 / A163-A172. It found that the summary's "every corner, four
modules" ran on two plant versions. This file fixes the final configuration, lists which plant version each result
comes from, and says what may be claimed.

## 1. The final configuration (frozen)

| part | setting | source |
|---|---|---|
| controller | frozen RTL: one module A143 (lo_learn 4) on A129 g125 + vff {rel_q8 320, rel_lp 1, seed 2} + floor_late; four modules C12 + lo_learn 4 (C13). One register added by user decision on 2026-10-09: cfg_ton_s, mode S's own Ton (A184; scb_vff's C10 seed and the loop's reset value keep cfg_ton; equal values = the old controller bit for bit) | A143, C13, A184 |
| loop | 50 pH, ideal parallel damper at ring Q 7 | A168, A157 |
| devices | EPC2067, EPC's model (vendor library at run time), 2 + 3 per phase; spread corners ff (V_th −0.3 V, driver ×0.8), ss (V_th +1.0 V, Q_G ×1.29, driver ×1.2), hot (125 °C) | D79, A163 |
| drive | 3.0 Ω turn-on / 0.3 Ω turn-off per device, ±20 %; R_G 0.3 Ω; every switch gate-driven | A164, A169 |
| controller-side lead | high-side turn-on earlier by 8 ns, or by 9.5 ns on slow boards (the corner read from the 25 °C trim), ramped in over 20 µs after the handover. The 9.5 ns lead closes the slow corner's 125 °C post-step miss (A191). On its other rows it costs 3-5 A of peak and 3-5 mV of dip at 25 °C on +4.8 V / 1 µs (S75 ≤ 197.1 A, A192). Below 25 °C the same row holds: S75 ≤ 195.0 A at −40 °C and ≤ 197.8 A at 0 °C (A193, three step positions each; margin 2.2 A) | A167, A191, A192, A193 |
| start-up | **since 2026-10-10 (A188):** mode S at t0 = 200 ns, so every turn-on is hard and the series-capacitor ladder stays balanced (A183; at 400 ns slow boards split to 15.6 / 14.8 / 8.9 / 8.7 V). Per-board trim of mode S's Ton (cfg_ton_s) to Vo(143.5 µs) = 1.035 V: nominal 23.65-23.68 ns at L × 0.7-1.3, slow 35.45-35.80, ff 21.33 ns. The loop's seed is ton_ns = T_ss + (kp + ki)(Vo_entry − 1 V), from one closed-loop measurement (A185). The handover is requested at Vo ≥ 1.045 V or at 144 µs, whichever comes first: a sequencer comparator on the sampled Vo (A188; at 25 °C it never fires). Trims and seed are set once at 25 °C. Above 25 °C they stay locked (A188). Below 25 °C the mode-S trim follows a per-corner table, the corner read from the 25 °C trim: slow +0.531 / +1.441 ns, nominal +0.113 / +0.313 ns at 0 / -40 °C (A190, held on hold-out boards; device model extrapolated below 25 °C). Without the table slow boards fail cold (A189: -40 °C entry 0.956 V, 278 A; 0 °C 211 A). Checked at -40, 0, 25 and 125 °C. Superseded: t0 400 ns with ton = ton0 + (1.035 − Vo)/0.026 (A164-A181) | A183-A190 |
| calibrated vs adaptive | factory, once per board: the mode-S trim and the loop seed (one closed-loop measurement of T_ss). Adapting at run time: valley timing (dt_pred, dlo), low-side dead time (dtl), negative-current trim, the Vin feed-forward's filters. Fixed: drive resistors, lead (per corner class, set once), t_il | A143, A164, A192 |
| driver interlock | threshold form: a channel about to start while its complement conducts waits at that gate level, then starts t_il = 0.5 ns after the complement stops (modelled ideally). The release time is a timing spec, not a safety one: no delay up to 8.3 ns changed a peak or V_DS. At the slow corner it should release within 1.0 ns (A179: after the −8 V ramp the late fires rise at 1.4 ns at 2 of 4 step positions); a per-board comparator reference (V_th − 0.2 V, ~1.4 ns) is just above that, a fixed 1.0 V reference (8.3 ns) far above. This settles the ramp's late fires only: at 1.0 ns the load step's spike count still fails its registered tolerance (scatter, open), and a real comparator's offset, noise and early release are not modelled | A171, A173, A174, A177, A179 |
| reference cfgs | `experiments/track_A_periodic_steady_state/A172_p24_final_gate_plant/cosim/cfg_nom_L07_l_p48_1us.json` (one module), `cfg_m4_nom_l_p48_1us.json` (four) | A172 |

## 2. Plant versions

| | plant | experiments |
|---|---|---|
| V0 | ideal switches, no package | A124-A143, C05-C14 |
| V1 | loop + current-ramp edges | A144-A162 |
| V2 | gate model on the high sides; low sides ideal; no interlock | A163-A168 |
| V3 | every switch gate-driven; no interlock | A169 |
| V4 | every switch gate-driven; gate-form interlock | A170 |
| **V5** | **every switch gate-driven; threshold-form interlock (final)** | **A171 (S50 rows), A172, A173-A193** |

A V2 result does not count as a V5 check. V2 and V5 differ in the low sides' turn-off delay (≤ 2.9 + 1.8 ns), and
that delay is what made the lead shoot through (A169).

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
  206.1 A at 25 °C (A198). Not fixed: stated as a hold-off (Section 5).
The rest:
- falling steps (nom −4.8 V / 1 µs, ff −8 V / 10 µs): A148's valley loss on phases 2-4 turns into K3 restarts and
  10-20 A spikes, which V2 does not show (A176 supports the lead plus the gate-driven low sides as the cause; one
  step position per variant, so "none" on a variant is one sample);
- slow corner: Vo dips 3-5 mV deeper than V2 after line ramps (the low sides' turn-off delay plus holds);
- four modules ss: 10-16 A spikes, four of them A160's K4-window artefact.

## 4. Not covered by the final plant

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
- The drive specification "3.0 Ω ± 20 % on / ≤ 0.3 Ω off per device" was derived for hard high-side turn-ons. For
  the low sides, which turn on at zero voltage, it is not a specification but an oversight: they need their own,
  small turn-on resistance (A205; value and its effect on the low sides' rare hard turn-ons not yet determined).
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

