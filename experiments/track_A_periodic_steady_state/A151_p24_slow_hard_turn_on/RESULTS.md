# A151 - a slow hard turn-on (separate turn-on drive) against the package overshoot (RESULTS)
Boundary: 6cf7689. Records: release records-a151 (21 runs). Outputs: a151_screen.json, a151_summary.json.

## 0. Verdict
- **Solved in the plant: a slow turn-on with a fast turn-off holds every switch <= 40 V (the continuous rating) up to
  150 pH.** The frozen controller and the 72 A/ns turn-off are unchanged. Whole-run max V_DS, including start-up:
  - 50 pH at 36 A/ns: line step 37.1 V (from 41.8 V), load step and start-up 33.0 V.
  - 100 pH at 18 A/ns: 36.4 / 33.2 / 33.2 V (from 51.0 / 44.4 / 44.4 V).
  - 150 pH at 18 A/ns: line step 38.0 V (from 54.7 V), n0 36.3 V.
- **Price at 18 A/ns:**
  - Channel edge power on n0: +0.36 W at 50 pH, +0.12 W at 100 pH, +0.18 W at 150 pH (<= 0.15 % of 250 W).
  - Load-step Vo back within 1 %: +1.8-1.9 us (5.5-5.8 -> 7.4-7.6 us).
  - Post-step peaks: within -2..+2 A.
  - At 36 A/ns the edge power rises only +0.03-0.10 W.
- **9 A/ns is too slow.** At 100 pH: 1 NEW oracle event on the line step, load-step Vo +2.8 us, +0.63 W. At 150 pH: the
  line step's Vo stays outside 1 % for 44 us.
- **The bus-slew lever does not work.** At 72 / 72 A/ns, +4.8 V over 5 us still gives 41.5 / 49.1 V at 50 / 100 pH.
  Phase 1 still turns on hard; the hard turn-on is the cause, not the ramp rate.
- **Why it works** (A144 mechanism B; Dymond et al. 2018 show the same on a 40 V GaN bridge leg):
  - A hard turn-on of phase k-1 rings SH_k. Slowing only that edge removes the ring's excitation.
  - Under ZVS the turn-on carries no V_DS, so it costs only in transients and at phase 1's 3.8 V partial turn-on.
  - The event's energy stays the same (harness: 1.05-1.13 uJ per 17 V event); it moves from the loop damper into the
    channel.
- **What changes for the package:** the switch voltage no longer limits the loop up to 150 pH. The binding loop limit
  becomes loss: A145's turn-off ring costs 1 % at ~70 pH, and slowing the turn-on does not touch that.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | harness change within +-2 V of cosim, >= 5 of 7 | FAIL 1/7: cosim falls further at 100 / 150 pH (-9.8 / -14.6 / -17.1 V vs harness -2.2 / -9.1 / -10.7 at 100 pH); 50 pH -4.7 vs -6.9, -7.2 vs -8.1 |
| 2 | 50 pH <= 40.0 V on 3 rows | PASS at 36 A/ns (37.1 / 33.0 / 33.0 V) |
| 3 | 100 pH <= 40.0 V on 3 rows | PASS at 18 A/ns (36.4 / 33.2 / 33.2 V); 36 A/ns 41.2 V (<= 48 V) |
| 4 | controller unchanged at that di/dt | PASS at both (peaks <= +1.3 A, 0 NEW, late 0, Vo back <= +1.9 us) |
| 5 | n0 edge power <= +0.5 W | PASS: +0.10 W (50 pH, 36), +0.12 W (100 pH, 18) |

Predictions: 50 pH 36 A/ns 34.8 V (37.1 V measured). 100 pH 48.8 / 42.0 / 40.3 V (41.2 / 36.4 / 33.9 V measured): the
reduction was larger than predicted. 150 pH 48.1 / 42.2 V (38.0 / 36.5 V measured). The 5 us bus-slew prediction was
wrong. Criterion 1 failing at 100 / 150 pH was predicted.

## 2. Device rating (read alongside, from EPC's documents in the workspace)
- EPC2067: 40 V continuous, 48 V for up to 10,000 5 ms pulses at 150 C.
- EPC Phase 16 reliability report, Section 3.2.6: repetitive drain overshoot up to 120 % of VDS,max for <= 1 % of
  lifetime. Measured on 100 V parts at 75 C, so applying it to a 40 V part is an extrapolation.
- With the slow turn-on no switch exceeds 40 V, so the result does not depend on that rule.
- Without the slow turn-on, 50 pH stays inside the rule: 23 sections > 40 V per line step, none > 48 V. 100 pH
  does not: 13 sections > 48 V.

## 3. Limits
- The plant's edge is a linear current ramp: no gate model, no Miller plateau. Which gate resistor or drive sequence
  gives 18-36 A/ns on EPC2067 with P24's driver is open (Mihai; Dymond 2018 gives the active-drive alternative).
- One module, L x 1.0, Q 7, rows l_p48_1us / n0 / s_p62 only. No falling steps, no L corners, no four modules, no
  loop above 150 pH (published embedded loops reach 230-320 pH).
- The edge power is the channel's only; the damper's share falls (harness), so the net cost is lower than quoted.

## 4. Post hoc correction (A152, 2026-10-06)
- Criterion 4 checked post-step peaks only. **The whole-run peak at 18 A/ns is over 200 A at the start-up handover
  (144.5 us):** 205 / 224 / 240 A at 50 / 100 / 150 pH, 276 / 288 A at 9 A/ns. 36 A/ns gives 154-163 A; 72 A/ns (A145) 141-147 A.
- Cause: mode S runs open loop at ton_ns 35.5. Its turn-ons are hard, and a slow turn-on loses on-time, so Vo reaches
  only 0.958 V by the handover (1.016 V at 72 A/ns). The loop's P term then adds ~15 ns to Ton (51 ns).
- So "100 pH at 18 A/ns solves it" holds only with a start-up Ton compensation (ton_ns 37.5: 148 A). A152 tests that spec.
