# A107 / D60 - the integrated design over the series-capacitor range (RESULTS)

Track A, main line. One factor: Cs.

**Boundary:** `BOUNDARY.md`, committed with the code and D60's
predictions (6036f41) before any run.

**Records:**
- `cosim/run_*.json` and `cfg_*.json`;
- `a107_summary.json` (`a107_analyze.py`, on the shared
  `scb_ivr.cosim.matrix`);
- `d60_predictions.json`.

**Models:**
- **Physical:** Verilog RTL, A88's plant (kernel2) with `circuit {cs}`,
  A105's I2 (timed phase-1 turn-off, A103's start, PI 100 kHz), 5%, 25 C,
  4 mΩ load. Six standard-matrix rows at Cs = 0.6 and 8.7 µF.
- **References:** A105 and A106 at 3 µF.
- **Mathematical:** D60.

## 0. Verdict

1. **The ladder does not resonate anywhere in the range.**
   - After every line step, A73's ladder deviation decays with a rebound
     of at most 0.11 percentage points.
   - n0 and j30 are stable (Vo peak-to-peak ≤ 0.6 mV).
   - The low side keeps zero voltage at n0.
   - **The 100 kHz loop's recommendation holds for Cs 0.6-8.7 µF.**
     Roberts' resonance does not apply in mode P (D60's structural
     result).
   - **The ±62.5 A steps do not depend on Cs** (within ±12% of 3 µF), as
     D60 predicted.
2. **A large Cs breaks the 200 A limit, in the start-up and in fast line
   steps.**

   | Cs | start-up peak | line step −4.8 V over 1 µs | +4.8 V over 1 µs |
   |---|---|---|---|
   | 0.6 µF | 156 A | 156 A | 179 A |
   | 3 µF (A105/A106) | 170 A | 193 A | 207 A |
   | 8.7 µF | **215 A** | **244 A** | **221 A** |

   - **The start-up peak is mode S's.** After 152 µs no high-side
     turn-off exceeds 137 A at any Cs. As D60 predicted, the fixed 68.61 µs
     input ramp's margin over Roberts' first resonance falls from 32x
     (3 µF) to 19x (8.7 µF).
   - **The fix is a parameter, not a design:** scale the ramp with √Cs, as
     Roberts' rule does (about 117 µs at 8.7 µF for 30x). **Not run.**
   - **Fast line steps:** the slower ladder leaves the phase rails
     unequal for longer, so they need a slower bus slew or input
     feed-forward at a large Cs.
3. **A small Cs costs switching quality.** At 0.6 µF the in-cycle
   capacitor ripple (Q/Cs ≈ 1.8 V) shows up as:
   - peak V_DS 28.2-29.5 V (3 µF: 26.5-28.9 V);
   - the high side's turn-on at ~10.0 V instead of 8.9 V, so more hard
     turn-on loss;
   - phases 1-4's turn-off sd at n0 0.18-0.30 A (3 µF: 0.14-0.16 A);
   - a sampled ladder deviation of 2.7% in steady state (the sample at
     phase 1's turn-on catches the ripple).
4. **D60 has the structure but not the rate.** Its relaxation rate
   matches at 0.6 µF and is too slow at larger Cs: the co-simulation
   relaxes faster than ∝ Cs.

   | Cs | capacitor 1's relaxation, co-simulation (fit) | D60's slowest time constant |
   |---|---|---|
   | 0.6 µF | 1.9 µs | 2.2 µs |
   | 3 µF | 7.5 µs | 11.1 µs |
   | 8.7 µF | 5.7 µs | 32.1 µs |

   - Likely cause: the controller's per-phase timing (slots, correctors)
     adds a restoring term that D60 lacks. **Not shown.**
   - The ladder peaks agree within ±30% except at 0.6 µF. There, the
     steady 2.7% offset breaks the "back below 1%" metric, as it does
     D60's settling criterion.
5. **Cs is a trade, for evaluation:**
   - **smaller:** lower start-up and line-step peaks, but higher
     blocking voltage, harder high-side turn-on and more spread;
   - **larger:** cleaner switching, but the start-up ramp must lengthen
     with √Cs and the bus slew must be limited.
   - **Not tested:** the middle of the range (1.5-4.3 µF).

## 1. Gates

| check | result |
|---|---|
| cfg `circuit` | `--full` regression PASS; `{cs: 3e-6}` (the default) gives identical sections and steps (A105 i2_n0 to 30 µs) |
| `scb_ivr.cosim.matrix` | regenerates A105's and A106's configurations exactly; its statistics equal theirs (`tests/test_cosim_matrix.py`) |
| D60 | `tests/test_p24_ladder_loop.py`, 3 of 3 |
| provenance | every run from committed code |

## 2. Rows against the registered criteria

| run | peak current | Vo / ladder | criteria missed |
|---|---|---|---|
| cs0p6_n0 | 156 A | Vo p-p 0.51 mV | none |
| cs0p6_j30 | 156 | 0.60 mV; turn-off sd 0.43-0.53 A (3 µF 0.48-0.53) | none |
| cs0p6_s_m62 | 156 | +11.0 mV (3 µF +11.6) | none |
| cs0p6_s_p62 | 176 | −12.9 mV (3 µF −14.7) | none |
| cs0p6_l_m48_1us | 156 | −8.9 mV; ladder peak 3.48% (D60 5.87%), rebound 0.09 pp, steady offset 2.7% | settle, peak vs D60 |
| cs0p6_l_p48_1us | 179 (3 µF 207: lower, as predicted) | +7.8 mV; 7.37% (D60 5.14%), rebound 0.10 pp | settle, peak vs D60 |
| cs8p7_n0 | **215** | 0.51 mV | 200 A (start-up) |
| cs8p7_j30 | **215** | 0.58 mV; turn-off sd 0.47-0.52 A | 200 A (start-up) |
| cs8p7_s_m62 | **215** | +11.6 mV | 200 A (start-up) |
| cs8p7_s_p62 | **215** | −15.0 mV | 200 A (start-up) |
| cs8p7_l_m48_1us | **244** | −23.6 mV (3 µF −18.5); ladder 7.80% (D60 8.50%), back below 1% at 22.6 µs (D60 66.1), rebound 0.05 pp | 200 A |
| cs8p7_l_p48_1us | 221 (higher than 3 µF, as predicted) | **−15.1 mV at 20.9 µs** after a rising step; ladder 6.61% (D60 7.07%), back at 27.1 µs (D60 92.1), rebound 0.11 pp | settle vs D60 (0.29x, band 0.3-1.2x) |

**Unexplained:** at 8.7 µF the rising line step ends in a late Vo dip
(−15.1 mV at 20.9 µs) instead of an overshoot. The averaged model has no
term for it.
