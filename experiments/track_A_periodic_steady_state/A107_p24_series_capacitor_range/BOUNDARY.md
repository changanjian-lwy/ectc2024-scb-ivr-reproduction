# A107 / D60 - the integrated design over the series-capacitor range (BOUNDARY)

Track A, main line. One factor: Cs.

**Written before any A107 run.** The code changes are committed with
this file:
- the cfg `circuit` key;
- the shared standard matrix `src/scb_ivr/cosim/matrix.py`;
- D60 and the predictions (`d60_predictions.json`).

## 1. Question

Every result since A72 uses Cs = 3 µF. P24 gives no value; the project
carries 0.6-8.7 µF as a first-principles range
(`paper_locked/00_boundaries/CFLY_FIRST_PRINCIPLES_ESTIMATE.md`).

A104 recommended a 100 kHz voltage loop. Roberts' Eq. 3.44 puts the
ladder's first resonance at 82 kHz for 8.7 µF.

**Does the recommended design (A105's I2) hold over the range?**

## 2. D60 (before the runs)

`symbolic_derivations/03_P24_native/D60_P24_LADDER_RELAXATION.md`.

1. **In mode P the ladder relaxes and does not resonate.** Each cycle
   starts from the fixed negative current, so the inductor currents are
   not states. The ladder is a first-order system with time constants
   ∝ Cs:

   | Cs | time constants |
   |---|---|
   | 0.6 µF | 2.2 / 0.65 / 0.38 µs |
   | 3 µF | 11.1 / 3.2 / 1.9 µs |
   | 8.7 µF | 32 / 9.4 / 5.5 µs |

   Roberts' resonances apply to fixed-frequency PWM, here mode S during
   the input ramp. The ramp's margin is 71x / 32x / 19x.
2. **The averaged output equation does not contain the ladder's split**
   (the phase currents sum to (Vin − 4Vo)·Ton terms). The loop, and the
   load steps, do not depend on Cs.
3. **Checked on A106 (3 µF):**
   - the ladder decays without ringing;
   - its peaks agree within 15%;
   - **D60 is slow:** a fitted slowest time constant of 7.5 µs against
     11.1 µs.

## 3. Cases

**Physical model:** Verilog RTL; A88's plant (kernel2) with `circuit
{cs}`; A105's I2 (timed phase-1 turn-off, A103's start, PI 100 kHz); 5%;
25 C; 4 mΩ load.

**Runs:** Cs = 0.6 µF and 8.7 µF, each on the standard-matrix rows n0,
j30, s_m62, s_p62, l_m48_1us, l_p48_1us (12 runs). Configurations are from
`matrix.configs` on A105's i2_n0.

**References:** A105's i2 rows and A106's pi100 rows, at 3 µF.

## 4. Registered predictions and criteria

1. **Hard constraints.**
   - No overlap.
   - Peak current ≤ 200 A, except l_p48_1us. At 3 µF that row reached
     207 A. **Prediction: lower at 0.6 µF (the ladder follows faster),
     higher at 8.7 µF.**
2. **No resonance.**
   - After each line step's peak, A73's ladder deviation does not rise
     again by more than 0.5 percentage points.
   - n0 and j30 are stable: Vo peak-to-peak ≤ 5 mV.
3. **Ladder settling** (back below 1%) within 0.3-1.2 × D60's
   prediction (D60 is expected to be slow):
   - 0.6 µF: 5.5 / 6.9 µs;
   - 8.7 µF: 66.1 / 92.1 µs (falling / rising step).
   - Ladder peak within ±30% of D60's: 0.6 µF 5.87 / 5.14%; 8.7 µF
     8.50 / 7.07%.
4. **Load steps independent of Cs:** within ±20% of A105's I2 at 3 µF
   (+11.6 / −14.7 mV).
5. **Switching:** turn-off-current spreads and per-phase high-side
   turn-on V_DS are reported against A105's I2.
   - At 0.6 µF the in-cycle capacitor ripple (Q/Cs ≈ 1.8 V) raises
     phases 2-4's rails against phase 1's. Their turn-on V_DS may differ
     by up to ~2 V. **D60 does not model this.**
   - Low-side turn-on V_DS ≤ 0 at n0.
6. **Start-up** (every run): no overlap; the peak current is reported
   against the mode-S margin (19x at 8.7 µF).

## 5. What stays assumed

- Equal Cs for the three capacitors.
- No capacitor ESR or DC-bias derating.
- 25 C.
- Cout 4.672 mF (A108's question).
