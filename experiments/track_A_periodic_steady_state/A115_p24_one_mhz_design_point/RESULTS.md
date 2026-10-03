# A115 - P24's 1 MHz design point: high-side zero voltage within 10% negative current (RESULTS)

Track A, main line. One factor: the design point (P24 Table I's 1 MHz
column instead of its 5 MHz column).

**Boundary:** `BOUNDARY.md`, committed (6ac7466) before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `a115_predictions.json` (`a115_predict.py`, registered);
- `a115_summary.json` (`a115_analyze.py`).

**Models:**
- **Physical:**
  - Verilog RTL;
  - A88's plant (kernel2: datasheet Coss(V), reverse conduction);
  - A105's I2 with C02's `slot_lo`;
  - L 7.333 nH, Cs 15 µF;
  - controller times ×5 (period) or ×√5 (node);
  - D59 loop at 60 kHz;
  - 25 C, one module.
- **Mathematical:**
  - D57's free valley;
  - the charge-balance orbit (checked on A110);
  - D62's middle-case loss model on each run's measured waveforms;
  - D59.

## 0. Verdict

1. **At P24's 1 MHz point the high side switches at (near) zero voltage
   within the papers' 10%.**

   | target | high-side turn-on, phases 1/2/3/4 | D57 (phase 1 / 4) | ripple, peak − valley | frequency | efficiency, D62 middle (ideal inductor) |
   |---|---|---|---|---|---|
   | 5% | 6.58 / 6.19 / 6.20 / 6.09 V | 6.54 / 5.86 | 140.4-140.9 A | 0.90 MHz | 89.07% (93.45%) |
   | 7.5% | 4.29 / 3.86 / 3.87 / 3.56 V | 4.24 / 3.35 | 146.5-147.0 A | 0.87 MHz | 89.08% (93.56%) |
   | **10%** | **1.94 / 1.47 / 1.47 / 0.94 V** | 1.87 / 0.75 | **152.7-153.1 A** | 0.83 MHz | **88.98% (93.57%)** |
   | 12.5% | **−0.50 / −1.06 / −1.05 / −1.88 V** (zero voltage) | ≤ 0 / ≤ 0 | 158.9-159.3 A | 0.80 MHz | 88.79% (93.48%) |

   **The 5 MHz references (A110):**
   - 5%: 8.9-9.1 V, 140.6 A, 87.92%.
   - Zero voltage needed 25%: ripple 190.0 A.

   - **At 10%:**
     - the high side turns on at 0.9-1.9 V of the 12 V rail;
     - its hard turn-on costs 0.05 W per module (5 MHz at 5%: 8.93 W);
     - the ripple is 152.7 A, **+8.6%** over the 5 MHz 5% design's
       140.6 A (at 5 MHz, 25% gave +35%).
   - **At 12.5%:** every phase is at zero voltage, as D57's 11.9%
     predicts.
   - **D57** holds within +0.07 V on phase 1 and +0.23 V on phase 4.
   - **The charge-balance orbit:**
     - period +0.2 to +0.3%;
     - peaks within 0.9 A;
     - ripple within 0.5 A;
     - Ton −1.3 to −1.4%.
2. **The efficiency moves from the switches to the inductor.**
   - **Per module, 5 MHz 5% → 1 MHz 10%:**
     - hard turn-on + turn-off overlap + gate drive: 16.84 → 1.59 W;
     - inductor copper: 2.64 → 13.78 W.
   - **Why the copper grows:** D62's middle case keeps the technology's
     R/L, and L is ×5.
   - **Result:** the middle case gains only 1.1 points (87.92 → 88.98%),
     below A110's 20% optimum at 5 MHz (90.17%). With an ideal inductor,
     93.6%.
   - **Whether 1 MHz is better therefore depends on the inductor's
     R/L.** This is P24 Table 2's question. Every 0.1 mΩ per phase costs
     ~2.4 W (~6000 A² mean square per phase).
3. **The time-scaled controller holds the steady state and the load
   increase, but not every transient.**
   - **Steady state, 5-10%:**
     - after the handover's dip (35.9 mV; 5 MHz: 13.1 mV), Vo stays
       within 0.3 mV;
     - no late fire; turn-off sd ≤ 0.01 A;
     - with 30 ps jitter, 0.13-0.16 A (5 MHz: 0.49-0.54 A).
   - **+62.5 A:** −19.3 / −19.9 mV (5% / 10%), back within 1% in 24.8 /
     13.7 µs.
   - **−62.5 A at 10% runs away.**
     - Vo 0.50-1.55 V, peaks 554 A, hundreds of late fires; not
       recovered in 1000 µs.
     - At 5% it recovers, but slowly: 45 µs against D59's 15.
     - **Mechanism, A112/A113's:** after the step the loop cuts Ton.
       Phase 1's timed turn-off (dlo, learned at the old Ton) is then
       too late, so its valley falls from −12.5 to −37 A. The slotted
       phases follow phase 1's reference and fall with it. The lost
       charge and the loop then oscillate with growing amplitude (period
       ~8 µs, Table 3.1).
     - **Why it is stronger than at 5 MHz:**
       - in switching periods, dlo's adaptation is time-scaled
         (`lo_smax` ×5);
       - the 60 kHz loop is not: fs/fc = 14 against 43 at 5 MHz, so the
         loop is ~3× faster per period.
       - At 5 MHz the same mechanism needed 25% and only slowed recovery
         (A113: 183 µs).
   - **12.5% (not registered, found in the analysis):**
     - from the handover until phase 1's turn-off becomes timed
       (1619 µs), Vo oscillates by ±45 mV;
     - Ton swings 2341-4013 LSB; the slotted phases' valleys swing
       −47 to +35 A, and their high sides turn on at up to 15 V;
     - it settles once the turn-off is timed. The registered window
       (last 200 periods) is clean.
     - **This is A110's 30% mechanism:** the node reaches the rail, the
       valley is flat, and the predictive turn-on has no target.
     - **So 12.5% is the edge, and 10% the design:** practical zero
       voltage (0.05 W of hard turn-on) with a valley the measurement
       can still see.

## 1. Registered criteria (BOUNDARY Section 5)

| criterion | n5 | n7p5 | n10 | n12p5 |
|---|---|---|---|---|
| high side: D57 ±0.6 V (phases 1-3), ±1.0 V (phase 4); 10% ≤ 2.5 V; 12.5% ≤ +0.3 V | pass | pass | pass | pass |
| period ±2%, Ton ±5%, peaks ±5 A, ripple ±5 A | pass | pass | pass | pass |
| 10%: ripple ≤ 1.10 × 140.6 A | | | pass (1.086) | |
| no overlap, peak ≤ 200 A, low side ≤ 0 V, Vo ±1 mV, late ≤ 5 | pass | pass | pass | pass (182 A at 1275 µs, in the oscillation; late 1) |
| efficiency ±0.7 points | pass (+0.11) | pass (+0.10) | pass (+0.09) | pass (+0.08) |

| step / jitter row | result |
|---|---|
| n5_s_p62 | **step −19.33 mV against D59 −28.26: 32% below (miss, on the favourable side)**; back 24.8 µs pass |
| n5_s_m62 | +19.54 mV against +27.01 (−28%) pass; back 45.3 µs pass (≤ 60) |
| n10_s_p62 | **−19.90 mV against −28.81: 31% below (miss, favourable side)**; back 13.7 µs pass |
| n10_s_m62 | **miss: runaway** (+546 mV, 554 A, not recovered) |
| n10_j30 | sd 0.13-0.16 A pass; high side within 0.02 V of n10 pass |

**D59 over-predicts the load-step extremes by ~30% at 1 MHz** (at 5 MHz
by 8-27%, C02 against A104). Its delay model, 0.75 Ts, likely
overstates the loop delay. Each phase takes the newest Ton at its own
turn-on.

### 3.1 The runaway, n10_s_m62

Phase 1's crossing reports after the step at 2000 µs (current at the
timed turn-off, A):

| µs | 2001 | 2003 | 2004 | 2005 | 2007 | 2009 | 2012 | 2016 | 2020 | 2024 | 2028 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | −17.5 | −28.7 | −37.2 | −42.9 | −16.6 | −2.8 (early) | −46.4 | −7.7 (early) | −58.4 | +5.2 (early) | −70.7 |

- Ton, in LSB: 2881 → 2626 → 3022 → 2787 → 3547 → 2706 → 3986. It
  reaches its limits (1420 / 5680) from 2060 µs.
- **The largest peak:** 553.8 A at 2170.8 µs.

## 2. What this answers

**The user's question:** "the papers keep the negative current within
5-10%; 25% is too much ripple."

- **The 25% came from our 5 MHz design point,** not from the physics
  of the converter. P24's own integrated design runs at 1 MHz.
- **At P24's 1 MHz point:**
  - 10% gives practical zero voltage: 0.9-1.9 V, 0.05 W per module;
  - 12.5% gives full zero voltage;
  - the ripple is only +8.6% over the 5% design.
- **P24's 1-2% (Sec. III) does not hold at 48 V** at either point. At
  1 MHz, 5% still leaves 6.1-6.6 V.
- **The cost moves to the inductor:**
  - with D62's middle-case R/L, 1 MHz gains only ~1 point;
  - with a low-R/L inductor, up to 93.6%.

## 3. Next

**A116 (candidate): the 1 MHz 10% design's load-decrease runaway.**
Three remedies, each tested already at 5 MHz:
- the comparator phase-1 turn-off (A113 cmp; A114: rising line steps
  run away);
- dlo feed-forward k = 11 (A113 ff: fixes load steps, falsified for
  line steps);
- **a slower loop** (fc 30 kHz, fs/fc ≈ 28). Untested, and the most
  direct fix for the 3× relative speed found here.

Then the 10% design through the standard matrix, line steps included.
