# A91 - gate-driver timing non-idealities in the P24 module (RESULTS)

Track A, `CROSS_PAPER_EXTENSION` + `EXTERNAL_DEVICE_DATA`.

**Boundary:** `BOUNDARY.md`.
- Sections 1-7 were written before any run.
- Section 8 was written after the runs were launched, before any result
  was read.
- Section 9 was written after m3p and m3n stopped, before m3p_s45 and
  m3n_s45 ran.

**Records:**
- `cosim/run_*.json`, with configurations `cosim/cfg_*.json`;
- `a91_summary.json` (from `a91_analyze.py`).

**Model: the physical model at implementation level.**
- The A89 RTL, unchanged: `cfg_low_pred = 1`, `cfg_blank` = 20 ns, FB 7.
- A copy of A89's bridge (`cosim/test_cosim.py`) with an opt-in driver
  model:
  - low-side edges are applied m later than high-side edges;
  - each edge gets independent Gaussian jitter σ, from a seeded RNG;
  - a cross-conduction check: a turn-on applied while the complementary
    switch still conducts. The runs stop on the first one.
- A88's plant: datasheet Coss(V), reverse drop, 25 C.

**The mathematical-model counterpart is D49**
(`symbolic_derivations/03_P24_native/D49_P24_DRIVER_MISMATCH_OFFSET.md`).

**All runs:** 5%, the A89 r2 settings (timed low side, 20 ns blanking,
asynchronous phase-1 path, learning at restarts, ki 0.25 ns/V), from a zero
start to 388.61 us. The handover to mode P is at 88.804 us.

## 0. Verdict

1. **The adopted controller does not tolerate the datasheet driver
   mismatch.** Every run with a static mismatch except m = +1 ns stopped
   on a cross-conduction (an applied turn-on while the complementary
   switch still conducted).
   - **m = ±3.4 ns (LMG1210 maximum):** P24's fixed 2.15 ns start-up dead
     time is shorter than the mismatch. Both runs overlapped in mode S,
     within 62 ns of the start.
   - **With a 4.5 ns start-up dead time:**
     - m = -3.4 ns overlapped at the first mode-P edge, as predicted.
     - m = +3.4 ns overlapped 0.5 us after the handover, which was not
       predicted. A handover transient made one high-side swing take
       1.2 ns, and the corrector learned that time.
   - **m = -1 ns (typical, low side faster):**
     - 94% of the low-side turn-ons were hard: Vds mean 4.7-5.9 V, an
       estimated 2.0-6.9 W.
     - It then overlapped at 138 us. Phase 4's crossing (0.98 ns) is
       shorter than |m|.
   - **m = +1 ns (typical, low side slower):** ran to the end with no
     overlap.
     - The low side lands 1.0 ns after the crossing, and P_rev is
       **4.30 W**. D49 gives 4.31 W.
     - The high side runs the sawtooth of BOUNDARY Section 8.
     - The dither is 2.35 A, against 0.91 A without the driver model.
2. **The mechanism** (Section 8). Both correctors **set** their delay to a
   time measured from an actual edge, but add it to a command time. A
   static mismatch m is therefore never learned. The actual dead time on
   the faster side is the natural transition time - |m|, with no floor.
   This confirms BOUNDARY Section 3. A89's hypothesis that a mismatch "is
   learned into dtl" is false.
3. **Jitter does not cost loss, but it multiplies the dither.**
   - Neither σ = 30 ps nor σ = 100 ps caused an overlap.
   - P_rev is at most 0.06 W, and every phase is still predictive once
     per cycle.
   - The dither rises from 0.91 A to 2.75 A (σ = 30 ps) and 4.73 A
     (σ = 100 ps), against criterion 2's 1 A threshold
     (`PROJECT_DECISION`).
   - The correctors turn tens of picoseconds of jitter into 0.2-0.6 ns
     timing steps.
4. **The gate passes.** With the driver model off (g0), the bridge
   reproduces A89 r2 bit-identically.
5. **So the driver is a factor the current controller cannot absorb.**
   Before the next factor at this level, the correctors need:
   - an error-based update;
   - a dead-time floor;
   - a start-up dead time above the maximum mismatch.

   See Section 10.

## 1. The gate (g0)

g0 runs the A91 bridge with no `driver` entry. Against A89 r2 it gives:
- 1747 of 1747 sections, maximum |Δv|, |Δi| = 0 and |Δt| = 0;
- equal final registers: `dt_pred`, trim, Ton, late fires, asynchronous
  fires, steps, peak Vds and peak current.

**The bridge additions are inert when off.**

## 2. Maximum mismatch with P24's fixed start-up dead time (m3p, m3n)

Both runs stopped on a cross-conduction in mode S, before the handover.
Mode S uses P24's fixed dead time of 2.15 ns at both transitions.

| run | m | stop | where | arithmetic (edges applied at command + 10 ns, low side + m) |
|---|---:|---:|---|---|
| m3n | -3.4 ns | 25.41 ns | phase 1: SL turned on while SH conducted (high-off to low-on) | SH off at t + 10; SL on at t + 2.15 + 10 - 3.4 = t + 8.75. Overlap 1.25 ns. |
| m3p | +3.4 ns | 62.16 ns | phase 2: SH turned on while SL conducted (low-off to high-on) | SL off at t + 13.4; SH on at t + 2.15 + 10 = t + 12.15. Overlap 1.25 ns. |

**Correction.** BOUNDARY Section 9 gives m3p's overlap at 76 ns. The
record (`first_overlap`) says 62.16 ns, phase 2, SH. The amendment is left
as written.

**Finding.** LMG1210's mismatch applies to both transition pairs. A fixed
dead time therefore has to exceed the maximum mismatch plus margin in both
directions. P24's 2.15 ns does not exceed 3.4 ns.

## 3. Start-up dead time 4.5 ns (m3n_s45, m3p_s45)

**m3n_s45 (m = -3.4 ns): as predicted.**
- It stopped at 88.825 us. That is the first mode-P high-off to low-on,
  21 ns after the handover: phase 1, SL turned on while SH conducted.
- dtl still had its start value, 2.156 ns. So the actual dead time was
  2.156 - 3.4 = -1.24 ns.

**m3p_s45 (m = +3.4 ns): not as predicted.**
- Section 9 predicted that it would run to the end.
- It stopped at 89.327 us, 0.52 us after the handover: phase 4, SH turned
  on while SL conducted.

The mechanism, from the records:
1. In this run's handover transient, phase 4's low side turned off at
   -155.6 A (89.1095 us). At 5% in steady state that current is about
   -6 A.
2. With that current the node swings in about 1.2 ns.
   - The high-side corrector measured the end of the swing 1.22 ns after
     the actual low-side turn-off.
   - It set dt_pred4 to that time: the final register value is 1.219 ns.
3. The next phase-4 high-side command therefore came 1.22 ns after the
   low-side turn-off command. The low-side edge is 3.4 ns slower, so the
   high side turned on 2.18 ns before the low side turned off.
4. Phases 2 and 3 were at the edge.
   - Their dt_pred was 3.406 and 3.469 ns, so the actual dead times were
     0.006 and 0.069 ns.
   - Their last high-side turn-ons were hard, at 11.9 V and 11.1 V: the
     node had not yet moved.

**Finding.** The high-side corrector has no floor. A transient that makes
one swing faster than m is enough for a cross-conduction.

## 4. Typical mismatch, low side faster (m1n, m = -1 ns)

**It stopped at 137.97 us** on a cross-conduction: phase 4, SL turned on
while SH conducted. That is 49 us after the handover, while Vo was still
recovering: Vo had reached a minimum of 0.939 V, against 0.956 V in A89 r2.

**Up to that point the low side ran the limit cycle predicted in Section
3.**
- Of 914 mode-P low-side edges, 860 (94%) came before the zero crossing
  and 54 at or after it.
- The early edges turned on at Vds mean 4.7-4.8 V (phases 1-3) and 5.9 V
  (phase 4); the maximum was 12.1 V.
- The cycle:
  - a late edge resets dtl to the measured crossing time;
  - the next edge is then 1 ns early;
  - the early rule adds 62.5 ps per cycle (the 0.05 ns step, quantised);
  - after about 16 cycles the edge passes the crossing again.

  Observed: 13-14 late edges in 227-229 cycles per phase, one per 16-18
  cycles.

**The hard turn-on loss is estimated, not simulated.** The plant does not
record a channel's dissipation when it turns on at a positive Vds.
- Per early edge, at its recorded Vds, the loss lies between two bounds:
  - lower bound: Eoss(Vds) of the three low-side devices (78 nJ at
    4.7 V);
  - upper bound: Qoss(Vds)·Vds of the five devices on the node (263 nJ at
    4.7 V).
- Both bounds use the datasheet Coss(V).
- Summed edge by edge over the 49.1 us of mode P, the loss is about
  **2.0-6.9 W**. This interval is the handover transient.

**The cross-conduction.** Phase 4's crossing comes 0.978 ns after the
actual high-side turn-off. That is less than |m|. D47's steady-state orbit
gives 0.96 ns for phase 4, and 1.15-1.17 ns for phases 1-3.

The last phase-4 edges, in ns after the actual high-side turn-off:

| edge | time (ns) | Vds at the edge (V) |
|---|---:|---:|
| early | 0.688 | 3.39 |
| early | 0.750 | 2.88 |
| early | 0.813 | 1.91 |
| early | 0.875 | 1.28 |
| early | 0.938 | 0.30 |
| late (crossing at 0.978 ns) | 1.000 | -0.27 |

After the late edge:
- dtl4 was reset to 0.969 ns (31 LSB);
- the next low-side edge came 0.031 ns **before** the actual high-side
  turn-off.

The checker stops on any overlap, and with ideal switches 31 ps is a
short across the flying capacitor. With real gate ramps, which are not
modelled, the effect of so short an overlap is not decided here. The
margin, however, is zero:
- phase 4 crosses in under 1 ns;
- phases 1-3 have only 0.15-0.17 ns to spare.

**The high side in m1n.** Its edges are |m| late relative to the valley,
a fixed point of the late rule.
- Turn-on Vds mean by phase, in mode P up to the stop: 8.6, 8.9, 9.5 and
  9.8 V.
- At the valley it is 8.9-9.1 V (D47).

## 5. Typical mismatch, low side slower (m1p, m = +1 ns), against D49

The run completed with no overlap. Last 50 cycles, against g0 and D49
(m = 1 ns, low side at crossing + m, high side at its natural valley):

| | g0 (m = 0) | **m1p** | D49 (m = 1 ns) | m1p - D49 |
|---|---:|---:|---:|---:|
| low-side edge after the crossing, mean [min, max] (ns) | 0.014 [0.003, 0.051] | **0.996 [0.974, 1.021]** | 1 (imposed) | - |
| reverse time per low-side edge, phases 1-3 / 4 (ns) | 0 | 0.768-0.773 / 0.833 | 0.780-0.782 / 0.841 | -0.012 / -0.008 |
| **P_rev (W)** | 0 | **4.30** | **4.31** | -0.01 |
| Ton (ns) | 17.750 | 18.000 | 17.922 | +0.078 |
| period (ns) | 231.97 | 231.63 | 231.76 | -0.13 |
| phase 4 at its turn-off, mean [min, max] (A) | -5.87 [-6.32, -5.39] | -5.89 [-7.64, -5.23] | -5.84 | -0.05 |
| high-side turn-on Vds, mean (max) by phase (V) | 8.90-9.06 (9.22) | 8.88-9.08 (9.33) | 8.93-9.07 | - |
| high-side delay after the actual low-side turn-off, phase 2, min-max (ns) | 9.03-9.28 | 8.22-9.59 | - | - |
| dither (A) | 0.91 | **2.35** | - | - |
| Vo (V) / settling after the handover (us) | 0.9999 / 67.5 | 1.0001 / 60.6 | 1 | - |

**Readings:**
1. **The low side settles at the crossing + m, a fixed point,** as
   BOUNDARY Section 3 predicted. There are no early edges.
2. **The two models agree on the loss within 0.01 W, and on the reverse
   time within 0.012 ns.**
3. **The high side runs the sawtooth of Section 8.**
   - Phase 2's delay climbs by 0.19 ns per cycle, from about 8.3 to
     9.6 ns, and is reset after 6-7 cycles.
   - Against g0, the mean high-side delay moves by -0.49, -0.28, -0.43
     and -0.41 ns (phases 1-4). The prediction was about
     -m/2 = -0.5 ns.
   - The turn-on Vds hardly moves (+0.1 V at the maximum), because the
     valley is flat.
   - The sawtooth is what moves the currents: the dither is 2.35 A, and
     the period spread over the last 20 cycles is 2.91 ns against
     0.29 ns.
4. **Ton is 0.078 ns (2.5 LSB) above D49.** In g0 the difference from D47
   is 0.003 ns. D49 leaves out the high-side sawtooth, which is a likely
   cause. That is not tested.

## 6. Jitter (j30, j100)

No overlap. Last 50 cycles:

| | g0 | j30 (σ = 30 ps) | j100 (σ = 100 ps) |
|---|---:|---:|---:|
| low-side edges at or after the crossing / early | 175 / 26 | 140 / 64 | 124 / 80 |
| early edges: Vds mean, max (V) | 0.15, 0.16 | 0.34, 1.02 | 1.10, 3.63 |
| late edges: offset after the crossing, mean, max (ns) | 0.014, 0.051 | 0.054, 0.239 | 0.139, 0.574 |
| P_rev (W) | 0 | 0.00 | 0.06 |
| hard turn-on estimate (Section 4 method, last 1000 edges) (W) | < 0.001 | 0.004-0.012 | 0.05-0.17 |
| high-side turn-on Vds, max (V) | 9.22 | 9.72 | 10.65 |
| phase 4 at its turn-off, min / max (A) | -6.32 / -5.39 | -6.94 / -3.90 | -9.18 / -1.19 |
| **dither (A)** | **0.91** | **2.75** | **4.73** |
| period spread, last 20 cycles (ns) | 0.29 | 2.84 | 6.19 |
| Vo ripple, last 20 cycles (mV) | 0.02 | 0.23 | 0.65 |
| Ton (ns) / Vo (V) | 17.750 / 0.9999 | 17.750 / 0.9999 | 17.781 / 1.0000 |
| every phase predictive once per cycle | yes | yes | yes |

**Readings:**
1. **The loss stays small.**
   - The low side's free window after the crossing (0.16-0.23 ns at
     25 C, D48) absorbs most of σ = 30 ps.
   - At σ = 100 ps some late edges pass it: 0.06 W of reverse
     conduction.
   - Some early edges turn on at up to 3.6 V: an estimated 0.05-0.17 W.
2. **The dither does not stay small.** It triples at σ = 30 ps.
3. **The amplification has an interpretation, consistent with the delay
   traces but not isolated by a separate run.** Both correctors are
   asymmetric: "late: set to the measured time; early: add a step".
   - Even g0 sits in a two-cycle alternation: phase 2's high-side delay
     alternates 9.03 / 9.22 ns.
   - With jitter, an edge that lands a few picoseconds before the event
     counts as early. It adds a full step: 0.2 ns on the high side, 62.5
     ps on the low side.
   - The next measurement then resets it.
   - So 30 ps of jitter becomes high-side delay excursions of 0.6 ns on
     phase 2 (8.88-9.49 ns, against 9.03-9.28 ns), and the phase currents
     follow.

## 7. Predictions against outcomes

| prediction (where) | outcome |
|---|---|
| A static mismatch is not learned. It reappears as an offset of m (Section 3). | **Confirmed.** m1p: low side +0.996 ns. m1n: the limit cycle. |
| m = +1 ns: P_rev about 4-6 W, soft switching kept (Section 3). | **Confirmed:** 4.30 W, soft, no overlap. But the dither rose to 2.35 A, which was not predicted. |
| m = +3.4 ns: P_rev about 18-22 W (Section 3). | **Not reached** in the co-simulation (stopped). D49 gives 17.92 W. |
| m < 0: a limit cycle of mostly hard low-side turn-ons (Section 3). | **Confirmed** for m = -1 ns: 94% early. **Not predicted:** the cross-conduction when the crossing time (0.98 ns) is shorter than \|m\|. |
| The high side runs a sawtooth from valley - m to the valley, mean about -m/2 (Section 8). | **Confirmed in form** (m1p): range 1.2-1.4 ns. The mean shift is -0.28 to -0.49 ns, against -0.5 ns. |
| m3n_s45 stops at the handover (Section 9). | **Confirmed:** 21 ns after the handover. |
| m3p_s45 runs to the end (Section 9). | **Wrong.** The high-side corrector learned a 1.22 ns swing time in a handover transient (Section 3). |
| σ = 30 ps: little effect (Section 3). | **Wrong for the dither** (0.91 to 2.75 A). Right for the loss (0.00 W). |
| σ = 100 ps: some reverse conduction, some small hard turn-ons, more dither (Section 3). | **Confirmed:** 0.06 W reverse, early edges up to 3.6 V, dither 4.73 A. |

Three outcomes were not predicted:
- the m1n cross-conduction;
- the m3p_s45 cross-conduction;
- the size of the jitter dither.

All three have the same root: the correctors have no lower bound on the
actual dead time, and they **set** their delay to whatever they measured.

## 8. What the mechanism is

Both A89 correctors **set** their delay to a time that is measured from an
**actual** edge, and the RTL adds the delay to a **command** time.
- With a mismatch m, the actual dead time on the side whose turn-on
  channel is faster becomes (the natural transition time) - |m|:
  - for m < 0, the low side: crossing time - |m|;
  - for m > 0, the high side: swing time - m.
- Nothing bounds that difference from below. A cross-conduction follows
  whenever the natural transition is shorter than |m|.
- At 5%:
  - the low-side crossing takes 0.96-1.17 ns (D47);
  - the high-side swing takes 8.1-9.3 ns in steady state, but only
    1.2 ns in the handover transient of m3p_s45.

So **the datasheet's typical mismatch (1 ns) already reaches the low-side
crossing time, and the maximum (3.4 ns) reaches the high-side swing in a
transient.**

## 9. Limits

- Switches are ideal: zero rise and fall times, no gate-loop dynamics.
  The size of the cross-conduction is therefore not meaningful. The runs
  stop at the first one.
- The mismatch is static and the same on all four phases. Its spread
  between phases and its temperature drift are not modelled.
- The jitter is Gaussian and independent per edge, with a sensitivity
  value, because the datasheet gives none.
- A single load, 5%, from a zero start. The stopped runs only cover the
  start-up and the first part of the handover transient.
- The hard turn-on loss in Section 4 is an estimate from Coss(V), not a
  simulated value.

## 10. Next

**A92 (proposed): correctors that tolerate the driver.** This is opt-in
and gated as before. The literature named in BOUNDARY Section 2 should be
read first.
1. **An error-based low-side update.**
   - Late: subtract the measured reverse-conduction time (the time below
     -Vf). This is the body-diode-conduction sensing of the adaptive
     dead-time literature.
   - Early: add a step.
   - Unlike a reset to the absolute crossing time, this converges to the
     crossing window whatever m is.
   - P_rev would then be about 0 W, instead of D49's 4.3-17.9 W.
2. **The same idea on the high side.**
   - Reduce on late, step on early.
   - Use smaller steps, or average, so that jitter is not amplified.
   - The trade-off is tracking speed in transients.
3. **A floor on the actual dead time,** at both transitions.
   - Without knowing m, a command-side floor of |m|max + margin would
     cost about floor + m of reverse conduction on the other side
     (D49: 17.9 W at 3.4 ns).
   - So the floor needs the actual edges: gate-signal feedback, or a
     start-up calibration of m.
4. **Mode S's fixed dead time above |m|max plus margin** (4.5 ns here).

Then re-run this A91 matrix (m = ±1, ±3.4 ns; σ = 30, 100 ps) with the
new correctors.
