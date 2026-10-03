# A125 - conformal intervals for the registered predictions (RESULTS)

Extension `ml_design_assist`.

**Boundary:** `BOUNDARY.md`, committed with the code (5a9d830) before
the test.

**Records:**
- `a125_summary.json` (`run_a125.py`: the sequential test, every band,
  row by row);
- `a125_calibration.json` (the 43 bounded registered rows, for
  `register_band`).

## 0. Verdict

1. **Conformal bands work on D63's registered predictions** (criterion 1
   passes).
   - **Peak, S at nominal 80%:** prospective coverage **74%** of 34 rows,
     median width ±11% of the prediction.
   - **At 90%:** 88%, ±18%.
2. **The hand ±10% band was in effect a ~76% band.**
   - It covered 76% of the same 34 rows, now with a stated level.
   - **The signed band G does best:**
     - 82% at nominal 80%, at the same width (21%);
     - on all 43 rows it is **−1.3% to +18.4%** of D63.
     - **D63 under-predicts the peak,** so an asymmetric band fits it.

   | peak, nominal 80% | coverage (34 rows) | rising / other | median width |
   |---|---|---|---|
   | hand ±10% | 76% | 80 / 75% | 20% |
   | S symmetric (primary) | **74%** | 80 / 71% | 22% |
   | **G signed** | **82%** | 80 / 83% | 21% |
   | M Mondrian | 76% | 90 / 71% | 22% |
   | ACI | 82% | 80 / 83% | 36% |

3. **Criterion 2 misses, and the miss shows something.**
   - Calibrated on all 43 rows, M's 80% peak band is ±12.5% for rising
     line steps and ±12.9% for the others, so not wider.
   - **"Other" holds a second weak domain:** the −8 V / 10 µs falling
     step at 1 MHz.
     - D63 under-predicts its peak by **+18 to +22%** (A119, and A123 ×3).
     - At 2.5 MHz (A124) it is off by only +2.7%.
   - **The split chosen in advance** (rising steps only) was incomplete.
     The calibration data found the gap.
4. **The Vo extreme: a signed score is the wrong question.**
   - The absolute band is ±54 mV at 80%, which is useless.
   - **9 of 43 rows flip sign:** where over- and undershoot are of
     similar size (the −8 V steps, some slow rising steps), D63 picks the
     other one.
   - **Post hoc** (not registered): a magnitude score |Vo| covers 88% at
     nominal 80%, with band ×0.56-×1.44 of D63.
   - **Registrations should state both excursions.**
5. **The recovery time:** D63 is good only to a factor ~3. The 80% band is
   **×0.31-×3.2**.
   - This is why A118's "back ≤ 30 µs" missed.
   - **Future boundaries register a band, not a tight threshold.**
6. **ACI** reaches 82% on the peak, but wider (36%). With five batches it
   mostly reacts to A118's misses. It is no better than G here.
7. **D63's outcome rule:** 43 rows were predicted bounded, and 4 of them
   ran away.
   - All four are A117's:
     - three are 3 µF handover oscillations (the in-cycle low, D63's
       known blind spot, A117 RESULTS);
     - one is c3_tim_l_p48_1us.
   - **Since A118: 0 of 34.**

## 1. Criteria (BOUNDARY Section 2)

| # | criterion | result |
|---|---|---|
| 1 | peak, S at 80%: coverage ≥ 70% on 34 test rows | **pass** (74%) |
| 2 | M's 80% peak band wider for rising line steps | **miss** (±12.5% against ±12.9%; the −8 V / 10 µs rows at 1 MHz are in "other") |
| 3 | unit tests (the guarantee on exchangeable data) | **pass** (6) |

**Predictions (Section 3):**
- hand ±10% coverage ~85%: actual 76%, lower;
- S's final half-width 7-10%: actual 12.5%, wider, because of the −8 V
  rows;
- ACI at least as close to 80% as S: 82% against 74%, holds;
- recovery log band ×1.5-2: actual ×3.2, wider.

## 2. Calibrated bands for the next registration (all 43 rows)

`register_band(pred, q, group, alpha, method)` in `run_a125.py`.

| quantity | method, 80% | band |
|---|---|---|
| peak | M rising | ×0.875 - ×1.125 |
| peak | M other | ×0.871 - ×1.129 |
| peak | G (all) | ×0.987 - ×1.184 |
| peak, 90% | G (all) | ×0.944 - ×1.214 |
| recovery | M rising / other | ×0.27 - ×3.6 / ×0.40 - ×2.5 |
| \|Vo extreme\| (post hoc) | S rel on magnitudes | ×0.56 - ×1.44 |

## 3. Decision (BOUNDARY Section 4)

**Criterion 1 holds,** so from the next co-simulation experiment on:
- Each boundary registers **M at 80%** next to D63's point prediction,
  as registered.
- **G** is registered beside it, so the next experiment is a prospective
  test of both.
- **The hand ±10% is retired.**
- **The recovery time** gets its log band, and **the Vo extreme** gets
  both excursions with the magnitude band (flagged as chosen post hoc).

## 4. Limits

- **Small and correlated data:** 34 test rows, and rows within one
  experiment share a design. Coverage on 34 rows has a sampling sd of ~7
  points.
- **Not exchangeable:** the designs drift (1 MHz timed → floor →
  2.5 MHz). The guarantee is formal only within a fixed design.
  The sequential test measures how it holds across the drift.
- **Retrospective for the method** (BOUNDARY Section 1). The next
  experiment's registration is the prospective test.
