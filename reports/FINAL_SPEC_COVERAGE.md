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
| start-up | per-board trim: ton = ton0 + (1.035 − Vo(143.5 µs)) / 0.026 | A164 |
| driver interlock | threshold form: a channel about to start while its complement conducts waits at that gate level, then starts t_il = 0.5 ns after the complement stops (modelled ideally). The release time is a timing spec, not a safety one: no delay up to 8.3 ns changed a peak or V_DS. The slow corner's timing wants < 1.4 ns: a per-board comparator reference (V_th − 0.2 V, ~1.4 ns) nearly meets the criteria, a fixed 1.0 V reference (8.3 ns) does not | A171, A173, A174, A177 |
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
- ff at 1.0 ns (its fixed-reference value) and L × 0.7 at 2.0 ns: same as 0.5 ns.

Step position (A174, 4 more phases per row): L × 0.7 +4.8 V / 1 µs 199.7, 199.9, 199.8, 199.5, 201.5 A. At the
201.5 A phase Vo stays outside 1 % for 37.9 µs. ff −8 V / 10 µs: 181.5-183.0 A, Vo 30.6-31.8 mV at every phase,
the spike at 2 of 5.

Only on earlier plants: the corners ff / hot / ss on the ramps and −4.8 V (V2, A164 for some); random stimuli (V0,
A142 / C13); the inductor spread beyond ±5 % (V0, C14).

The misses are regulation or oracle events, none on voltage; the only current miss is L × 0.7 at one step phase
(201.5 A, A174):
- falling steps (nom −4.8 V / 1 µs, ff −8 V / 10 µs): A148's valley loss on phases 2-4 turns into K3 restarts and
  10-20 A spikes, which V2 does not show (cause: A176);
- slow corner: Vo dips 3-5 mV deeper than V2 after line ramps (the low sides' turn-off delay plus holds);
- four modules ss: 10-16 A spikes, four of them A160's K4-window artefact.

## 4. Not covered by the final plant

- **The interlock is an idealised function.** It senses the complement's channel exactly and holds the gate at its
  own channel start. Where it acted (L × 0.7, slow corner), zero shoot-throughs are imposed by the rule, not
  shown. Where it never acted (0 holds: nom / ff / hot one module, four modules nominal), they do not depend on it.
  A173 / A174 set t_il to realisable forms (above). A comparator reference above a device's channel-off level
  would release early; the spec excludes it, and it is not modelled.
- Devices inside a board are identical (mismatch only in LTspice single edges, D79 4.7). Four-module boards
  share one corner.
- The damper is an ideal Q 7 resistor; the driver is an ideal source behind a resistor.
- 50 pH is the bound **for this drive and this controller** (A168). It is not a package limit in general.

## 5. How to state the results

- "The final plant passed the listed rows (Section 3)", not "every corner" or "every test".
- Inductance tolerance (A174 / A178, +4.8 V / 1 µs, five step phases per board): 0.75 L0 ≤ 198.3 A, 0.8 L0 ≤
  194.7 A, 0.7 L0 199.5-201.5 A. State "≥ 0.75 L0 keeps ≤ 200 A at every tested phase; 0.7 L0 reaches 201.5 A".
  The 0.7 board's open-loop start-up is 200.2 A (registered limit ref + 3 A = 205.5 A).
- The interlock: "closes in the model with an idealised threshold interlock. Its release time is a timing spec: any
  delay up to 8.3 ns keeps peaks and voltages; the slow corner's timing wants < 1.4 ns, which a per-board
  comparator reference nearly meets and a fixed reference does not (A174, A177)".
- Edge power: per module 2.26 / 2.45 / 2.86 / 4.57 W at ff / nom / hot / ss (A171), 4.18 W at L × 0.7 (A172),
  2.44-2.46 W on four modules (steady window; A172's 2.87 W included the step). D62's ideal-edge terms were
  0.94 W. The thermal result with these losses: D80.
