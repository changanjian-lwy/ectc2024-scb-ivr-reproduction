# A206 - the low side's zero-voltage turn-on in the plant (V6), and the low sides' own turn-on resistance (RESULTS)
Boundary: b110c31 (Sections 1-4), e443b1f (Section 5, written before the second round). Records: release
records-a206 (29 second-round and 12 first-round cosim records, logs); the replay comparisons are in replays/
(second round) and replays_r1/ (numbers only). Analysis: a206_analyze.py -> a206_summary.json (first round:
a206_summary_r1.json). Second-round runs from e443b1f (stage 1, start-up T0), 24b01d9 (T1) and 40e5762 (stage 2);
cosim_sources_modified False on all 29. Plant V6 = V5 + gate zvs_edge + gate miller + r_sw with R = 0. One module.
LTspice as in A205: EPC's typical EPC2067 on all 20 switches, 25 C, started from the plant's state, same gate
commands, two periods per replay. Identity: with the three parts off, regression quick 4 / 4 and A205's N0 record
bit for bit to 160 us (751 sections, 7 snapshots), checked after both model rounds.

## 0. Verdict
- **V6 agrees with LTspice where V5 did not** (nominal devices, 25 C, 26 replays, second round). One period later
  the phase currents are within 0.68 A settled (V5: 3.5-5.0 A), 0.41 A in mode S and 1.05 A after N0's step. The
  settled loss books are within 0.5-0.7 % at 3.0, 1.0 and 0.3 ohm (V5: 12.6 of 27.4 W missing). c2 passes on 23 of
  26, c5 at the three resistances.
- **Stated error of V6: N75 at the step's peak.** c2 misses on 3 of 3: currents 1.52-1.57 A against 1.5 A, single
  peaks up to 2.3 A lower in LTspice. The plant is the higher one (its largest peak 193.0 A against 192.8 A).
  Traced cause: after the step the valleys reach -54..-63 A, and a high side commanded on at V_DS > 0 sees its node
  swing past the rail before its gate reaches threshold. The plant then conducts through the V_GS = 0 fit at 2.2 V;
  in LTspice the gate is part-charged and the drop is 0.43 V. This is the second miss, so by the rule it is
  reported, not fixed here.
- **Low sides' turn-on resistance: 0.3 ohm** (times the board's drive factor: 0.36 ohm on slow boards), chosen by
  the registered rule in both rounds. Semiconductor loss in the plant's books, settled N0, 250 W, switches at the
  datasheet maximum: 20.15 W at 0.3 ohm, 22.63 W at 1.0 ohm, 29.59 W at 3.0 ohm; V5 booked 15.75 W. As
  Pout / (Pout + loss): 92.54 / 91.70 / 89.42 % (V5: 94.07 %).
- **The specification's 3.0 ohm on the low sides does not hold on V6**: with switches at the datasheet maximum the
  handover peaks at 206.4 A (run_E_N0_steady_ls3: phase 2 at 147.2 us, Vo down to 0.969 V, late fires 0 / 5 / 3 / 0).
  With typical switches the same resistance passes (167.4 A). Not traced further: 3.0 ohm is not the chosen value.
- **Start-up needs a new trim on V6**: with V5's ton_s, Vo before the handover is 14-15 mV higher on nominal boards
  and 13-16 mV lower on slow ones (25 and 0 C; 32 mV at 125 C). New trims: N0 -0.279 ns, N75 -0.261 ns, S75 +0.289 ns. The five start-up runs
  with them pass c6, Vo before the handover within 3.1 mV of V5's.
- **Stage 2: the twelve binding rows hold 200 A on V6.** Largest post-step peak 197.57 A (S75, 125 C). Margins:
  S75 125 C 2.4 A, N75 3.8 A, S75 25 C 4.2 A, S75 0 C 4.6 A, N0 21.0 A. Every run: 0 shoot-throughs, 0 forced
  edges, V_DS <= 33.7 V, Vo within 13.6 mV of 1 V from 20 us after the handover.
- **What may be claimed.** V6 is the plant for new claims at nominal devices and 25 C, with the stated error above
  (in the conservative direction). The margin of the binding row, S75 at 125 C, rests on a corner LTspice has not
  replayed (Section 5).

## 1. Replay criteria (LTspice minus plant; passes of n)
| group | n | c1 peaks | c2 one period | c3 V_DS | c4 hard turn-on | second-round numbers |
|---|---|---|---|---|---|---|
| mode S, N0, 3.0 ohm | 4 | 0 -> 4 | 0 -> 4 | 4 | 4 | peaks -0.50..+0.05 A; currents -0.18..-0.41 A; Vo -0.02 mV; books -0.6 % |
| settled, N0, 3.0 ohm | 6 | 6 | 6 | 6 | 6 | peaks -0.59..-0.05 A; currents -0.68..+0.21 A; Vo -0.12 mV; books -0.5 % |
| settled, N0, 1.0 ohm | 3 | 3 | 3 | 3 | 3 | currents -0.54..-0.22 A; Vo -0.11 mV; books -0.6..-0.7 % |
| settled, N0, 0.3 ohm | 3 | 3 | 3 | 3 | 3 | currents -0.49..-0.36 A; Vo -0.10 mV; books -0.5..-0.7 % |
| N0 step, at the step | 2 | 2 | 2 | 2 | 2 | currents -0.68..+0.21 A |
| N0 step, at the peak | 3 | 3 | 3 | 3 | 1 -> 2 | peaks -0.81..-0.08 A; currents -1.05..-0.21 A |
| N75 step, at the step | 2 | 2 | 2 | 2 | 2 | currents -0.87..+0.32 A |
| N75 step, at the peak | 3 | 0 -> 1 | 0 | 1 -> 3 | 0 | peaks -2.32..-0.17 A; currents -1.57..+0.43 A; V_DS 1.43 V |
| **all** | 26 | 19 -> 24 | 19 -> 23 | 24 -> 26 | 21 -> 22 | "a -> b" = first -> second round |
- c5 (settled N0, first period, plant books against LTspice's channels and phase resistance): 26.44 against
  26.58 W at 3.0 ohm, 19.63 against 19.76 W at 1.0 ohm, 17.26 against 17.36 W at 0.3 ohm (typical switches).
- **c0 fails on all 26, on capacitor 1's voltage alone**: 5.7-8.8 mV against 5 mV. The replay holds every node
  through 1 mOhm while the phase current flows. Currents arrive within 0.003 A, Vo within 0.01 mV. A limit of the
  tool, and my limit was too tight for it.
- First round (replays_r1/): mode S missed c2 on 4 of 4, LTspice 1.62-1.79 A higher per period. Cause: a low side
  commanded off at 37 A reverse current keeps conducting while its gate discharges; the plant opened it at once
  (18.4 against 12.5 nVs in 9 ns). V5 has the same simplification, which there offset the missing turn-on. Fixed in
  the one model round the rule allows (harness: 12.73 against 12.50 nVs).
- c4's other misses: N0 at the peak, one turn-on at V_DS near zero, where "channel start" is the current's
  reversal (2.4 ns); N75 at the peak, the traced cause itself (6.4 ns, 2.25 V).
- c6: 28 of 29 runs pass; the miss is run_E_N0_steady_ls3 (Section 0).

## 2. Loss books and start-up (settled N0, last 10 us; W per module)
| | V5 | V6 3.0 ohm | V6 1.0 ohm | V6 0.3 ohm |
|---|---|---|---|---|
| high-side edges | 2.43 | 2.48 | 2.48 | 2.44 |
| low-side edges (reverse conduction while the gate moves) | 0.00 | 8.20 | 3.23 | 1.41 |
| reverse fit (dead time) | 0.00 | 3.39 | 1.36 | 0.66 |
| conduction | 13.32 (lumped R) | 1.70 + 13.82 | 1.63 + 13.94 | 1.61 + 14.04 |
| **total, switches at the datasheet maximum** | **15.75** | **29.59** | **22.63** | **20.15** |
| total, typical switches / LTspice's first period | - | 26.73 / 26.58 | 19.81 / 19.76 | 17.32 / 17.36 |
| on-time command, ns | 40.27 | 41.59 | 41.00 | 40.88 |
| settled peak, A | 144.0-147.2 | 147.7-150.3 | 144.9-148.6 | 144.7-148.1 |
- Conduction alone is 2.3 W above V5's, mostly because a low side also carries the next phase's current during that phase's
  on-time, which a lumped per-phase resistance does not count. This part does not depend on the turn-on resistance.
- Start-up with the new trims (T1 runs; Vo half a microsecond before the handover, V6 / V5): N0 1.0330 / 1.0326 V,
  N75 1.0318 / 1.0329 V, S75 25 C 1.0345 / 1.0340 V, S75 0 C 1.0371 / 1.0340 V. S75 125 C: handover requested at
  133.4 us (V5 131.4), Vo at most 1.0476 V (limit 1.05), handover peak 182.0 A (V5 184.5). Other handover peaks
  162.0 / 150.5 / 154.5 / 154.4 A.
- Low sides' hard turn-ons at 0.3 ohm: at most 77 per run (N0), all but one or two of them in start-up and
  handover; low-side V_DS <= 19.6 V.

## 3. Stage 2: +4.8 V / 1 us at 500 us + k T / 6, 0.3 ohm, new trims (V5 = the same row's record, read to the same time)
| board | k | peak V6, A | peak V5, A | Vo - 1 V after the step V6, mV | V5, mV | late fires after the step V6 / V5 |
|---|---|---|---|---|---|---|
| N0 25 C | 0 | 178.99 | 182.83 | -4.8 / +6.7 | -5.8 / +6.3 | 0 / 0 |
| N75 25 C | 0, 2, 4 | 189.05, 189.04, **196.24** | 198.52, -, - | -8.9 / +8.5 | -8.7 / +6.2 | 0 / 0 |
| S75 25 C | 0, 2, 4 | 194.92, 195.35, **195.81** | 196.10, 195.85, 197.06 | -12.1 / +10.2 | -17.5 / +10.5 | 51-78 / 45-92 |
| S75 0 C | 0, 2, 4 | 195.36, 194.95, **195.42** | 194.54, 194.67, 197.79 | -12.7 / +9.8 | -14.5 / +10.4 | 82-106 / 91-106 |
| S75 125 C | 1, 5 | 196.14, **197.57** | 195.42, 196.27 | -13.6 / +10.3 | -17.4 / +11.8 | 7-10 / 5-7 |
- Vo and late fires: extremes over the board's positions. V5's N75 record of the final configuration exists at
  k 0 only (A205) and ends 31 us after the step.
- Peaks fall 3.8-9.5 A on nominal devices and move -2.4..+1.3 A on slow ones. The 125 C rows are the only ones
  that rise at every position (+0.7, +1.3 A). There the switches' resistance is 1.58 times its 25 C value, which
  V5's lumped R was not; this was not separated from the other changes.

## 4. Predictions
- Held: i1, i2; settled c2 at the three resistances (within 1.0 A); c4 (at least 18: 21, 22); c3 in the second
  round (26); 0.3 ohm passes c6 and is chosen; stage 2's N75 196-203 A (196.24) and S75 0 C 195-203 A (195.42).
  Second round: mode S within 1.0 A; settled replays move under 0.1 A; books move under 0.3 W; mode S's Vo rises
  20-35 mV (27); at 0.3 ohm 8-22 mV above V5 (14.9).
- Missed: c0; c2 in mode S in the first round; c3 and c1 in the first round (24, 19); N75 at the peak after the
  fix (predicted 0.5-1.5 A: 1.52-1.57); c5 (predicted 3-8 % low: 0.5-0.7 %); loss against V5's 14.8 W (+14.8 /
  +7.8 / +5.4 W against +11..13 / +5..7 / +3..5); on-time +1.3 / +0.6 ns (0.9 / 0.4); settled peak at 3.0 ohm
  +3.1 A (2); the first round's start-up (Vo -37 / -12 mV, handover 176 / 165 A; the reverse turn-off was missing).
- My registration errors (BOUNDARY Section 5): the start-up slope was the older start-up's (28.3 for 53.5 / 54.5 mV
  per ns), and the trim rule named one board and one direction.

## 5. Limits
- LTspice comparison at nominal devices and 25 C only. The binding row on V6 is S75 at 125 C with 2.4 A, and slow
  devices, 125 C and 0 C are not replayed: the plant's error there is not known. The reverse fit is the typical
  25 C device at every corner.
- Open loop over two periods, one module, LTspice with the vendor's typical model (a second model, not hardware).
- On V6 only the twelve binding rows ran: three (two) step positions per board. V5's other rows (falling steps,
  load steps, L x 1.3, fast devices with 0.24 ohm low sides, four modules) are not re-run.
- V6's simplifications (BOUNDARY Section 1) and the stated error at N75's peak remain. A V6 run takes about three
  times a V5 run (43-95 min for 581 us at 10 jobs).
