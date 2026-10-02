# A104 / D59 - the output-voltage loop as a PI on Ton (RESULTS)

Track A, main line (scorecard T6).

**Boundary:** `BOUNDARY.md`. It was committed with the RTL change, D59 and
the predictions (74298e6) before any run.

**Records:**
- `cosim/run_*.json` and `cfg_*.json`;
- `a104_summary.json` (`a104_analyze.py`);
- `d59_predictions.json`;
- `synth/stat_scb_ctrl.txt`.

**Models:**
- **Physical:** Verilog RTL with `cfg_kp`, A88's plant (kernel2), the
  adopted design (A92 + A97), 5%, 25 C, 4 mΩ load.
  - A103's c1d start: load from 0, handover at 72 µs, mode S Ton
    17.75 ns.
  - ±62.5 A at 400 µs, to 600 µs.
- **Mathematical:** D59
  (`symbolic_derivations/03_P24_native/D59_P24_VOLTAGE_LOOP.md`), a
  sampled PI on D58's current-source plant.

## 0. Verdict

1. **A proportional term raises the crossover 4-20 times, with every
   registered criterion met in all ten runs.**

   | design | crossover (D59) | ±62.5 A excursion | back within 1% | start-up: above 1 V / 1.005 V |
   |---|---|---|---|---|
   | ref (A79, I only) | 7.5 kHz | +121.7 / −127.2 mV | 97 / 111 µs | 17.6 / 5.6 µs |
   | PI 30 kHz | 29 kHz | +46.2 / −47.1 | 51 / 77 | 6.9 / 3.9 |
   | PI 60 kHz | 60 kHz | +25.7 / −26.3 | 17 / 24 | 5.2 / 3.2 |
   | **PI 100 kHz** | 101 kHz | **+16.3 / −16.8** | **7.5 / 9.5** | 4.2 / 2.5 |
   | PI 150 kHz | 153 kHz | +11.3 / −11.5 | 3.3 / 3.7 | 3.5 / 2.3 |

   - No overlap. The low side keeps zero voltage before and after every
     step.
   - The high side's turn-on V_DS is unchanged (8.9-9.1 V).
   - Vo is steady to 0.5 mV.
2. **D59 predicted the co-simulation closely:**
   - excursions within 7% (always slightly smaller than measured);
   - recovery times within 4-21% (the largest, fc150: 2.6 against
     3.3 µs);
   - **the present loop within 2 mV and 5 µs.**

   **The series-capacitor resonance (140 kHz, unmodelled) shows no effect
   even at 153 kHz.** The fc150 runs are as stable and as close to D59 as
   the others.
3. **The price is Ton dither, as Peterchev and Sanders's conditions
   predict.** One Ton LSB moves Vo by ~1.8 mV against a 0.5 mV ADC LSB.
   - Ton peak-to-peak after the step:
     - ref: 2 LSB;
     - 30 kHz: 1;
     - 60 kHz: 3;
     - 100 kHz: 7;
     - 150 kHz: 9.
   - After the −62.5 A step (187.5 A), phases 2-4's turn-off-current sd:
     - ref: 0.24-0.25 A;
     - 60 kHz: 0.22-0.23 A;
     - 100 kHz: 0.27-0.29 A;
     - 150 kHz: 0.33-0.36 A.
   - **With 30 ps jitter** (diagnostic, after the registered runs), the
     spread is 0.59-0.69 A (ref) against 0.67-0.75 A (150 kHz): +9% at
     most. Steps and stability are unchanged.
4. **Recommendation: PI at 100 kHz** (kp 188.9 ns/V, ki 5.51 ns/V per
   sample).
   - Its ±62.5 A excursion is ±1.7%, against ±12% now.
   - It recovers within 10 µs.
   - Its ZVS-margin cost is small (+15% spread at light load, +6% under
     30 ps jitter).
   - It keeps a margin below the first series-capacitor resonance.
   - 150 kHz is faster still and worked here; 60 kHz costs nothing in
     spread.
   - Cost in hardware: one 12 × 24-bit multiplier, +5.8% cells (46 468
     against 43 924).
   - **The choice among them is a trade for evaluation, not a single
     answer.**

## 1. Gates

| check | result |
|---|---|
| RTL `cfg_kp` | unit tests 46 of 46 (2 new); synthesis `check -assert` clean, 46 468 cells; `--full` regression PASS (kp = 0 is A79's loop) |
| D59 | `tests/test_p24_voltage_loop.py`, 4 of 4; A100's steps within 2 mV |
| the reference here against A103 c1d and A100 | start-up identical to c1d (1.0131 V at 72.0 µs, 17.6 µs above 1 V); steps +121.7 / −127.2 mV against A100's +121.9 / −127.0 mV (different start-up, same loop) |
| provenance | every run from committed code |

## 2. Runs, against the registered criteria (BOUNDARY 5)

Before the step: Vo peak-to-peak 0.07-0.12 mV, and Ton within 1 LSB of
568 in every run.

| run | step: excursion (D59) at time (D59) | back within 1% (D59) | last 50 µs: Vo / Ton p-p | low side max, after | phases 2-4 turn-off sd, after | criteria |
|---|---|---|---|---|---|---|
| ref_m62 | +121.7 (+120.1) mV at 19.5 (19.2) µs | 96.7 (92.5) µs | 4.21 mV / 2 | −0.59 V | 0.24-0.25 A | all met |
| ref_p62 | −127.2 (−127.1) at 22.1 (21.7) | 110.9 (110.6) | 1.70 / 2 | −1.00 | 0.17-0.20 | all met |
| fc30_m62 | +46.2 (+44.0) at 10.4 (9.4) | 51.1 (47.9) | 0.52 / 1 | −0.64 | 0.21-0.23 | all met |
| fc30_p62 | −47.1 (−45.3) at 10.5 (10.4) | 76.5 (73.0) | 1.33 / 1 | −1.38 | 0.16-0.18 | all met |
| fc60_m62 | +25.7 (+24.3) at 5.4 (4.8) | 17.3 (16.0) | 0.52 / 3 | −0.75 | 0.22-0.23 | all met |
| fc60_p62 | −26.3 (−25.2) at 5.7 (5.5) | 24.4 (23.0) | 0.51 / 3 | −1.38 | 0.17-0.18 | all met |
| fc100_m62 | +16.3 (+15.5) at 3.2 (2.8) | 7.5 (6.7) | 0.51 / 7 | −0.58 | 0.27-0.29 | all met |
| fc100_p62 | −16.8 (−15.9) at 3.3 (3.1) | 9.5 (8.9) | 0.52 / 7 | −1.34 | 0.16-0.19 | all met |
| fc150_m62 | +11.3 (+10.6) at 2.2 (1.9) | 3.3 (2.6) | 0.51 / 9 | −0.54 | 0.33-0.36 | all met |
| fc150_p62 | −11.5 (−11.2) at 2.3 (2.1) | 3.7 (3.4) | 0.50 / 9 | −1.32 | 0.15-0.16 | all met |

**Start-up** (A103's c1d, all designs): Vo max 1.0131 V at the handover
(72.0 µs). That is mode S's open-loop output, the same for every loop.
After the handover each loop pulls it down at its own speed (table in
Section 0).

## 3. Diagnostic: 30 ps jitter on every edge (−62.5 A step; after the registered runs)

| design | before: phases 2-4 turn-off sd | period sd | step | back within 1% |
|---|---|---|---|---|
| ref | 0.59 / 0.65 / 0.69 A | 0.594 ns | +121.0 mV | 96.4 µs |
| 60 kHz | 0.58 / 0.64 / 0.68 | 0.576 | +25.7 | 17.1 |
| 100 kHz | 0.62 / 0.69 / 0.73 | 0.614 | +16.3 | 7.4 |
| 150 kHz | 0.67 / 0.72 / 0.75 | 0.623 | +11.3 | 3.1 |

- Every run completes with no overlap.
- The low side's worst turn-on reaches +0.02 to +0.43 V under jitter **in
  every design, the reference included**. This is the jitter's own
  effect (A97, A100), not the loop's.

## 4. What is not covered

- **The ADC:** ideal sample at phase 1's turn-on; no filter, no added
  latency. A real ADC's latency would cut the phase margin (D59 can
  include it).
- **Line steps; other loads and targets; temperature.**
- **A load line (AVP) or current feed-forward:** a VR would add them.
- **The output capacitance** (4.672 mF, the init run's): every gain here
  scales with it.
- **The extension's branch:** it lowers Ton by 16-19% (A102), which
  changes the plant gain g. Not tested with these loops.
