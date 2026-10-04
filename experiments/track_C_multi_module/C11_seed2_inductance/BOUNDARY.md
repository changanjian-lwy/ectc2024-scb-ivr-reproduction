# C11 - the four-module final design (vff seed 2) at L x 1.2 and 1.3 (BOUNDARY)
Track C. Written and committed before any C11 run. Looked at beforehand: C08's l12a / l12q_s_p62, A137's s130 rows,
C10's L0 rows (ladder references), and the analysis run on C08's l12q record.
Decision it changes: whether the four-module final design's L claim (C08: holds L x 1.2) carries over to the adopted
seed 2, and whether seed 2 also removes C08's L x 1.2 handover (rail 1 17.2 V for 52 us, start-up 210-213 A).
Cheaper check done first: A137's single-module L x 1.3 rows (seed 1 = seed 2, C10) hand over cleanly from the same
1136 seed although the need is ~1600 (rail 12.8 V, 152-179 A, 0 late fires). Budget: 4 runs in parallel, ~30 min.

## 1. What and why
- C08 ran four modules at L x 1.2 only on s_p62, without the restart: no lock in operation (ladder 1.12 %, Vo 1.000),
  but every module's rail 1 at 17.2-17.3 V for 52 us in the handover and whole-run peaks 210-213 A (> 200 A).
- At L x 1.2 the steady Ton is ~1450, above the seed's cap 1.25 x 1136 = 1420, so phase 1 may start capped; the
  single module at L x 1.3 shows the low-pass catches up without a lock.
- Runs (cfg = C10's row, every module's L x k; steps at 1000 us, end 1400 us; m3n ends 1200 us): l120_s_p62 (= C08's
  l12q_s_p62 but for seed), l120_m3n (handover stress), l120_l_p48_1us (the rising row, highest peaks above L0),
  l130_s_p62. Phase 1 is timed from 767 us (four modules, L x 1.2) / 813 us (one module, L x 1.3): the steps land in
  the operating mode.
- Not tested: L x 0.7-0.9 (the handover there is mode S's fixed Ton, the next line of work); the other C06 rows.

## 2. Criteria (every run)
1. Every module's rail 1 (mode P, before 242 us) <= 13.5 V and above 13.3 V for <= 5 us (C10's G1, now on the master
   too: C10's master <= 12.56 V).
2. Whole-run peak <= 200 A.
3. No lock: A134's rule on every module against C10's same row at L0 (ladder deviation over the last 200 sections
   <= reference + 0.5 points: s_p62 0.93 %, m3n 0.61 %, l_p48_1us 0.47 %; Vo within 1 %).
4. l120_s_p62's post-step peak within 7 A of C08's l12q (177.8 A).
5. Late fires <= 100 per run, no overlap.
The analysis on C08's l12q record: 1 and 2 fail, 3 and 5 pass.

## 3. Predictions
- Like A137's s130: rail 1 <= 13.0 V, whole-run peaks 160-190 A (C08 l12q 210-213 A), late fires below C08's 54.
- No lock; l120_s_p62 ladder ~1.1 % as C08's l12q; post-step 175-182 A.
- l120_l_p48_1us 180-195 A (A136 single module, rising rows <= 189 A at L x 1.15 / 1.3).
- l130_s_p62: as l120, ladder up to ~1.3 %.

## 4. Decision rule
- 1-5 pass: the four-module final design's L claim reads L x 1.0-1.3 with the handover inside the limits (MULTI_MODULE
  SUMMARY Section 8, CURRENT_STATUS item 52, scorecard T16).
- 3 fails: the L claim is withdrawn to what passes, traced before anything else.
- 1, 2 or 5 fail with 3 passing: the operating-mode claim stands (C08), the handover at that L is listed as open.
