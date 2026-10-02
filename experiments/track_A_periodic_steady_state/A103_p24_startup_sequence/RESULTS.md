# A103 / D58 - the P24 module's start-up sequence (RESULTS)

Track A, main line.

**Boundary:** `BOUNDARY.md`, with D58 and the predictions committed
before the runs (6cb57f5).

**Records:**
- `cosim/run_*.json` and `cfg_*.json`;
- `a103_summary.json` (`a103_analyze.py`);
- `d58_predictions.json`.

**Models:**
- **Physical:** Verilog RTL (unchanged) with A88's plant (kernel2) and the
  adopted design (A92's correctors, A97's averaged slots), 5%, 25 C,
  4 mΩ resistive load, the 68.61 µs input ramp, 500 µs.
- **Mathematical:** D58, an averaged model
  (`symbolic_derivations/03_P24_native/D58_P24_STARTUP_AVERAGED.md`).

## 0. Verdict

1. **The sequence alone fixes the start-up**, provided the module starts
   into its load. Load from t = 0, handover at 72 µs, mode S's Ton at the
   full-load value (c1d):
   - Vo peaks at **1.013 V**, is **17.6 µs above 1 V**, and is within 1%
     from **73.5 µs**;
   - before: 1.277 V, then 0.903 V, within 1% from 205.7 µs.
   - This meets VRD 11.1's overshoot limits: ≤ 50 mV, ≤ 25 µs above VID.
   - No overlap. The final state is the adopted design's.
   - No RTL or hardware change.

   | run | Vo max | time above 1 V | min after the handover | within 1% from |
   |---|---|---|---|---|
   | c0 (as before) | 1.277 V | 45 µs | 0.903 V | 205.7 µs |
   | c1: load from 0 | 1.007 V | 61 µs | 0.957 V | 126.7 µs |
   | c1b: + handover at 72 µs | 1.008 V | 62 µs | 0.948 V | 106.9 µs |
   | **c1d: + mode S Ton 568 LSB** | **1.013 V** | **17.6 µs** | **0.998 V** | **73.5 µs** |

2. **Why it works** (D58, confirmed by c0):
   - The overshoot was mode S running open loop at no load.
   - The dip was the 250 A load arriving at the handover while the loop
     started at the wrong Ton.
   - With the load present, mode S stops at its loaded output, and the
     loop has only a few mV to correct.
3. **The condition: the boot load must be near the full load.** In mode
   S the module is a voltage source behind ~1.3 mΩ (D58, refit on c1).
   At the end of the ramp, open loop:

   | boot load | Ton 533 | Ton 568 |
   |---|---|---|
   | 100% | 0.968 V | 1.031 V |
   | 75% | 1.030 V | 1.098 V |
   | 50% | 1.101 V | 1.173 V |
   | 25% | 1.182 V | 1.260 V |

   - **A processor's real reset current is not known here.**
   - For a light boot load, the loop must also run in mode S, with a
     reference soft start (an RTL change).
   - The light-load limit of mode P (≈ 100 A at the lower Ton clamp, D58)
     also applies.
4. **c1 and c1b miss VRD's 25 µs** (61-62 µs above 1 V by 7-8 mV). That
   tail is the integral loop's own slowness, as D58 predicted (scorecard
   T6), not the sequence.

## 1. Gates

| check | result |
|---|---|
| bridge keys `t_load_us`, `t_hand_us` (off by default) | `--full` regression PASS |
| c0 against A100's reference run | 1375 sections before 300 µs identical |
| D58 | `tests/test_p24_startup_averaged.py`, 3 of 3 |
| provenance | every run from committed code |

## 2. Against the registered criteria (BOUNDARY Section 5)

| criterion | c0 | c1 | c1b | c1d |
|---|---|---|---|---|
| no overlap | ok | ok | ok | ok |
| peaks within 24.8 V and the reference's current | MISS (26.7 V) | MISS (24.7 V, 163 A) | MISS (24.7 V, 163 A) | MISS (24.6 V, 170 A) |
| ladder ≤ 3% before the handover (Vin ≥ 12 V) | MISS (7.3%) | MISS (5.5%) | MISS (5.5%) | MISS (4.6%) |
| D58: Vo max ±15 mV, ±15 µs | ok | ok (1.007 / 1.011; 159 / 148 µs) | ok (1.008 / 1.018; 138 / 125 µs) | MISS (1.013 at 72 µs; D58 at 112 µs) |
| D58: Vo at the handover and min after ±0.03 V | ok | MISS (0.968 / 0.932) | MISS (0.954 / 0.898) | MISS (1.013 / 0.957) |
| D58: 1% settling ±20 µs | ok | MISS (127 / 156) | MISS (107 / 146) | MISS (74 / 125) |
| final state = c0 | ok | ok | ok | ok |
| VRD: Vo max ≤ 1.050 V | - | ok | ok | ok |
| VRD: ≤ 25 µs above 1 V | - | MISS (61) | MISS (62) | ok (17.6) |

**Two criteria were mis-set.**
- **Peaks:** 24.8 V is A73's value on an older plant. c0, the adopted
  design's own start-up, peaks at 26.7 V. Against c0:
  - the new sequences' peak V_DS is lower (24.6-24.7 V);
  - their peak current is +2 A (c1, c1b) and +9 A (c1d, 170 A). c1d
    runs mode S at the full-load Ton under load for the whole ramp.
- **Ladder:** 3% is also A73's. With A73's formula, max |VCs_k/Vin −
  (4−k)/4|:

  | | c0 | c1 / c1b | c1d |
  |---|---|---|---|
  | Vin ≥ 12 V | 7.3% | 5.5% | 4.6% |
  | Vin ≥ 24 V | 4.8% | 2.7% | 2.2% |
  | at the handover | 0.28% | 0.36-0.43% | 0.41% |

  - The early samples include the switch node's ~2 V reverse-conduction
    drop (the capacitor voltage is a_k − x_k at phase 1's turn-on).
  - **The new sequences are better than c0 throughout.**
  - (The first analysis computed a relative deviation by mistake. It was
    corrected to A73's formula before this report.)

**D58's miss is mode S under load.**
- Its output resistance came from A73 (1.47 mΩ, an older plant). c1 gives
  1.275 mΩ.
- Refit on c1, D58 predicts c1b within 2 mV (peak) and 3 µs (time above
  1 V). c1d is within 14 mV at the handover.
- The mode-P and loop part matched c0 within 0.03 V and 15 LSB.
- **This refit is post-hoc.**

## 3. Final state (last 200 periods, all four runs)

- **Vo:** 0.9998-1.0000 V.
- **High-side turn-on V_DS:** 8.94 / 8.89 / 8.89 / 9.04 V.
- **Low-side turn-on V_DS:** max −0.94 to −1.74 V.
- **Low-side turn-off current:** −6.37 / −6.98 / −6.99 / −5.92 A.
- **c1d's start leaves the same steady state** (low side −1.04 / −1.23 /
  −1.23 / −1.74 V, within the criteria).

## 4. What is not covered

- **A light boot load:** a regulated mode S (loop and reference soft
  start during the ramp) is an RTL change. Mode P's light-load limit
  remains.
- **The voltage loop's tail** (T6).
- **Jitter, temperature, other negative-current targets.**
- **The extension's branch enable**
  (`extensions/aux_commutation_branch/`) can now be placed into this
  sequence. That belongs to the extension.
