# A106 - line steps on the integrated single-module design (BOUNDARY)

Track A, main line. The last operating condition of the single-module
level (A105 BOUNDARY Section 1).

**Written before any A106 run.** The plant change (input step), its gates
and D59's predictions (`d59_predictions.json`) are committed with this
file.

## 1. Question

The 48 V bus moves. How does the integrated design (A105's I2) ride a
step of the input? The series-capacitor ladder must re-divide the new
input among the four phases.

## 2. What is modelled

- **Plant (A106, opt-in):** the input changes by dv from t, linearly over
  a slew time.
  - Python plants and the C kernel use the same expression.
  - Without a step, every plant is bit-identical (`--full` regression).
  - With one, `tests/test_cosim_plants.py` `CosimPlantLineStep` (−4.8 V
    over 10 ns inside the lockstep window) shows Reference, Fast, Kernel
    and Kernel2 bit-identical.
- **Cases:** ±4.8 V (±10% of 48 V) over 1 µs and 10 µs, and −8 V (to
  40 V, a common low end of a 48 V bus) over 10 µs, at 400 µs.
  - **I2 with its PI at 100 kHz** (5 runs);
  - **the same design with A79's I-only loop** (4 runs, without the
    −8 V case).
- **Physical model:**
  - Verilog RTL;
  - A88's plant (kernel2);
  - A105's I2: timed phase-1 turn-off (ADM32), A103's start, PI 100 kHz;
  - 5%, 25 C, 4 mΩ load;
  - run to 600 µs.

## 3. D59's predictions

D59 takes the ladder as following the input: V_rail = Vin / 4. It
predicts Vo's excursion from the change of the module's current
(∝ V_rail − Vo).

| case | PI 100 kHz | I-only |
|---|---|---|
| −4.8 V over 1 µs | −8.2 mV at 4.1 µs | −60.5 mV at 21.4 µs |
| +4.8 V over 1 µs | +7.0 mV at 3.3 µs | +58.4 mV at 20.1 µs |
| −4.8 V over 10 µs | −6.3 mV at 10.7 µs | −59.7 mV at 26.4 µs |
| +4.8 V over 10 µs | +5.2 mV at 10.7 µs | +57.4 mV at 24.9 µs |
| −8 V over 10 µs | −11.6 mV at 11.1 µs | - |

**Final Ton:** 637 LSB at 43.2 V, 512 at 52.8 V, 694 at 40 V.

## 4. Criteria

1. **No overlap.** Peak phase current ≤ 200 A. Peak V_DS reported against
   the parts' 40 V. A higher input raises every block, about 26.5 V ×
   52.8/48 ≈ 29 V.
2. **Vo excursion within ±30% of D59, PI and I-only.** A larger
   excursion would be the ladder's re-division, which D59 does not
   model.
3. **After the step** (last 200 periods):
   - the low side's turn-on V_DS ≤ 0;
   - phases 2-4's turn-off sd within 1.5 × the same run's before the
     step;
   - phase 1's turn-off mean within ±1 A of its target band (ADM32
     tracks it).
4. **The ladder settles.** A73's deviation max |VCs_k/Vin − (4−k)/4| is
   back below 1% within 100 µs, and its peak is reported.

## 5. What stays assumed

- **An ideal input source**, with no source impedance or input filter.
- **25 C.**
- **One step size per direction.**
