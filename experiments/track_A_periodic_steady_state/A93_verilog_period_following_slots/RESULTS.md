# A93 - period-following slots and a missed-slot guard (RESULTS)

Track A, `PAPER_LOCKED` (phase shift T/nP) + `CROSS_PAPER_EXTENSION`.

**Boundary:** `BOUNDARY.md`, written before any code or run.

**Records:**
- `cosim/run_*.json`, configurations `cosim/cfg_*.json`;
- `a93_summary.json` (from `a93_analyze.py`);
- unit tests `tb/`;
- synthesis `synth/stat_scb_ctrl.txt`.

**Model: the physical model at implementation level.**
- A93's RTL: A92's, plus two opt-in bits.
- A92's bridge, with the two bits wired.
- A88's plant: datasheet Coss(V), reverse drop, 25 C.
- All runs except g1 use A92's configuration: error-based correctors,
  94 ps targets, gain 1/2, 4.5 ns mode-S dead time and dtl_init.

**The mathematical-model counterpart is D51**
(`symbolic_derivations/03_P24_native/D51_P24_PERIOD_FOLLOWING_SLOTS.md`).

## 0. Verdict

1. **The starvation is gone with period-following slots.** At m = -3.4 ns:

   | run | peak current | peak Vds |
   |---|---:|---:|
   | A92 | 827 A | 34.0 V |
   | m3n_follow (slots follow T_meas) | 174 A | 26.9 V |
   | m3n_both (follow and guard) | 172 A | 26.9 V |

   This is the level of A89 r2 (173 A). No run cross-conducted, and every
   run ended soft and regulated.
2. **The guard alone only bounds the starvation:** 267 A and 30.2 V.
   - Phase 4 then turns off at each reference change: 182 late fires.
   - That just misses the predicted < 250 A / < 30 V.
3. **But period-following slots raise the steady-state dither above
   criterion 2's 1 A.** This was not predicted. Across the deterministic
   runs, against A92:

   | run | A92 | A93 (both rules) |
   |---|---:|---:|
   | n0 | 0.71 A | 1.04 A |
   | m1p | 0.43 A | 1.27 A |
   | m1n | 0.46 A | 1.60 A |
   | m3p | 0.75 A | 1.22 A |

   - m3n: 0.64 A in A92, 1.42 A with both rules, 0.61 A with follow only.
     The dither metric varies by about ±0.3 A between runs; see Section 3
     for a sturdier measure.
   - The cause is a larger two-cycle alternation, growing with the phase
     index (Section 3).
   - The guard alone leaves the steady state as A92.
4. **Losses and the operating point do not move.**
   - P_rev: 0 W; 11.79 to 11.785 W at m3p.
   - Ton: unchanged to the LSB.
   - Flying-capacitor voltages: within 20 mV.
   - D51 (mathematical model) confirms that period-following slots do not
     change the orbit: Ton +0.0035 ns, currents ≤ 0.005 A, VCs ≤ 0.2 mV.
   - **The effect is on the cycle-to-cycle dynamics, not on the orbit.**
5. **The gate passes.** With both bits off, g1 is bit-identical to A92 m3n
   (1778 sections). Unit tests: 36 of 36, with A92's 32 unchanged.
   Synthesis is clean.
6. **Not adopted as is.** The bits stay off by default, and the adopted
   design remains A92's. The next step at this point is slots from a
   **two-cycle average** of the period (Section 5).

## 1. Gate and implementation

| check | result |
|---|---|
| g1 (bits off, A92 m3n's configuration) against A92 m3n | 1778 of 1778 sections, \|Δv\|, \|Δi\|, \|Δt\| = 0; equal final registers |
| unit tests | 36 of 36. New: the guard fires a missed slot (fine 0, one late fire per phase); without it the slot moves to the new reference; slots at t_ref + (k-1)·T/4 after two turn-ons; the configured slot before that. |
| synthesis | check: 0 problems; 39571 cells (A92: 38456). The 3 extra warnings are ABC's "network is combinational" notices, of the same kind as A92's 34. |

## 2. The m3n case: which rule removes the starvation

All runs at m = -3.4 ns. Vo at the handover is 1.539 V in every one, since
the start-up is identical.

| run | follow | guard | peak current | peak Vds | largest section current, mode P | shortest period after the handover cycle | late fires, phases 2-4 |
|---|---|---|---:|---:|---:|---:|---|
| A92 m3n (= g1) | - | - | 827 A | 34.0 V | 826 A | 126.2 ns | 47 / 74 / 59 |
| m3n_guard | - | on | 267 A | 30.2 V | 212 A | 131.3 ns | 0 / 31 / 182 |
| m3n_follow | on | - | **174 A** | 26.9 V | 146 A | 130.6 ns | 0 / 1 / 6 |
| m3n_both | on | on | **172 A** | 26.9 V | 146 A | 130.5 ns | 0 / 0 / 9 |

**Readings:**
- **Follow removes the cause.** Phase 4's slot becomes 3·T_meas/4, about
  98 ns at a 131 ns period, so it fires inside the cycle.
- **The guard treats the symptom.** It fires phase 4 when the next
  phase-1 turn-on arrives. So phase 4 is aligned with phase 1 during the
  short-period interval, and its current is bounded by one period instead
  of growing for 969 ns.
- **The handover cycle** (135 ns, T_meas still 200 ns from mode S) still
  makes a few late fires under follow (6 on phase 4). The guard turns them
  into immediate fires, but this makes no difference to the peaks.

## 3. Steady state with both rules (last 50 cycles)

| run | dither A92 → A93 (A) | P_rev (W) | Ton (ns) | period (ns) | phase-4 turn-off current spread, A92 → A93 (A) | peak current A92 → A93 |
|---|---|---:|---:|---:|---|---|
| n0 | 0.71 → 1.04 | 0 | 17.750 | 232.20 → 232.32 | 0.78 → 1.73 | 186 → 174 |
| m1p | 0.43 → 1.27 | 0 | 17.750 | 232.12 → 232.16 | 0.81 → 1.85 | 175 → 174 |
| m1n | 0.46 → 1.60 | 0 | 17.719 | 231.65 → 231.89 | 0.85 → 1.89 | 197 → 173 |
| m3p | 0.75 → 1.22 | 11.79 → 11.785 | 18.156 | 231.88 → 232.03 | 0.90 → 1.84 | 152 → 169 |
| j30 | 1.65 → 1.86 | 0.004 → 0.003 | 17.750 | 232.02 → 231.91 | - | 186 → 174 |
| j100 | 5.51 → 6.21 | 0.091 → 0.089 | 17.781 | 231.52 → 231.69 | - | 184 → 174 |

**Measure.** The two-cycle component of each phase's low-side turn-off
current, over the last 200 cycles: half the mean of the alternating
differences. Phase 1 stays at 0.12 A (the trim's ±1 LSB) in every run.

| | phase 2 | phase 3 | phase 4 |
|---|---:|---:|---:|
| A92 (n0, m1p, m1n, m3n, m3p) | 0.14-0.19 A | 0.15-0.18 A | 0.14-0.18 A |
| m3n_guard | 0.16 A | 0.16 A | 0.15 A |
| A93 with follow (all) | **0.24-0.30 A** | **0.34-0.47 A** | **0.43-0.59 A** |

**The growth is proportional to the slot index (k - 1).** The period's own
two-cycle component is unchanged (0.08-0.10 ns).

**Interpretation, consistent with these numbers but not isolated by a
separate run:**
1. The loop already has a lightly damped two-cycle mode. It is the
   alternation seen since A89, for example the high side's 0.19 / 0.03 ns
   errors.
2. It makes t_ref, phase 1's turn-on, alternate. T_meas = t_on - t_ref
   then alternates with twice that amplitude.
3. The follow rule passes (k - 1)/4 of T_meas into phase k's slot. That
   forces each phase at exactly the mode's frequency, so a small forcing is
   strongly amplified.
4. Fixed slots add no such term.
5. D51's orbit is unchanged because the effect is in the cycle-to-cycle
   dynamics around the orbit, not in the orbit itself.

## 4. Predictions against outcomes

| prediction (BOUNDARY Section 4) | outcome |
|---|---|
| g1 bit-identical to A92 m3n | **Confirmed.** |
| m3n_guard: no starvation, peak < 250 A and < 30 V | **Partly.** No runaway, but 267 A and 30.2 V. |
| m3n_follow: no starvation after the first mode-P cycle; peak ≤ 200 A | **Confirmed:** 174 A. |
| m3n_both: peak ≤ 200 A | **Confirmed:** 172 A. |
| Matrix: steady state moves slightly, stays soft, P_rev as A92 | **Confirmed:** 0 W, and 11.785 W at m3p. |
| Matrix: dither within 0.2 A of A92 | **Wrong:** +0.33 to +1.14 A (Section 3). |
| Jitter runs as A92 ±30% | **Confirmed:** 1.86 against 1.65 A; 6.21 against 5.51 A. |
| No run cross-conducts; every peak ≤ 200 A | No cross-conduction: **confirmed.** Peaks ≤ 200 A in every run with follow; m3n_guard 267 A. |

## 5. Next

**A95 (after the code clean-up): period-following slots from a two-cycle
average of the period,** T_avg = (T_k + T_k-1)/2.
- It cancels an exact two-cycle alternation, so the injection of Section 3
  disappears.
- It still follows a step in the period. At the handover, (200 + 135)/2 =
  168 ns gives phase 4 a 126 ns slot, inside the 135 ns cycle.
- Prediction: the transient as m3n_follow, the steady-state dither as A92.

**The guard stays available** as a safety net. On its own it is not
enough.

## 6. Limits

- One load (5%) and one start-up sequence, from a zero start.
- The dither metric of the last 20 sections varies by about ±0.3 A between
  runs that should be equivalent (A92 m3n 0.64 against m3n_guard 0.39 A).
  That is why Section 3 adds the two-cycle measure over 200 cycles.
- The mechanism in Section 3 is an interpretation. The averaged-period run
  (A95) will test it.
- The idealisations of A92 apply: ideal sensors and switches, a static
  mismatch, and Gaussian jitter.
