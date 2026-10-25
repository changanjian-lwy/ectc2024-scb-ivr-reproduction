# A245 - a turn-on delay that keeps finding the swing finished (item 6c) (RESULTS)
Boundary: c629cb9 (code 6d215ad). Records: release records-a245 (45 runs and logs, plus the 12 pilot runs of BOUNDARY
Section 1), all from 6d215ad, cosim_sources_modified False, all COMPLETED. Analysis a245_analyze.py -> a245_summary.json;
figure a245_figure.py -> a245_reverse_conduction.png. Plant V7, one module (stage 2 also four modules); arm f = final
configuration, arm r = f + rev_n 16.

## 0. Verdict
- **Adopted by user decision on 2026-10-25, after these results** (rev_n 16 in the final configuration, one and four
  modules; four modules checked for identity only). Item 6c closes for start-ups into >= 5 A on N0 / N75 and into 30 %
  on S75, 25 / 125 C.
- **Not adopted as registered: g2 misses on N0 at 10 % and 20 %, one oracle NEW event each, inside the release window.**
  Both are a skipping pause that begins after phase 3 (phase 4's pulse withheld), read as an order hit at the resume
  (150.6 / 153.9 us; records `cosim/run_r_u_N0_10.json`, `run_r_u_N0_20.json`). Vo there >= 0.9969 V, peaks <= 96 A.
  The same pause occurs in arm f of the 5 A rows (u5_N0 2, u5_N75 1; arm r 0) and 1-33 times in A244's skipping rows.
  By the decision rule (misses only inside the window, Vo >= 0.9827 V, peaks <= 200 A) adoption goes to the user.
- **Item 6c is fixed on every row (g1 20 / 20).** The three locked S75 rows: 4.6-5.4 V -> 0.1 V at 300 us, inside 1 V
  by 152-168 us (figure, upper left). 5 A: 0.9-2.6 V -> 0.3-0.9 V. Nominal 10-30 %: 0.1-0.7 V in both arms.
- **The lock is the delay (figure, upper middle):** arm f's phase 3 on S75 at 125 C turns on at V_DS -2.1 V on every
  report from 100 to 300 us; arm r's first act is at 100.1 us, and from 103 us its command sees 7-12 V, like the other
  phases.
- **Vo is better, not worse (g3 20 / 20):** the minimum after mode P's entry rises on 13 rows (u5 0.989-0.993 ->
  0.996-1.001 V; S75h 0.9904 -> 0.9954 V), falls on 2 (S75 0.9976 -> 0.9941 V, N0 30 % 0.9999 -> 0.9980 V) and is
  equal on the 5 full-load rows. The lead row, whose lock releases by itself in arm f, dips to 0.9827 V at 167 us;
  arm r acts at 100 us and stays >= 0.9974 V. Lowest arm-r value: 0.9931 V (N75 20 %). Vo maxima are
  equal in both arms (before the rule acts).
- **Loss at the end of the run (last 50 us, edge + reverse conduction):** S75 rows 14.9-22.6 -> 14.6-16.2 W; nominal and
  5 A rows within 0.2 W; full load equal. Hard turn-ons (> 6 V) in the last 50 us: the three locked rows 468-778 -> 0,
  u5_N75 34 -> 14, u5_N75h 6 -> 20, the others within 3.
- **Limits:** peaks <= 125 A (S75 106 -> 125 A; N75 30 % 103 -> 120 A), V_DS <= 29.8 V (the 5 A rows 30.5-36.7 ->
  27.2-27.6 V: SH2 no longer follows a high rail 1), no overlap. Late fires rise during the release on S75 (64-149 ->
  151-326; phases 3-4 join phase 2), elsewhere <= 11.
- **Identity:** full-load start-ups never reach 16 in a row and equal arm f bit for bit; stage 2's five rows equal
  A244's records bit for bit, including four modules (m4_l_m80_10us, phase 1 up to 30 in a row, left out by design).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| g0 | unit 132 / 132, regression quick + full, stage 2 bit for bit (5 rows) | pass |
| g1 | every rail within 1 V at the end, no phase 2-4 with 16 in a row in the last 40 us | pass (20 / 20) |
| g2 | peak, V_DS, overlap; NEW outside the window <= arm f, inside only spikes | **miss 2 / 20**: u_N0_10, u_N0_20 (one order hit each, inside) |
| g3 | Vo after entry within [min(0.99, f), max(1.05, f)] | pass (20 / 20) |
| g4 | rows where the rule never acts = arm f bit for bit | pass (5 full-load rows) |

## 2. Predictions
- Held: S75 rows in band by 152-168 us, end 0.1 V, Vo minimum 0.9941-0.9974 V (predicted 0.994-0.996), peaks <= 125 A,
  the three locked rows' loss 3.2-6.5 W lower; full load and stage 2 bit for bit; nominal rows end within 0.7 V.
- Missed: nominal Vo "within 2 mV of arm f" (up to 8.2 mV higher; N0 30 % 1.9 mV lower); 5 A "<= 1 V" held
  (0.3-0.9 V), but N75 / N75h enter the band only at 256 / 278 us; NEW on the nominal rows was not foreseen.

## 3. Limits
- Not tested: a true no load (item 6b), four modules starting into a light load, F0 / N13 start-ups, disturbances while
  the rule acts after the start-up (A244's rows never reach 16 in a row).
- The threshold 16 comes from the pilot on S75 only; A244's records leave a margin of 10 reports on phases 2-4.
