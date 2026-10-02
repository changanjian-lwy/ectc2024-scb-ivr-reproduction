# A105 - the integrated single-module design on the standard matrix (RESULTS)

Track A, main line.

**Boundary:** `BOUNDARY.md`. It was committed with the references and
predictions (b4f7fb3) before any run.

**Records:**
- `cosim/run_*.json` and `cfg_*.json`;
- `a105_summary.json` (`a105_analyze.py`);
- `reference_stats.json` and `matrix_stats.py`.

**Models:**
- **Physical:** Verilog RTL (`cfg_kp`), A88's plant (kernel2), 5%, 25 C,
  4 mΩ load.
- **Mathematical:**
  - D59 for the steps;
  - A97 / A100 archived runs, with the same statistics, as references
    for the switching rows.

**Candidates:**
- **I1:** the comparator design (A92 + A97), A103's start, A104's PI at
  100 kHz.
- **I2:** I1 with A100's timed phase-1 turn-off (ADM32).

**Statistics:** the last 200 periods (before the step for step runs).

## 0. Verdict

1. **Both integrated candidates pass every hard constraint on the whole
   standard matrix**, 22 of 22 runs:
   - no overlap;
   - peak phase current 165-176 A (limit 200 A);
   - peak V_DS 24.5-26.6 V (40 V parts).
2. **I2 is better than I1 on every switching row and equal on the steps.**

   | row | I1: phases 2-4 turn-off sd | I2 | I2's reference, A100 (I-only loop) |
   |---|---|---|---|
   | n0 | 0.18-0.20 A | 0.14-0.16 A | - |
   | m −1 / +1 ns | 0.27-0.31 / 0.22-0.24 | 0.11-0.12 / 0.10-0.12 | - |
   | m −3.4 / +3.4 ns | 0.22-0.25 / 0.29-0.32 | 0.02 / 0.15-0.16 | - |
   | j30 | 0.63-0.72 | 0.49-0.53 | 0.42-0.48 |
   | j100 | 1.64-1.84 | 1.04-1.19 | 1.04-1.20 |
   | ±25 A (D59) | +6.6 / −6.7 mV (+6.2 / −6.3) | +5.3 / −5.6 mV | - |
   | ±62.5 A (D59) | +16.3 / −16.8 mV (+15.5 / −15.9) | +11.6 / −14.7 mV | A100 I-only: +120 / −127 mV |

3. **T6, the open half: not a blocking loop.** With the PI's Ton dither,
   I2's phase 1 at 0 ps has a turn-off sd of 0.16 A.
   - A100 without the PI: 0.02 A.
   - Predicted: 0.1-0.6 A; the stated threshold was 0.6 A.
   - Under jitter, I2's phases 2-4 spread is A100's +3% to +24% at j30
     (within the ±30% band) and equal at j100.
4. **I1 misses its band on the four mismatch rows.** Phases 2-4's
   turn-off sd is +22% to +94% against A97 (limit +25%).
   - With a mismatch, Vo toggles between two ADC codes (0.5 mV
     peak-to-peak; n0 stays inside one code, 0.09 mV).
   - The PI's proportional term turns each toggle into ~3 LSB of Ton.
     This is Peterchev and Sanders's quantisation condition.
   - In absolute terms it is 0.22-0.32 A, half of the 30 ps jitter's
     spread.
   - A ±1-code deadband or a two-sample average on the proportional path
     would remove it. **Not tested.**
   - I2's timed phase 1 does not show it.
5. **Recommended single-module design: I2.**
   - Timed phase-1 turn-off (ADM32);
   - A103's start;
   - PI at 100 kHz.
   - **Open decision:** phase 1's turn-off-current limit (scorecard
     Section 6). I2 gives sd 0.16 A at 0 ps, 0.48 A at 30 ps and 1.16 A
     at 100 ps.

## 1. Gates

| check | result |
|---|---|
| I1's ±62.5 A rows | section by section identical to A104's fc100 runs (the same configuration) |
| statistics | one function (`matrix_stats.window_stats`) for the references and the candidates |
| provenance | every run from committed code |

## 2. Every row

**I1** (comparator + start + PI 100 kHz). Phases 1-4 turn-off sd, with
A97's I-only reference:

| row | sd (A) | A97 (A) | period sd (ns), A97 | low side max (V) | checks |
|---|---|---|---|---|---|
| n0 | 0.124 / 0.182 / 0.191 / 0.201 | 0.125 / 0.180 / 0.185 / 0.210 | 0.135 (0.140) | −0.94 | all met |
| m1n | 0.124 / 0.271 / 0.294 / 0.311 | 0.125 / 0.186 / 0.199 / 0.210 | 0.264 (0.216) | −0.87 | sd MISS |
| m1p | 0.124 / 0.221 / 0.222 / 0.237 | 0.124 / 0.164 / 0.157 / 0.188 | 0.194 (0.126) | −0.87 | sd, period MISS |
| m3n | 0.125 / 0.218 / 0.236 / 0.245 | 0.125 / 0.179 / 0.182 / 0.182 | 0.205 (0.175) | −0.93 | sd MISS |
| m3p | 0.124 / 0.290 / 0.318 / 0.320 | 0.124 / 0.171 / 0.166 / 0.165 | 0.269 (0.205) | −2.36 | sd, period MISS |
| j30 | 0.176 / 0.628 / 0.646 / 0.721 | 0.174 / 0.623 / 0.556 / 0.656 | 0.623 (0.589) | +0.27 (ref +0.49) | all met |
| j100 | 0.186 / 1.638 / 1.676 / 1.837 | 0.187 / 1.695 / 1.594 / 1.795 | 1.634 (1.648) | +4.87 (ref +5.42) | all met |

**I1 steps:**

| step | excursion (D59) | back within 1% | after: phases 2-4 sd | low side max | checks |
|---|---|---|---|---|---|
| −25 A | +6.6 (+6.2) mV | 0 | 0.20 A | −0.80 V | all met |
| +25 A | −6.7 (−6.3) | 0 | 0.28-0.32 | −1.11 | all met |
| −62.5 A | +16.3 (+15.5) | 7.5 µs | 0.25-0.28 | −0.58 | all met |
| +62.5 A | −16.8 (−15.9) | 9.5 µs | 0.17-0.21 | −1.34 | all met |

**I2** (timed + start + PI 100 kHz). The timed turn-off engages at
309.4-310.1 µs.

| row | phases 1-4 turn-off sd (A) | period sd (ns) | low side max (V) | checks |
|---|---|---|---|---|
| n0 | 0.156 / 0.141 / 0.152 / 0.158 | 0.152 | −0.87 | all met (T6: phase 1 ≤ 0.6 A) |
| m1n | 0.111 / 0.106 / 0.115 / 0.116 | 0.099 | −0.87 | reported (no reference) |
| m1p | 0.115 / 0.104 / 0.113 / 0.117 | 0.098 | −0.87 | reported |
| m3n | 0.019 / 0.018 / 0.018 / 0.018 | 0.016 | −1.01 | reported |
| m3p | 0.156 / 0.146 / 0.156 / 0.156 | 0.125 | −2.36 | reported |
| j30 | 0.479 / 0.489 / 0.521 / 0.526 (A100: 0.431 / 0.475 / 0.421 / 0.459) | 0.388 (0.374) | +0.30 | all met |
| j100 | 1.164 / 1.035 / 1.191 / 1.164 (A100: 1.161 / 1.200 / 1.035 / 1.170) | 0.466 (0.558) | +4.89 | all met |

**I2 steps:**

| step | excursion (D59) | back within 1% | after: phases 2-4 sd | checks |
|---|---|---|---|---|
| −25 A | +5.3 (+6.2) mV | 0 | 0.02 A | all met |
| +25 A | −5.6 (−6.3) | 0 | 0.17-0.18 | all met |
| −62.5 A | +11.6 (+15.5) | 5.8 µs | 0.02 | all met |
| +62.5 A | −14.7 (−15.9) | 8.4 µs | 0.22-0.25 | all met |

- **I2's steps are smaller than D59** (−25% at −62.5 A, within the ±30%
  band). D59 does not model the timed turn-off.
- **Under 100 ps jitter**, the low side's worst turn-on reaches +2.6 to
  +4.9 V in both candidates and in both references (A97, A100). This is
  the jitter's, not the design's. The hard constraints hold.

## 3. Where the single-module level stands

**Finish line** (BOUNDARY Section 1):
1. **Done (A105).** One integrated design passes the standard matrix.
2. **Done.** The model cross-checks:
   - D59 for every step;
   - the archived A97 and A100 runs for the switching rows;
   - D51-D55 for those references.
3. **Open.** The summary of the choices for evaluation.

**Also open: line steps.** The plant has no input step yet (A106).
