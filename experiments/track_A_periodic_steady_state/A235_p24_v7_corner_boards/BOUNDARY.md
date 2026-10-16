# A235 - the final configuration on plant V7 for the boards V7 has not run: F0, S0, N13 (BOUNDARY)
Method: cosim (cfg only; code as at 63d7c8b).
Track A. Written and committed before the runs. Looked at beforehand: boards.py rebuilds the adopted N0, N75 and S75
cfgs exactly from A194's boards (only out / note / t_end differ), so the same builder gives F0, S0 and N13.
Decision it changes: which columns of FINAL_SPEC_COVERAGE Section 3 can be stated on the final plant and controller.
Since V6 the ff (F0), ss-at-L0 (S0) and L x 1.3 (N13) columns rest on V5 records only (V5: ff +4.8 V / 1 us 181.8 A,
ss 178.7 A, L x 1.3 188.7 A; hot 179.3 A).
Cheaper check done first: none - no model below the cosim carries the V6 drive and the mode-S trim. Budget: 3 runs to
160 us, then 14 runs to 200-620 us, about 1.5 h at 10 jobs.

## 1. What and why
- Boards (one module): F0 = fast devices at L0 (drive x 0.8), S0 = slow devices at L0, N13 = nominal at 1.3 L0;
  r_core (2 pi 8 MHz)^2 L / 2.557e6 (2.90 / 2.90 / 3.77 ohm); skipping and the 0.7 us handover lead on F0 and N13 (not
  slow), none on S0, as the final configuration states them per corner.
- Mode-S trim (A188: Vo(143.5 us) = 1.035 V at 25 C, locked for other temperatures): V6 / V7 moved it by -0.24 / -0.20
  ns (N0 / N75) and +0.39 ns (S75) from V5. Stage 1 starts each board at its corner's mean shift (nominal and fast
  -0.22 ns, slow +0.39 ns).
- Rows (stage 2, 25 C): +4.8 V / 1 us, -4.8 V / 1 us, +62.5 A, -8 V / 10 us at 500 us; S0 at 125 C its start-up and
  +4.8 V / 1 us. One step position each.
- Not tested: other temperatures for F0 / N13, other step positions, four modules on these boards.

## 2. Criteria
- Trim rule (stage 1 -> 2): dton += round((1.035 - Vo(143.5 us)) / slope / 31.25 ps) x 31.25 ps, slope 53.5 mV/ns
  (nominal, fast), 54.5 mV/ns (slow) - A206's measured slopes; recorded in a235_trims.json before stage 2 runs.
- c1 (stage 2, every run): completes, whole-run peak <= 200 A, V_DS <= 40 V, no overlap or shoot-through, Vo <= 1.05 V
  before 300 us, Vo within 1 % over the last 20 us, no NEW oracle event after the event.
- c2 (stage 2, 25 C start-ups): Vo(143.5 us) within 1.035 +- 0.002 V.

## 3. Predictions (not criteria)
- Stage 1 Vo(143.5 us) within 1.035 +- 0.006 V on every board (one or two trim steps off).
- Stage 2 +4.8 V / 1 us: F0 180-186 A, S0 178-185 A, N13 186-192 A; S0 125 C 180-190 A; other rows <= 185 A.

## 4. Decision rule
- c1 and c2 pass: the ff, ss (L0) and L x 1.3 columns move to V7 with the final controller for these rows.
- A miss is traced before the column moves; the V5 numbers stay labelled as V5.
