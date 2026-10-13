# A210 - the minimum load on the other boards: the 4.0 ns lower Ton limit on N75 and S75 at 0 / 25 / 125 C (RESULTS)
Boundary: c380dd8. Records: release records-a210 (9 cosim records, logs). Analysis: a210_analyze.py ->
a210_summary.json. Runs from c380dd8, cosim_sources_modified False. Final configuration on plant V6 with
ton_min_ns = 4.0 ns (A208), one module; part of the 250 A load released at 300 us, run to 450 us.

## 0. Verdict
- **30 % of the load (75 A) is the lowest row that works on every board tested** (N0 in A208; N75 at 25 C; S75 at
  0, 25 and 125 C). The specification's minimum load per module is 30 %, tested.
- **Nominal 0.75 L0 (N75) stops at about 26 %.** 40 and 30 % work (register 7.81 / 5.06 ns). At 20 % the register
  sits at 4.0 ns, 65.0 A are delivered and Vo ends at 1.060 V; the switching stays clean. With the smaller
  inductance the same load needs a shorter on-time, so the limit binds earlier than on N0 (about 19 %).
- **Slow 0.75 L0 (S75) regulates at 30 and 20 % at the three temperatures, but it is lossy there, and at 20 % its
  high sides never finish turning on.**
  - Loss books at 30 %: 17.6 / 19.1 / 15.8 W at 25 / 0 / 125 C, which is 81.0 / 79.7 / 82.6 %; at 20 %: 15.8 /
    16.4 / 14.9 W, 76.0 / 75.3 / 77.0 %. High-side edges alone are 9.0-12.4 W: the module runs at 5.5-6.6 MHz and
    a slow device's edge costs more. N75 books 6.5 W at 30 % (92.0 %), N0 4.2 W (94.7 %, A208).
  - At 20 % the gate command is 18-20 ns (register 8.5-10.5 ns plus the 9.5 ns lead) and the slow gate needs about
    as long to turn on: in the last 20 us the gate model records no high-side turn-off of a conducting switch
    (none of about 530 on each of the three rows; at 30 % all of them; records cosim/run_r_S75_*_20.json). The switch is turned off while still
    turning on, at 31-37 A. Vo, valleys and late fires are normal, so the registered criteria pass. The plant has
    never been compared with LTspice in this regime. It is not counted as covered.
- **What the limit does and does not do.** Moving it opens the range from 70 % to 30 % on every board at no cost to
  the existing rows. It does not make light load efficient on slow boards: the frequency rises as the load falls.
  That part needs a mode that holds the frequency down, or fewer modules running (A211 measures what that saves).
- r1 passes on all nine rows: peak <= 182.0 A over the run (the 125 C handover), V_DS <= 31.1 V, 0 shoot-throughs.

## 1. Criteria
| row | r1 | r2 | r3 | r4 | Vo end | register at the end | MHz | delivered | loss books | Pout / (Pout + loss) | high-side turn-ons completed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| N75 25 C, 40 % | pass | pass | pass | pass | 1.0000 V | 7.81 ns | 4.73 | 100.0 A | 6.86 W | 93.6 % | all |
| N75 25 C, 30 % | pass | pass | pass | pass | 1.0000 | 5.06 | 5.56 | 75.0 | 6.52 | 92.0 % | all |
| N75 25 C, 20 % | pass | **miss** | **miss** | pass | 1.0601 | 4.00 (limit) | 6.29 | 65.0 | 6.31 | - | all |
| S75 25 C, 30 % | pass | pass | pass | pass | 0.9999 | 12.88-13.06 | 5.60 | 75.0 | 17.57 | 81.0 % | all |
| S75 25 C, 20 % | pass | pass | pass | pass | 0.9999 | 10.06 | 6.64 | 50.0 | 15.77 | 76.0 % | **none** |
| S75 0 C, 30 % | pass | pass | pass | pass | 1.0001 | 13.22 | 5.76 | 75.0 | 19.12 | 79.7 % | all |
| S75 0 C, 20 % | pass | pass | pass | pass | 1.0000 | 10.34-10.69 | 6.64 | 50.0 | 16.43 | 75.3 % | **none** |
| S75 125 C, 30 % | pass | pass | pass | pass | 0.9998 | 11.41-11.59 | 5.54 | 75.0 | 15.79 | 82.6 % | all |
| S75 125 C, 20 % | pass | pass | pass | pass | 1.0000 | 8.34-8.69 | 6.60 | 50.0 | 14.92 | 77.0 % | **none** |
- "High-side turn-ons completed" was not a registered criterion; it was added to the analysis after the runs, when
  one row had no high-side turn-off records at its end (hs_incomplete_share in the summary).
- Vo after the release: 0.982..1.041 V on S75, 0.986..1.036 V on N75 at 40 and 30 %.
- Lowest working row by the registered criteria: N75 30 %, S75 20 % at each temperature.

## 2. Predictions
- Held: the registers (N75 8.3 / 5.8 ns predicted: 7.81 / 5.06; S75 13-14 and 10-11.5 ns: 11.4-13.2 and 8.5-10.5);
  N75 works at 40 and 30 % and not at 20 %, with clean switching; S75 works at 30 % at the three temperatures; r1.
- Missed: the loss on slow boards, by a factor of three (5-7 W predicted at 30 %: 15.8-19.1 W), and N75's
  (4-5 W: 6.5 W): I did not carry the slow edge's energy to the higher frequency. S75 at 20 % does not fail the
  registered criteria as predicted; it fails in a way they do not see. N75 at 20 % delivers 65 A, not 57, and ends
  at 1.060 V, not 1.02-1.04. r3 misses on N75's 20 % row only.

## 3. Limits
- Two or three loads per board, an instantaneous release, 150 us; N75 at 25 C only. The loss books leave out the
  gate drive, which also grows with the frequency.
- The plant against LTspice (A206) covers nominal devices at 25 C with complete on-pulses; slow devices and a
  switch turned off during its turn-on are outside it.
- Fast devices, L x 1.3, -40 C and four modules are not run.
