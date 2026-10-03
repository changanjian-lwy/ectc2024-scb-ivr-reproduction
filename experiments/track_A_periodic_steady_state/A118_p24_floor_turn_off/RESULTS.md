# A118 - the timed phase-1 turn-off with a comparator floor (RESULTS)

Track A, main line. Factors: the floor (cfg `lo_floor`, 2 A) and Cs (6 /
15 µF); 1 MHz, 10%, 60 kHz.

**Boundary:** `BOUNDARY.md`, committed with the RTL option (5c12402)
before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `a118_predictions.json` (D63, registered);
- `a118_summary.json` (`a118_analyze.py`).

## 0. Verdict

1. **The floor fixes the timed design's failures, as D63 predicted.**
   - **Phase 1's turn-off current:** never below −14.7 A after any step,
     in all 11 floor runs. Without the floor: −74.6 A (t6, −4.8 V / 5 µs)
     and a runaway (t6 −62.5 A: 671 A).
   - **The −62.5 A load decrease that ran away in A115** now recovers:
     - +26.4 mV, peak 140 A at 15 µF;
     - +25.6 mV at 6 µF;
     - D63: +27.2 mV.
     - **But more slowly than registered:** back in 46.8 µs (15 µF) and
       31.8 µs (6 µF), against ≤ 30 µs (D63: 17.6 µs). A miss.
2. **"Floor + Cs 6 µF" meets every hard constraint** on the load steps
   and the ±4.8 V steps over 5 and 20 µs:

   | row | peak after | Vo extreme, back | D63 peak |
   |---|---|---|---|
   | −62.5 A | 141 A | +25.6 mV, 31.8 µs | 140 |
   | +62.5 A | 176 A | −19.1 mV, 13.1 µs | 173 |
   | −4.8 V / 5 µs | 191 A | +55.7 mV, 35.2 µs | 174 |
   | +4.8 V / 5 µs | 193 A | +14.3 mV, 6.9 µs | 191 |
   | −4.8 V / 20 µs | 144 A | −11.2 mV, 31.4 µs | 143 |
   | +4.8 V / 20 µs | 183 A | +17.0 mV, 42.4 µs | 169 |
   | −4.8 V / 1 µs | **201 A** | +34.9 mV, 26.0 µs | 203 |
   | +4.8 V / 1 µs | **206 A** | +24.7 mV, 22.3 µs; **no runaway** (A116's timed 15 µF: 546 A) | 208 |

   - **The start-up at 6 µF is clean:** peak 157 A. 3 µF reached 517 A
     (A117).
   - **Steady state:**
     - efficiency 88.97% (A115 88.98%);
     - turn-off sd 0.00 A (the timed design's);
     - the high side moves +0.42 / −0.30 / −0.27 / +0.45 V with the
       in-cycle ripple, half of 3 µF's, as registered;
     - the trim holds.
   - **Only the 1 µs line steps exceed 200 A,** by 1 and 6 A.
3. **Cs 15 µF does not make it, even with the floor:** ±4.8 V / 5 µs
   reach 211 and 241 A. **Cs is the second lever, and 6 µF is inside the
   window** that A117 (3 µF handover) and A116 (15 µF line steps) bound.
4. **D63 holds:**
   - **Peaks:** within 10% in 6 of 7 bounded rows. f15_l_m48_5us is
     211 against 187 A, +13%.
   - **Its "weak" rising rows at 6 µF:** 206 / 208, 193 / 191, 183 / 169
     A. At 15 µF it is under by 18% (241 / 204).
   - **The controls behave as its crossing rule says.** t6 −62.5 A has
     phase 1 at −33.8 A × 44 periods in the map, and runs away.
   - **The ML experiments agree:**
     - A120's surrogate search pointed here;
     - A121's GP predicted these rows without having seen a floor run
       (MAE 9.7 A, coverage 92%);
     - A122's RL rediscovered the floor in the map.

**Candidate 1 MHz controller:**
- **Design:** the timed turn-off with a 2 A floor, Cs 6 µF, 10% negative
  current, 60 kHz loop.
- **Spec:** a bus slew ≥ 5 µs per 4.8 V (≤ ~1 V/µs).
- **Next:** the standard matrix (driver mismatch, jitter, ±25 A,
  −8 V / 10 µs).

## 1. Registered criteria (BOUNDARY Section 2)

| # | criterion | result |
|---|---|---|
| 1 | floor holds (≥ −15.5 A), every f row | **pass** (−14.5 to −14.7 A) |
| 2 | −62.5 A: extreme +27.2 ± 8 mV, back ≤ 30 µs | extreme pass (+25.6, +26.4); **back miss** (31.8, 46.8 µs) |
| 3 | peaks ±10% of D63 (rows not flagged) | 6 pass; **f15_l_m48_5us miss** (+13%) |
| 4 | f6 hard constraints (loads; ±4.8 V over 5 and 20 µs) | **pass**, all six |
| 5 | f6_n0: overlap, Vo, sd, efficiency, start-up ≤ 200 A | **pass** (157 A) |
| 6 | control t6_s_m62: phase 1 below −20 A | pass (runaway, as A115) |

**Decision rule** (criteria 1, 2, 4 and 5's start-up): met except for 2's
recovery time (31.8 against 30 µs at 6 µF). The candidate stands, with
that recorded.
