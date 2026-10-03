# A115 - P24's 1 MHz design point: high-side zero voltage within 10% negative current? (BOUNDARY)

Track A, main line. **Written before any A115 run.** The only run before
this commit was a 20 µs start check of `cfg_n12p5` (into a scratch
directory, not analysed) to confirm that the configuration loads and
mode S runs at 1000 ns.

**The design:** C02's `cfg_s1_n0`, i.e. A105's I2 with `slot_lo`.

**One factor:** the design point. It moves from P24 Table I's 5 MHz
column to its 1 MHz column (4 phases × 4 modules, IL,pk 125 A,
Ton 83.4 ns).

## 1. Why

- **A110** reached high-side zero voltage only at 25% negative current.
  - **Cause:** at 5 MHz with Eq. (4)'s 1.4667 nH, D57 needs 26.7%.
  - **But** the ripple ΔI = peak − valley grows with the negative
    current: 143 A at 5% → 192 A at 25%.
- **The papers' range:**
  - P25 (12 V → 1 V, 0.5 MHz) uses 5-10% of the peak.
  - P24 Sec. III claims 1-2%.
- **D57's scaling:** the needed current ∝ V_rail √(C_node / L) /
  I_peak. A larger L, at a lower frequency, needs less.
  - **P24's integrated package (Sec. IV) runs at 1 MHz.**
  - **At P24's 1 MHz point, D57 needs 11.9%** (phase 1's node).
- **Question:** does the module switch its high side at (near) zero
  voltage with ≤ 10% there, and at what ripple and efficiency?

## 2. What changes with the design point (`make_cfgs.py`)

**Circuit**
- **L:** 7.333 nH, Eq. (4) at 1 MHz.
  - This is the project's rule throughout: Eq. (4), not Table I.
  - Table I prints 13.44 nH, 1.83 × Eq. (4) at every frequency (an
    open question for Mihai).
  - With 13.44 nH the 125 A peak needs Ton ≈ 165 ns, so the module
    would run at ~0.5 MHz, not at 1 MHz.
- **Cs:** 3 → 15 µF, the same per-cycle ripple Q/Cs as the 5 MHz
  design. P24 gives no value.

**Controller times set by the period (×5)**
- Mode S's Ton and T0: 88.75 / 1000 ns.
- Phase 1's low-side restart: 2000 ns.
- Input ramp: 343.05 µs.
  - D60's margin over Roberts' first ladder resonance ∝ ramp / √(L Cs).
  - So this keeps the 5 MHz design's 32× margin.
  - New bridge key `t_ramp_us`; the default is unchanged.
- Handover: 360 µs. Run: 2500 µs. Load step: at 2000 µs, run to
  3000 µs.
- Largest step of the timed turn-off, `lo_smax`: 32 → 160 LSB, since
  its interval is ×5.

**Controller times set by the node resonance √(L C_node) (×√5)**
- The predictive delay's start / step / cap: 25.9 / 0.447 / 77.8 ns.
- The high-side restart: 44.7 ns.

**Voltage loop:** D59's design at the 1 MHz point.
- Values: kp 574.46 ns/V, ki 47.926 ns/V per sample; crossover 60 kHz,
  phase margin 69°.
- **Not 100 kHz** (A105's choice), for two reasons:
  - one sample per period gives 5× the delay, so the margin falls to
    53°;
  - ki per sample (×24) needs register 139 596, beyond the 16-bit
    gain.

**Unchanged**
- Devices: 2 high-side + 3 low-side EPC2067 per phase (P24 Table 3,
  4 × 4 row).
- Circuit: R 0.54 mΩ; Co 4.672 mF; 4 mΩ load; 25 C.
- Controller: low-side transition timing (dtl: current-driven, the
  same peak current); dead time; driver; comparators and blanking;
  error targets; `lo_learn` (a count).

**Deviations from P24, each with its reason**
- **L:** Eq. (4), not Table I (above).
- **Cs, Co, R:** P24 does not give them.
  - Co is kept, so the output voltage ripple grows ~×5 with the period.
- **The node:** P24 Sec. IV's 1 MHz package uses 1 high-side + 2
  low-side devices. Its smaller node needs ~9.5-12.8% (D57). **Not
  run:** it changes the devices, a second factor.

## 3. Runs (`cosim/cfg_*.json`)

| run | i_target | row |
|---|---|---|
| n5, n7p5, n10, n12p5 | −6.25, −9.375, −12.5, −15.625 A (5, 7.5, 10, 12.5%) | n0, 2500 µs |
| n5_s_p62, n5_s_m62, n10_s_p62, n10_s_m62 | 5%, 10% | load step ±62.5 A at 2000 µs, to 3000 µs |
| n10_j30 | 10% | 30 ps jitter on every edge, 2500 µs |

**References at 5 MHz:** A110 / C02.

## 4. Registered predictions (`a115_predict.py` → `a115_predictions.json`)

**Method**
- **D57's free valley** (phase 1's node: 2 + 3 devices plus the next
  phase's 2; phase 4's without a next phase).
- **The boundary-mode orbit by charge balance:**
  - 62.5 A average per phase;
  - R in both slopes;
  - the current from −i_neg to 0 over the valley time;
  - the high side on at the valley at ~0 A.
- **D62's middle-case budget** on those waveforms, with L = 7.333 nH.
  - The inductor's copper scales with L at fixed technology R/L.

**Checked on A110's measured 5 MHz rows (5-25%)**
- Period: × 0.9996-1.0024.
- Ton: × 0.967-0.968.
- Peaks: −2.0 to −3.0 A.
- Efficiency: +0.25 points.
- The orbit relation holds. The 3.3% Ton offset and ~2.5 A peak offset
  are systematic.

| 1 MHz, 7.333 nH | 5% | 7.5% | 10% | 12.5% |
|---|---|---|---|---|
| high-side turn-on V_DS, phase 1 (D57) | 6.54 V | 4.24 V | 1.87 V | ≤ 0 (−0.58) |
| phase 4 (no next phase) | 5.86 V | 3.35 V | 0.75 V | ≤ 0 (−2.00) |
| peak | 134.4 A | 137.3 A | 140.2 A | 143.2 A |
| Ton | 89.9 ns | 91.8 ns | 93.8 ns | 95.8 ns |
| period (frequency) | 1106 ns (0.90 MHz) | 1150 ns (0.87) | 1195 ns (0.84) | 1240 ns (0.81) |
| ripple, peak − valley | 140.6 A | 146.6 A | 152.7 A | 158.8 A |
| efficiency, D62 middle | 88.96% | 88.98% | 88.89% | 88.71% |
| D62 with an ideal inductor | 93.36% | 93.49% | 93.50% | 93.42% |

**The 5 MHz references (same method)**
- 5%: 8.96 V, ripple 143.4 A.
- 25%: 0.74 V, ripple 191.6 A.
- A110 measured: 87.92% at 5%, 90.17% at 20%.

**Loss terms, 1 MHz 5% against 5 MHz 5% (middle case)**
- High-side hard turn-on: 8.9 → 1.0 W.
- Gate drive: 7.4 → 1.6 W.
- Turn-off overlap: 0.56 → 0.11 W.
- **But the inductor's copper: 2.8 → 13.3 W.**
- So the middle-case efficiency rises only ~1 point. With an ideal
  inductor it rises ~5.5 points. The trade-off moves to the inductor:
  P24's Table 2 question.

**D59 load steps at 1 MHz (fc 60 kHz)**
- +62.5 A: −28.3 / −28.8 mV, back within 1% in 22.6 / 21.9 µs (5% /
  10%).
- −62.5 A: +27.0 / +27.6 mV, 14.7 / 15.0 µs.

## 5. Criteria (last 200 periods; before the step for step rows)

1. **High-side turn-on V_DS:**
   - at 5, 7.5 and 10%: phases 1-3 within ±0.6 V of D57 phase 1;
     phase 4 within ±1.0 V of its own;
   - at 10%: every phase ≤ 2.5 V;
   - **at 12.5%: every phase ≤ +0.3 V (zero voltage).**
2. **Orbit:**
   - period within ±2%; Ton within ±5%;
   - per-phase peak within ±5 A;
   - ripple (mean peak − mean valley) within ±5 A;
   - at 10%: ripple ≤ 1.10 × the 5 MHz 5% design's measured 140.6 A
     (A110 n5).
3. **Operation:**
   - no overlap;
   - peak ≤ 200 A, the start-up included (predicted ≤ 185 A: mode S
     is time-scaled; 5 MHz 170 A);
   - low-side turn-on V_DS ≤ 0;
   - Vo 1.000 V ± 1 mV;
   - late fires ≤ 5.
4. **Efficiency:** D62 middle on each run's measured waveforms,
   reverse conduction included; within ±0.7 points of the table.
5. **Load steps (5%, 10%):**
   - no overlap, peak ≤ 200 A;
   - extreme within ±30% of D59;
   - back within 1% (finite) and ≤ 60 µs.
6. **Jitter (n10_j30):**
   - turn-off sd ≤ 0.5 A per phase (5 MHz: 0.49-0.54 A at C02 s1_j30;
     predicted lower, since the current slope at the turn-off is ÷5);
   - high-side V_DS within ±0.3 V of n10.

**What would falsify**
- **D57's scaling:** 12.5% not reaching zero voltage, or 10% above
  2.5 V.
- **The time-scaled controller:** losing its timing at 1 MHz (overlap,
  late fires, Vo, peaks).
- **The charge-balance orbit:** period off by more than 2%.

## 6. What stays assumed

- **Device data:** the datasheet's typical Coss(V); D62's middle case
  (R_on max, MPC 500 nH-class inductor R/L, Cs ESR 1 mΩ, QG typical,
  t_f 0.75 ns).
- **Inductor technology** at 7.333 nH: carried as scenarios (middle,
  ideal); no core loss.
- **Not done:**
  - the 13.44 nH (~0.5 MHz) point;
  - P24 Sec. IV's 1 + 2 device node;
  - the standard matrix's line steps.
