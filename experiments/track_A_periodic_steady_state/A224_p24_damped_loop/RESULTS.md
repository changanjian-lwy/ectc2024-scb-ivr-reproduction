# A224 - a damped voltage loop for large load steps (RESULTS)
Boundary: c0ca36d (code + boundary), Section 5 and stage 2 4a2f2ab. Records: release records-a224 (22 cosim records,
logs). Analysis: a224_analyze.py -> a224_summary.json. Runs from c0ca36d (stage 1) and 4a2f2ab (stage 2),
cosim_sources_modified False. Final configuration on plant V7 (A222's trims) + vff rel_gate 25 (A223) + the
derivative term; references d0 = A223's g25 records (A224's code without kd reproduces them bit for bit).

## 0. Verdict
- **Not adopted as registered: e5 misses on two skipping rows; everything else passes at kd 355.** The two misses
  are traced in A226 / A227 (one is my reference, the other open there).
- **The derivative term removes the ring and item 9's excess**: the re-applications from light load to full load
  give 152.5 / 163.4 / 152.6 / 158.1 A (N0 from 0 / 5 / 20 %, N75 from 5 %; A223 150.0 / 214.4 / 218.0 / 219.2 A),
  S75 125 C +175 A from 30 % 153.7 A after the step (158.3); Vo's dips shrink by 2-13 mV, and Vo is within 1 % at
  the end of every row.
- **Unchanged where specified**: +62.5 A on N0 181.3 A (Vo -13.9 -> -12.8 mV), +62.5 A from 5 % 58.6 A (58.0),
  +4.8 V / 2 us 179.3 A (178.5), -8 V / 10 us 165.3 A (168.3), S75 125 C +4.8 V / 1 us 192.9 A (193.0); start-up
  and handover within 1.9 A (S75 25 C 151.3 -> 153.2 A).
- **kd has a ceiling at the hot slow handover**: S75 125 C's handover 178.9 / 187.0 / 276.6 A at kd 355 / 440 / 530
  (d0 180.0 A; records cosim/run_k_S75h_d355.json, run_h_S75h_d440.json, run_k_S75h_d530.json). At 530 the term
  drives Ton to 52 ns while Vo falls from the 1.045 V request, Vo undershoots to 0.993 V and the valleys are lost.
  355 sits 1.24-1.5x below that edge on this board.
- **More late fires**: after the S75 125 C handover 12 -> 74 in 40 us, after the re-applications 30 -> 72 (N0 5 %),
  104 -> 166 (N0 20 %); no overlap or shoot-through, V_DS <= 32.3 V.
- **e5**: N75 10 % passes; N0 no load -23.1 A against the registered -22.2 A (A221 - 1 A) - A226: the final
  configuration without kd gives -22.8 A, the reference had the old N0 trim; N0 10 % s3t misses, true valleys
  -16.8..-11.6 A against -20..-12 A (A221 with the old trim -16.8..-13.5 A). Ton leaves its 4.0 ns limit while
  skipping in both records, up to 4.41 ns in A221 and 4.91 ns here: the term acts on the skipping (A227).

## 1. Criteria
| row | kd 355 (d0 -> kd) | result |
|---|---|---|
| j1 | unit 107 / 107, regression quick + full, i_u_N0_g25 = A223's record | pass |
| w5_N0 / w20_N0 / w5_N75 (e1, e4) | 214.4 -> 163.4 / 218.0 -> 152.6 / 219.2 -> 158.1 A | pass (kd 530: 157.0 / 151.5 / 164.9) |
| w0_N0 / w30_S75h (e1, e4) | 150.0 -> 152.5 / post 158.3 -> 153.7 A | pass |
| k_N0 / u_N0 (e2, e4) | 181.3 -> 181.3 / 58.0 -> 58.6 A; -13.9 -> -12.8 / -10.1 -> -8.4 mV | pass (kd 530 k_N0 181.2) |
| l_N0_p48 / l_N0_m80 / k_S75h (e3, e4) | 178.5 -> 179.3 / 168.3 -> 165.3 / 193.0 -> 192.9 A | pass; kd 530 k_S75h e4 **miss** (276.6) |
| h_S75_25 (e4, Section 5) | handover 151.3 -> 153.2 A, Vo max 1.0351 V | pass |
| h_S75h_d440 (information) | handover 180.0 -> 187.0 A | - |
| z_N75_10 (e5) | s1, s2, s3t (-18.0..-12.1), z1r 0.25 A | pass |
| z_N0_0 (e5) | s1, s2; true valleys -23.1..-15.6 A | **miss** vs -22.2 (A226: reference) |
| z_N0_10 (e5) | s1, s2, z1r 0.23 A; s3t -16.8..-11.6 A | **miss** by 0.4 A |
- The skipping cfgs carry no snapshot (make_cfgs drops snap_us); the loss books read the circuit's snapshot from
  A221's record of the same row (same board, V7, same r_core), as a224_analyze notes.

## 2. Predictions
- Held: kd 355's w rows within 185-205 A or below (152.6-163.4, lower), line rows within 1 A at 355, start-up /
  handover within 1 A (1.9 A at S75 25 C), kd 530 +2-5 A on k_N0 (-0.1: missed).
- Missed: kd 530 below 195 A everywhere (its handover); the skipping rows within 2 A of A221 (no-load -1.9 A,
  10 % valleys' upper end +1.9 A).

## 3. Limits
- One module, one step position per row, 25 C except S75 at 125 C. The kd margin was probed on one board.
