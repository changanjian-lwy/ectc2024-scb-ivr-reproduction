# A109 - a valley trim for the slotted phases (BOUNDARY)

Track A, main line, with four-module checks. **Written before any A109
run.**

**Source:** A108 RESULTS 0.3-0.4.
- The slotted phases' turn-offs follow phase 1's period with no
  correction from their own current.
- So a lagging ladder leaves their valleys positive: +9.6 / +12.1 A
  even at 0.096 V/µs falling.
- C01 found the same gap for slave modules: they have no valley target.

## 1. The factor: cfg `slot_trim` = 1 (`st_smax` 64)

**RTL (`scb_phase.v`, `scb_ctrl.v`):**
- Every slotted phase (phases 2..N, a slave's phase 1) has an offset
  `sofs` added to its slot, in mode P only.
- **Each residual-current report at its turn-off moves `sofs`:**
  - later when the current was still above the target (r_below 0);
  - else earlier.
- **The step:** it doubles while the decisions agree, up to `st_smax`
  (64 LSB = 2 ns per cycle), and returns to 1 when they differ. This is
  A100's adaptive step.
- **|sofs| ≤ 1024 LSB (32 ns)**, a safety bound against moving a phase
  into its neighbour's window.
- **Phase 1 of a master is untouched**: its timed turn-off has its own
  learning (A99/A100).

**Bridge:** with `slot_trim`, the residual-current sign
(i < i_target = −6.25 A) is reported at every low-side turn-off, not
only the current-decided ones. The final offsets are recorded
(`slot_ofs_final_lsb`).

**Gates, before the runs:**
- RTL unit tests 53 of 53. New: `slot_trim_adaptive_step`,
  `slot_trim_moves_the_slot`, `slot_trim_not_phase1`,
  `slot_trim_not_in_mode_s`.
- Synthesis `check -assert` clean: SLAVE 0, 47 914 cells (46 443);
  SLAVE 1, 42 072 (40 127).
- The wrapper regenerates identically.
- `--full` regression, and A105 i2_s_p62 and C02 m4_n0 rerun with the
  default: identical (recorded in the CHANGELOG at commit).

## 2. Runs (`make_cfgs.py`; each the source configuration plus `slot_trim`, `st_smax`)

| run | source | to |
|---|---|---|
| s1_n0, s1_j30, s1_s_m62, s1_s_p62 | C02's one-module rows (A105 I2 + `slot_lo`) | 500 / 500 / 600 / 600 µs |
| s1_m48_1us, s1_m48_10us, s1_m48_50us, s1_p48_1us, s1_p48_10us | A108's rows | 600 µs |
| m4_n0, m4_ls_p10, m4_l_m48_10us | C03's rows (four modules) | 500 / 500 / 600 µs |

## 3. Registered predictions and criteria

**Steady state (s1_n0, m4_n0), the last 200 periods:**
1. **Every slotted phase's valley within ±0.3 A of −6.25 A.**
   - Without the trim: phases 2-3 at −6.92, phase 4 at −5.84.
   - Phase 1 as C02: −6.30 ± 0.05 A.
2. **High-side turn-on V_DS within ±0.15 V of C02's.** Low-side turn-on
   V_DS ≤ 0.
3. **Final offsets within ±64 LSB (2 ns).** The slots move by about
   (valley change) / (Vo/L) ≈ 0.65 A / 0.68 A/ns ≈ 1 ns.
   - The 16 gaps stay within T/16 ± 2 ns (m4_n0).
4. Vo 1.000 V ± 1 mV; no overlap; peak ≤ 200 A.

**Jitter and load steps (s1_j30, s1_s_m62, s1_s_p62):**

5. Turn-off sd within C02's s1_j30 × (1 ± 0.3). Step extremes within
   ±10% of C02's s1 (+11.30 / −14.59 mV).

**Line steps against A108 (30 µs or slew + 20 µs from the step):**

6. **Falling 50 µs and 10 µs:** every valley negative. The most
   positive ≤ −2 A (A108: +12.1 and +29.2 A).
7. **Falling 1 µs:** the slotted phases' most positive valley falls
   from +55.7 to ≤ +25 A. The 2 ns-per-cycle step limits the correction
   over the ~4 cycles of the ramp.
8. **Rising steps:**
   - phase 1 unchanged from A108 (its valley +56.7 / +1.4 A at 1 / 10 µs;
     peak ~207 A at 1 µs);
   - the slotted phases' most negative valleys move toward −6.25 A,
     from −28 / −33 A in A108 to ≥ −15 A.

**Four modules:**

9. **m4_ls_p10:** slave 1's valleys within ±0.3 A of −6.25 A, so its
   current follows D61's fixed-valley law: −10.0% ± 1% of a nominal
   module (C03 without the trim: −8.6%). Zero-voltage switching kept.
10. **m4_l_m48_10us:** every valley in every module negative (C03 had
    the A108 pattern).

**What would falsify the trim:**
- a steady-state limit cycle of the offsets larger than ±64 LSB;
- a valley worse than without it;
- an overlap.

## 4. What stays assumed

- The residual-current comparator is ideal (no offset, no delay), as
  for the existing trim of phase 1.
- `st_smax` 64 and the ±1024 LSB bound are design choices, not tuned.
- The other A105/C02/C03 assumptions.
