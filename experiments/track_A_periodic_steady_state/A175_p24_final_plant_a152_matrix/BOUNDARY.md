# A175 - the final gate-level plant on the rest of A152's matrix at nominal devices (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, threshold-form driver interlock; frozen RTL controller;
cfg only)
Track A, package layer. Written and committed before the runs. Looked at beforehand: A173 (all rows), A163's S50
rows (V2: high-side gates at 2.5 ohm, no lead).
- On the final plant, A152's 13-row matrix at nominal devices lacks six rows: -4.8 V / 1 us, L x 1.3 load step,
  +4.8 V over 2 / 3 / 5 / 10 us. They ran only on V1 (A152) and V2 (A163).
- No 3.0 ohm V2 run of these rows exists. On the two rows both A163 and the final plant ran, the final plant's
  post-step peak is +0.5 / +4.7 A (l_p48_1us / slew4) and its |Vo extreme| +1.6 / +4.0 mV. That is the drive
  (3.0 ohm, 8 ns lead), not a defect.
Decision it changes: whether "the final plant at nominal devices passed A152's whole matrix" can be stated (coverage
table, Mihai summary). Cheaper check done first: none (cfg-only system rows). Budget: 6 runs, --jobs 6 once A174's
first wave frees the cores, ~2 h wall.

## 1. What and why
- Rows: nom slew10 / slew5 / slew3 / slew2 / l_m48_1us (A164's nominal trim 39.615 ns) and nom L13_s_p62 (A173's
  L x 1.3 re-trim 40.916 ns). Built as A173's cfgs (identity-checked against A173's nom_slew4 and
  nom_L13_l_p48_1us).
- Not tested: these rows at the other device corners.

## 2. Criteria (reference: A163's s50 run of the same row)
1. Whole-run V_DS <= 40.0 V.
2. Vo(143.5 us) 1.035 +- 0.02 V; physical start-up and handover <= 200 A.
3. Post-step physical peak <= 200 A; 0 overlaps, 0 shoot-throughs, COMPLETED; late <= 1.5 x A163 + 5; NEW 0.
4. |Vo extreme| <= |A163| + 5 mV (the drive offset above + A168's 2 mV); where > 11 mV, back within 1 % <= A163 + 5 us.

## 3. Predictions (not criteria)
- Post-step A163 + 1-5 A: slew10 181-185, slew5 179-183, slew3 / slew2 178-182, l_m48_1us 167-172, L13 s_p62
  180-184 A. Vo extreme A163 + 2-4 mV. Late 0-5. Interlock holds 0 (nominal devices; A173's nominal rows had none).
- Start-up / handover as A173's nominal board (162.1 / 149.7 A) and L x 1.3 board (146.5 / 137.2 A).

## 4. Decision rule
- All six pass: the coverage table states the final plant passed A152's 13-row matrix at nominal devices.
- Any miss: that row is named open on the final plant, with its mechanism.
