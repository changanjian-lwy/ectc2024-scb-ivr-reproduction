# A194 - random stimuli on the final plant (RESULTS)
Boundary: 7ca3b0d. Records: release records-a194 (36 runs, logs). Analysis: a194_analyze.py -> a194_summary.json;
draws in draws.json. Plant V5, one module, t_il 1.0 ns, the A188 start-up with A190's cold trims, lead 9.5 ns on
slow boards and 8 ns elsewhere. cosim_sources_modified False on all 36. The runs started at four commits (7ca3b0d
6, d38a4d2 7, b4292a7 9, 71f1777 14) whose differences are documents and experiment directories only (git diff on
src/ is empty).

## 0. Verdict
- **36 of 36 draws pass c1-c5.** Every run COMPLETED with 0 shoot-throughs and 0 overlaps.
- Largest values over the 36 runs:
  - peak current 184.6 A (limit 200): S80 at 0 C, +2.24 V over 10.2 us, 47 us after the handover (r02);
  - handover 184.5 A on S75 at 125 C and 182.0 A on S80 at 125 C; at most 166.4 A on every other board and
    temperature; start-up at most 139.0 A;
  - V_DS 33.9 V (limit 40): N13 at -40 C, +4.75 V over 1.9 us (r34);
  - Vo within 13.1 mV of 1 V from 20 us after the handover (limit 50 mV);
  - 33 runs never leave the 1 % band; the other three are back after 3.1 / 7.9 / 10.3 us (limit 60 us).
- **By the decision rule the coverage file now states "36 random draws inside the stated windows pass on V5, one
  module".** The draws found nothing above the designed rows: the worst known case stays S75, +4.8 V / 1 us
  (197.8 A at 0 C, A193).
- **What the draws did not reach** (Section 3): the first 37 us after the handover, and a rising step of 4 V or
  more on a slow board with a reduced inductance.
- 36 of 36 is not zero risk: under this draw distribution it bounds the miss rate at about 8 % (95 %).
- Found while checking these records: A191's 125 C slow rows ran with A186's handover request (1.03 V), not the
  adopted 1.045 V. Rerun registered as A197.

## 1. Criteria, by group (largest value in the group)
| group | draws | start / hand (A) | after the event (A) | V_DS (V) | Vo from 1 V (mV) | back in 1 % (us) | late fires after / NEW events |
|---|---|---|---|---|---|---|---|
| slow, -40 C | 5 | 135.5 / 158.8 | 180.3 | 30.5 | 13.1 | 10.3 | 0-76 / 7-165 |
| slow, 0 C | 3 | 132.6 / 165.9 | 184.6 | 29.9 | 11.7 | 3.1 | 0-21 / 7-38 |
| slow, 25 C | 6 | 135.7 / 164.1 | 165.1 | 28.4 | 8.5 | 0 | 0-21 / 5-45 |
| slow, 125 C | 6 | 139.0 / 184.5 | 173.0 | 29.6 | 11.3 | 0 | 0 / 0-55 |
| nominal, -40 C | 1 | 116.6 / 152.6 | 175.5 | 33.9 | 10.5 | 0 | 0 / 0 |
| nominal, 0 C | 4 | 136.5 / 149.3 | 181.6 | 30.1 | 9.0 | 0 | 0 / 0 |
| nominal, 25 C | 3 | 136.6 / 165.4 | 183.6 | 31.5 | 10.6 | 0 | 0 / 0 |
| nominal, 125 C | 3 | 125.8 / 158.8 | 174.5 | 30.2 | 13.1 | 7.9 | 0 / 0-3 |
| fast, 25 C | 2 | 125.0 / 166.4 | 148.7 | 32.3 | 10.5 | 0 | 0 / 0 |
| fast, 125 C | 3 | 125.2 / 148.8 | 173.6 | 30.8 | 8.3 | 0 | 0 / 0-4 |
| **all** | 36 | 139.0 / 184.5 | 184.6 | 33.9 | 13.1 | 10.3 | 0-76 / 0-165 |
- By event: rising line step 17 draws (after the event at most 184.6 A), falling up to 4.8 V 9 (173.6 A), falling
  4.8-8 V 4 (163.8 A), load step 6 (173.0 A). By instant: 14 early draws, 37.2-145.3 us after the handover
  (184.6 A); 22 at 500 us (183.6 A).
- Diagnostic layer, not judged: nominal and fast boards (16 draws) have no late fire after the event and 0-4 NEW
  events. Slow boards have up to 76 late fires (S0, -40 C, +4.15 V over 7.1 us, early) and up to 165 NEW events,
  the largest counts on S75 at -40 C (150, 165), as A193 found. The interlock held on 12 of the 20 slow draws
  (all six at 125 C) and on no other board.

## 2. Predictions
- Held: c1 and c3 on all 36; c2 0-3 misses (0); c4 on all; c5 0-2 misses (0).
- Not tested by the draws: the combination named as most exposed (S75 / S80 after a rising step near 4.8 V) and the
  lead ramp (Section 3).

## 3. Limits
- **No draw falls in the first 37 us after the handover.** The earliest event is 37.2 us after mode P's entry
  (r09). The BOUNDARY drew 14 instants from 146-300 us to cover the 20 us lead ramp and the settling; none landed
  there (chance about 1 in 20). The decision rule does not extend the draws. So "a step shortly after the
  handover", where A142's defect was on V0, is covered from 37 us on, not from 2 us.
- **No large rising step on a slow board with a reduced inductance.** Rising draws on S75 / S80 are +1.3..+2.7 V.
  The largest rising steps are on S0 (+4.15 V, -40 C, 180.3 A), N0 (+4.60 V, 183.6 A) and N13 (+4.75 V, 175.5 A).
- One module, one event per run, 36 draws; L x 0.7, +8 V steps, fast devices below 25 C and four modules are
  outside the windows (BOUNDARY Section 1).
