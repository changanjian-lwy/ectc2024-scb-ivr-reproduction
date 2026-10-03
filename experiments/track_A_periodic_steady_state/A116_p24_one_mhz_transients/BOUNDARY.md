# A116 - the 1 MHz 10% design's transients: loop speed or phase 1's turn-off? (BOUNDARY)

Track A, main line. **Written before any A116 run.**

**The design:** A115's 1 MHz 10% design (`cfg_n10`): Eq. (4)'s
7.333 nH, Cs 15 µF, timed phase-1 turn-off (A105's I2) with `slot_lo`,
D59 loop at 60 kHz.

**One factor:** the controller variant, `make_cfgs.py`.

| variant | loop | phase 1's turn-off |
|---|---|---|
| t60 | 60 kHz (kp 574.46 ns/V, ki 47.926) | timed (A115 as is) |
| t30 | 30 kHz (kp 287.23, ki 11.982; D59 PM 86°) | timed |
| c60 | 60 kHz | comparator (I1, `lo_pred` 0; A113's cmp) |
| c30 | 30 kHz | comparator |

**Rows:**
- **Load:** n0 and the ±62.5 A load steps at 2000 µs. t60's are
  A115's.
- **Line:** ±4.8 V over 1 µs at 2000 µs (A106's l_p48_1us /
  l_m48_1us), for all four. A115 ran no line step.
- 17 runs.

## 1. Two hypotheses for A115's runaway (−62.5 A at 10%)

**What A115 saw:**
- The loop cut Ton at once (2881 → 2626 LSB in one sample).
- Phase 1's timed turn-off kept its learned interval, so its valley
  fell from −12.5 to −17.5, −28.7, −37.2 A in three periods. The
  slotted phases followed.
- The high sides then turned on clamped at −2.2 V (reverse conduction,
  the node at the rail), then hard at up to 15 V. That is A110's 30%
  breakdown.

**Key number: the zero-voltage threshold (D57, phase 1).**
- 1 MHz: 14.9 A, only 2.4 A beyond the 10% target (12.5 A).
- 5 MHz: 33.4 A, 27 A beyond the 5% target.

**H1 (threshold):**
- The runaway starts when a valley crosses the threshold, where the
  predictive high-side turn-on loses its target.
- **A slower loop does not prevent it:** at 30 kHz the first cut halves,
  but the valley still passes 15 A within a few periods.
- **Holding phase 1's valley does** (the comparator).

**H2 (loop speed):**
- The 60 kHz loop is ~3× faster per switching period than A105's
  100 kHz at 5 MHz (fs/fc 14 against 43).
- **The slower loop suffices.**

## 2. Registered predictions and criteria

**Window:** the last 200 periods for n0, and before the step for the
step rows. Steps by `matrix.step_stats(t_step = 2000 µs)`.

**Reference:** D59's extremes scaled by 0.70, A115's measured ratio at
60 kHz (−19.9 / −28.8, +19.5 / +27.0).

| variant | −62.5 A: extreme, back | +62.5 A: extreme |
|---|---|---|
| t60 (A115) | runaway | −19.9 mV |
| t30 | **H1:** runaway or back > 60 µs; **H2:** +32 ± 10 mV, ≤ 60 µs | −33 ± 10 mV |
| c60 | +19 ± 6 mV, ≤ 30 µs | −20 ± 6 mV |
| c30 | +32 ± 10 mV, ≤ 60 µs | −33 ± 10 mV |

**Criteria:**
1. **n0 (t30, c60, c30), against A115 n10:**
   - high side within ±0.2 V per phase;
   - efficiency within ±0.1 points; ripple within ±1 A;
   - Vo ±1 mV; no overlap; peak ≤ 200 A; late fires ≤ 5;
   - for c60 / c30, phase 1's valley within ±1 A of −12.5 A.
2. **−62.5 A:** as the table.
   - The c rows add: phase 1's valley stays within −12.5 ± 3 A, every
     period after the step.
   - For t30, H1 and H2 are told apart by the recovery. The minimum
     valley is reported either way. **H1 predicts it below −15 A.**
3. **+62.5 A:** as the table; peak ≤ 200 A.
4. **Line steps, 1 µs:**
   - **t60, t30:**
     - −4.8 V recovers (back ≤ 60 µs, peak ≤ 200 A);
     - +4.8 V reaches at least the 5 MHz design's 207 A (A106 / A107):
       the same 1 µs ramp, but the ladder relaxes 5× slower (D60, τ ∝
       Cs).
   - **c60, c30:**
     - −4.8 V recovers (A113: the comparator fixes the fast falling
       step);
     - **+4.8 V runs away** (A114's mechanism at 5 MHz: 246-290 A).
       Registered as the expected failure.
5. **No overlap in any run.**

**Decision rule:**
- **Adopt** the variant that passes n0, both load steps and −4.8 V.
- If several pass, **prefer the 60 kHz loop** (smaller droop).
- **The rising line step stays the open limit** if every variant fails
  it, as at 5 MHz: an architecture question (each phase on its own
  boundary), or an input slew limit.

## 3. What stays assumed

- Everything in A115's BOUNDARY Section 6.
- The line-step slews are the standard matrix's physical values (1 µs),
  not time-scaled. The source does not change with the converter's
  frequency.
