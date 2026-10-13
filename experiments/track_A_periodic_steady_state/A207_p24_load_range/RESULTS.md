# A207 - the load range of the final configuration: where one module stops regulating (RESULTS)
Boundary: a58bfb2. Records: release records-a207 (8 cosim records, logs). Analysis: a207_analyze.py ->
a207_summary.json; figure a207_vo.png (a207_figure.py, drawn from the records). Runs from a58bfb2,
cosim_sources_modified False. Final configuration, plant V6 (low sides 0.3 ohm, switches at the datasheet maximum,
A206's trim), board N0, 25 C, one module; part of the 250 A load released at 300 us, run to 450 us.

## 0. Verdict
- **One module regulates down to about 174 A, 70 % of its load. Below that the output voltage runs away upward.**
  The rows at 100 % (A206's run) and 75 % pass. At 60 / 55 / 50 / 45 / 40 / 30 / 10 % Vo ends at
  1.09 / 1.14 / 1.19 / 1.23 / 1.28 / 1.37 / 1.56 V (figure a207_vo.png; records cosim/run_f60.json .. run_f10.json).
- **Cause, read from the controller's own register** (sections "ton_lsb"): Ton is 32.85 ns at 250 A and 24.09 ns at
  187.5 A. Its lower limit is 22.25 ns: bridge.py sets cfg_ton_min to half of cfg ton_ns, and the final
  configuration has ton_ns = 44.48 ns. On every failing row the register reaches the limit 1.4-2.8 us after the
  release and stays there. At the limit the module still delivers 164-174 A; the surplus charges the output until
  the 4 mOhm load takes it. Linear in the register, the limit is reached at 174.3 A (69.7 %).
- **How it got there** (arithmetic on the configurations, not a run): in A124 the limit was 17.75 ns against an
  on-time of 38.6 ns, and D63 puts that design's floor near 40 %. Since then ton_ns grew to 44.48 ns as the
  handover's loop seed (A185), which moved the limit with it, and with the 8 ns lead (A167) and the gate delays
  the register sits 5.7 ns below the on-time D63 needs for the same load. No run of the project had less than 75 %
  of the load on a module, so neither showed.
- **It is a regulation failure, not a current or voltage-stress one**: r1 passes on all eight rows (peak after the
  release <= 146.6 A, V_DS <= 32.9 V, 0 shoot-throughs, 0 forced edges).
- **Inside the range**: 75 % runs at 2.42 MHz with 12.39 W of semiconductor loss (93.8 % as Pout / (Pout + loss));
  100 % at 1.96 MHz with 20.15 W (92.5 %).
- **LSCB's shedding, at the level where P24 can use it** (whole modules; a composition for four equal modules, not
  a run). With the module's range at 174-250 A: all four on cover 697-1000 A only. Shedding modules covers
  174-250 A with one, 349-500 A with two, 523-750 A with three: the range becomes 17-100 % with gaps at 250-349 A
  and 500-523 A. No gaps needs a module's own range down to 50 %. Shedding alone does not close the problem.
- LSCB's other feature, all inductors energized at once in a load transient, was not run: with 2.93 nH the present
  topology's own slew bound for a 62.5 A step is 0.15 mV, against 12-15 mV measured in closed loop (+-62.5 A,
  reports/MIHAI_SUMMARY_2026-10-06). The loop's one sample per period sets the excursion, not the inductors.

## 1. Criteria
| row | load left | r1 | r2 | Vo at the end | Vo after the release | Ton register | frequency | delivered | loss books |
|---|---|---|---|---|---|---|---|---|---|
| A206 | 250 A | pass | pass | 1.0000 V | - | 32.85 ns | 1.96 MHz | 250.0 A | 20.15 W |
| f75 | 187.5 A | pass | pass | 1.0000 V | 0.9961..1.0162 V | 24.09 ns | 2.42 MHz | 187.5 A | 12.39 W |
| f60 | 150 A | pass | **miss** | 1.0945 V | 0.9885..1.0978 V | 22.25 ns (limit) | 2.76 MHz | 173.5 A | 11.13 W |
| f55 | 137.5 A | pass | **miss** | 1.1423 V | 0.9781..1.1458 V | limit | 2.87 MHz | 173.0 A | 11.24 W |
| f50 | 125 A | pass | **miss** | 1.1872 V | up to 1.1890 V | limit | 2.97 MHz | 171.7 A | 11.24 W |
| f45 | 112.5 A | pass | **miss** | 1.2334 V | up to 1.2348 V | limit | 3.08 MHz | 170.8 A | 11.27 W |
| f40 | 100 A | pass | **miss** | 1.2797 V | up to 1.2808 V | limit | 3.18 MHz | 169.9 A | 11.25 W |
| f30 | 75 A | pass | **miss** | 1.3731 V | up to 1.3749 V | limit | 3.40 MHz | 168.2 A | 11.40 W |
| f10 | 25 A | pass | **miss** | 1.5562 V | up to 1.5562 V | limit | 3.81 MHz | 164.1 A | 11.41 W |
- "Delivered" = Vo / 4 mOhm minus the released current, mean of the last 10 us. The gate command is the register
  plus the 8 ns lead (30.25 ns at the limit).
- Lowest passing row: 75 %. The floor lies between 60 and 75 %; 174 A is its estimate from two passing rows.
- On seven rows Vo falls back by 20-67 mV between about 7 and 15 us after the release before rising again (a
  pause at 10 %; figure). The period is 30-100 ns longer there than at the end, and at 60 and 55 % the register
  leaves the limit for about 7 us. Why the period stretches was not traced.

## 2. Predictions
- Held: r1 on every row; the 75 % row's overshoot (16.2 mV; D63 16.8 mV); efficiency 92.5-94 % inside the range.
- Missed: the floor. D63 gave 50-55 %. My correction for the cosim went the wrong way: I read the full-load gate
  command (40.85 ns) as the register and predicted 45-50 %. The command contains the 8 ns lead; the register is
  32.85 ns, 5.7 ns below D63's on-time, so the limit binds at a higher load, not a lower one. With that offset
  D63 gives 69 % (post hoc). Also missed: the failing rows' Vo (1.28 V at 40 % against 1.06-1.12 V) and the loss
  at 75 % (12.39 W against 13-14.5 W).

## 3. Limits
- One board (N0, nominal devices, 25 C), an instantaneous release, 150 us. Two rows bracket the floor.
- How high Vo goes depends on the load model (a 4 mOhm resistor plus a current fed back); that it goes does not.
- Four modules are composed from one module's rows with equal sharing and idle modules at 0 W; no four-module run,
  and the frozen controller has no way to shed or re-enter a module.
- Not run: start-up into a light load, slow load changes, other boards and temperatures, loads above 250 A.

## 4. What follows (decision rule)
- The coverage file states the tested range and the specification gains a minimum-load line (done with this commit).
- A remedy changes the controller's configuration or the controller: the user's decision. Candidates, cheapest
  first: (1) give cfg_ton_min its own cfg value instead of half the loop seed (bridge only, default unchanged, RTL
  untouched) and find where the gate itself limits (a high side needs 7-17 ns through 3.0 ohm to turn on);
  (2) a light-load mode; (3) shedding whole modules as LSCB sheds phases, which needs (1) to reach 50 % first.
