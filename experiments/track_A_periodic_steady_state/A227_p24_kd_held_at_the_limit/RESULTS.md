# A227 - the derivative term held at the lower Ton limit (RESULTS)
Boundary: 3341c47 (code + boundary). Records: release records-a227 (7 cosim records, logs). Analysis: a227_analyze.py
-> a227_summary.json. Runs from 3341c47, cosim_sources_modified False. Plant V7, A222's trims; held arm = vff rel_gate
25 + kd 355 ns/V (dead band 2) + kd_hold 1; z_N0_10_d0 = the final configuration as it is.

## 0. Verdict
- **Not adopted as registered: h1 misses on N75 10 % and h2 on w5_N0.** The final configuration stays V7 + A222's
  trims, without the gate and the derivative term; item 9 stays open with A224's numbers as the best tested.
- **The hold does what it was for on N0**: N0 10 % true valleys -16.8..-12.2 A (A224 without the hold -16.8..-11.6 A,
  s3t now passes); N0 no load -23.1 A (h1 against A226's -22.8 A passes).
- **N75 10 % moves the other way**: -18.5..-11.2 A (A224 -18.0..-12.1 A), 0.8 A over the band's -12 A edge. Both
  10 % rows sit within about 1 A of the band edge with or without the hold: the band test resolves the run's own
  scatter, not the change.
- **h2 as I wrote it is two-sided**: w5_N0 falls 163.4 -> 153.1 A (-10.3 A, Vo -35.7 -> -34.1 mV), outside +-5 A;
  w0_N0 152.5 A unchanged, w5_N75 158.1 -> 159.9 A. All three <= 200 A, Vo within 1 % at the end.
- **The missing reference**: the final configuration (new trim, no gate, no kd) at N0 10 % gives -16.2..-13.6 A
  (s3t passes): A224's 0.4 A miss on that row was the derivative term's.

## 1. Criteria
| row | result |
|---|---|
| j1 | unit 108 / 108, regression quick + full bit for bit - pass |
| z_N0_10_h (h1) | s1, s2, s3t (-16.8..-12.2), z1r 0.23 A - pass |
| z_N75_10_h (h1) | s1, s2, z1r 0.27 A; s3t -18.5..-11.2 A - **miss** |
| z_N0_0_h (h1) | s1, s2; true valleys -23.1 A >= -23.8 A - pass |
| w0_N0_h / w5_N0_h / w5_N75_h (h2) | 152.5 / 153.1 / 159.9 A; against A224 0.0 / **-10.3** / +1.8 A |
| z_N0_10_d0 (information) | -16.2..-13.6 A, s3t passes |

## 2. Limits
- One run per row: the skipping rows' valley bands move by about 1 A between configurations that differ only in
  what the derivative term does between pauses; a criterion at the band's edge needs more than one run per arm.
