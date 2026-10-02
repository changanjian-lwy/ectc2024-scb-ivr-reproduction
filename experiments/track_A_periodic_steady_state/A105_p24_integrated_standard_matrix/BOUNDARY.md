# A105 - the integrated single-module design on the standard matrix (BOUNDARY)

Track A, main line.

**Written before any A105 run.** The references (`reference_stats.json`,
from A97's and A100's archived runs, with this experiment's
`matrix_stats.py`) and D59's step predictions
(`d59_step_predictions.json`) are committed with this file.

## 1. Where this sits: the finish line of the single-module level

The current level is one four-phase P24 module, at P24's operating point,
with device realism from the datasheet.

**It is finished when:**
1. one integrated design (controller, start-up, voltage loop) passes the
   standard matrix (TRADEOFF_SCORECARD Section 5) with no hard-constraint
   violation;
2. each row is cross-checked against the mathematical model where one
   exists;
3. the choices left open are written up as cases for evaluation, with the
   assumed values each one rests on.

**A105 is item 1. Done before it:**
- the circuit and device realism (A86-A88);
- the controller (A92, A97; A100's timed turn-off as an option);
- the start-up (A103);
- the voltage loop (A104).

**Left after it:**
- item 3 (a summary for Mihai);
- line steps, which the standard matrix does not include.

**Deferred to later levels:** multi-module, package, thermal, protection,
light-load operation.

## 2. Candidates

- **I1:**
  - the adopted comparator design (A92's correctors, A97's averaged slots
    and guard);
  - A103's start (load from t = 0, handover at 72 µs, mode S Ton
    17.75 ns);
  - A104's PI at 100 kHz (kp 188.851 ns/V, ki 5.5105 ns/V).
- **I2:** I1 with phase 1's turn-off timed (A100's ADM32: 1024 learned
  cycles, adaptive dlo step capped at 32 LSB).
  - It also tests the open half of scorecard T6: whether the faster loop's
    Ton dither disturbs dlo.

## 3. The standard matrix (each candidate)

- **No step:** n0; m −1, +1, −3.4, +3.4 ns (low-side edges later than
  high-side by m); j30, j100 (Gaussian jitter on every edge). To 500 µs.
- **Steps:** ±25 and ±62.5 A at 400 µs, to 600 µs.

**Physical model:** Verilog RTL (`cfg_kp`), A88's plant (kernel2), 5%,
25 C, 4 mΩ load, stop on overlap. 22 runs.

**Statistics:** `matrix_stats.window_stats`, the last 200 periods (before
the step for step runs).

## 4. References and predictions

**Comparator design with the I-only loop**, A97's runs (window
342-388 µs):

| row | phases 1-4 turn-off sd (A) | period sd | low side max (V) |
|---|---|---|---|
| n0 | 0.125 / 0.180 / 0.185 / 0.210 | 0.140 ns | −0.94 |
| m1n | 0.125 / 0.186 / 0.199 / 0.210 | 0.216 | −0.91 |
| m1p | 0.124 / 0.164 / 0.157 / 0.188 | 0.126 | −0.93 |
| m3n | 0.125 / 0.179 / 0.182 / 0.182 | 0.175 | −0.98 |
| m3p | 0.124 / 0.171 / 0.166 / 0.165 | 0.205 | −2.36 |
| j30 | 0.174 / 0.623 / 0.556 / 0.656 | 0.589 | +0.49 |
| j100 | 0.187 / 1.695 / 1.594 / 1.795 | 1.648 | +5.42 |

**Timed design (ADM32), A100's runs** (window 454-500 µs):

| row | phases 1-4 turn-off sd (A) | period sd |
|---|---|---|
| j30 | 0.431 / 0.475 / 0.421 / 0.459 | 0.374 ns |
| j100 | 1.161 / 1.200 / 1.035 / 1.170 | 0.558 ns |

**Predictions:**
1. **I1, rows without a step:** each phase's turn-off sd within the A97
   row ×(1 ± 0.25), or ≤ +0.05 A at 0 ps. The 25% covers A104's PI
   dither: +6% at j30, +15% at light load.
   - Period sd within ±30%.
   - Low side max as A97's ±0.3 V; in j30 and j100, as A97's ±1 V.
2. **I1, steps** (D59): ±25 A: +6.2 / −6.3 mV; ±62.5 A: +15.5 / −15.9 mV,
   each within ±30%. The ±62.5 A runs reproduce A104's fc100 runs
   bit-identically (the same configuration).
3. **I2, j30 and j100:** phases 2-4 sd within A100's ×(1 ± 0.3); phase 1
   as A100's ×(1 ± 0.5).
   - **T6 expectation:** the PI's Ton dither (7 LSB p-p at 100 kHz) moves
     phase 1's current crossing by about ±0.6 ns per period.
   - ADM32 must track it, so **at 0 ps phase 1's turn-off sd is expected
     to rise from A100's 0.02 A to 0.1-0.6 A.**
   - Above 0.6 A, T6 is confirmed as a loop to resolve before I2 can be
     adopted.
4. **I2, m rows:** no reference exists. Reported.
5. **I2, steps:** as I1 within ±30% (the same loop). Phase 1 is reported
   (A100: ADM32 tracked ±62.5 A within 1.74 A).

**Hard constraints (every run):**
- no overlap;
- peak phase current ≤ 200 A;
- the low side's maximum turn-on V_DS is reported against the reference
  row.
- Phase 1's turn-off-current limit is still a decision (scorecard
  Section 6). It is reported.

## 5. What stays assumed

- 25 C;
- the 4.672 mF output capacitance;
- an ideal ADC sample;
- the 4 mΩ boot load (A103);
- no line steps.
