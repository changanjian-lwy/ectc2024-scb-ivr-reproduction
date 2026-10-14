# A222 - mode S's trim on plant V7 (BOUNDARY)
Method: cosim, cfg only (no code changes).
Track A. Written after A221's results, committed before A222's runs.
Decision it changes: whether skipping (A221's rows) is adopted and the final configuration moves to plant V7; A221's
decision rule held that back because k1 missed by 0.14 mV.
Cheaper check done first: A221's records. Mode S's Vo half a microsecond before the handover on V7 against V6: N0
-2.14 mV, N75 -2.36 mV (handover at 144 us), S75 125 C +0.58 mV (handover requested by Vo at 134 us). The core
resistor draws current in open-loop mode S, and the per-board trim of mode S's Ton was set on V6 (A206).
Budget: 3 runs, about 2.5 h for the N0 row, 40 min for the others.

## 1. What and why
- A206's rule, applied to V7: ton_s moves by the difference of Vo before the handover / 53.5 mV per ns (nominal
  boards; A190's measured slope), in whole 31.25 ps steps: N0 +1 step (23.4375 ns, about +1.7 mV), N75 +2 steps
  (23.46875 ns, about +3.3 mV). S75 stays (its handover is requested by Vo; A206's 10 mV threshold is far off).
  In a product this is the factory trim (one measurement per board), so it changes nothing of the design.
- Rows: A221's k row (+62.5 A on N0) with the new trim, the whole run; A215's 25 C binding rows of N75 and S75 on
  V7 to 200 us (the start-up only; N75 retrimmed, S75 as it was). References: A215's V6 records.
- Not tested: the cold table (A190) on V7, other temperatures' start-ups, four modules.

## 2. Criteria
1. k1 (A221's, unchanged): the N0 row passes A212's c6 + c7 on V7, its post-step peak within 3 A of A215's record,
   Vo's maximum before 300 us within 2 mV of it.
2. t1 (the two start-up rows): A206's c6 over the run, and Vo half a microsecond before mode P's entry and Vo's
   maximum before 200 us within 2 mV of A215's V6 record of the same board.

## 3. Predictions (not criteria)
- N0: Vo before 300 us -0.5 mV from V6 (k1 passes), the post-step peak as in A221 (181.2 A, within 0.3 A).
- N75: +1.0 mV before the handover; S75 25 C: +0.5 mV, handover requested by Vo as on V6, its time within 0.5 us.
- Start-up and handover peaks within 4 A of V6's (A221: -0.8 / -4.2 A at the handover).

## 4. Decision rule
- k1 and t1 pass: skipping is adopted on nominal boards (skip hi 5 / lo 1 mV, res_ofs_a, zcd_a = 8 ns x Vo / L, with
  A221's period fix), and the final configuration moves to plant V7 with these trims; N0 no load (A221: -21.2 A, 1.2 A
  outside the band) is stated as measured. Earlier rows stay results of the plant version they ran on.
- k1 or t1 fails: the trim is moved once more by the same rule and the failing row repeated; a second miss is reported
  and V7 is not adopted.

## 5. Round 2 (added after round 1, before its runs)
- Round 1: k1 passes on N0 (Vo before 300 us -0.49 mV, post-step peak 181.30 A), t1 on N75 (+0.98 / +0.95 mV); t1
  misses on S75 25 C: -4.96 mV. My premise was wrong: S75's handover is requested by Vo only when hot (A221's row,
  134 us); at 25 C it is at 144 us, as on V6.
- Section 4: the trim moves once more by the same rule, S75 +4.96 mV / 54.5 mV per ns = +0.091 ns, 3 steps
  (35.84375 ns, about +5.1 mV), and the failing row is repeated (s_S75_25_r2, criterion t1).
- Added as a check (reported, not in the decision rule's text): the S75 125 C start-up with the same trim
  (s_S75_hot_r2), because A206 uses the 25 C trim at every temperature and A221's hot start-up reached 1.0481 V of
  A206's 1.05 V limit. If it misses A206's c6, the trim is not adopted for S75 and V7 is not adopted.
- Prediction: s_S75_25_r2 +0.2 mV from V6 (t1 passes); the hot start-up's maximum 1.0481-1.0490 V (its handover is
  requested by Vo; a faster rise brings the request earlier, and the overshoot past 1.045 V grows little).
