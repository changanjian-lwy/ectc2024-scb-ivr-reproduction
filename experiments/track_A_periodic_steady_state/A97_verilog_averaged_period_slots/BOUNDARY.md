# A97 - period-following slots from a two-cycle average of the period (BOUNDARY)

Track A, `PAPER_LOCKED` (phase shift T/nP) + `CROSS_PAPER_EXTENSION`.
Written before any code or run.

## 1. Question

A93's period-following slots, phase k at t_ref + (k-1)·T_meas/N with
T_meas the last phase-1 period:
- **removed the m3n starvation:** peak 827 A → 174 A;
- **but raised the steady-state dither:**
  - n0 went from 0.71 to 1.04 A, and the other cases went up to 1.60 A;
  - the two-cycle component of the low-side turn-off current grew in
    proportion to the slot index: phase 4 went from 0.14-0.18 A to
    0.43-0.59 A.

A93's interpretation was not isolated by a separate run.
1. The loop has a lightly damped two-cycle mode, so T_meas alternates.
2. The follow rule passes (k-1)/N of that alternation into phase k's slot
   in every cycle.

**Does a slot from the average of the last two periods,
T_avg = (T_{n-1} + T_{n-2})/2, keep the transient benefit and bring the
dither back to A92's?**

Answering this also tests A93's interpretation:
- an exact two-cycle alternation of the period cancels in T_avg;
- a step in the period still passes, one cycle later.

## 2. What the papers and earlier work say

- **P24 (Sec. II-B) and P25 (Figs. 1-2): the phase shift is T/nP.** T
  varies in this boundary-mode converter.
- **Huber, Irving, Jovanovic, "Open-Loop Control Methods for Interleaved
  DCM/CCM Boundary Boost PFC Converters"**, IEEE TPEL 23(4):1649-1657,
  2008, DOI 10.1109/TPEL.2008.924611 (from the abstract; the full paper
  was not read).
  - Master-slave interleaving of variable-frequency boundary-mode
    converters.
  - The only stable open-loop method is to synchronise the slave to the
    master's turn-on, with a delay of half the master's period measured in
    its previous switching cycle, both under current-mode control.
  - **That is A93's rule** (N = 2 there).
- **Closed-loop alternatives filter the phase through a loop:**
  - PLL-based interleaving: Huber, Irving, Jovanovic, IEEE TPEL
    24(8):1992-1999, 2009, DOI 10.1109/TPEL.2009.2018560;
  - closed-loop interleaving: Xu, Liu, Huang, IEEE TPEL 24(12):3003-3013,
    2009, DOI 10.1109/TPEL.2009.2019824.
- **No published source was found for a two-period average.** Here it is
  the smallest filter with a zero at the two-cycle frequency.
  - It is a 2-tap moving average, with gain |cos(ωT/2)|.
  - That gain is 1 at DC, 0.71 for a four-cycle component, 0.5 for a
    three-cycle one, and 0 for a two-cycle one.
- **D51 (mathematical model):** the slot rule does not change the orbit.
  On a period-1 orbit T_avg = T, so A97's orbit is D51's.

## 3. The change (RTL, opt-in, in the shared package)

The change goes into `src/scb_ivr/cosim/rtl/` (A93's RTL), the copy that
new experiments use. No archived folder is touched.

**New configuration bit `cfg_slot_avg`, default 0. It acts only with
`cfg_slot_follow`.**
- `scb_ctrl` keeps the period before last, t_per2: at each phase-1
  turn-on, t_per2 ← t_per.
- It also keeps a flag that three phase-1 turn-ons have been seen, so that
  both periods are valid.
- With both bits set and the flag set, phase k's slot is
  t_ref + ((k-1)·(t_per + t_per2)) / (2N), with integer division and a
  31.25 ps LSB.
- Before the flag is set, the configured slot applies, as A93 does before
  two turn-ons. Mode S runs many cycles first, so this never matters in
  the co-simulation.
- **With `cfg_slot_avg` = 0, A93's expression is unchanged.** So every
  earlier configuration is bit-identical.

**Bridge:** cfg key `"slot_avg"`, absent = 0.

**Unit tests:**
- A93's 36 tests are unchanged.
- New tests:
  - after three turn-ons with two different periods, phase k's slot is
    t_on3 + (k-1)·(P1 + P2)/8;
  - after two turn-ons, the configured slot still applies;
  - `cfg_slot_avg` without `cfg_slot_follow` leaves the configured slot.

**Gates:**
- the unit tests;
- `scripts/cosim_regression.py --full` (A89 r2, A92 j100, A92 m3p and A93
  m3n_both, all without `slot_avg`): bit-identical;
- `tests/test_cosim_plants.py`;
- synthesis clean (yosys `check -assert`).

## 4. Runs and predictions (written before the runs)

**Configuration.** All runs start from
`src/scb_ivr/cosim/presets/p24_5pct_adopted.json`, A92's adopted design:
- error-based correctors, 94 ps targets, gain 1/2;
- 4.5 ns mode-S dead time and dtl_init;
- plant `kernel2`.

Only the slot bits and the driver change. **The matrix is A93's.**

| run | follow | avg | guard | m | σ | prediction |
|---|---|---|---|---:|---:|---|
| m3n_avg | on | on | - | -3.4 ns | 0 | No starvation. The handover cycle still uses T_meas = 200 ns from mode S, so phase 4's slot (150 ns) is skipped once, as under follow. In the next cycle T_avg ≈ (135 + 200)/2 ns, which gives a slot of about 126 ns, inside the cycle. Peak current ≤ 200 A (m3n_follow: 174 A). |
| m3n_avg_guard | on | on | on | -3.4 ns | 0 | As m3n_avg; the handover skip becomes a late fire. Peak ≤ 200 A. |
| n0, m1p, m1n, m3p (avg and guard) | on | on | on | 0, +1, -1, +3.4 ns | 0 | See below. |
| j30, j100 (avg and guard) | on | on | on | 0 | 30, 100 ps | Dither as A92's ± 30% (1.65 and 5.51 A). The jitter amplification is not addressed here. |

**Predictions for n0, m1p, m1n, m3p:**
1. **Primary criterion:** the two-cycle component of phases 2-4's
   low-side turn-off current comes back to A92's level, at most 0.20 A per
   phase.
   - A92: 0.14-0.19 A; A93 follow: 0.24-0.59 A.
   - The measure is A93 RESULTS Section 3's: over the last 200 cycles,
     half the absolute mean of the alternating differences.
2. **The dither** (largest section-current change over the last 20
   sections) is within 0.2 A of A92's: n0 0.71, m1p 0.43, m1n 0.46, m3p
   0.75 A. That metric varies by ±0.3 A between equivalent runs, so it is
   secondary.
3. **The orbit is unchanged:** Ton, P_rev (0 W; m3p about 11.8 W) and the
   flying-capacitor voltages as A93's (D51).

**If prediction 1 fails, A93's interpretation is wrong or incomplete.**
The follow rule would then raise the alternation by another path, for
example through its one-cycle lag at frequencies other than the two-cycle
one.

**Criterion:**
- no run may cross-conduct;
- every peak current ≤ 200 A.

**Adoption:** if m3n_avg_guard meets the criterion and predictions 1 and 2
hold in all four deterministic runs, the averaged slots and the guard
become the adopted design.
- `presets/p24_5pct_adopted.json` gains the three bits.
- The change is recorded in the package CHANGELOG.

## 5. Mathematical model (D52): the closed-loop cycle-to-cycle linearisation

D50 Section 8.3 and D51 Section 6 both left the same piece open: the
correctors' states in the map's Jacobian. Without it, the two-cycle mode
and the effect of the slot rule cannot be computed. D52 builds it.

**Map and operating point.**
- D47's map (`LowPredEventMap`: datasheet Coss(V), reverse drop, timed
  low side), at 25 C and 5%.
- Linearised at each rule's own fixed point, with m = 0 and
  e* = 93.75 ps:
  - D50's for fixed slots (50/100/150 ns);
  - D51's for follow and for average, since the orbits are the same.

**State at the section (phase-1 turn-on):**
- the circuit's free section variables;
- per phase, the high-side delay d_k and the low-side delay dl_k;
- Ton;
- the slot rule's memory: none, T_{n-1}, or T_{n-1} and T_{n-2}.

**Updates, as the RTL, linear (quantisation ignored):**
- d_k ← d_k - g·(d_k - valley_k - e*);
- dl_k ← dl_k - g·(dl_k - crossing_k - e*);
- g = 1/2;
- the voltage loop's Ton update from Vo at the section, with the RTL's
  timing.

**Jacobian:** by finite differences of one cycle.

**Input and outputs.**
- Input: phase 1's current threshold, which the trim moves by ±1 LSB
  (±0.125 A around its mean) in a two-cycle bang-bang.
- Outputs: each phase's low-side turn-off current, the period, and the
  high- and low-side errors.

**Computed:** the closed-loop eigenvalues, and the gain from the input to
each output at the two-cycle frequency (z = -1) and over the band.

**Predictions (written before D52 is built):**
1. **All three rules are stable,** and each has a lightly damped mode near
   z = -1, with |λ| ≥ 0.8. This is the alternation seen since A89.
   - If no such mode exists, A92's alternation is a quantisation limit
     cycle of the correctors. The linear model then cannot give its
     amplitude.
2. **Fixed slots:** a ±0.125 A input gives phases 2-4 a two-cycle
   component within a factor of 2 of A92's 0.14-0.19 A.
3. **Follow:** the two-cycle gain grows with k, and at phase 4 it is about
   3 times the fixed-slot gain (A93: 0.43-0.59 against 0.14-0.18 A).
4. **Average:** at z = -1 the slot memory enters through
   (1 + z^-1)/2 = 0. So the two-cycle gain equals that of fixed slots at
   the same orbit.
   - This is a property of the model, not a prediction.
   - The prediction is that the average rule adds no eigenvalue of larger
     modulus than the largest one under fixed slots (excluding the slow
     modes, which are common to all three).

## 6. Decides / does not decide

**Decides:**
- whether averaged slots keep the transient benefit of A93 and remove its
  dither increase;
- whether A93's interpretation (two-cycle injection through the slot)
  holds, in both models.

**Does not decide:**
- the open-loop mode-S start-up, whose end state depends on m;
- the jitter amplification;
- other loads, line and load steps, and the Coss spread.
