# A211 - the loss books against the load on the binding boards, and what shedding modules would save (RESULTS)
Boundary: a9eabde. Records: release records-a211 (9 cosim records, logs). Analysis: a211_analyze.py ->
a211_summary.json; figure a211_curves.png (a211_figure.py). Runs from a9eabde, cosim_sources_modified False. Final
configuration on plant V6 with ton_min_ns 4.0 ns, 25 C, one module, books over the last 10 us of each run. Curves
also use A206's, A207's, A208's and A210's rows. The four-module figures are a composition, not a run.

## 0. Verdict
- **The slow board is the lossy one at every load, and its efficiency falls as the load falls.** Semiconductor loss
  per module in the plant's books, and Pout / (Pout + loss):

  | load | nominal L0 (N0) | nominal 0.75 L0 (N75) | slow 0.75 L0 (S75) |
  |---|---|---|---|
  | 100 % | 20.15 W, 92.5 % | 22.32 W, 91.8 % | 31.92 W, 88.7 % |
  | 75 % | 12.39 W, 93.8 % | 14.18 W, 93.0 % | 24.38 W, 88.5 % |
  | 60 % | 8.66 W, 94.5 % | 10.50 W, 93.5 % | 20.87 W, 87.8 % |
  | 50 % | 6.71 W, 94.9 % | 8.33 W, 93.8 % | 20.67 W, 85.8 % (r4 missed) |
  | 40 % | 5.27 W, 95.0 % | 6.86 W, 93.6 % | 19.86 W, 83.4 % (r4 missed) |
  | 30 % | 4.24 W, 94.7 % | 6.52 W, 92.0 % | 17.57 W, 81.0 % |
  | 20 % | 3.37 W, 93.7 % | below its floor | 15.77 W, 76.0 % (high sides not fully on) |

- **Why**: the frequency rises as the load falls (S75: 2.60 MHz at 100 %, 5.60 MHz at 30 %), and a slow device's
  edges cost several times a nominal one's. S75's high-side edges are 8.0 W at 100 % and 9-11.5 W below 60 %
  (N0: 2.5 and 1.6-1.9 W); its low-side edges 5.5 W at 100 % (N0: 1.4 W). Conduction is the same on the three boards.
- **At full load the slow 0.75 L0 board books 31.9 W, 11.8 W more than N0.** The thermal note (D80) carried 3.9 W
  of slow-corner edges from plant V5; on V6 this board has 13.5 W of edges. D80 is not rerun here.
- **Shedding whole modules pays on slow boards from about half load down** (four equal modules, composed): at 50 /
  40 / 30 % of the system's load, two modules on instead of four lose 63.8 / 51.8 / 41.7 W against 79.1 / 74.7 /
  70.3 W, a saving of 19 / 31 / 41 %. On nominal boards it saves little above the floor: N75 21 % at 30 %, N0 7 %
  at 30 % and 22 % at 20 %. It is also the only thing here that reaches below 30 % of the system's load (down to
  7.5 % with one module on). By the rule it is named as worth building, for slow-device boards. It needs RTL.
- **Seven of nine rows work.** S75 at 50 and 40 % miss r4 on the valley band alone: the slow boards' two-cycle orbit
  (A195) is wider at mid load, valleys alternate between -17 and -7 A (band's edge -8 A; at full load -18..-11 A).
  They regulate, with no late fire at the end.

## 1. Criteria
| row | r1 | r2 | r4 | valleys, last 20 us | MHz | loss: high-side edges / low-side edges / conduction |
|---|---|---|---|---|---|---|
| S75 100 % | pass | pass | pass | -17.5..-12.2 A | 2.60 | 7.97 / 5.50 / 16.41 W |
| S75 75 % | pass | pass | pass | -16.1..-10.2 | 3.26 | 8.72 / 6.12 / 9.55 |
| S75 60 % | pass | pass | pass | -16.1..-9.9 | 3.80 | 9.22 / 5.28 / 6.37 |
| S75 50 % | pass | pass | **miss** | -16.9..-6.9 | 4.42 | 10.99 / 4.48 / 4.53 |
| S75 40 % | pass | pass | **miss** | -16.6..-7.6 | 5.02 | 11.36 / 3.02 / 3.07 |
| N75 100 % | pass | pass | pass | -17.3..-14.9 | 2.58 | 3.84 / 1.86 / 15.74 |
| N75 75 % | pass | pass | pass | -16.9..-15.2 | 3.18 | 3.33 / 1.65 / 9.20 |
| N75 60 % | pass | pass | pass | -15.9..-15.4 | 3.70 | 3.18 / 1.17 / 6.15 |
| N75 50 % | pass | pass | pass | -16.7..-14.9 | 4.16 | 2.90 / 1.02 / 4.41 |
- r1: peak <= 154.5 A over each run, V_DS <= 31.4 V, 0 shoot-throughs. In the 30 us after the release S75's valleys
  reach -76 / -78 A (50 / 40 %) with 51 / 31 late fires, then settle.
- The band's upper edge was registered as -8 A where "full load widened by 3 A" gives -7.6 A; the 40 % row's -7.6 A
  is at that edge, the 50 % row's -6.9 A beyond it either way.

## 2. Predictions
- Held: N75's four losses (22.3 / 14.2 / 10.5 / 8.3 W against 21-24 / 13-15 / 9.5-11.5 / 8-9.5); registers far
  from the limit; S75's high-side edges staying near 9-11 W while conduction falls; shedding on S75 saves 20 % or
  more from half load down (19 % at 50 %, 31 % at 40 %); under 10 % on N0 above 20 % of the load.
- Missed: S75's level, which I put too low (24-30 W at 100 %: 31.9; 17-21 W at 75 %: 24.4; 15-19 W at 60-40 %:
  19.9-20.9), and its efficiency (90-91.5 % at 100 %: 88.7 %); "every row works" (two miss r4).

## 3. Limits
- 25 C only on these rows; one module; the loss books are the switches' only (no gate drive, which grows with the
  frequency; no inductors or capacitors). Slow devices have not been compared with LTspice (A206: nominal only).
- The composition assumes equal sharing, an idle module at 0 W, and loss linear between rows; S75's "all on"
  figures at 50 and 40 % interpolate across two rows that miss r4 (their own books: 20.67 and 19.86 W).
- Shedding itself, a module leaving and re-entering in operation, is not modelled anywhere: the frozen controller
  cannot do it.
