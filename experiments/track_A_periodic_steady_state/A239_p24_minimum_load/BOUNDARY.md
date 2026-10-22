# A239 - the minimum load (5 A, 2 % per module) on the rows A237 did not run (BOUNDARY)
Method: mixed (cosim on plant V7; a first-principles return time Co ΔV / I checked against it).
Track A. Written and committed before the runs. Looked at beforehand: A230 / A231 start-up summaries, A237's records
(c2_N0's return and skipping valleys, to place m3 / m4's thresholds).
Decision it changes: whether item 6b closes as a stated condition, "at least 5 A per module on nominal boards, start-up
and 125 C included", or the minimum has to be raised or limited to the conditions that pass.
Cheaper check done first: the return time of a paused module is the load's discharge of Co, t = Co (V_pk - 1.01 V) / I
(A237 c2_N0: 43.5 us predicted, 43.4 us from its peak in the record). Budget: 8 runs, one wave, ~35-60 min.

## 1. What and why
- Item 6b: below its lower Ton limit a module pauses with every switch off and cannot sink current, so only the load
  takes an overshoot back (A237: 0 A stays at 1.058 V; A238's sink mode latched on N75, not adopted). A237 showed 5 A
  (2 %) returning within 1 % 47.5 us after a full-load release, on N0 at 25 C only.
- Not yet run at 5 A: a start-up (the original 6b row: a start into 1 kOhm ends at 1.018-1.043 V), N75, 125 C. One row
  at 2.5 A (1 %) tests the 1 / I scaling the stated condition will use.
- Rows (final configuration, nominal boards, one module, A231's 0.7 us handover lead; cfgs from make_cfgs.py):
  - u5_N0, u5_N75 (25 C), u5_N0h, u5_N75h (125 C): start-up into 0.2 Ohm (5 A at 1 V) from t = 0, to 300 us.
  - c2_N75 (25 C), c2_N0h, c2_N75h (125 C): release from 250 A at 300 us to a true 5 A current (A237's method).
  - c1_N0 (25 C): the same release to 2.5 A.
- Not tested: slow boards (30 % minimum, they do not reach the Ton limit at 10 %), four modules (the slaves do not
  follow a pause), 0 C, line steps while paused, a load that changes slowly.
- No code change: runs from committed code, no identity check needed.

## 2. Criteria
| # | rows | criterion |
|---|---|---|
| m0 | all | provenance.cosim_sources_modified False |
| m1 | all | COMPLETED, whole-run gate-level peak <= 200 A, V_DS <= 40 V, 0 overlaps, 0 shoot-throughs |
| m2 | all | Vo within 1 % of 1 V over the last 20 us |
| m3 | c2_*, c1_N0 | time from the overshoot's peak to Vo's last exit from 1 % within 15 % + 3 us of Co (V_pk - 1.01 V) / I (Co 4.672 mF, I the constant current) |
| m4 | c2_*, c1_N0 | skipping valleys (A221 true_valleys, last 60 us) within -20..-12 A |
| m5 | u5_* | time from Vo's maximum to its last exit from 1 % <= 60 us |

## 3. Predictions (not criteria)
- Start-ups: Vo max N0 1.052-1.054 V, N75 1.047-1.049 V, each 125 C row within 1.5 mV of its 25 C row (A230: N0 into
  0 / 10 % 1.0534 / 1.0518 V, N75 into 0 % 1.0487 V; A231: 125 C at 30 % within 0.5 mV of 25 C). N0 rows above the
  start-up's 1.05 V reference for 2-6 us. Back within 1 % 30-45 us after the maximum. Handover peaks <= 110 A.
- Releases: N75 / N75h +44..+47 mV, back within 1 % 33-40 us after the release; N0h +55..+59 mV, 45-52 us; c1_N0 +55..+58 mV,
  88-96 us. Valleys -16.5..-14.5 A. Every whole-run peak is the start-up / handover's (<= 165 A).

## 4. Decision rule
- All pass: the coverage's load-range row and item 6b state the condition: at least 5 A per module on nominal boards
  (start-up and 125 C included), return time Co (V_pk - 1.01 V) / I; item 6b closes. The scorecard's T35 follows.
- m3 misses: the formula is not stated; the measured times are.
- m1 / m2 / m4 / m5 miss on a row: the condition excludes that row's case, traced first.

## 5. Note added after the commit, before any result (2026-10-22)
Lesson 8's threshold check was done late, on A230's records: at start-up the overshoot is brief and the module itself
pulls it down (N0 into 0 %: 1.0534 V, 1.017 V 5 us later, then 1.0218 V paused), and N0 into 10 % hovers near 1.01 V
with its last exit from 1 % 62.5 us after its maximum. So m5's 60 us sits on that reference, and the start-up's return
is not the load's discharge from the peak. The criteria and predictions stay as registered; RESULTS will state m5
against this.
