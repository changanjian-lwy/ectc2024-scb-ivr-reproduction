# A100 / D55 - the timed phase-1 turn-off under load steps: an adaptive dlo step (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`.

**Boundary:** `BOUNDARY.md`.
- Sections 1-4 were written before any code or run.
- Section 5 records the reference runs, D55's choice and the registered
  bands. It was committed (ac96d47) before the timed runs.

**Records:**
- `cosim/run_*.json` and `cfg_*.json`;
- `a100_summary.json` (`a100_analyze.py`);
- `d55_predictions.json`;
- `synth/stat_scb_ctrl.txt`.

**Models:**
- **Physical:** Verilog RTL with A88's plant (kernel2), the adopted design
  (A92's correctors, A97's averaged slots and guard), 5%, 25 C.
  - Phase 1's turn-off is timed after 1024 learned comparator cycles.
  - Load steps of ±25 and ±62.5 A at 400 us, on the ~250 A load, to
    600 us.
- **Mathematical (D55):**
  - a replay of each dlo rule against the interval phase 1 needs, measured
    in the comparator design's reference runs;
  - D54's Monte Carlo for jitter.
  - `symbolic_derivations/03_P24_native/D55_P24_DLO_RULE_LOAD_STEPS.md`.

## 0. Verdict

1. **The adaptive step (ADM32) tracks every step.** It doubles while
   consecutive decisions agree, up to 32 LSB.

   | step | phase 1's largest turn-off current deviation (predicted) | Vo excursion, ADM32 / comparator design |
   |---|---|---|
   | +25 A | 0.61 A (0.86) | 49.9 / 49.6 mV |
   | −25 A | 0.68 A (0.80) | 49.2 / 50.1 mV |
   | +62.5 A | 1.74 A (2.42) | 125.6 / 127.0 mV |
   | −62.5 A | 1.44 A (1.91) | 120.4 / 121.9 mV |

   - No cross-conduction; peaks as the comparator design's.
   - **All four meet the registered criteria.** The replay over-predicts
     the error by 25-30%; it does not include the loop's own response.
2. **A99's ±1 rule cannot track:** 23.3 A (+62.5 A) and 18.6 A (−62.5 A),
   against the predicted > 10 A.
   - Phase 1's turn-off current reaches +16.9 A and −24.9 A. It then runs
     as an uncontrolled current source: Vo moves less (103 and 83 mV), but
     phase 1 is far from its operating point.
3. **The jitter benefit stays, minus the price of tracking:**

   | phases 2-4 turn-off current spread | comparator (A97) | ±1 rule (A99) | **ADM32 (A100)** |
   |---|---:|---:|---:|
   | 30 ps | 0.56-0.66 A | 0.39-0.43 A | **0.42-0.47 A** (−24 to −30% against A97) |
   | 100 ps | 1.59-1.79 A | 1.02-1.16 A | **1.04-1.20 A** (−29 to −35%) |
   | 0 ps (before the step) | 0.18-0.21 A | 0.018 A | **0.021 A** |

   - ADM32 costs 7-13% against the ±1 rule at 30 ps. D55 predicted 9%.
   - This is the noise-against-tracking trade-off, now measured on both
     sides.
4. **Against D55's jitter bands:**
   - j100 agrees.
   - j30 is within on the spreads, early fraction and phase 1's mean, but
     its period spread is **+39%** (0.374 against 0.269 ns), outside the
     ±30% criterion. A99's j30 missed the same way. The co-simulation
     sits above the model at small σ in A98, A99 and A100.
5. **Recommended for adoption, pending the trade-off review.** It is the
   first timed turn-off that holds in steady state, under jitter and under
   load steps. The open limits are in Section 4.

## 1. Gates

| check | result |
|---|---|
| load step and record length (plant, C kernel, bridge) | `--full` regression PASS; plant tests passed |
| RTL `cfg_lo_adm` / `cfg_lo_ff` | 44 of 44 unit tests; `--full` PASS; **A99 n0 replayed bit-identically**; synthesis 0 problems, 43 924 cells |
| every A100 timed run, before the switch (321.5 us) | the same RTL path as A99, hence as A97 (A99's gate) |

## 2. Reference runs (comparator design)

| step | Vo extreme | Ton | phase 1's on-low interval | its change per cycle, 95th % / largest |
|---|---|---|---|---|
| +25 A | 0.950 V | 568 → 624 LSB | 203.7 → 221.6 ns | 13.6 / 31 LSB |
| −25 A | 1.050 V | 568 → 512 | 203.7 → 185.7 | 13.4 / 32 |
| +62.5 A | **0.873 V** | 568 → 706 | 203.7 → 248.2 | 24 / 54 |
| −62.5 A | **1.122 V** | 568 → 427 | 203.7 → 158.9 | 16 / 44 |

The voltage loop (A79, ki = 0.25 ns/V) lets Vo move ±5% for ±10% steps and
±12% for ±25% steps. **That belongs to the voltage loop, not to the
turn-off.**

## 3. Phase 1's switching under the steps (after 400 us)

| step | rule | turn-off current | high-side turn-on V_DS max |
|---|---|---|---|
| +62.5 A | comparator | -6.50 to -6.00 A | 9.31 V |
| +62.5 A | ADM32 | -6.88 to -4.56 A | 9.58 V |
| +62.5 A | ±1 | -6.10 to **+16.93** A | 10.48 V |
| −62.5 A | comparator | -6.52 to -6.00 A | 9.03 V |
| −62.5 A | ADM32 | -7.74 to -5.80 A | 9.01 V |
| −62.5 A | ±1 | **-24.90** to -6.49 A | 8.90 V |

No turn-on in any run exceeded 12 V.

## 4. Limits

- **The learning length** (1024 cycles) is chosen for this start-up's
  settling. The handover itself still uses the comparator.
- **Not tested:**
  - line steps;
  - loads far from 250 A;
  - other ZVS targets (the 2% case);
  - m ≠ 0 with the timed turn-off.
- **The −62.5 A step has a floor of about 1.4-1.9 A** in phase 1's
  deviation. The measurement is one cycle late while the required interval
  changes by up to 54 LSB per cycle.
- **The slow voltage loop** dominates Vo's response for both designs, and
  is not addressed here.
