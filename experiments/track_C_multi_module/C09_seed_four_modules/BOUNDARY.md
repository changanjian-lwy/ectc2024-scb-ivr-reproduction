# C09 - the four-module final design with the adopted vff setting (BOUNDARY)
Track C. Written and committed before any C09 run. Looked at beforehand: C06 / C08 records (m3n, s_m25, all
steady windows), A137 RESULTS.
Decision it changes: whether the four-module final design takes the adopted single-module setting (vff rel_q8 320,
rel_lp 1, seed 1), so that both levels carry one version of scb_vff.
Cheaper check done first: C08's two open steady/step items traced on the existing records (below), no new run.
Budget: 19 four-module runs, two batches at 10 jobs, ~40 min; at most 3 contingency reruns (criterion 3).

## 1. What and why
- C08 (A136's cap, no restart) held the hard limits but left three items: handover late fires on every row, m3n's
  end-window turn-off current sd 0.11 A (C06 0.01 A), s_m25 +7.3 A after the step. A137's restart (seed 1) removed
  the handover regression on one module at L0 / L x 1.3 and was adopted by the user on 2026-10-04.
- Traced before this boundary (C08 records):
  - **m3n is the voltage loop's quantisation limit cycle, not the cap.** Master Ton 1209 -> 1203 (one period) -> 1208
    (~9 periods) -> 1214 (one period) -> 1209, every 20-50 periods, in all 16 phases at once: the P kick of one ADC
    code (kp x 0.5 mV = 5.69 Ton LSB) plus one integral step. The ADC rounds to 0.5 mV (decision levels vref +-0.25
    mV): C08's Vo reaches +0.269 / -0.255 mV, C06's stays within +0.160..+0.202 mV at the same Ton 1209. The two runs
    differ in the learned timed turn-off (master dlo1 14569 vs 14573 LSB), i.e. in the start-up path. C06 itself shows
    the same cycle on ls_p10 (20 Ton changes, Vo +0.267 / -0.279 mV), so it predates the cap.
  - **s_m25's step lands at a different point of the cycle:** C06's 101.8 ns before phase 1's turn-on, C08's 81.3 ns
    after it; C08's 153.4 A is the master's phase 1 1.47 us after the step, C06's 146.1 A comes 13 us after it.
    A129 measured 2-7 A from moving a step by under a period.
- Rows: C06's 18 with {rel_q8 320, rel_lp 1, seed 1} in every module, C06's timing (steps at 800 us). Plus
  c06al_s_m25: C06's s_m25, design unchanged, step at 800.1831 us (C08's offset after the master's phase-1 turn-on).
- Analysis: C08's (c06_analyze.analyse on C09's records, C05-identity criterion dropped), with C06's whole-run peak
  criterion restored (C08 judged peaks only after 600 us because of A136's start-up regression).
- Not tested: L corners with four modules (C08 settled the lock; A137 the single-module corners); Cs / Coss corners.

## 2. Criteria
1. Hard constraints on the 18 rows: no overlap, whole-run peak <= 200 A, locked, post-step peak <= 200 A. Every
   other C06 criterion passes wherever it passed in C06 (no new failure), with one rule for sd_band: a miss whose
   master end window shows the limit cycle (>= 2 Ton codes and the sampled Vo beyond vref +-0.25 mV) is reported as
   the limit cycle, not counted as a new failure; any other sd_band miss counts.
2. The handover regression is gone: every row's late-fire total <= 1.5 x C06's same row + 6 (C08: n0 13 vs 0, m3n 509
   vs 68).
3. Every stepped row's post-step peak within 7 A of C06's row. A row above that is rerun with C06's design and the
   step moved to C09's offset after the master's phase-1 turn-on (at most 3 reruns), and is compared with that rerun.
4. c06al_s_m25's post-step peak within 2 A of C08's s_m25 (153.4 A): C08's +7.3 A is the step's offset, not the cap.

## 3. Predictions
- Late fires and start-up peaks back to C06's (A137 at L0: m3n 11, start-up 163-182 A on one module).
- Post-step peaks within the 2-7 A step-offset floor of C06's rows.
- m3n's sd: the cycle depends on where the start-up leaves Vo in the ADC code, so 0.01 or ~0.11 A; not predicted.
- c06al_s_m25: 151-156 A.

## 4. Decision rule
- 1-4 pass: the four-module final design is C06 + vff {rel_q8 320, rel_lp 1, seed 1}; MULTI_MODULE_SUMMARY and
  CURRENT_STATUS item 52 say so. A limit cycle seen under criterion 1 goes on the scorecard as an open item of the
  loop's quantisation (ADC 0.5 mV vs Ton 31.25 ps), shared with C06.
- 1 or 2 fails on some row: the row's mechanism is traced before any adoption; the single-module adoption stands.
- 4 fails: s_m25's difference is not the step offset; traced in C09's RESULTS before adoption.
