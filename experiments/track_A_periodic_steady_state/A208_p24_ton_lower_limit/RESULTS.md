# A208 - the loop's lower Ton limit as its own value: how far down one module regulates (RESULTS)
Boundary: 3a2d2c2 (Sections 1-4), bb5aa2d (Section 5, before the second stage). Records: release records-a208
(8 cosim records, logs). Analysis: a208_analyze.py -> a208_summary.json, a208_identity.json; figure a208_vo.png
(a208_figure.py, drawn from the records). Runs from 3a2d2c2 / bb5aa2d, cosim_sources_modified False. Final
configuration, plant V6, board N0, 25 C, one module; part of the 250 A load released at 300 us, run to 450 us.
Code: bridge.py reads cfg "ton_min_ns" (cfg_ton_min); absent = half of ton_ns. RTL unchanged.

## 0. Verdict
- **With the limit out of the way one module regulates down to 20 % of its load (50 A); the floor was the limit's
  value, not the controller.** Limit at 2.0 ns: 60, 50, 40, 30 and 20 % work (Vo within 0.3 mV of 1 V at the end,
  no late fire, valleys -16.5..-12.8 A). 10 % does not: the register sits at 2.0 ns, 38 A are delivered, Vo ends at
  1.0525 V and late fires keep coming (59 / 0 / 118 / 43 in the last 20 us; record cosim/run_m10.json).
- **Proposed value: ton_min_ns = 4.0 ns** (the rule: 20 %'s smallest end register, 4.22 ns, rounded down). Run on
  its own: 20 % works with it (register 4.25-4.72 ns at the end). At 10 % the register sits at 4.0 ns, 46.6 A are
  delivered and Vo ends at 1.0867 V, but the switching stays clean (no late fire, valleys -15.7..-14.9 A). The
  limit keeps the gate command at 12 ns or more, the shortest shown to switch cleanly.
- **Tested minimum load of one module on this board: 20 % (50 A); the limit is reached at about 19 % (46.6 A).**
  It was about 70 % (174 A) with the limit at half the loop seed (A207).
- **The 18 earlier V6 records are not affected**: their registers never reach the old limit (lowest 20.4-31.8 ns).
- **Light load is efficient**: semiconductor loss 8.66 / 6.71 / 5.27 / 4.24 / 3.37 W at 60 / 50 / 40 / 30 / 20 %,
  which is 94.5 / 94.9 / 95.0 / 94.7 / 93.7 % as Pout / (Pout + loss); the frequency rises to 2.82 / 3.18 / 3.65 /
  4.26 / 5.18 MHz. High-side edge loss stays at 1.6-1.9 W while conduction falls with the current.
- **Four modules, composed** (not a run): all on cover 200-1000 A (20-100 %); with whole modules shed 50-1000 A
  without a gap. Shedding is no longer needed above 20 % of the system's load, and nothing covers below 5 %.
- **Price and open points.** A release of 200 A or more in zero time overshoots by 52.6 mV (r3 misses at 20 % and
  below); with the 4.0 ns limit the same row then undershoots to 0.9635 V before it settles (2.0 ns: 0.9854 V).
  Below 19 % the output still runs away; that needs a light-load mode. Other boards: A210.

## 1. Criteria
| row | limit | left | r1 | r2 | r3 | r4 | Vo end | Vo after the release | register at the end | MHz | delivered | loss |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| m60 | 2.0 ns | 60 % | pass | pass | pass | pass | 0.9999 V | 0.9891..1.0266 V | 18.66-18.97 ns | 2.82 | 150.0 A | 8.66 W |
| m50 | 2.0 | 50 % | pass | pass | pass | pass | 0.9998 | 0.9858..1.0334 | 15.19-15.47 | 3.18 | 125.0 | 6.71 |
| m40 | 2.0 | 40 % | pass | pass | pass | pass | 0.9998 | 0.9844..1.0401 | 11.63-11.88 | 3.65 | 99.9 | 5.27 |
| m30 | 2.0 | 30 % | pass | pass | pass | pass | 0.9998 | 0.9854..1.0467 | 8.09-8.44 | 4.26 | 74.9 | 4.24 |
| m20 | 2.0 | 20 % | pass | pass | **miss** | pass | 1.0000 | 0.9854..1.0526 | 4.22-4.72 | 5.18 | 49.9 | 3.37 |
| m10 | 2.0 | 10 % | pass | **miss** | **miss** | **miss** | 1.0525 | 1.0063..1.0590 | 2.00 (limit) | 5.88 | 38.2 | 3.30 |
| v20 | 4.0 | 20 % | pass | pass | **miss** | pass | 1.0000 | 0.9635..1.0526 | 4.25-4.72 | 5.18 | 49.9 | 3.40 |
| v10 | 4.0 | 10 % | pass | **miss** | **miss** | pass | 1.0867 | 0.9712..1.0895 | 4.00 (limit) | 5.66 | 46.6 | 3.23 |
- i1: regression quick 4 / 4. i2: A207's 14 us record bit for bit with the key absent and at 22.24 ns (69 sections,
  1032 edges, snapshots, gate records).
- r1 on every row: peak <= 162.0 A over the run (the handover), V_DS <= 33.9 V, 0 shoot-throughs, 0 forced edges.
- At 20 % the register is at the 2.0 ns limit for 19 periods during the transient (4.1-7.5 us after the release)
  and late fires occur until 60 us after it (3 / 12 / 13 / 6 in the first 20 us, then 0 / 0 / 4 / 2), none later.

## 2. Predictions
- Held: i1, i2; D63 on every row that regulates (register 19.05 / 15.64 / 12.23 / 8.82 / 5.42 ns against 18.79 /
  15.29 / 11.70 / 8.25 / 4.53; overshoot within 1 mV; frequency within 2 %); mine: 60-30 % work, 10 % does not, r1
  everywhere, r3 misses at 20 and 10 %; second stage: v20 works, v10 delivers 46.6 A (46-49) and ends at 1.0867 V
  (1.085-1.10) with r4 passing.
- Missed: the loss books, which I put too high (7.5-9 / 5.5-7 W at 50 / 30 %: 6.71 / 4.24 W) by scaling every edge
  with the frequency; v20's overshoot (1.053-1.060 V predicted: 1.0526 V) and its undershoot, which I did not foresee.

## 3. Limits
- One board (N0, nominal devices, 25 C), instantaneous releases, 150 us each. Other boards in A210.
- 20 % is the lowest row that works; the floor itself (about 19 %) is read from v10's delivered current.
- Four modules are a composition with equal sharing and idle modules at 0 W. Start-up into a light load, slow load
  changes and the upper limit (2 ton_ns) are not run. The loss books leave out gate drive, inductors and capacitors,
  and the gate-drive loss grows with the frequency.
