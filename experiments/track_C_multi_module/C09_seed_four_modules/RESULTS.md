# C09 - the four-module final design with the adopted vff setting (RESULTS)
Boundary: a6f34bf (contingency cfg f64447b). Records: cosim/run_*.json (18 rows, c06al_s_m25, c06al9_l_p48_5us);
c09_summary.json.

## 0. Verdict
- **Not adopted: the restart (seed 1) does not fix the four-module handover; the slaves seed at the wrong value.**
  The master enters mode P at 144.0 us with Vo 37 mV high; its first ADC sample kicks Ton 1136 -> 683 LSB. The slaves
  enter 30-80 ns later, when the broadcast Ton is already 683, so their restart seeds Ton's low-pass at 683-722
  (the master's took the value before the kick, judging by its balanced rails): their phase-1 cap (1.25 x low-pass x rss / rail) sits near 0.7 of the Ton the load
  needs, phase 1 under-delivers, rail 1 rises (slaves 13.8-15.4 V, master 12.6-13.0 V), which lowers the cap further
  (A134's lock, held for ~35 us until the low-pass catches up). The master's loop drives Ton to 1582-1665 (C06
  1247-1419), whole-run peaks 192.5-203.5 A (m1n 201.8, m3n 203.5 > 200), handover late fires (n0 10, m3n 415).
  C08 (no restart) locks all four modules this way (rail 1 14.6-15.2 V); the restart fixes the master only.
  m3p is milder (slaves 12.7 V, 163.3 A, no late fire).
- After the handover the design is C06's: every peak from 242 us to the step <= 147.5 A; post-step peaks within
  -1.4..+5.4 A of C06 on 8 of 9 stepped rows; no overlap, the modules stay period-locked.
- **C08's s_m25 +7.3 A was the step's offset:** C06's design with the step at C08's offset gives 152.7 A (C08 153.4).
- **C08's m3n sd was the voltage loop's ADC limit cycle** (traced before the runs, BOUNDARY Section 1); C09's m3n shows
  it again (Ton 1203-1214, Vo -0.263 / +0.287 mV), so it is classified as such, not as a new failure.
- l_p48_5us: 184.6 vs C06 175.5 A (+9.1); C06 at C09's offset gives 176.1 A, so it is not the offset. It is one
  period: slave 1's phase 1, 32.12 us after the step, records two turn-ons (0.6 A / 1.8 V, then 22.1 A / 0 V); every
  other peak is <= 176.5 A, as C06 / C08 (176.1-176.2). Not traced; C10 checks whether it recurs.
- Next: C10 - seed every module's low-pass from a value that does not depend on its entry time (the Ton before mode
  P), identity-check the single module, rerun these 18 rows.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | hard / no new failure | **fail**: whole-run peak 201.8 (m1n), 203.5 A (m3n); late_fires new on 11 rows (handover); sd_band on m3n = limit cycle (rule) |
| 2 | late fires <= 1.5 x C06 + 6 | **fail** on 16 rows (n0 10 vs 0, m1n 90 vs 19, m3n 415 vs 68; m1p 1 and m3p 0 pass) |
| 3 | post-step peaks within 7 A of C06 | **fail** on l_p48_5us (+8.5 A against C06 at the same offset, 176.1 A; one period); others -1.4..+5.4 A |
| 4 | c06al_s_m25 within 2 A of C08's 153.4 A | pass (152.7 A, offset 81.3 ns) |
Predictions: late fires and start-up peaks back to C06's - wrong (the slaves' seed); post-step peaks within the
2-7 A floor - right on 8 of 9 rows; c06al_s_m25 151-156 A - right.

## 2. Limits
- The seed values (683-722) are read from the slaves' sections (the broadcast Ton at their entry), not from an RTL
  probe of scb_vff's tlp; the lock is read from the rails in the sections (the event records start at 242 us).
- The ADC limit cycle's occurrence depends on where the start-up leaves Vo in the code; C10 may see it or not.
