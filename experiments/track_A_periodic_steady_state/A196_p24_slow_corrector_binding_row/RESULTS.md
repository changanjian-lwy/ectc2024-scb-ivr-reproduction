# A196 - the slow boards' corrector setting on the binding row (RESULTS)
Boundary: b4292a7. Records: release records-a196 (6 runs, logs). Analysis: a196_analyze.py -> a196_summary.json.
Code b4292a7, plant V5, t_il 1.0 ns, A188 start-up (A190's cold trim at 0 C), lead 9.5 ns, board S75 (slow devices,
L x 0.75), +4.8 V / 1 us at 500 us + k T / 3. Corrector: dt_step_ns 0.0625, err_shift 2. cosim_sources_modified False.
References: A193 (0 C) and A192 (25 C), same cfgs but for the two registers.

## 0. Verdict
- **Not adopted: c4 fails, so by the decision rule this line stops.** On S75 the setting cuts the valley's
  cycle-to-cycle change from 4.7-5.9 A to 0.84-1.40 A, but not to 1.0 A on every phase (0 C: 1.08-1.40 A on all
  four; 25 C: 1.17 / 1.26 A on phases 2-3). c1-c3 pass.
- **c5 passes: the worst post-step peak falls at both temperatures.** 0 C: 194.4 A against 197.8 A. 25 C: 194.7 A
  against 197.1 A. Every position is lower, by 0.3-4.3 A. On these six runs the margin is 5.3 A instead of 2.2 A.
- **The price is at the handover, and it is larger than the gain: 177.5-177.7 A against 150.7-154.0 A
  (+23.5..+27.0 A).** It comes 0.5-3.4 us after mode P's entry on phases 3-4 (10-15 turn-offs above 165 A; the
  reference has none). Predicted 156-162 A from S0's +6.0 A, so the prediction missed by 15 A.
  - Still below 200 A here. Not run at 125 C, where the slow boards' handover is already 188.5 A (S75) and 185.4 A
    (S80) with the adopted setting (A191). Those peaks come later (+17..+19 us, phase 1), so the two effects need
    not add, but 11.5 A is what is left.
- **So the two halves of the run want different corrector settings.** The handover needs the fast late correction
  (the period jumps there); the steady state and the step after it do better with the slow one. One per-class
  value cannot give both. A setting that changes after the handover is a host register write (test bench change,
  no RTL) or a controller change; neither is run here.
- Other effects after the step (diagnostics): oracle NEW events fall to 10-19 per run (reference 37-79). Late fires
  rise to 69-174 (reference 45-106; lower on one run of six). The Vo dip is unchanged at 0 C (-10.5..-14.8 against
  -13.2..-14.5 mV) and smaller at 25 C (-10.6..-11.3 against -13.8..-17.5 mV). Before the step, late fires fall
  to 7 and 2 (reference 35 and 43).

## 1. Criteria
| run | start / hand (A) | post-step (A), reference | V_DS (V) | valley change, phases 1-4 (A) | late / NEW after step, reference | Vo dip (mV) / back within 1 % (us), reference |
|---|---|---|---|---|---|---|
| 0 C, k 0 | 135.7 / 177.7 | 192.8 (194.5) | 32.5 | 1.08 / 1.27 / 1.40 / 1.09 | 135 / 17 (91 / 79) | -14.8 / 16.7 (-13.5 / 14.0) |
| 0 C, k 1 | same | 194.4 (194.7) | 32.1 | same | 132 / 15 (106 / 58) | -14.6 / 14.2 (-14.5 / 35.2) |
| 0 C, k 2 | same | 193.5 (197.8) | 31.3 | same | 166 / 19 (103 / 64) | -10.5 / 20.6 (-13.2 / 22.1) |
| 25 C, k 0 | 135.7 / 177.5 | 193.1 (196.1) | 30.9 | 0.84 / 1.17 / 1.26 / 0.98 | 174 / 13 (51 / 44) | -11.3 / 10.4 (-17.5 / 37.0) |
| 25 C, k 1 | same | 194.7 (195.8) | 30.9 | same | 69 / 10 (92 / 37) | -11.2 / 10.2 (-13.8 / 20.9) |
| 25 C, k 2 | same | 192.8 (197.1) | 30.9 | same | 143 / 17 (45 / 37) | -10.6 / 23.9 (-16.1 / 36.2) |
- c1 (COMPLETED, 0 shoot-throughs, 0 overlaps, V_DS <= 40 V): pass, 6 / 6.
- c2 (whole-run peak <= 200 A): pass, largest 194.7 A (after the step in every run).
- c3 (Vo <= 1.05 V over 0-300 us): pass, 1.0345 V, as the reference.
- c4 (valley change <= 1.0 A on every phase, 459-499 us): **fail** at both temperatures.
- c5 (worst post-step <= 195.5 A and no position more than 1.0 A above its reference): pass at both.

## 2. Predictions
- Held: c1-c3; the worst post-step peak in 193-199 A; 0.5-1.5 A of orbit left at 0 C.
- Missed: the handover (177.5-177.7 A against 156-162 A); c4 at 25 C (predicted to pass); the spread over the
  positions at 0 C (1.6 A against "below 1.5 A"; reference 3.3 A). At 25 C the spread is 1.9 A against 1.2 A, so
  the orbit is not the only thing that makes the step position matter.

## 3. Limits
- One board, two temperatures, one row, three positions. The 5.3 A margin is for these six runs only.
- The handover's cost was measured at 0 and 25 C. The 125 C statement is a comparison of two separate records, not
  a run.
- c4's threshold (1.0 A) came from the nominal boards' level; 0.84-1.40 A misses it by little. The rule was
  registered as written and is applied as written. The reason not to adopt that would stand without c4 is the
  handover.
