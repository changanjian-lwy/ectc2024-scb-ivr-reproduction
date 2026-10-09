# A181 - a start-up trim set once at 25 C, locked, under joint adverse conditions (RESULTS)
Boundary: 2b845b1 (analysis cd829cc; stage 2 cfgs 0fbdaed). Records: release records-a181 (3 start-ups, 10 runs,
logs). Analysis: a181_analyze.py -> a181_summary.json. All runs from committed code, plant V5, t_il 1.0 ns.

## 0. Verdict
- **FAIL as registered on the slow-corner L x 0.75 board (decision rule, branch 2): the inductance tolerance depends
  on the device corner.** A178's "L x 0.75 keeps 200 A" holds with nominal devices only.
- **S75** (slow devices, L x 0.75, trimmed once at 25 C to 43.325 ns):
  - open-loop start-up 202.1 A at 25 C and 207.3 A at 125 C; stage 1 gave 201.9 / 206.2 / 210.7 A at 43.4 /
    44.4 / 45.4 ns, so no trim near the Vo target stays below 200 A;
  - at 25 C the handover runs away: 24 switch turn-offs above 200 A over 145.2-156.2 us, up to 278.4 A, 18 of them
    on phase 1 (stage 1: 282 A at 43.399 ns); it recovers before the step. At 125 C the handover peaks at 191.2 A;
  - post-step 190.8-198.7 A at 25 C, 194.7-202.8 A at 125 C (202.8 A at one of three positions).
- **The 25 C trim holds hot (criterion 4) at L0:**
  - nominal at 125 C: Vo(143.5 us) 1.040 V (25 C target 1.035; estimated 1.044), start-up / handover 162.8 /
    149.2 A, post-step 179.5 A;
  - slow corner at 125 C: Vo 1.057 V (25 C 1.029; +29 mV, three times the nominal shift, inside 0.99-1.17),
    start-up 171.4 A (25 C 188.8), post-step 179.1-183.5 A.
- Safety layer on every run: V_DS <= 33.8 V, 0 shoot-throughs and overlaps, all COMPLETED.
- Diagnostics: the S75 board also times poorly - late fires before the step 135 (25 C) / 91 (125 C) against 72-83
  on the slow L0 board, NEW 63-73 / 23-32.

## 1. Criteria (engineering layer)
| condition | positions | c1 start-up / handover <= 200 A | c2 post-step <= 200 A | c3 V_DS / shoot-through | c4 Vo(143.5) |
|---|---|---|---|---|---|
| N0 nominal L0, 125 C | 1 | PASS (162.8 / 149.2) | PASS (179.5) | PASS (32.6 V) | PASS (1.040) |
| S0 slow L0, 125 C | 3 | PASS (168.2 / 171.4) | PASS (179.1-183.5) | PASS (<= 32.2 V) | PASS (1.057) |
| S75 slow L x 0.75, 25 C | 3 | **FAIL** (202.1 / 278.4) | PASS (190.8-198.7) | PASS (33.8 V) | PASS (1.034) |
| S75 slow L x 0.75, 125 C | 3 | **FAIL** (207.3 / 191.2) | **FAIL at 1 of 3** (202.8) | PASS (<= 32.6 V) | PASS (1.071) |

Steps landed 0.15-0.88 of a period after phase 1's last low-side turn-off (read, not imposed). Predictions: N0 -
right; S0 Vo shift +5..+12 mV - wrong (+29), start-up 185-195 A - wrong (171, lower hot); S75 trim 43.5-45.5 ns -
just below (43.325); start-up / handover 210-225 A - the open loop lower (202-207), the 25 C handover higher (278);
post-step 195-205 A - right (191-203).

## 2. Decision (BOUNDARY Section 4)
- FINAL_SPEC: "L x 0.75 with nominal devices only". The slow corner's own inductance limit is open. Estimate from
  the open-loop start-up alone (188.8 A at L0, 202.1 A at 0.75 L0, linear): about 0.8 L0. The handover runaway at
  25 C is not in that estimate, so the limit needs runs (not done here).
- The start-up trim is a one-time 25 C calibration at L0: no temperature compensation needed up to 125 C on the
  nominal and slow boards. Below 25 C is not tested.

## 3. Limits
- One row (+4.8 V / 1 us); nominal and slow devices; ff with a small L not run (its start-ups are lower).
- N0 at 125 C was still settling at the step (Cs 1 -9.0 mV between 400-450 and 450-495 us); its post-step peak may
  carry that.
- The handover runaway depends sharply on the trim (282 A at 43.399 ns, none at 44.4 / 45.4 ns): one trim value
  per board was run in stage 2, as registered.
