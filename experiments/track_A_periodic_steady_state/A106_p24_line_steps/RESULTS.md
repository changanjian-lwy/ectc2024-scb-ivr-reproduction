# A106 - line steps on the integrated single-module design (RESULTS)

Track A, main line.

**Boundary:** `BOUNDARY.md`, committed with the plant change and D59's
predictions (2c9fd6f) before any run.

**Records:**
- `cosim/run_*.json` and `cfg_*.json`;
- `a106_summary.json` (`a106_analyze.py`);
- `d59_predictions.json`.

**Models:**
- **Physical:**
  - Verilog RTL;
  - A88's plant (kernel2) with the input step (A106);
  - A105's I2: timed phase-1 turn-off, A103's start, PI 100 kHz; and the
    same design with the I-only loop;
  - 5%, 25 C, 4 mΩ load, the step at 400 µs.
- **Mathematical:** D59. It takes the ladder as following the input.

## 0. Verdict

1. **The integrated design rides ±10% input steps.**
   - No overlap.
   - The low side keeps zero voltage after every step.
   - The ladder re-divides within 5-25 µs (A73's deviation back below 1%;
     its peak 3.5-7.0%).
   - Vo moves:

   | step | PI 100 kHz | I-only loop |
   |---|---|---|
   | −4.8 V over 1 µs | −18.5 mV | −70.1 mV |
   | +4.8 V over 1 µs | +11.8 mV | +46.3 mV |
   | −4.8 V over 10 µs | −3.9 mV | −39.0 mV |
   | +4.8 V over 10 µs | +4.2 mV | +51.1 mV |
   | −8 V (to 40 V) over 10 µs | −7.4 mV | - |

2. **One hard-constraint miss: a fast rising step.** +4.8 V over 1 µs
   peaks at **207 A** with the PI (228 A with the I-only loop), above the
   200 A limit. Over 10 µs it is 171 A.
   - The ladder lags the input. For a few µs the phase rails sit above
     Vin/4, and the same Ton drives more current.
   - **Not tested:**
     - an input-voltage feed-forward to Ton (standard in voltage
       regulators);
     - a limit on the bus slew. 4.8 V/µs is fast for a 48 V bus with its
       bulk capacitance.
3. **D59 misses where the ladder matters, as BOUNDARY Section 4
   expected.**
   - Over 1 µs: it under-predicts by ×2.3 (falling) and ×1.7 (rising).
   - Over 10 µs it over-predicts: −3.9 against −6.3 mV; −7.4 against
     −11.6 mV.
   - Of the nine runs, 4 meet the ±30% criterion.
   - **The averaged model needs the ladder for line steps.** The loop and
     load-step results (A104, A105) are unaffected.

## 1. Gates

| check | result |
|---|---|
| input step, off by default | `--full` regression PASS |
| input step in the plants | `tests/test_cosim_plants.py` `CosimPlantLineStep`: Fast, Kernel and Kernel2 bit-identical with Reference |
| provenance | every run from committed code |

## 2. Runs

| run | Vo extreme (D59) at time | back within 1% | peak current, V_DS | ladder peak, back below 1% | after: phases 2-4 sd (before) | low side max after | criteria missed |
|---|---|---|---|---|---|---|---|
| pi100_m48_1us | −18.5 (−8.2) mV at 2.4 µs | 3.1 µs | 193 A, 26.5 V | 6.97%, 5.0 µs | 0.018 A (0.10-0.12) | −0.94 V | D59 |
| pi100_p48_1us | +11.8 (+7.0) at 2.2 | 2.4 | **207 A**, 28.9 V | 6.66%, 16.8 | 0.18-0.20 (0.10-0.12) | −0.76 | **200 A**, D59, spread |
| pi100_m48_10us | −3.9 (−6.3) at 6.9 | 0 | 170, 26.5 | 4.09%, 24.7 | 0.018 | −1.00 | D59 |
| pi100_p48_10us | +4.2 (+5.2) at 21.6 | 0 | 171, 28.2 | 3.50%, 22.1 | 0.19-0.21 | −0.76 | spread |
| pi100_m80_10us | −7.4 (−11.6) at 16.9 | 0 | 170, 26.5 | 5.83%, 24.6 | 0.018 | −0.95 | D59 |
| ionly_m48_1us | −70.1 (−60.5) at 10.5 | 51.6 | 170, 24.6 | 6.92%, 9.6 | 0.03-0.04 (0.018) | −0.92 | spread |
| ionly_p48_1us | +46.3 (+58.4) at 21.7 | 55.4 | **228 A**, 28.9 V | 6.60%, 14.4 | 0.03 | −0.99 | **200 A**, spread |
| ionly_m48_10us | −39.0 (−59.7) at 34.2 | 75.7 | 170, 24.6 | 4.39%, 27.2 | 0.03-0.04 | −0.92 | D59, spread |
| ionly_p48_10us | +51.1 (+57.4) at 38.3 | 70.2 | 172, 28.2 | 3.55%, 22.0 | 0.03 | −1.00 | spread |

- **"spread":** phases 2-4's turn-off sd after the step exceeds 1.5 × its
  value before. The absolute values are small (≤ 0.21 A; I2's n0 in A105:
  0.14-0.16 A).
  - The PI design sits at a different Ton quantisation point at 52.8 V
    (Ton 512) than at 48 V.
  - At 43.2 and 40 V it is quieter (0.018 A).
- **Peak V_DS at 52.8 V:** 28.2-28.9 V, about 72% of the parts' 40 V.
- **Final Ton:** 637 / 512 / 694 LSB at 43.2 / 52.8 / 40 V, as D59
  predicted.

## 3. The single-module level

- **The finish line's item 1 now covers line steps too.** The one miss
  is the fast rising step's current peak.
- **Left:**
  - item 3, the summary of choices for evaluation;
  - the fast rising step: input feed-forward or a slew limit, as a case.
