# A229 - the derivative term held within a band above the lower Ton limit (RESULTS)
Boundary: 82e9a1e (code + boundary). Records: release records-a229 (20 cosim records, logs). Analysis: a229_analyze.py
-> a229_summary.json. Runs from 82e9a1e (14) and 092b377 (6; D83 docs and a docstring outside the cosim sources),
cosim_sources_modified False. Plant V7, A222's trims, one module, 25 C unless named. Arm b = vff rel_gate 25 + kd 355
ns/V, dead band 2, kd_hold 1, kd_band_ns 4.0; d0 = A228's records of the final configuration at the same instants.

## 0. Verdict
- **Adopted as registered: j1 and q1-q4 pass.** The final configuration becomes V7 + A222's trims + vff rel_gate 25 +
  kd 355 ns/V (dead band 2 codes) + kd_hold 1 + kd_band_ns 4.0. Item 9 closes.
- **The skipping rows are back at d0** (true valleys, last 20 us; mean over the four release instants, b against d0):
  - N0 10 %: -16.10 / -13.80 A against -16.16 / -13.60 A;
  - N75 10 %: -16.23 / -14.33 A against -16.73 / -14.52 A;
  - no load: -21.49 / -15.63 A against -21.68 / -15.63 A.
  Every 10 % run stays inside -20..-12 A (8 of 8; A228's k / h: 3-4 of 8). The Ton register's maximum over the last
  20 us is 4.19-4.38 ns, at or below d0's at the same instant (4.19-4.41 ns; A228's k up to 4.72 ns).
- **Item 9, the re-applications from light load to full load**: N0 from 0 / 5 / 20 % 153.9 / 159.8 / 149.3 A, N75
  from 5 % 159.6 A (final configuration without gate and term, A223: 223.6 / 248.3 / 214.0 / 232.1 A); S75 at 125 C
  +175 A from 30 % 153.7 A after the step (A223: 181.0 A). u_N0 (+62.5 A from 5 %, the specified step) 58.6 A.
  No overlap or shoot-through; Vo within 1 % at the end of every row.
- **The re-application peak moves by up to 10 A between arms that differ only near the limit** (w5_N0 163.4 / 153.1 /
  159.8 A in k / h / b; w20_N0 152.6 / 159.0 / 149.3 A): all stay at or below 163.4 A, 37 A under 200 A.
- **Full-load rows are arm h bit for bit** (k_N0, k_S75h; also w30_S75h): the band never acts there.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| j1 | unit 109 / 109, cosim_regression --quick and --full bit for bit | pass |
| q1 | skipping runs failing, b against d0 | 0 against 0 on every row - pass |
| q2 | b's mean lowest >= d0's - 1 A, mean highest <= d0's + 1 A | N0 10 % +0.06 / -0.20; N75 10 % +0.50 / -0.19; no load +0.19 / 0.00 A - pass |
| q3 | e1 / e2 / e4 on the six re-application rows | pass |
| q4 | k_N0, k_S75h bit for bit arm h | pass |

## 2. Predictions
- Held: part S means within 0.5 A of d0 (largest 0.50 A, N75's lower end); part I bit for bit; w30_S75h bit for bit
  arm h; w0_N0, w5_N75 and u_N0 within 3 A of arm h.
- Missed: the Ton register's maximum within 0.1 ns of d0 (3 of 12 runs 0.19 ns lower); w5_N0 and w20_N0 within 3 A of
  arm h (+6.7 / -9.7 A).

## 3. Limits
- One module, 25 C (S75 at 125 C on w30). The gate and the derivative term have now run on: A223-A229's rows (N0 / N75
  / S75 re-applications, +62.5 A steps, +4.8 V / 2 us, -8 V / 10 us, S75 125 C +4.8 V / 1 us, two start-ups, three
  skipping rows) and A225's items 2 / 5 / 6 (arm k). The rest of the coverage tables (device corners, L x 0.7 / 1.3,
  other temperatures, four modules) ran without them.
