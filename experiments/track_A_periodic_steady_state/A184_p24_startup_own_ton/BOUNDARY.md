# A184 - A183's start-up with mode S's own Ton: the loop keeps the validated seed and clamps (BOUNDARY)
Method: mixed (cosim, plant V5: EPC2067 gate model on all eight switches, threshold interlock 1.0 ns; RTL change
authorised by the user on 2026-10-09: scb_ctrl cfg_ton_s / scb_vff tseed, code e1cf0a7; cfg: t0_ns 200, ton_s_ns =
A183's trims, ton_ns = each board's validated t0 = 400 ns trim)
Track A, package layer. Written and committed before the runs.
Decision it changes: whether a 200 ns mode-S period with its own per-board trim becomes the start-up spec.
FINAL_SPEC would then say that L x 0.75 holds at the slow corner (+4.8 V / 1 us, 25 / 125 C, tested points) and
that the four-module start-up is covered.
Cheaper check done first: A183 (the coupling, measured); unit tests 89/89 (mode_s_own_ton); cosim_regression --full
PASS; an A183 start-up rerun with the new code (no ton_s_ns) bit for bit. Budget: 14 runs, --jobs 6, ~3 h.

## 1. What and why
- A183: t0 200 ns balances the ladder on all seven boards, and S75 passes 200 A (135.7 / 151.0 / 192.1 A). It was not
  adopted, because ton_ns (now the 200 ns trim, 0.55-1.1x the loop's steady Ton) also set the loop's reset value,
  scb_vff's seed and the 0.5x / 2x clamps. N13 sat at 1.83x its trim against a 2x clamp, and the handover Vo
  dipped to 0.954 V.
- Now: mode S runs at ton_s_ns; ton_ns = the validated trim, so mode P's seed and clamps are those of the A164-A181
  design. Mode S is unchanged from A183 (g0). After settling, mode P should be the validated design (c5), so the
  earlier mode-P coverage carries over.
- Runs (A183's conditions and positions; step at 500 us + k T / 3):
  - Full runs (+4.8 V / 1 us, end + 400 us): S75 25 C k = 0, 1, 2; S75 125 C; N0 25 C.
  - To 500 us: S0, N75, N07, N13, F0 at 25 C; N0, S0, F0 at 125 C (trims locked at 25 C); four nominal modules
    (A173's m4 cfg, t_il 1.0 ns).
- Not tested: other rows (falling ramps, load steps, -8 V); four modules at the corners; below 25 C.

## 2. Criteria (every module of the four-module run)
 g0 Sections before mode P's entry equal A183's run of the same board and condition, bit for bit (the 10 runs A183 also ran).
 c1 Start-up (before mode P) and handover (entry .. + 25 us) physical peaks <= 200 A.
 c2 Post-step peak <= 200 A (full runs).
 c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs and overlaps.
 c4 Vo(143.5 us) in 0.99-1.17 V (A163's window; hot runs use the locked 25 C trims).
 c5 Mode P is the validated design: the mean per-phase peak over 450-495 us lies within +-2 A of the same board's
    t0 = 400 record at the same temperature (a184_analyze.REF; F0 125 C has none and is reported only).
 c6 The handover is no worse: Vo's minimum over entry .. + 50 us >= the reference record's minimum - 5 mV.
Diagnostic: ladder max/min at entry, peaks between entry + 25 us and the step, the loop's Ton at entry vs steady.

## 3. Predictions (not criteria)
- g0 holds: mode S never reads cfg_ton.
- First mode-P Ton ~ ton_ns + kp x (1.0 - 1.035 V) ~ ton_ns - 12 ns: S75 31 ns (steady 32.3), N07 23.4 (21.4),
  N0 27.2 (32.3), N13 28.5 (43.3). Handover Vo minima therefore within ~5 mV of the t0 = 400 records (N13 / S0
  ~0.98, the rest >= 0.99); S75 above its reference's 0.961. Handover peaks <= 180 A everywhere.
- Locked trims hot: Vo(143.5) +60..+100 mV (A183 S75 +95), so 1.09-1.14 V, inside c4 with >= 25 mV margin.
- Four modules: each ladder <= 1.05, start-up <= 150 A, handover <= 185 A.
- c5 within 1.5 A (A183's full runs: 0.0-1.4 A at 400-495 us).

## 4. Decision rule
- g0 fails: code defect. Stop, fix, rerun; nothing else is read.
- c1-c6 pass: adopt t0 200 ns + per-board mode-S trim (cfg_ton_s) with ton_ns as before. Update FINAL_SPEC (start-up
  row; L x 0.75 at the slow corner, tested points), docs and the acceptance gate.
- c4 fails only on hot runs: adopt for 25 C and name the hot limit (the locked mode-S trim needs temperature
  compensation at 200 ns).
- c5 or c6 fails: the separate Ton does not restore the validated mode P. Not adopted; the mechanism is named.
- Only the four-module run fails c1 / c3 / c6: adopt for one module; four modules are named open.
