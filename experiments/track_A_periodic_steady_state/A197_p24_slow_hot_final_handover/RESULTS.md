# A197 - the slow corner at 125 C with the adopted handover request (RESULTS)
Boundary: 6d8c700. Records: release records-a197 (12 runs, logs). Analysis: a197_analyze.py -> a197_summary.json
(A191 alongside). Plant V5, t_il 1.0 ns, the A188 start-up (handover requested at Vo 1.045 V), lead 9.5 ns, boards
S75 / S80 (slow devices, L x 0.75 / 0.8), 125 C, +4.8 V / 1 us at 500 us + k T / 6. Only hand_vo_v differs from
A191. cosim_sources_modified False; 10 runs started at 6d8c700 and 2 at 8744c8f (documents and cfgs between them).

## 0. Verdict
- **PASS, 12 of 12: the slow corner holds 200 A at 125 C with the final configuration.**
  - S75: post-step 194.6-196.3 A (A191, 1.03 V request: 194.1-196.9 A).
  - S80: 190.8-194.8 A (A191: 190.6-192.8 A).
- Run for run the peak moves by -2.2..+2.2 A against A191. The step phases are different (the entry is 1.6 us
  later, the steps are at the same absolute times), so this is the step-position spread, not an effect of the
  request level. The largest value at 125 C is now 196.3 A (margin 3.7 A); it was 196.9 A.
- **The slow corner's worst case over -40..125 C is unchanged: 197.8 A at 0 C (A193), margin 2.2 A.**
- Start-up 139.0 / 136.0 A, handover 184.5 / 182.0 A (A191: 188.5 / 185.4 A), V_DS <= 33.7 V, 0 shoot-throughs.
- **Vo over 0-300 us reaches 1.0486 V on S80 and 1.0473 V on S75, against the 1.05 V limit.** With the request at
  1.045 V a hot slow board overshoots it by 2-4 mV before mode P pulls back. The margin to c7 is 1.4 mV.
- Late fires on phases 3-4 in the first 30 us after the step: 3-6 per run, as in A191 (1-10).
- By the decision rule the coverage file cites A197 for the 125 C slow rows and labels A191's figures with their
  1.03 V request. No further runs.

## 1. Criteria
| board | step phases | c1 start / hand (A) | c2 post-step (A), A191 in brackets | c3 V_DS | c7 Vo max |
|---|---|---|---|---|---|
| S75 | 0.41 / 0.58 / 0.74 / 0.91 / 0.07 / 0.24 | 139.0 / 184.5 | 194.7 / 195.4 / 194.6 / 194.8 / 194.9 / 196.3 (196.9 / 194.2 / 196.1 / 194.1 / 195.4 / 194.1) | <= 33.7 V | 1.0473 V |
| S80 | 0.43 / 0.59 / 0.76 / 0.92 / 0.09 / 0.25 | 136.0 / 182.0 | 191.3 / 194.8 / 190.8 / 191.6 / 191.0 / 191.8 (190.6 / 192.8 / 191.7 / 190.8 / 191.5 / 190.7) | <= 33.4 V | 1.0486 V |
Post-step Vo minimum 0.983-0.987 V (S75) and 0.982-0.986 V (S80), as A191 (0.982-0.986 V).

## 2. Predictions
- Held: all four criteria on all 12; start-up 136-139 A; handover 184.5 / 182.0 A; S75 in 192-199 A; S80 in
  188-195 A (194.8 A, at the band's edge).

## 3. Limits
- One row at one temperature. The six positions cover the period (phases 0.07-0.92) but are six points; the
  spread between neighbouring positions is up to 4 A on S80 (190.8-194.8 A).
- c7's 1.4 mV margin is on one board at one temperature. A hotter board, or a slow board with a higher mode-S Vo,
  is not run.
