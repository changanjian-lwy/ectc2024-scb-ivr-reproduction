# A239 - the minimum load (5 A, 2 % per module) on the rows A237 did not run (RESULTS)
Boundary: d5f9172 (+ note bec3ff7, before any result). Runs from it (cosim_sources_modified False). Records: release
records-a239. Analysis a239_analyze.py -> a239_summary.json; figure a239_figure.py -> a239_minimum_load.png. Plant V7,
final configuration, one module, nominal boards.

## 0. Verdict
- **Releases: 5 A is enough, and the return time is the formula.** From full load to 5 A, N75 (25 C), N0 and N75 (125 C)
  come back within 1 % 32.3 / 45.1 / 33.6 us after the overshoot's peak (+44.7 / +58.4 / +46.0 mV); to 2.5 A, N0 in
  89.5 us (35.0 / 49.2 / 36.2 / 93.6 us after the release). Co (V_pk - 1.01 V) / I gives 32.5 / 45.2 / 33.7 / 89.5 us
  (figure, right). VRD 11.1's 25 us above +50 mV: N0 9.2 us at 5 A (125 C) and 15.9 us at 2.5 A (25 C); N75 never above.
- **The skipping valleys at 5 A on N75 reach -22.6 / -22.7 A (25 / 125 C), and N0 at 2.5 A -21.0 A** (band
  -20..-12 A; N0 at 5 A, 125 C: -15.9..-15.0 A). Same kind as A226's no-load -22.8 A on N0. m4 misses.
- **Start-ups into 5 A: Vo is first back within 1 % 15-30 us after its maximum** (1.0477-1.0520 V, 0.3 us above
  1.05 V on N0), **but the ladder is left unbalanced, and that is new** (figure, left; record `cosim/run_u5_N75h.json`):
  the light load lets Vo reach the 1.045 V request at 97-101 us, while the input is still ramping (34-35 V of 48 V
  until 137 us). The module then pauses, and the rest of the ramp lands on rail 1: 18.5-22.5 V, above 13.5 V for
  65-154 us, 1.0-2.6 V off balance at 300 us. Phases 2-4 run deep valleys while it rebalances (-61..-103 A after mode
  P + 40 us); on N75 at 125 C the rebalance at 200-220 us takes Vo to 0.9902-1.0189 V. V_DS stays <= 36.7 V, peaks
  <= 146.0 A.
- **The same mechanism is in the adopted start-ups below full load** (A230 / A231 records, never checked for it):
  rail 1 max 14.0-16.3 V on nominal boards at 20-30 %, above 13.5 V for 4-26 us (0.1-0.6 V off at 300 us), and **S75 into 30 %
  (the slow boards' plain request) 17.4 / 18.7 V at 25 / 125 C, still 4.6 / 5.2 V off balance at 300 us**. Full-load
  start-ups hand over at 144 us, after the ramp: 0.2 V. Item 6c (new).
- m5 misses on 3 of 4 start-ups for a reason other than the return: the skipping sawtooth at 5 A peaks at
  1.0100-1.0108 V, so the last exit from 1 % falls 94-130 us after the maximum. The release rows' sawtooth is the same
  (to 1.0099 V) but stayed under.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| m0 | sources unmodified | pass (8 / 8) |
| m1 | limits | pass (8 / 8): peaks <= 151.0 A, V_DS <= 36.7 V |
| m2 | Vo within 1 % over the last 20 us | pass (8 / 8); u5_N75h is outside 47 times in its last 100 us |
| m3 | return within 15 % + 3 us of Co (V_pk - 1.01 V) / I | pass (4 / 4), within 0.2 us |
| m4 | skipping valleys -20..-12 A (last 60 us) | **miss 3 / 4**: c2_N75 -22.56, c2_N75h -22.69, c1_N0 -20.97 A |
| m5 | start-up: last exit from 1 % <= 60 us after the maximum | **miss 3 / 4** (94-130 us; the sawtooth, Section 0) |

## 2. Predictions
Held: start-up Vo max (N0 1.0517 / 1.0520, N75 1.0477 / 1.0482 V); handover peaks <= 110 A (91.1-99.9 A); release
peaks (N75 +44.7 / +46.0 mV, N0h +58.4, c1 +57.9 mV); returns after the release (N75 35.0 / 36.2 us, N0h 49.2, c1
93.6 us); N0h's valleys. Missed: N0 above 1.05 V 0.3 us (predicted 2-6 us); start-up returns 30-45 us after the
maximum (first entry 15-30 us, last exit 30-130 us); valleys -16.5..-14.5 A on N75 and at 2.5 A (-22.7 / -21.0 A).

## 3. Decision (Section 4 of the boundary)
- Item 6b closes for operation: at least 5 A per module on nominal boards at 25-125 C; after a release Vo returns
  within 1 % in Co (V_pk - 1.01 V) / I (Co 4.672 mF). The valley band is missed by up to 2.7 A at 5 A on N75.
- The start-up below full load is excluded from that statement: item 6c (the ladder after a handover inside the input
  ramp) is opened, with the slow board at 30 % as its worst adopted case.

## 4. Limits
- One module; one release instant per row; the start-up rows end at 300 us (rebalancing not seen to its end on S75).
- Vo is sampled at the record's sections (about 0.2-0.5 us).
