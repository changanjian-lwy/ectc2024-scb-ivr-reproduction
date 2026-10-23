# A240 - a typical point of load: a 1 kW accelerator's repeated load steps on one module (RESULTS)
Boundary: 2002663 (plant option 54e8943). Runs from c480a06 and ae89e24 (nothing under src/ changed between them;
cosim_sources_modified False). Records: release records-a240. Analysis a240_analyze.py -> a240_summary.json; figure
a240_figure.py -> a240_accelerator_load.png. Plant V7, final configuration, one module (a quarter of P24 Fig. 6's
1 kW processor). From 300 to 600 us a constant-current load of 250 <-> 25 A (S75 at 125 C: 250 <-> 75 A), 1250 A/us,
50 % duty, applied at Co; 250 A to 700 us.

## 0. Verdict
- **The repeated load breaks the 200 A budget:** N75 at 100 / 200 kHz 210.3 / 203.3 A, N75 and S75 at 1 MHz 237.5 /
  221.9 A (2 / 1 / 13 / 5 events above 200 A). N0 stays under 200 A but reaches 196.5 / 195.7 A at 60 / 100 kHz
  against 161.5 A for one re-application (A237). **Every one is A143's turn-on-delay swing, set off again by the load:**
  in the 12 us before the peak the same phase (2 or 4) runs valleys of -72..-128 A and its turn-on delay falls to
  1.0-7.7 ns; it then turns on at +70..+112 A (figure, lower left: N75 at 100 kHz, phase 2's valley -92 A and delay
  1.3 ns at 526 us, then +110 A and 210 A at 531 us; record `cosim/run_p_N75_100k.json`). A deep valley alone does
  not decide it: N75 at 60 kHz reaches -105.8 A and its next valleys stay at +12 A (161.7 A), N0 at 200 kHz swings
  -67.7 -> +66 A (166.8 A). At 1 MHz the load period is about two switching periods.
- Vo never goes above 1.05 V (highest 1.0498 V). V_DS <= 33.7 V, rail 1 <= 12.79 V, and every row is back within 1 %
  at the end.
- **On N0, Vo dips to 0.941 / 0.937 V at 30 / 60 kHz** (single re-application -40.7 mV). At 30 kHz all 9
  re-applications dip -54..-59 mV, starting from the same state as at 10 kHz (Vo 1.000-1.005 V, Ton at the 128 floor),
  where the dip is -30 mV. **The difference is where phase 1's timed low-side edge sits.**
  - At 10 kHz, 50 us at 25 A moves the edge onto the light-load crossing (report error 0.1-0.3 ns in the last 5 us).
    After the re-application the edge comes first, so phase 1's valley climbs from -8 to +37 A in 1.5 us and there
    are 63 turn-ons in 3 us.
  - At 30 kHz the edge is still 13.9-14.0 ns late, as in A237's cw5_N0. Phase 1 turns on at -12 A every period, the
    period stretches from 0.19 to 0.37 us, and there are 37 turn-ons in 3 us (records `run_p_N0_10k.json` and
    `run_p_N0_30k.json` at 500 us).
- **The 10 kHz edge costs late fires** (figure, lower right): 118-190 per re-application on N0 (cw5_N0: 0), 62-134 on
  N75 (cw5_N75: 53) and 152-159 on S75 (c30_S75h: 162).
  - They fall in the first 20-40 % of the high half, while phase 1 reports early with +1..+77 A for about 30 us and
    relearns at most 2 ns per decision (T33). On N0 at 406-407 us phases 1 and 2 turn on at +17..+51 A.
  - No limit is touched: peaks <= 166.1 A, V_DS <= 30.9 V.
  - On S75, 30 kHz also gives 160 per re-application. From 60 kHz up they spread into the low halves.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| q0 | sources unmodified | pass (18 / 18) |
| q1 | whole run: peak <= 200 A, V_DS <= 40 V, no overlap or shoot-through | **miss 4 / 18**: N75 100k / 200k / 1M, S75h 1M (V_DS, overlaps and shoot-throughs pass) |
| q2 | every excursion above 1.05 V shorter than 25 us | pass (18 / 18), never above |
| q3 | Vo >= 0.95 V (our bound, no source) | **miss 2 / 18**: N0 30k 0.9408, 60k 0.9368 V |
| q4 | peak <= single re-application + 10 A | **miss 6 / 18**: N0 60k / 100k, N75 100k / 200k / 1M, S75h 1M |
| q5 | Vo within 1 % over the last 20 us | pass (18 / 18) |

## 2. Predictions
- Held: 10 kHz on N0 +49.7 / -30.0 mV (predicted +45..+50 / -30..-38); S75's dip -24.9 mV (-20..-25).
- Missed:
  - N75 at 10 kHz +42.4 / -23.6 mV (predicted +38..+42 / -25..-30); S75 +33.0 mV (+27..+31).
  - The largest dip: N0 at 60 kHz is 2.1x the 10 kHz one (predicted at most 1.3x).
  - 1 MHz is outside +-15 mV (N0 +20.6, N75 -22.7, S75 -23.8 mV).
  - Peaks are above the single-event references at 60 kHz-1 MHz.
  - Not every row passes.

## 3. Decision (Section 4 of the boundary)
- q1 / q4 miss: a repetition effect exists. It is traced above and opens **controller item 10 (repeated load steps)**.
  The accelerator load is not covered for one module above 30 kHz (N75) or at 1 MHz.
- Fix candidates, none tested:
  - limit how far phases 2-4's turn-on delay may fall (A143's open candidate);
  - a rule for the first periods after skipping ends (the 10 kHz edge builds the current in 1.5 us but costs about
    30 us of hard turn-ons).
- q3 (N0 at 30-60 kHz, our own bound) is stated as a limit with its mechanism.

## 4. Limits
- One module; four modules not run. No package or die capacitance, so the steps act at Co, which is severe at 1 MHz.
  Our frequencies and 1250 A/us have no source for an accelerator's spectrum.
- Each row starts the train at 300 us; the peak's timing within the train varies (N75 200 kHz at 351 us, 100 kHz at
  531 us).
