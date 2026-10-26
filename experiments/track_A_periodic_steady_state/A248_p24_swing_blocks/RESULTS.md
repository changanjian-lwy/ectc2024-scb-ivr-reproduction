# A248 - which plant blocks make the free swing late and shallow (RESULTS)
Boundary: f8f003f. The post hoc checks were added after h1's miss (aa2d6a1; Section 2). Harness: a248_swing.py ->
tmp/a248_swing.npz. It holds 3850 single edges: 5 boards x 7 variants x 2 phase groups x rails 10-14 V x i_off -60..-10 A.
Analysis: a248_analyze.py -> a248_summary.json, against A247's records (records-a247). Figure: a248_figure.py ->
a248_swing_blocks.png. Release records-a248 holds the harness table and the logs.

## 0. Verdict
- **h2 passes: the plant's core is D57.** With the gate model, Miller, r_core, loop and edges all dropped, the plant's
  single edge equals D57: shift -0.05 ns, offset +0.01 V, RMSE 0.07 V. With them all present, the plant runs 1.65 ns
  later and 0.28 V higher than D57 (figure (a)).
  - The delay is the low side's gate (91 % of the shift): its channel stops 2.6 ns after the command (median), and its
    current starts to fall 1.6 ns after it.
  - The level is r_core (105 % of the offset). The loop adds 16 %; the gate takes 38 % off.
  - Miller and the edge rates change nothing here: with the gate model on, the gate sets the edges.
- **h1 misses as registered:** RMSE 0.346 V (bar 0.35). Median |e| is 0.44 V on N0, 0.34 V on N75 and 0.58 V on N13
  (bar 0.30); agreement on N13 is 94.0 % (bar 95 %). S75h passes at 0.27 V and N0 at 125 C at 0.05 V.
- **Traced (post hoc; figure (b)): the miss is the rail I fed in, not the swing.**
  - Sections sample the ladder at a different instant of the period from the swing. A Cs ripple of about 0.5 V
    (100 A x 40 ns / 6 uF) puts the rail at the swing 0.30-0.64 V above the interpolated one.
  - The residual is the same at the command (S75h: 2.4 ns in, before the node moves) and at the turn-on, so it is a
    level, not a timing error.
  - With each edge's rail taken from its own V_DS at the command, the full harness predicts the turn-on V_DS within
    0.064 V RMS (median 0.011-0.026 V on every board; 39,977 rows), with no fitted number.
- **A247 re-read.** Its fitted 0.92 V offset was 0.28 V of plant blocks plus this rail artifact; its c1 miss on N13 is
  the artifact (N13's rail +0.64 V).
- **A247's conclusions hold on the plant's own physics** (figure (c)).
  - All 50 board / phase group / rail cells nest.
  - One delay per cell keeps V_DS <= 2 V over +-0.5 ns for 99.5 % of the grid currents that have a window. The
    choice is the least mean V_DS among the delays covering the most.
  - At 12 V (phases 2-3 / phase 4): N0 11.6 / 10.55 ns, N75 10.2 / 9.75, S75h 10.05 / 9.6, N0 at 125 C 11.7 / 10.7,
    N13 12.8 / 12.3.
- **Against the learner on the own-rail rows** (rails 10.3-13.7 V, i_off -60..-10 A; open loop):
  - Overall the two are equal: median 4.34 V both, p99 7.28 V recorded against 7.14 V.
  - Where the learner is more than 2 ns off (502 rows, 63 % shorter), one delay gives median 0.05 against 2.87 V,
    p99 7.5 against 12.1 V, hard 37 % against 55 % (figure (d)). A247's wider sample had 4.9 % of rows that far off.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| h1 | RMSE <= 0.35 V; each board median <= 0.30 V and agreement >= 95 % | **miss**: 0.346 V; N0 0.44, N75 0.34, N13 0.58 V (agreement 94.0 %). Traced to the rail's sampling: 0.064 V with each edge's own rail |
| h2 | bare: shift <= 0.30 ns, offset <= 0.20 V | pass (-0.05 ns, +0.01 V) |
| h3 | D57 + r_core + start at the current fall's middle within 0.30 V of the full harness | **miss**: 0.49 V. The physical start (2.1 ns) lags the fitted 1.65 ns, and holding x at 0 is too crude |

## 2. Changes after the first run
- Post hoc, after h1's miss:
  - each edge's rail from its own command V_DS;
  - the harness's windows and one delay per cell;
  - that delay against the learner.
- The fixed delay was first taken as the earliest of the most-covering delays (8.8 ns on N0, worse than the learner).
  It is now the least mean V_DS among them, because the valley turn-ons without a window must count too.

## 3. Predictions
- Held:
  - the gate takes most of the shift (predicted > 70 %, got 91 %);
  - r_core takes most of the offset (predicted > 60 %, got 105 %);
  - Miller and edge are small; bare passes.
- Missed:
  - the offset is 0.28 V, not 0.7-1.1 V (the rest was the rail artifact);
  - h1: I expected the records to fit, but the input rail was off;
  - h3: predicted 0.15-0.30 V, got 0.49 V.

## 4. Decision and next
- By the rule, h1's miss has to be traced before step 2. It is traced: a single edge carries the records once the rail
  at the swing is right.
- **Step 2 takes the plant's single-edge table** (per board and phase group, over rail and i_off) as its swing model,
  rather than D57 (h3 missed).
  - D63's block must feed it the rail at the moment of each phase's swing, i.e. the ladder's ripple within the
    period, not a per-period value.
- Limits:
  - the table covers rails 10-14 V and i_off -60..-10 A (extend it for start-ups and deep releases);
  - the other phases sit idle in the harness;
  - all comparisons here are open loop.
