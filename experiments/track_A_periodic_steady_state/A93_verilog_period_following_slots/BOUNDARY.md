# A93 - period-following slots and a missed-slot guard (BOUNDARY)

Track A, `PAPER_LOCKED` (phase shift T/nP) + `CROSS_PAPER_EXTENSION`.
Written before any code or run.

## 1. Question

In A92's m3n run (driver mismatch m = -3.4 ns), phase 4's low side stayed
on for 969 ns and its current reached -826 A. The cause is not the
correctors.
1. **The start-up ends high.** The open-loop mode-S start-up ends at a Vo
   that depends on the actual dead times: 1.02-1.54 V at the handover
   across m.
2. **The period shortens.** The voltage loop then lowers Ton, and the
   period falls to 141 ns.
3. **Phase 4 starves.** The RTL places phases 2-4's low-side turn-offs at
   **fixed** slots 50, 100 and 150 ns after phase 1's turn-on: k·T0/4,
   with T0 = 200 ns, mode S's period. When phase 1 turns on again before
   phase 4's slot, the slot moves with the new reference and never fires.

Also, the first mode-P cycle is about 140 ns in **every** A92 run, so
phase 4's 150 ns slot is skipped once at every handover.

**Do slots that follow the period, and a guard that fires a missed slot,
remove the starvation without changing anything that works?**

## 2. What the papers and earlier work say

- **P24 (Sec. II-B) and P25 (Figs. 1-2): the phase shift is T/nP**
  (paper-locked baseline, `paper_locked/00_boundaries/PAPER_LOCKED_REPRODUCTION_BASELINE.md`).
  T is the switching period, which in this boundary-mode converter varies.
- **The RTL's fixed T0/4 slots are not T/4 in steady state either:** the
  period is 232 ns, so T/4 = 58 ns, not 50 ns. That was A80's
  simplification ("fixed slots").
- **A74 (physical model, older plant)** implemented period-following
  shifts, k·T_meas/N:
  - the period changed by ≤ 0.023 ns and Vo by ≤ 0.45 mV against fixed
    shifts;
  - VCs3 moved slightly.
  - It was a diagnostic and was not adopted.
- **The event map (D43-D50)** uses fixed slots k·T0/N too.

## 3. The change (RTL, opt-in)

A copy of A92's RTL in `rtl/`. A92's files are not modified. Two new
configuration bits, each off by default.

**cfg_slot_follow (mode P).**
- At each phase-1 turn-on, the controller records T_meas = t_on - t_ref
  (the previous turn-on).
- Phase k's slot becomes t_ref + k·T_meas/N.
- The rule applies once two turn-ons have been seen. Before that, and in
  mode S, the configured slots apply.

**cfg_slot_guard (mode P, phases 2..N).**
- A phase in LOW that is waiting for its slot of reference r fires at once
  (fine 0, counted as a late fire) if the reference changes before the
  slot fires.
- The guard fire counts as the new reference's slot. So a phase still
  turns off once per phase-1 cycle.

## 4. Predictions (written before the runs)

All runs use A92's configuration: error-based correctors, 94 ps targets,
gain 1/2, 4.5 ns mode-S dead time and dtl_init. The m3n runs isolate the
two rules; the matrix then re-runs A92's cases with both rules.

| run | follow | guard | m | σ | prediction |
|---|---|---|---:|---:|---|
| g1 | off | off | -3.4 ns | 0 | bit-identical to A92 m3n (gate) |
| m3n_guard | off | on | -3.4 ns | 0 | No starvation: every phase turns off once per phase-1 cycle. During the short-period interval phase 4 fires at the reference change, so the interleaving is distorted but the current is bounded: peak below 250 A and peak Vds below 30 V. |
| m3n_follow | on | off | -3.4 ns | 0 | No starvation after the first mode-P cycle (slots at k·T/4 < T). The handover cycle still skips phase 4 once (T_meas = 200 ns there), as in every A92 run. Peak current at the level of A92's other runs (≤ 200 A). |
| m3n_both | on | on | -3.4 ns | 0 | As m3n_follow, and the handover skip becomes a late fire. Peak current ≤ 200 A. |
| n0, m1p, m1n, m3p, j30, j100 (both) | on | on | as A92 | as A92 | **The steady state moves** (slots 58/116/174 ns instead of 50/100/150 ns), but stays soft. P_rev as A92 (0 W; m3p about 11.8 W). Dither within 0.2 A of A92 for the deterministic runs. The jitter runs keep A92's amplification (not addressed here): 1.65 and 5.51 A ± 30%. |

**Criterion:** no run may cross-conduct. The peak current of every run
should be ≤ 200 A.

## 5. Mathematical model (D51)

D47's map with period-following slots, made self-consistent: the slots
are k·T/4, with T the orbit's own period. The orbit is computed at
A92's error-based fixed point (D50's offsets, m = 0) and compared with
n0. A new script; D47-D50 are not changed.

## 6. Decides / does not decide

Decides:
- whether these two slot rules remove the starvation found in A92;
- what the period-following slots do to the steady state.

Does not decide:
- the start-up itself: an open-loop mode S whose end state depends on m;
- the jitter amplification;
- other loads, and line and load steps.
