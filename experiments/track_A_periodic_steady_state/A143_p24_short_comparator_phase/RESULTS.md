# A143 - shortened mode-P comparator phase (RESULTS)
Boundary: 9a14b08 (amended 3cc0e55, records_last, before any result). Records: a143_summary_1.json, a143_summary_2_k4.json
(`a143_analyze.py 1`, `a143_analyze.py 2 4`); raw records (106 runs) in GitHub release records-a143. Stage 1 16:14-16:41
(64 runs), stage 2 16:43-17:16 (42 runs incl. 4 four-module), 10 jobs.

## 0. Verdict
- **Pass, 6/6, at lo_learn K = 4** (smallest K passing stage 1; 16 and 64 passed too). Phase 1 goes timed 1.1-1.9 us
  after the handover (145.1-145.9 us at L x 0.7-1.3) instead of at 507-814 us.
- **A142's rows** (step at 295 us, now in timed mode): z104 351 -> 196 A, R +4.8 V at 4 / 5 us 254 / 247 -> 176 /
  176 A, Q +6.4 V at 4 us 388 -> 186 A; phase 2-4 low-offs >= 0 A in the 60 us after the step 21-75 -> 0; Vo never
  outside 2 %. K 16 / 64 give the same within 2 A.
- **Residual window (g2, step at 146 / 160 us, nominal):** K 4: 177-194 A on +4.8 / +6.4 V; K 16: 213 A on +6.4 V at
  146 us (2 NEW hits, 12.7 us outside 2 %); K 64 and K 1024: 380 / 394 A on +6.4 V at 146 us.
- **The handover improves:** L x 0.7 m3n handover peak 182 -> 146 A, m1n 203 -> 182 A; L x 1.0 m3n late fires 11 -> 1;
  L x 1.3 rail 1 12.81 -> 12.38 V, Vo excursion 3.06 -> 2.28 %. The comparator phase was part of the handover
  transient. L x 0.7's start-up peaks (202-217 A) and Vo excursion (8.6-18 %) are mode S's and do not change.
- **No side effect elsewhere:** A129's matrix at L x 1.0 plus s_p62 / l_p48 at L x 0.7 / 1.3 (19 rows): -1.7 ... +4.8 A
  vs K 1024, max 191.4 A (L x 1.3 l_p48_1us). Four modules (C12 rows): n0 163.4 (163.4), m3n 163.6 (179.3) with late
  fires 4 (108), s_p62 177.7 (177.9), l_p48_1us 184.7 (180.1) A; rail 1 <= 12.41 V, 0 floor-first duplicates.
- **One design shift:** the residual-current trim learns only in comparator turn-offs and starts at 0. At K 4 it stays at
  4 codes (+1 A) instead of converging to 22 / 14 / 12 (L x 0.7 / 1.0 / 1.3), so the floor (i_target + trim - 2 A) turns
  off 4.5 / 2.5 / 2 A deeper than A118 intended. Steady state at 1400 us is unchanged (dlo within 5 LSB, same Ton,
  dt_pred, peaks 142.3-144.1 A, valleys -16.6 ... -15.6 A); the floor-sensitive falling and load rows move -1.7 ... +3.9 A.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | g1 at K: R <= 200 A, z104 / Q <= 210 A, no phase 2-4 low-off >= 0 A, <= 5 us outside 2 % | pass: 176 / 176 / 196 / 186 A, 0, 0 us |
| 2 | g3 at K vs K 1024: peaks <= +7 A, late <= +5, Vo <= +0.2 points, rail 1 <= +0.3 V | pass: every metric equal or lower |
| 3 | COMPLETED, 0 overlaps, 0 floor-first, 0 NEW, settles (g1, g3, g4, g5) | pass (K1 / K4 known classes only) |
| 4 | identity n0 and l_p48_1us at K 1024 = A141 records | pass: bit for bit (last 6000 events, sections, ipk, late) |
| 5 | g4 at K vs K 1024: <= +7 A, <= 200 A, late <= +5 | pass: max +4.8 A, max 191.4 A, late max +2 |
| 6 | g5 at K vs C12: <= +7 A, late <= +5, rail 1 gate, 0 floor-first | pass: max +4.6 A, rail 1 12.41 V |

Predictions: g1 within the registered bands except the R rows (176 A, below 185-200: the timed-mode step lands with
phase 1's valley taking the error, as in P2). t_lo_timed as predicted (145.5 / 151.4 / 175.7 us at L x 1.0). g2 wrong
in part: +4.8 V at 146 / 160 us does not oscillate even at K 1024 (195-198 A; the slew window of A142 is narrow), +6.4 V
does (394 / 231 A); K 4 / 16 bounds held (+4.8 V <= 194 A, +6.4 V <= 213 A). g3, g4, g5 within noise or better.

## 2. Limits
- The fix removes the window; it does not fix comparator-mode control. Mechanism (dt_pred collapse after deep phase 2-4
  valleys) is read from the records; D63 lacks the dt_pred block and the fall limit was not tested.
- Residual: steps that start within ~2 us of the handover (4 periods; g2 at 146 us clean at K 4). A139's envelope and
  A142's random strata were not rerun at K 4 (19 + 4 + 4 regression rows only). A142's oracles start at mode P + 20 us,
  so the switch itself (~145.5 us) is covered by criterion 2's metrics only.
- The floor sits 2-4.5 A deeper (trim not converged). A trim seed (bridge trim_init, now 0) would restore A118's level.
