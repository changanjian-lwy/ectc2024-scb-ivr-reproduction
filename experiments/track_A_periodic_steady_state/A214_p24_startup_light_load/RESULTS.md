# A214 - start-up into less than the full load (RESULTS)
Boundary: aac801c. Records: release records-a214 (5 cosim records, logs). Analysis: a214_analyze.py ->
a214_summary.json. Runs from aac801c, cosim_sources_modified False. Final configuration on plant V6 (low sides
0.3 ohm x the board's factor, A206's trims, ton_min_ns 4.0 ns), one module, the load resistance 4 mOhm / share from
t = 0, run to 300 us.

## 0. Verdict
- **The start-up holds down to half load on the three boards tested, and overshoots by 2.8 mV at 30 %.** N0 with
  75 and 50 % of the load, and S75 with 50 % at 25 and at 125 C, pass c6: Vo at most 1.0492 V, peaks <= 161.5 A,
  V_DS <= 30.6 V, 0 shoot-throughs, Vo back at 1 V at the end. N0 with 30 % reaches 1.0528 V, 0.6 us after mode P's
  entry (limit 1.05 V; record cosim/run_u_N0_25_30.json); everything else on that row is inside its limits.
- **What makes it work is the handover on Vo** (A188: requested once a sample reaches 1.045 V). With less load Vo
  rises earlier, and the request comes at 137.4 / 130.0 / 118.4 us on N0 (75 / 50 / 30 %) and at 114.2 / 108.8 us
  on S75 (25 / 125 C), instead of at 144 us. Mode P then enters while Vin is still ramping (48.0 / 45.5 / 41.5 V on
  N0; 40.0 / 38.1 V on S75) and takes over without a peak above the full-load start's.
- **Tested start-up range: 50 to 100 % of the load.** At 30 % the 1.05 V limit is missed by 2.8 mV on the nominal
  board; slow boards at 30 % are not run. This goes on the controller's list under the start-up item.
- After the entry Vo dips to 0.990-0.998 V and the loop settles at the load's own Ton register (23.9-24.3 / 15.1-
  15.5 / 7.8-8.1 ns on N0), the same values as after a release (A207, A208).

## 1. Criteria
| row | c6 | handover requested, Vin there | Vo max | Vo min after the entry | start-up / handover peak | late fires (whole run) |
|---|---|---|---|---|---|---|
| N0 25 C, 75 % | pass | 137.4 us, 48.0 V | 1.0478 V | 0.9996 V | 111.3 / 124.0 A | 0 |
| N0 25 C, 50 % | pass | 130.0 us, 45.5 V | 1.0473 V | 0.9961 V | 94.5 / 120.3 A | 0 |
| N0 25 C, 30 % | **miss** | 118.4 us, 41.5 V | **1.0528 V** | 0.9899 V | 81.2 / 117.9 A | 2 |
| S75 25 C, 50 % | pass | 114.2 us, 40.0 V | 1.0492 V | 0.9939 V | 113.9 / 161.5 A | 4 / 73 / 74 / 77 |
| S75 125 C, 50 % | pass | 108.8 us, 38.1 V | 1.0479 V | 0.9981 V | 112.8 / 158.9 A | 0 / 21 / 0 / 53 |
- The slow board's late fires fall mostly in the first 20 us after the entry (25 C: 0 / 19 / 18 / 27 later;
  125 C: 0 / 0 / 0 / 5); its full-load start has 3 / 15 / 11 / 13 (A206).

## 2. Predictions
- Held: the handover is requested by Vo on every row; 75 % passes; peaks and V_DS inside their limits; every row
  regulates at the end; 30 % misses on Vo.
- Missed: I expected 50 % to fail on Vo as well, on N0 and on S75: all three pass. The requests come later than I
  put them (130 us at 50 % against 95-115; 118 us at 30 % against 65-85): mode S's Vo depends on the load much less
  than a fixed current per pulse would give.

## 3. Limits
- A resistive load present from t = 0; a load that switches on during the start, or a current sink, is not run.
- N0 at three loads, S75 at one; 0 C, N75, fast devices and four modules are not run. One trim per board (25 C).
- Between 30 and 50 % the boundary is not located; the miss at 30 % is 2.8 mV against a 50 mV band.
