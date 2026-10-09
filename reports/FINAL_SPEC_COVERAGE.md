# Final package specification: configuration and what it was checked on

Written 2026-10-08 after an external review of D70-D79 / A163-A172. It found that the summary's "every corner, four
modules" ran on two plant versions. This file fixes the final configuration, lists which plant version each result
comes from, and says what may be claimed.

## 1. The final configuration (frozen)

| part | setting | source |
|---|---|---|
| controller | frozen RTL: one module A143 (lo_learn 4) on A129 g125 + vff {rel_q8 320, rel_lp 1, seed 2} + floor_late; four modules C12 + lo_learn 4 (C13) | A143, C13 |
| loop | 50 pH, ideal parallel damper at ring Q 7 | A168, A157 |
| devices | EPC2067, EPC's model (vendor library at run time), 2 + 3 per phase; spread corners ff (V_th −0.3 V, driver ×0.8), ss (V_th +1.0 V, Q_G ×1.29, driver ×1.2), hot (125 °C) | D79, A163 |
| drive | 3.0 Ω turn-on / 0.3 Ω turn-off per device, ±20 %; R_G 0.3 Ω; every switch gate-driven | A164, A169 |
| controller-side lead | high-side turn-on 8 ns earlier, ramped in over 20 µs after the handover | A167 |
| start-up | per-board trim: ton = ton0 + (1.035 − Vo(143.5 µs)) / 0.026. Every tested condition was trimmed at its own corner, the 125 °C board included (39.289 vs 39.615 ns at 25 °C); a trim locked at 25 °C and started hot is estimated (Vo(143.5 µs) +8.5 mV, 1.044 V, away from the 0.99 V cliff), not run | A164 |
| calibrated vs adaptive | factory, once per board: the start-up trim. Adapting at run time: valley timing (dt_pred, dlo), low-side dead time (dtl), negative-current trim, the Vin feed-forward's filters. Fixed: drive resistors, lead, t_il | A143, A164 |
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
| **V5** | **every switch gate-driven; threshold-form interlock (final)** | **A171 (S50 rows), A172, A173** |

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
149.7, ss 193.0 / 193.0, ±5 % 169.1 / 161.9 A.

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

Only on earlier plants: the corners ff / hot / ss on the ramps and −4.8 V (V2, A164 for some); random stimuli (V0,
A142 / C13); the inductor spread beyond ±5 % (V0, C14).

The misses are regulation or oracle events, none on voltage; the only current miss is L × 0.7 at one step phase
(201.5 A, A174):
- falling steps (nom −4.8 V / 1 µs, ff −8 V / 10 µs): A148's valley loss on phases 2-4 turns into K3 restarts and
  10-20 A spikes, which V2 does not show (A176 supports the lead plus the gate-driven low sides as the cause; one
  step position per variant, so "none" on a variant is one sample);
- slow corner: Vo dips 3-5 mV deeper than V2 after line ramps (the low sides' turn-off delay plus holds);
- four modules ss: 10-16 A spikes, four of them A160's K4-window artefact.

## 4. Not covered by the final plant

- **The interlock is an idealised function.** It senses the complement's channel exactly and holds the gate at its
  own channel start. Where it acted (L × 0.7, slow corner), zero shoot-throughs are imposed by the rule, not
  shown. Where it never acted (0 holds: nom / ff / hot one module, four modules nominal), they do not depend on it.
  A173 / A174 set t_il to realisable forms (above). A comparator reference above a device's channel-off level
  would release early; the spec excludes it, and it is not modelled.
- **Each limit was found with the others at nominal.** Not run together: a small inductance with the slow
  corner, a 1.0 ns interlock, a trim locked at 25 °C and an adverse step phase. Step positions are offsets in
  absolute time, not aligned to a physical event across variants.
- Devices inside a board are identical (mismatch only in LTspice single edges, D79 4.7). Four-module boards
  share one corner.
- The damper is an ideal Q 7 resistor; the driver is an ideal source behind a resistor.
- 50 pH is the bound **for this drive and this controller** (A168). It is not a package limit in general.

## 5. How to state the results

- "The final plant passed the listed rows (Section 3)", not "every corner" or "every test".
- Inductance tolerance (A174 / A178, +4.8 V / 1 µs, five step phases per board): 0.75 L0 ≤ 198.3 A, 0.8 L0 ≤
  194.7 A, 0.7 L0 199.5-201.5 A (nominal devices, t_il 0.5 ns, each board trimmed). State "at 0.75 and 0.8 L0
  every tested phase stays ≤ 200 A; 0.7 L0 reaches 201.5 A" - not "every L ≥ 0.75 L0": the peak is not monotone
  in L (L0 182.5 A, 1.3 L0 188.7 A).
  The 0.7 board's open-loop start-up is 200.2 A (registered limit ref + 3 A = 205.5 A).
- The interlock: "closes in the model with an idealised threshold interlock. Its release time is a timing spec: any
  delay up to 8.3 ns keeps peaks and voltages; at the slow corner it should release within 1.0 ns, which a
  per-board comparator reference (~1.4 ns) just misses and a fixed reference misses by far (A174, A177, A179)".
- Two layers. Engineering: peak current, V_DS, Vo extreme and recovery, loss. Diagnostic: late fires, oracle NEW
  events, restarts. The interlock's 1.0 ns is a diagnostic target: in A179 peaks (169-171 / 183-185 A), V_DS
  (≤ 32.9 V) and Vo extremes (within ~2 mV) do not separate 0.5-1.4 ns; up to 8.3 ns peaks and V_DS held and
  four-module Vo was −13.7 against −9.9 mV (A174).
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
| 1 | each corner re-trimmed (125 °C too): shows "works after re-calibration", not "a board trimmed once still starts hot" | correct; estimated impact small (nominal board: hot trim 0.33 ns shorter → Vo(143.5 µs) +8.5 mV, away from the cliff); slow corner + hot never run | row "start-up" and "calibrated vs adaptive" in Section 1; locked-trim test proposed, not run |
| 2 | relative criteria (late ≤ 1.5 ref + 5, NEW ≤ ref + 2, Vo ± 2 mV) are regression checks, not hardware requirements | correct in principle; the 1.0 ns was already called a timing (not safety) spec, but it reads like a requirement | Section 5 "Two layers": 1.0 ns is a diagnostic target; engineering metrics do not separate 0.5-1.4 ns |
| 3 | A176 ran one step position per variant; "none" may be phase luck | correct; A176's own limits said so, its verdict and later docs said "only together" | reworded to "supports" (Section 3, D79, summary, status) |
| 4 | separately found limits do not combine; discrete points are not a range | correct; our data show the peak is not monotone in L (L0 182.5, 1.3 L0 188.7 A) | Section 5 states tested points; Section 4 "each limit found with the others at nominal" |
| 5 | an ideal interlock cannot release early, so its safety is preset by the model | correct; already stated in Section 4 ("imposed by the rule, not shown"; early release "not modelled") | none; a comparator model with offset / noise / mismatch would be new work |
| 6 | A180's step-2 rule tied the windowed clamp to the always-on clamp's loss | partly: A180 RESULTS already reads the rule as not authorising step 2; criterion 5 stood in for the windowed clamp's ideal trigger | A180 unchanged (FAIL stays); a separate windowed-clamp test with a real detector is the right next step, not run |

Proposed, not run (this phase is archived): lock each board's 25 °C trim, then run it hot, at the slow corner with
L × 0.75 and t_il 1.0 ns, with the step aligned to the same physical event (e.g. phase 1's low-side turn-off) at
several offsets; judge the engineering layer first.

## 7. Third external review (2026-10-09): the mathematical model

Details, numbers and the scripts: `symbolic_derivations/03_P24_native/D81_P24_MATH_MODEL_ACCEPTANCE.md`.

| # | point | verdict | action |
|---|---|---|---|
| 1 | stability eigenvalues taken from a reused (possibly stale) Jacobian | correct (D45-D51 used Newton's chord matrix); recomputed at all 36 orbits: largest modulus moves ≤ 8.1e-4, all < 1 (worst 0.9959). Step size matters more: 1e-6-1e-7 adds up to 4e-3 of integrator noise | `section_jacobian` (central, 1e-4, event-order flag) in the solver and gate; D45-D51 notes |
| 2 | lookups and event times leave their range silently; R = 0 | correct; the old code clamped I_th (8-17 V), and gave negative periods once a level was passed (only in runs that had already diverged). Rail < 8 V on falling steps: real thresholds move peaks ≤ 0.56 A, no outcome class changes. R = 0 raised, it did not return a wrong number | flags in every D63 record, `inf` for unreachable levels, R = 0 limit; D63 "≤ 4.7 A" → ≤ 5.5 A |
| 3 | "steady state" by a fixed warm-up, root finding without acceptance | correct; 139 of 142 simulate() warm-ups are periodic (fixed point or 2 / 4-period quantised cycle), 3 drift within 0.09 mV / 0.35 A; A134 / A135's L × 1.3 absolute cap locks before its step | `steady_check`, `metrics()["warm_settled"]`; `steady_ton` bracket + residual |
| 4 | reduced models cannot certify the final system | correct; the counterexamples were already in the repo (A142, A143 oscillations D60 / D63 cannot represent) | D60 scope note; final stability only from co-simulation of the named plant version |
| 5 | calibrated models counted as independent evidence | correct in principle; D58 / D63 / D68 already named their fits, but no overview existed | evidence-class table (D81 Section 4) |
| 6 | order-of-magnitude estimates written as proofs | correct for D71's "negligible" | reworded with its assumptions |

