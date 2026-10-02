# A104 / D59 - the output-voltage loop as a PI on Ton (BOUNDARY)

Track A, main line (scorecard T6).

**Written before any A104 run.** The RTL change (`cfg_kp`), its gates,
D59 and the predictions (`d59_predictions.json`) are committed with this
file.

## 1. Question

A79's loop is integral only, ki = 0.25 ns/V, picked without a design:
- crossover 7.5 kHz (D59), phase margin 51°;
- ±62.5 A steps move Vo by +122 / −127 mV (A100) and take ~100 µs to
  return within 1%;
- the start-up's tail (A103 c1, c1b: ~60 µs above 1 V) is the same
  slowness.

**How fast can the loop be made, and what limits it?**

## 2. Prior work

- **Voltage regulators for processors run fast loops.**
  - Wang, Li, Liang and Wang, "A Multi-phase Series Capacitor
    Trans-inductor Voltage Regulator with High Switching Frequency and
    Fast Dynamic Response", APEC 2023, pp. 2207-2212.
    - Constant on-time, 1.2 MHz.
    - Loop bandwidth 605 kHz (conventional design: 213 kHz).
    - 66 mV droop on a 50 → 550 A step at 1000 A/µs.
  - The same group's small-signal model of the series-capacitor TLVR
    under constant on-time current-mode control (IEEE TPEL 2024,
    DOI 10.1109/TPEL.2024.3488734). Read only as an abstract: the series
    capacitor enters the power stage's transfer function.
- **Digital loops:**
  - D. Maksimović and R. Zane, "Small-Signal Discrete-Time Modeling of
    Digitally Controlled PWM Converters" (local PDF), for the sampling
    delay;
  - Peterchev and Sanders, "Quantization resolution and limit cycling in
    digitally controlled PWM converters" (local PDF). Limit-cycle
    conditions: the DPWM step must move Vo by less than an ADC step, and
    the integral gain must be small. **Here one Ton LSB moves Vo by
    ~1.8 mV against a 0.5 mV ADC LSB, so a dither of a few LSB is
    expected.**
- **Series-capacitor resonances** (Roberts' dissertation Eq. 3.44, N = 4):
  140, 259, 339 kHz at Cs = 3 µF and the full-load duty. Neither D58 nor
  D59 models them.

## 3. D59 (mathematical model)

`symbolic_derivations/03_P24_native/D59_P24_VOLTAGE_LOOP.md`.

**Plant (D58, mode P):** the module is a current source set by Ton.
- g = dI/dTon = 0.486 A per LSB;
- its own conductance 25 S plus the 250 S load;
- Co = 4.672 mF;
- pole at 9.4 kHz.

**Loop:** sampled once per period (232 ns) at phase 1's turn-on. Each phase
takes the new Ton at its own turn-on. ADC (0.5 mV) and Ton (31.25 ps) are
quantised.

**Validation:** A100's ±62.5 A steps, the present loop: +120.1 / −127.1 mV
against +121.9 / −127.0 mV; times within 0.5 µs.

**Design rule:** kp sets the crossover (P alone); the integral zero is at
fc / 5.

## 4. Cases (co-simulation)

**Physical model:** Verilog RTL with `cfg_kp`, A88's plant (kernel2), the
adopted design (A92 + A97), 5%, 25 C, 4 mΩ load.

**Start:** A103's c1d (load from t = 0, handover at 72 µs, mode S Ton
17.75 ns).

**Steps:** ±62.5 A at 400 µs, to 600 µs, records of 6000 edges.

| design | kp (ns/V) | ki (ns/V per sample) | D59 crossover, phase margin |
|---|---|---|---|
| ref (A79) | 0 | 0.25 | 7.5 kHz, 51° |
| fc30 | 56.655 | 0.4959 | 29 kHz, 94° |
| fc60 | 113.31 | 1.9838 | 60 kHz, 84° |
| fc100 | 188.851 | 5.5105 | 101 kHz, 78° |
| fc150 | 283.276 | 12.3986 | 153 kHz, 73° (above the first series-capacitor resonance, 140 kHz) |

Each design is run with the −62.5 A and the +62.5 A step (10 runs).

## 5. Registered predictions and criteria

From D59 (`d59_predictions.json`):

| design | −62.5 A | +62.5 A | back within 1% | from c1d's handover state (1.013 V): time above 1.005 V |
|---|---|---|---|---|
| ref | +120.1 mV | −127.1 mV | 93 / 111 µs | 11.0 µs |
| fc30 | +44.0 | −45.3 | 48 / 73 µs | 3.5 µs |
| fc60 | +24.3 | −25.2 | 16 / 23 µs | 1.9 µs |
| fc100 | +15.5 | −15.9 | 6.7 / 8.9 µs | 1.2 µs |
| fc150 | +10.6 | −11.2 | 2.6 / 3.4 µs | 0.8 µs |

**Criteria:**
1. **Stable.**
   - No overlap.
   - Before the step (350-400 µs): Vo peak-to-peak ≤ 5 mV and Ton
     peak-to-peak ≤ 12 LSB at the sections.
   - No oscillation after the step: in the last 50 µs, Vo peak-to-peak
     ≤ 5 mV.
2. **Zero voltage kept**, before and after the step:
   - low-side turn-on V_DS ≤ 0 on every phase;
   - high-side turn-on V_DS within ±0.3 V of the reference design;
   - phases 2-4's turn-off-current spread (sd) ≤ 1.5 × the reference's.
3. **Against D59:**
   - step extremes within ±30%;
   - the time back within 1% within ±50% (or ±5 µs).
   - fc30-fc100 are expected to meet these.
   - **fc150 is the test of the unmodelled series-capacitor resonance:**
     a miss there is the expected sign of that limit.
4. **Start-up** (from c1d, 72 µs handover): Vo max ≤ 1.050 V; the time
   above 1 V and above 1.005 V are reported against VRD's 25 µs.

## 6. What stays assumed

- **The ADC:** ideal sample at phase 1's turn-on, 0.5 mV, no filter and
  no added latency.
- **No load line (AVP); no jitter; 25 C.**
- **The 4.672 mF output capacitance** (the init run's) and its ideal
  behaviour. A smaller Co would raise the plant gain and change every
  number here.
