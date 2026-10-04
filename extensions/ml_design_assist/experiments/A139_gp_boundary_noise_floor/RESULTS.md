# A139 - A138's boundary map with the noise floor measured and the budget split per direction (RESULTS)
Boundary: 96a5027. Records: a139_state.json (254 runs: inputs, prior, response, flags; the spec table with mean / bound
curves), a139_summary.json, cosim/cfg_*.json (raw records local). Log 04:04-06:01, 10 jobs. Supersedes A138's table.

## 0. Verdict
- **Pass, 3/3. The GP's bands now hold on fresh data:** rising cover90 1.00, classification 0.90 (D63 0.85), MAE 2.8 A
  (D63 4.2); falling cover90 0.85, classification 0.90 (D63 0.55), MAE 7.2 A (D63 15.8). Verification 20/20 at the table
  slews, 165.8-193.9 A.
- **The scatter is heavy-tailed, not Gaussian:** at five of six step positions the peak repeats within 0.2-1.1 A, but
  one position of six on (L 0.7, Cs 0.7, +6.4 V / 1 us) gives 198.3 A against 183.3-184.9 A - the single-period spike
  seen on l_p48_5us (C09 / C10). Pooled floors 4.12 A rising, 0.97 A falling; fitted noise 5.4 / 5.5 A.
- **A minimum slew is not a spec for this design (both directions are non-monotone in slew):**
  - rising at L x 0.7, +4.8 V: 185.2 A at 1 us, 188.6 A at 5 us, **205.9 A at 20 us** (+5.6 V / 20 us 207.4 A) -
    slower is worse at low L, as D63 predicted in A138;
  - falling at nominal L / Cs, -4.8 V: 173.5 A at 1 us, **192.2 A at 2.3 us**, 172.2 A at 5.1 us - the worst case is
    at 2-4 us, between the two slews A130 tested (1 and 5 us);
  - nominal +8 V: the mean sits at 197-209 A at every slew 1-20 us (A130's 10 us: 198.3 A, marginal); with ~5 A
    scatter no slew is certified.
- Certified table (mean + 1.645 sd <= 200 A from that slew up; '-' none <= 20 us), |dv| 4.8 / 6.4 / 8.0 V:
  rising L x 0.7: Cs 0.7 1.0/-/-, Cs 1.0 -/-/-, Cs 1.3 -/-/-; L x 1.0: 1.0/1.0/-, 1.0/-/-, 1.0/-/-;
  L x 1.3: 1.0/1.3/11.6, 1.0/1.3/-, 1.0/6.7/-. Falling L x 0.7: 3.9/3.9/5.1, 1.0/3.9/6.7, 2.3/8.8/11.6;
  L x 1.0: 5.1/6.7/6.7 (Cs 0.7 and 1.0), 3.9/8.8/8.8; L x 1.3: 6.7/8.8/5.1, 6.7/8.8/11.6, 6.7/11.6/11.6.
  The table is a 95 % bound: of ten '-' cells run at 20 us, five exceed 200 A (204.7-221.7 A), five do not (186-200).
- Against A130's spec (nominal L / Cs; <= 4.8 V at >= 1 us, -8 V >= 6 us, +8 V >= 10 us): rising <= 4.8 V at 1 us holds
  except at L x 0.7 with Cs >= 1.0; falling 4.8 V needs >= 5.1 us at nominal (the 2-4 us bump); -8 V needs 6.7-11.6 us;
  +8 V is not certified anywhere except L x 1.3, Cs x 0.7 (11.6 us).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | validity | pass: 254/254 |
| 2 | fresh test cover90 >= 0.8, accuracy >= 0.9 and >= D63 | pass: 1.00 / 0.85; 0.90 / 0.90 (D63 0.85 / 0.55) |
| 3 | verification 18/20 <= 200 A, none > 205 A | pass: 20/20, max 193.9 A |
Reported: the GP on A138 + scatter runs only (no new active points): cover90 0.95 / 0.90, accuracy 0.90 / 0.85 - the
noise floor fixed calibration; the 160 active runs (96 rising, 64 falling) raised falling accuracy 0.85 -> 0.90.
Predictions: scatter 2-7 A - pooled 4.1 / 1.0 A, from one outlier; rising coverage >= 0.8 - 1.00; falling 0.8-0.9 -
0.85; A138's table shape - kept, tighter on rising +8 V; most '-' cells above 200 A at 20 us - half.

## 2. Limits
- The 2-4 us falling bump and the low-L rising trend are read from 1-3 runs each plus the GP; their mechanism (vff's
  slope gate / the cap's low-pass) is not traced.
- Coss, load steps, four modules and start-up not covered; 20 test points per direction.
