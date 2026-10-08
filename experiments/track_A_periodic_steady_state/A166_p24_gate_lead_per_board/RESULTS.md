# A166 - an interlock-safe lead per board (RESULTS)
Boundary: 1ce1195. Records: release records-a166 (13 runs). Outputs: a166_summary.json (a166_analyze.py, side by side
with A164 / A165), leads.json. The runs span commits 1ce1195-06a69fa. The only source change between them is the
bridge's lead_ramp_us option (3c745f4), off here and bit-identical when off. ss_l_m80_10us was restarted once
(a166_rerun.log): its first start overlapped an uncommitted edit.

## 0. Verdict
- **FAIL as registered (3 of 12 rows pass, four modules miss). Not adopted.**
  - The rule does what it was built for: 0 shoot-throughs on every row. The slow corner commanded its high side
    ahead of the low side's turn-off 1669-1916 times per run.
  - But a lead of the board's shortest delay - 1 ns is too small for the transients. The nominal lead is 1.31 ns,
    while hard turn-ons after a rising step take ~6 ns on a nominal board and up to 16.6 ns on the slow one.
- **Late fires after rising line steps (lead 8 ns -> per board), per row:**
  | row | A164 / A165, 8 ns | A166, per board |
  |---|---|---|
  | nominal +4.8 V / 1 us | 0 | 24 |
  | slew4 | 0 | 37 |
  | hot | 0 | 19 |
  | four modules | 0 | 85, 2 NEW |
  | slow corner | ~160 | 193-219, NEW 10-24 |
- **L x 0.7 after +4.8 V / 1 us: 207.8 A physical, 192.0 A command-time** (A164: 192.1 / 177.2 A), with 71 late
  fires and 2 NEW. The handover is 191.5 A, as
  A165. Mode S still peaks at 202.5 A.
- **Where it holds:** nominal load step, L x 1.3, ff +4.8 V (38.4 V). The ff -8 V / 10 us row misses as in A164 / A165
  (Vo +29.1 mV), and its command-time peak is 170.5 A against 170.3 A allowed.
- **Reading.** The delay that matters is the one of the edge being commanded. A hard turn-on after a step takes
  several times the valley turn-on's delay, so a bound set by the shortest delay leaves the hard edges uncovered. A
  safe and sufficient lead would follow the edge's own V_DS. With the frozen controller the spec takes A167's ramped
  8 ns lead, and names the interlock as a requirement on the controller.

## 1. Criteria
| rows | 1 V_DS | 2 start / Vo | 3 post / late / NEW | 4 Vo | misses |
|---|---|---|---|---|---|
| nom (5) | 5/5 | 4/5 | 2/5 | 5/5 | L07 mode S 202.5 A, post 207.8 / 192.0 A, late 71, NEW 2; l_p48 late 24; slew4 late 37 |
| ff (2) | 2/2 | 2/2 | 1/2 | 1/2 | l_m80 cmd 170.5 A (170.3), Vo +29.1 mV |
| ss (4) | 4/4 | 4/4 | 0/4 | 4/4 | late 124-343, NEW 10-24 |
| hot (1) | 1/1 | 1/1 | 0/1 | 1/1 | late 19 |
| four modules | 33.8 V | 162.9 A | miss: late 85, NEW 2 | - | |

## 2. Limits
- The leads come from 150 us calibration start-ups, whose shortest delays were 0.1-0.4 ns below the full runs'
  (conservative).
- Otherwise as A164 / A165.
