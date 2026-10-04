# C10 - seed every module's low-pass with the Ton before mode P (BOUNDARY)
Track C. Written and committed before any C10 run. Looked at beforehand: C06 / C09 records (rails, post-step peak
periods), A137 records, and a dry run of c10_analyze.py on C06's and C09's records.
Decision it changes: whether the four-module final design and the single-module adopted setting share one scb_vff
(vff {rel_q8 320, rel_lp 1, seed 2}); if not, the four-module design keeps C06's absolute cap, which locks at L x 1.2 (C08).
Cheaper check done first: RTL unit tests (80/80); the single-module identity rows and the three gate rows run before the rest.
Budget: batch 1 = 6 single + 3 four-module runs (~22 min); batch 2 = 15 four-module + 12 single (~45 min);
at most 3 contingency reruns (~22 min). 10 jobs (EEK5101 VM down).

## 1. What and why
- C09: the slaves enter mode P 30-80 ns after the master, after its first ADC sample has moved the broadcast Ton
  1136 -> 683; seed 1 restarts ton's low-pass (tlp) from the Ton at the restart sample, so a slave's relative cap starts
  near 0.7 of the need: slave rail 1 13.8-15.4 V, 19-30 us above 13.3 V, whole-run peaks up to 203.5 A.
- RTL (scb_vff, cfg vff "seed": 2): register tpre follows ton at reset and while en is low; at the restart sample tlp
  starts from tpre instead of the sample's ton; lp2, lp20 and the prediction restart as with seed 1. scb_ctrl's ton_now
  is cfg_ton in mode S, so every module's tlp starts at cfg_ton (1136) whatever its entry time. cfg_vff_seed is 2 bits
  (scb_ctrl; scb_multi regenerated); the seed 0 / 1 paths are unchanged. Unit tests 80/80, new: Ton 133 -> 200 at en's
  rise gives phase 1 166 = 1.25 x 133 with seed 2, 200 with seed 1.
- Single module: seed 1 takes Ton at the first Vin sample after entry; if the loop has not moved Ton by then (C09's
  master: balanced rails), seed 2 equals seed 1 bit for bit. Rows: A137's 18 cfgs (L x 0.7 / 1.0 / 1.3 x m3n, m1n, n0,
  l_p48_1us, l_p48_5us, s_p62) with seed 2.
- Four modules: C06's 18 rows + vff {rel_q8 320, rel_lp 1, seed 2} in every module, C06's timing (steps at 800 us);
  the cfgs are C09's but for seed. Gate rows n0, m1n, m3n first.
- Not tested: four-module L corners (C08 settled the lock at L x 1.2 with this cap); Cs / Coss corners.

## 2. Criteria
S. Single-module identity: each s100 record equals A137's (every field but cfg, provenance, wall_s); then s070 / s130.
Gate (n0, m1n, m3n; all must pass before batch 2's four-module rows):
G1. Every slave's rail 1 (vin - vcs[0], sections in mode P before 242 us) <= 13.5 V and above 13.3 V for <= 5 us.
G2. Whole-run peak <= max(185 A, C06's row + 3 A) (m1n: 187.3 A).
G3. Late fires <= 1.5 x C06's row + 6 (C09's criterion 2).
Full, 18 rows: C09's criteria 1-3 unchanged (hard limits and no new failure, sd_band read as the ADC limit cycle when the
master's end window shows it; late fires as G3; post-step peak within 7 A of C06's row, a row above that rerun with C06's
design and the step at C10's offset, at most 3 reruns, and compared with the rerun), plus
4. G1 on every row; G2 on the 9 rows without a step (the stepped rows share n0's start-up).
Deviation from the hand-off's gate (13.0 V, 185 A): C06's own slaves reach 13.06-13.16 V on m1n / m3n (3.7-5.3 us above
13.0 V), its master 13.53 V, and C06's m1n peaks at 184.3 A. The thresholds sit clear of C06 and of C09's lock: the dry
run passes every criterion on C06's records and fails G1-G3 on all three gate rows with C09's.
Observation (not a criterion): l_p48_5us's post-step peak. C09's (184.6 A, slave 1 phase 1, +32.17 us) and C06's at
C09's offset (176.1 A, master phase 1, +35.30 us) both come right after two low-side turn-offs 6 ns apart and two
turn-ons (the second at 0 V, 21-22 A). The analysis records module, phase and this pattern for each stepped row's peak.

## 3. Predictions
- Single module: 18/18 identical to A137.
- Four modules: every slave like the master: rail 1 <= 13.2 V (C09's master 12.3-13.0 V), whole-run peaks 163-185 A,
  late fires at C06's level or below (C06 m3n 68; A137 single module 11).
- Post-step peaks within the 2-7 A offset floor of C06's; l_p48_5us 175-180 A.
- m3n's ADC limit cycle: not predicted (depends on the start-up path).

## 4. Decision rule
- S fails on s100: traced before any four-module run of batch 2.
- Gate fails: no batch 2 four-module rows; traced on the gate records; the four-module design stays C06.
- S, gate and 1-4 pass: four-module final design = C06 + vff {rel_q8 320, rel_lp 1, seed 2}; the single-module adopted
  setting becomes seed 2 (identical records); MULTI_MODULE_SUMMARY, CURRENT_STATUS item 52, scorecard T16, scb-map.
- s070 / s130 differ from A137: the single-module setting changes only where the records are identical; the rest traced.
- 1-3 fail on stepped rows only: traced first; adopted only if the miss is the step-offset floor (contingency rerun).
