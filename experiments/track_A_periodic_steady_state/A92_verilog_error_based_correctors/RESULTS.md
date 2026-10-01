# A92 - error-based correctors that tolerate the gate driver (RESULTS)

Track A, `CROSS_PAPER_EXTENSION` + `LITERATURE_METHOD`.

**Boundary:** `BOUNDARY.md`.
- Sections 1-8 were written before any code or run.
- Section 9 (the jitter-variance correction) was written after the runs
  were launched, while no result file existed.

**Records:**
- `cosim/run_*.json`, configurations `cosim/cfg_*.json`;
- `a92_summary.json` (from `a92_analyze.py`);
- the m3n diagnostic replay `cosim/dbg_m3n_transient.json`;
- unit tests `tb/`, synthesis `synth/stat_scb_ctrl.txt`.

**Model: the physical model at implementation level.**
- A92's RTL: A89's, plus the two opt-in bits.
- A92's bridge: A91's, with the driver model, plus the error reports.
- A88's plant: datasheet Coss(V), reverse drop, 25 C.

**The mathematical-model counterpart is D50**
(`symbolic_derivations/03_P24_native/D50_P24_ERROR_BASED_CORRECTORS.md`).

**All runs:**
- 5%, from a zero start to 388.61 us, stop on any cross-conduction;
- runs other than g0 use BOUNDARY Section 3's configuration: both bits on,
  targets 94 ps, gain 1/2, dtl_init and mode-S dead time 4.5 ns.

## 0. Verdict

1. **The error-based correctors remove A91's failure mode.**
   - No run cross-conducted. A91 stopped on cross-conduction in m3p, m3n,
     m1n and both s45 runs.
   - All eight runs completed. Every phase turned on predictively once per
     cycle, and Vo was regulated to 1.000 V.
   - **The actual edges sit where Section 6 says, whatever m is.** The
     low-side edge lands 0.103-0.111 ns after the crossing (target
     0.094 ns plus LSB rounding) at m = 0, ±1 and -3.4 ns. The command
     dead time absorbs m: 0.06-0.28 ns at m = +1, 1.06-1.28 ns at m = 0,
     2.06-2.28 ns at m = -1, 4.47-4.69 ns at m = -3.4.
   - **P_rev is 0 W at m = 0, ±1 and -3.4 ns.** A91 had 4.30 W at
     m = +1.
   - **At m = +3.4 ns the floor binds**, as predicted: 11.79 W. D50 gives
     11.77 W.
   - The dither at m = 0, ±1 and ±3.4 ns is 0.43-0.75 A, against 0.91 A in
     A89 r2. Criterion 2 (steady state) is met in full.
2. **The gate passes.** With both bits off and no driver model (g0), the
   run is bit-identical to A89 r2. Unit tests: 32 of 32, including A89's 26
   unchanged. Synthesis is clean (check: 0 problems).
3. **Two problems remain, and neither is a corrector failure in mode P.**
   - **(a) A start-up hazard: m3n, 826 A.** The open-loop mode-S start-up
     ends at a Vo that depends on the actual dead times. At the handover it
     is 1.02 V (m = +3.4) up to 1.54 V (m = -3.4).
     - The voltage loop then shortens the period, and in m3n the period
       fell to 141 ns.
     - The RTL's fixed slots put phase 4's low-side turn-off 150 ns after
       phase 1's turn-on. Each new phase-1 turn-on moved the slot before
       it fired.
     - So phase 4's low side stayed on for 969 ns, and its current ran to
       -826 A, with 34 V on SH4 (Section 4).
     - No cross-conduction is involved. The A80 design rule "fixed slots"
       has no guard for a period shorter than the last slot.
   - **(b) Jitter is still amplified.**
     - The dither is 1.65 A at σ = 30 ps (A91: 2.75 A) and 5.51 A at
       100 ps (A91: 4.73 A). Both are above criterion 2's 1 A.
     - The losses stay small: 0.09 W of reverse conduction and an
       estimated 0.03-0.10 W of hard turn-ons at 100 ps.
     - The cause is on the high side (Section 5). The valley time is not
       constant, as D50's scalar loop assumed: it moves with the previous
       edges through the circuit. Even with no jitter the high side
       alternates between two errors, 0.19 and 0.03 ns.
4. **So for the driver factor:**
   - the correctors are now correct and safe in mode P;
   - the start-up and slot rule need a fix before the full mismatch range
     is safe;
   - the jitter tolerance needs a closed-loop design: corrector and
     circuit together.

## 1. Gate and implementation

| check | result |
|---|---|
| g0 (bits off, no driver) against A89 r2 | 1747 of 1747 sections, maximum \|Δv\|, \|Δi\| = 0, \|Δt\| = 0; equal final registers |
| unit tests | 32 of 32 (A89's 26 unchanged; new: error update, both clamps, the high-side restart base, bits off) |
| synthesis (yosys) | check: 0 problems; 38456 cells, against A89's 30721 (the subtractors, shifters and clamps of 4 phases × 2 correctors) |

## 2. Mismatch runs (last 50 cycles)

| run | m | P_rev (W) | low-side edge after the crossing, mean ± sd (ns) | command dtl, phases 1-3 / 4 (ns) | high-side error, mean ± sd (ns); early | dither (A) | Ton (ns) | Vo at the handover (V) | peak current / Vds | A91, same m |
|---|---:|---:|---|---|---|---:|---:|---:|---|---|
| g0 | - | 0 | 0.014 ± 0.015 | 1.16-1.22 / 0.97 | 0.191 ± 0.017; 50% | 0.91 | 17.750 | 1.125 | 173 A / 27.0 V | - |
| n0 | 0 | 0 | 0.105 ± 0.004 | 1.25-1.28 / 1.06 | 0.117 ± 0.065; 1.5% | 0.71 | 17.750 | 1.264 | 186 A / 26.8 V | (g0) |
| m1p | +1 | 0 | 0.105 ± 0.004 | 0.25-0.28 / 0.06 | 0.110 ± 0.058; 0.5% | 0.43 | 17.750 | 1.178 | 175 A / 26.7 V | 4.30 W, dither 2.35 A |
| m1n | -1 | 0 | 0.103 ± 0.004 | 2.25-2.28 / 2.06 | 0.110 ± 0.063; 1.0% | 0.46 | 17.719 | 1.349 | 197 A / 26.8 V | cross-conduction at 138 us |
| m3p | +3.4 | **11.79** | 2.32 ± 0.08 (floor) | 0 / 0 | 0.116 ± 0.069; 2.0% | 0.75 | 18.156 | 1.017 | 152 A / 26.7 V | cross-conduction (mode S; with 4.5 ns: 0.5 us after the handover) |
| m3n | -3.4 | 0 | 0.111 ± 0.004 | 4.66-4.69 / 4.47 | 0.110 ± 0.063; 0% | 0.64 | 17.750 | **1.539** | **827 A / 34.0 V** | cross-conduction (mode S; with 4.5 ns: at the handover) |

**Readings:**
1. **The fixed point does not depend on m** (D50 Section 2).
   - The low-side edge sits at crossing + 0.103-0.111 ns in every run where
     the floor is free.
   - The command dead time is crossing - m + target: n0 1.06-1.28 ns,
     m1p lower by 1.0 ns, m1n higher by 1.0 ns, m3n higher by 3.4 ns.
   - This is the reverse of A89's rule, which put the actual edge at
     crossing + m.
2. **m3p: the floor binds** (dtl = 0 on all four phases). The low side
   lands 3.4 ns after the turn-off, 2.32 ns after the crossing.
   - P_rev is 11.79 W, within the predicted 11-13 W. D50 gives 11.77 W.
   - Ton rises 0.41 ns to pay for it. D50 gives +0.44 ns.
3. **The high side lands 0.11-0.12 ns after the valley** (target 0.094).
   - A two-cycle alternation remains: in n0, 0.19 / 0.03 ns. Section 5
     discusses it.
   - The turn-on Vds is unchanged: means 8.89-9.09 V, maximum 9.27 V.
4. **The dither falls** to 0.43-0.75 A. A89 r2 has 0.91 A, where the high
   side alternates between early and late.
5. **The cost: the settling after the handover is slower.** It takes
   117-125 us at m = 0, -1 and -3.4 ns, against 67.5 us in g0. The 4.5 ns
   mode-S dead time raises Vo at the handover (Section 4); the voltage loop
   (ki unchanged) needs longer.

## 3. Jitter runs (last 50 cycles)

| | g0 | n0 | j30 | j100 | A91 j30 / j100 |
|---|---:|---:|---:|---:|---:|
| low side: early / beyond 0.16 ns after the crossing | 12.9% / 0 | 0 / 0 | 0.5% / 12.7% | 34.2% / 35.6% | - |
| low-side error, crossed edges, mean ± sd (ns) | 0.014 ± 0.015 | 0.105 ± 0.004 | 0.108 ± 0.050 | 0.172 ± 0.112 | - |
| high side: early | 50% | 1.5% | **19.7%** | **37.1%** | - |
| high-side error, mean ± sd (ns) | 0.191 ± 0.017 | 0.117 ± 0.065 | 0.207 ± 0.144 | 0.341 ± 0.236 | - |
| valley time, phase 2, sd (ns) | - | 0.046 | 0.098 | 0.185 | - |
| phase-2 current at its low-side turn-off, sd (A) | - | 0.18 | 0.55 | 1.43 | - |
| P_rev (W) | 0 | 0 | 0.004 | 0.091 | 0.000 / 0.055 |
| hard turn-on estimate (W) | < 0.001 | 0 | < 0.001 | 0.03-0.10 | 0.004-0.012 / 0.05-0.17 |
| **dither (A)** | **0.91** | **0.71** | **1.65** | **5.51** | **2.75 / 4.73** |
| period spread, last 20 (ns) | 0.28 | 0.47 | 1.86 | 6.27 | 2.84 / 6.19 |
| high-side turn-on Vds, maximum (V) | 9.22 | 9.20 | 9.57 | 10.53 | 9.72 / 10.65 |

**Readings:**
1. **The low side behaves as D50 predicts at 30 ps.** Its error sd is
   0.050 ns, against σ_e = 49 ps. Early edges are rarer than predicted
   (0.5% against about 3%). Beyond-window edges are a little more frequent
   (12.7% against about 9%). At 100 ps: 34% early and 36% beyond, against
   about 28% and 34%.
2. **The high side does not.** At 30 ps, 20% of its edges are early,
   against about 3% for a constant valley.
3. **Why the high side does not (an interpretation consistent with the
   numbers, not isolated by a separate run):**
   - The valley time itself moves from cycle to cycle. Its sd is 0.046 ns
     with no jitter, 0.098 ns at 30 ps and 0.185 ns at 100 ps, comparable
     with the 94 ps target.
   - It moves with the current at the low-side turn-off, whose sd grows
     from 0.18 to 0.55 and 1.43 A.
   - That current depends on the previous edges of all phases. So the
     high-side corrector chases a target that the corrected edges
     themselves move.
   - The early branch's 0.2 ns step adds kicks on top.
   - D50's scalar loop takes the valley as fixed. The closed loop of
     correctors and circuit is the missing model.
4. **Net:** better than A91 at 30 ps (1.65 against 2.75 A), worse at
   100 ps (5.51 against 4.73 A). The loss stays below 0.2 W.

## 4. The m3n transient (diagnostic replay)

**The replay.** `dbg_m3n_transient` repeats m3n to 96.3 us with every
applied edge logged from 88.7 us. It is identical to the full run: 495
sections, |Δi| = 0.

1. **The start-up ends high.**
   - Mode S is open loop: fixed Ton, period and dead times.
   - With m = -3.4 ns and a 4.5 ns mode-S dead time, the actual dead times
     are 1.1 ns (high-off to low-on) and 7.9 ns (low-off to high-on).
   - In the longer dead time the high side conducts in reverse, which
     lengthens the effective on-time. Vo at the handover is 1.539 V.
   - Across the runs, Vo at the handover follows the low-off to high-on
     dead time:

     | run | Vo at the handover (V) |
     |---|---:|
     | m3p | 1.017 |
     | g0 | 1.125 |
     | m1p | 1.178 |
     | n0 | 1.264 |
     | m1n | 1.349 |
     | m3n | 1.539 |

   - A91's m3n_s45 had the same start: 1.556 V at 88.61 us.
2. **The voltage loop then shortens the period.** It lowers Ton (533 to
   451 LSB by 92.1 us), so phase 1's current reaches its target sooner.
   - The shortest period after the handover cycle falls in the same
     order: 222, 196, 193, 178, 163 and 126 ns.
   - In m3n it stays at 141-142 ns from 92.0 to 92.8 us.
3. **Phase 4 starves.**
   - Its low-side turn-off is slotted 150 ns after phase 1's turn-on (A80,
     T0/4 multiples of mode S's 200 ns).
   - With a 141 ns period, the next phase-1 turn-on (which updates t_ref)
     arrives before the slot fires, and the slot moves with it.
   - Phase 4's SL stayed on from 91.998 to 92.967 us (969 ns). Its current
     fell linearly to -709 A at the next section, and to -826 A in a second
     episode at 96.03 us.
   - Turning off -700 A slewed the node to 34 V (SH4) and 28.7 V (SL4).
   - It also displaced the flying capacitors: VCs3 rose from 12 V to as
     much as 26.1 V. From 102 us on, every section has phase currents
     below 200 A and VCs3 within 1 V of 12 V.
4. **m1n came within 13 ns of the same limit:** a shortest period of
   163 ns, phase-4 current at most 125 A.

**The starvation is independent of the corrector type.** It follows from
Vo at the handover and the slot rule. A91's m3n_s45 would have met it as
well had it not stopped at the handover.

## 5. Predictions against outcomes

| prediction (BOUNDARY) | outcome |
|---|---|
| g0 bit-identical to A89 r2 | **Confirmed.** |
| Fixed point independent of m; dtl about 0.05-0.26 (m1p), 2.0-2.3 (m1n), 4.4-4.6 ns (m3n) | **Confirmed:** 0.06-0.28, 2.06-2.28, 4.47-4.69 ns. |
| n0: soft, P_rev about 0, no early low-side edges, dither ≤ 0.91 A | **Confirmed:** 0 W, 0 early, 0.71 A. |
| m1p / m1n as n0, no cross-conduction | **Confirmed:** 0 W, dither 0.43 / 0.46 A. |
| m3n: runs to the end, no cross-conduction, steady state as n0 | **Confirmed**, but with a transient that was not predicted: 826 A (Section 4). |
| m3p: floor binds, P_rev about 11-13 W, no cross-conduction | **Confirmed:** 11.79 W. |
| j30: P_rev about 0.01 W, low side about 3% early and 9% beyond (Section 9), **dither ≤ 1.2 A** | Losses and low side confirmed (0.004 W, 0.5%, 12.7%). **Dither wrong: 1.65 A.** |
| j100: < 0.3 W, low side about 28% early and 34% beyond, **dither below 4.73 A** | Losses and low side confirmed (about 0.2 W, 34%, 36%). **Dither wrong: 5.51 A.** |
| No run stops on a cross-conduction | **Confirmed.** |

## 6. Limits

- **The sensors are ideal.**
  - The error reports have no comparator delay or offset, and are rounded
    to 31.25 ps.
  - Gate sensing on the low side and node-collapse sensing on the high
    side are assumed, as in APEC 2023's detector.
  - A comparator delay would add a fixed bias to each error. The error
    form would then learn the bias as part of the target.
- **The rest of the model is ideal too.** Switches have zero rise and fall
  times, and there are no gate-loop dynamics.
- **Coverage is narrow.**
  - The mismatch is static and the same on all phases.
  - The jitter is Gaussian, per edge, with sensitivity values.
  - One load (5%), one start-up sequence.
- **The parameters are fixed.** Targets (94 ps), gain (1/2) and the early
  steps are `PROJECT_DECISION`s, not optimised.

## 7. Next

In order, one at a time:
1. **Start-up and slots (the 826 A hazard).** Two options:
   - a slot that is never skipped: a pending slot fires when t_ref changes
     before it;
   - or slots that follow the measured period (A74's period-following
     rule).

   Either should be checked against the Vo-at-handover range found here
   (1.02-1.54 V). A start-up that does not depend on m (closed loop, or
   handover on Vo) is the alternative to read about first.
2. **Jitter: the closed loop of correctors and circuit.**
   - In the mathematical model: extend D47's map Jacobian with the
     corrector states, and find the closed-loop eigenvalues. This should
     explain n0's two-cycle alternation and the jitter gain.
   - Then choose the gain, steps and targets. This belongs to the
     system-level checkpoint.
3. **Negative command dead time** for m = +3.4 ns (the 11.8 W at the
   floor), if the worst-case mismatch matters for the design.
