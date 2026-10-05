# A141 - the floor's late report: A140's duplicate phase-1 turn-on (RESULTS)
Boundary: 007c8b8, amended in 04d35a8 (v2 code, all runs repeated). Records (local): `cosim/run_*.json` (20, v2),
`cosim/run_v1_F_l_p48_{1,5}us.json` (v1). `a141_summary.json` (v2), `a141_summary_v1.json` (v1), `a141_analyze.py`.

## 0. Verdict
1. **The duplicate is an RTL defect, not a bridge artefact.** In all 140 A140 duplicates the floor fires in the window
   before the RTL commits its timed edge; the floor's report needs two windows (synchroniser) and scb_phase took it only
   in LOW, so it was dropped in UP. The power stage turns on at the floor's edge, Ton counts from the RTL's later one
   (+0-6 ns). The bridge executes A81's hardware partition (async latch + delay line, 2-FF report) as specified.
2. **Fix (cfg floor_late 1, v2):** a late report in UP sets t_on = a_tlo + dt_pred and drops the pending turn-on; in
   HIGH an earlier floor turn-on moves t_on; t_lo keeps the clocked edge. Criteria 1-3 pass: 0 floor-first duplicates
   in 18 runs (references: 1-25 per row); every peak <= reference nodup + 1.9 A. No floor-then-clocked pair remains, so
   the HIGH path never acted (as predicted, dt_pred ~9.3 ns > two windows).
3. **L x 0.7 rising, adopted design + fix:** +4.8 V 185.2 / 188.6 / 191.6 / 184.6-185.7 (4 positions) / 179.3 A at
   1 / 5 / 10 / 20 / 40 us (were 213.4 A at 10 us, 192.1-208.9 A at 20 us). +8 V 210.1 A at 20 us (was 230.8),
   182.1 A at 50 us (was 203.7). L0 / L x 1.3 A124 rising rows, two falling rows: unchanged within +1.6 A.
4. **Four modules:** l_p48_1us 180.1 A, l_p48_5us 177.7 A (C10 180.6 / 179.3; module 3's spike gone). A 150 us replay
   shows C10's handover has one floor-first duplicate in every slave at 145.1 us (mode P entry, 144 us); the fix removes
   it, so four-module rows differ from C10 from 145.5 us on.
5. **v1 finding:** v1 also set t_lo = a_tlo. Single module was fine, four modules were not (l_p48_1us 357.5 A): the
   master's t_lo1 is the slaves' ext_ref, it changed twice in a late-report cycle, and a slave whose floor had consumed
   that reference (skip_pend) fired its slot a cycle early (+90 A at turn-off). Rule: t_lo1 changes once per cycle.
6. **Decision (Section 4):** floor_late 1 joins the adopted single-module design. L x 0.7 rising spec: +4.8 V allowed
   at 1-40 us (<= 191.6 A); +8 V forbidden at 20 us (210.1 A), allowed at 50 us (182.1 A). Four modules: adopted
   provisionally - the option changes every four-module row from the handover on and only two rows are checked (C12).

## 1. Criteria (v2)
| # | criterion | result |
|---|---|---|
| 1 | identity: I0 = A140 B_L070_p4.8_s10.0, I1 (floor_late 1) = C10 s100_n0 | PASS, both bit for bit |
| 2 | 0 floor-first duplicate turn-ons, every F run and module | PASS, 0 in 18 runs |
| 3 | peak <= reference nodup + 2 A | PASS, -6.0 to +1.9 A (max F_L070_p8.0_s50.0) |

Single-module rows replay their reference bit for bit up to one section after its first floor-first duplicate.
v1 against the same criteria: 1, 2 pass; 3 fails on four modules (+176.9 / +12.9 A) and on two rows (+2.5, +2.1 A).

## 2. Limits
- Transient late fires move by -2 to +4 per single-module run (e.g. +8 V 20 us 17 vs 13); peaks are unaffected.
- Four-module adoption rests on two rows; C10's 18-row matrix and C11's L x 1.2 / 1.3 rows are not rerun (next: C12).
- Not rerun: L x 0.7 falling rows and the load rows (no floor-first event on any single-module record; I1 shows the
  option is inert without a late report).
