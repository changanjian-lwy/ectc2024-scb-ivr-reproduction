# A257 - the adopted peak limit on the 3.813 nH board (N13, 140 A) (BOUNDARY)
Method: cosim. Track A. Written and committed before the runs.
Looked at beforehand:
- A256 was adopted on 2026-10-27 with ocp {110 / 125 / 140 A by L, t_ns 1.0, n_susp 6}. Its stated limit: the 140 A
  level on 3.813 nH was never run (A254 screened none of the N13 reference rows, and A254 / A256 ran no N13 row).
- A246's run_h_r_N13_lm48 at full load, 300-500 us: phase peaks reach 139.8 A, 0.2 A under the level. A limit
  turn-off comes 11 ns after the crossing (t_ns 1 + t_drv 10), and the current rises about 69 x 2.2 / 3.813 = 40 A in
  that time. So a pulse is cut only if its own peak would pass about 180 A. A crossing within 11 ns of the controller's
  turn-off is dropped and not counted.
- A235 (V7, before A244-A246): N13 +4.8 V / 1 us 187.9 A, +62.5 A 180.4 A.

Decision it changes: whether the 140 A level stands for N13 in the final configuration, or the stated limit stays and
the level is revised.

Cheaper check first: the record above (steady 139.8 A; the 40 A rise). No model gives the count's behaviour, so this is
a cosim question.

Budget: 4 runs at 4 jobs, about 50 min (A246's N13 row took 48 min).

## 1. What and why
- Rows, built on A246's cfg_h_r_N13_lm48 (the final configuration on N13, plant V7, one module, 25 C):
  - o125_N13: as k_N0 / A255. Drop line_step, skip and hand_lead_us; add +62.5 A at 500 us (125 % load); end at 620 us.
  - lp48_N13: the same cfg with line_step dv +4.8 V (1 us at 500 us). A235's row where N13 peaked at 187.9 A.
- Arms: h = the final configuration before the limit; s = + ocp {i_a 140, t_ns 1.0, n_susp 6}.
- Not tested: N13 at 1 MHz (A240's train has no N13 row), four modules on N13, 125 C.

## 2. Criteria
- n0: arm s equals arm h before its first fire: turn-ons and high-offs, edge for edge. With no fire, the records are
  equal (A246's same).
- n1: arm h, final configuration on N13:
  - whole peak <= 200 A;
  - ladder deviation <= 1 V after the event;
  - Vo within 1 % over the last 20 us;
  - V_DS <= 40 V.
- n2: arm s against arm h, A256's s2 test:
  - A253's o3: whole and post-event peak <= max(h, 200 A) + 2 A, NEW <= h's, |Vo extreme| <= h's + 2 mV;
  - ladder deviation after the event <= max(h, 1 V) + 0.2 V.

## 3. Predictions (not criteria)
- n0 and n1 hold: o125_N13 about 180 A, lp48_N13 about 185-190 A, ladder within 0.5 V.
- Arm s:
  - o125_N13 fires 0-5 times. If the count does not reach 6, there is no suspension and no kick.
  - lp48_N13 fires a few times and caps near 180-185 A.

## 4. Decision rule
- **n0 fails:** wiring; trace it.
- **n1 fails:** the final configuration has a gap on N13 that is not the limit's; report it and keep it apart from the
  limit.
- **n2 passes:** the 140 A level stands. The "not run" limit is removed from the docs.
- **n2 fails:** measure when and where the limit acts, then report; the user decides on N13's level.
