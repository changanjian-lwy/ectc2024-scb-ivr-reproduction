# A228 - adopting the damped loop: the skipping rows' scatter and arm h's remaining rows (RESULTS)
Boundary: 32d4b80. Records: release records-a228 (36 cosim records, logs). Analysis: a228_analyze.py ->
a228_summary.json. Runs from 32d4b80 (10) and e4f0cd8 (26; docs and the acceptance script only), cosim_sources_modified
False. Plant V7, A222's trims, one module, 25 C unless named. Arms: d0 = the final configuration; k = vff rel_gate 25 +
kd 355 ns/V, dead band 2; h = k + kd_hold 1.

## 0. Verdict
- **Neither arm is adopted: k and h miss q2 on both 10 % rows.** The final configuration stays V7 + A222's trims;
  item 9 stays open with A224's numbers as the best tested.
- **The skipping rows have almost no scatter, and the derivative term moves them** (true valleys, last 20 us, mean
  over the release instants 300.0 / 301.3 / 302.7 / 304.1 us). The upper end, d0 -> k / h:
  - N0 10 %: -13.60 -> -12.22 / -11.85 A;
  - N75 10 %: -14.52 -> -11.70 / -12.18 A.
  d0's four runs agree within 0.1 A (N0) and 0.6 A (N75) at both ends. k and h leave the band's -12 A edge in 2-3 of
  4 runs each; d0 stays inside 8 of 8. No load: all three arms -21.1..-23.1 / -15.6 A, q2 passes.
- **Correction to A227 RESULTS 0**: "the band test resolves the run's own scatter, not the change" was wrong. The
  change is the derivative term's, 1.4-2.8 A on the upper end.
- **Mechanism (N75 10 %, t1, last 20 us)**: the Ton register reaches 4.38 ns in d0, 4.72 ns in k and 4.53 ns in h
  (limit 4.0 ns). Inside a burst Vo moves by 2 codes or more per sample, so the term acts. It adds Ton kicks that phase
  1's low-side learner (at most 2 ns per period) does not follow, and the valleys drift towards zero: the same mechanism
  as A223's ring, at small Ton. The hold at the limit (h) removes only the kicks taken from the limit itself.
- **Arm h's other rows pass q3**: bit for bit arm k on w30_S75h, k_N0, l_N0_p48, l_N0_m80, k_S75h and h_S75_25. It
  differs on u_N0 (58.9 against 58.6 A) and w20_N0 (159.0 against 152.6 A). Every re-application <= 159.9 A.

## 1. Criteria
| row | d0 mean low / high | k (q1, q2) | h (q1, q2) |
|---|---|---|---|
| z_N0_10 | -16.16 / -13.60 | -16.55 / -12.22 (pass, **miss** +1.38) | -16.72 / -11.85 (pass, **miss** +1.75) |
| z_N75_10 | -16.73 / -14.52 | -17.99 / -11.70 (pass, **miss** +2.82) | -17.66 / -12.18 (pass, **miss** +2.34) |
| z_N0_0 | -21.68 / -15.63 | -21.84 / -15.63 (pass, pass) | -21.84 / -15.63 (pass, pass) |
- q3 (arm h): w20_N0 159.0, w30_S75h 153.7 (post), u_N0 58.9, k_N0 181.3, l_N0_p48 179.3, l_N0_m80 165.3, k_S75h
  192.9 A, h_S75_25 handover 153.2 A; A227's w0_N0 / w5_N0 / w5_N75 152.5 / 153.1 / 159.9 A - all pass e1-e4.

## 2. Predictions
- Held: arm k misses on N0 10 %'s upper end (+1.38 A, registered 1.2-2); h bit for bit k on the five full-load rows;
  u_N0 within 3 A of k.
- Missed: d0's spread (0.1-0.6 A at the 10 % rows' ends, not about 1 A; the no-load lower end 1.7 A, t0 the outlier);
  arm h passing q2; w30_S75h differing from k (it is bit for bit; its Ton register stays >= 11.9 ns); w20_N0 within
  3 A of k (+6.4 A).

## 3. Limits
- One module, 25 C, three skipping rows; the derivative term's action inside bursts read from the Ton register over
  one 20 us window per arm.
