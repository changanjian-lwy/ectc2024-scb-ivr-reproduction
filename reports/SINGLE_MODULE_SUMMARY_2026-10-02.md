# P24 single module - summary for evaluation (2026-10-02)

One four-phase module of the ECTC 2024 SCB-IVR:
- 48 V → 1 V, ~250 A resistive load;
- EPC2067, two high-side and three low-side devices per phase;
- Lf 1.4667 nH, Cs 3 µF, Co 4.672 mF.

The results below come from two models that check each other:
- a Verilog controller co-simulated with a circuit plant that has the
  datasheet's nonlinear Coss and reverse conduction;
- averaged / event-map mathematical models (D43-D59).

This closes the single-module level. Each open point is given as cases
with the value it rests on, for evaluation.

## 1. The integrated design (A105 "I2")

| part | what | where |
|---|---|---|
| switching | negative-current target 5% (−6.25 A); the high side turns on at its predicted valley (error-based correctors); phases 2-4 on period-following, averaged slots | A92, A97 |
| phase 1's turn-off | timed after 1024 learned comparator cycles, adaptive step (ADM32) | A100 |
| start-up | input ramped over 68.6 µs (Roberts' series-capacitor rule); load present from t = 0; handover to the closed loop at 72 µs; mode S Ton at the full-load value | A103 |
| output-voltage loop | PI on Ton, 100 kHz crossover (kp 189 ns/V, ki 5.5 ns/V per sample) | A104 |

## 2. Results (25 C)

| condition | result |
|---|---|
| standard matrix: n0, driver mismatch ±1 / ±3.4 ns, jitter 30 / 100 ps, load steps ±25 / ±62.5 A (11 runs) | no overlap; peak current ≤ 176 A; low side at zero voltage except under jitter (worst edge +0.3 V at 30 ps, +4.9 V at 100 ps, as in the reference designs) |
| turn-off-current spread, phases 2-4 | 0.02-0.16 A (0 ps), 0.49-0.53 A (30 ps), 1.04-1.19 A (100 ps) |
| load steps | ±25 A: ±6 mV; ±62.5 A: +12 / −15 mV, within 1% in 6-8 µs (I-only loop before: ±120 mV, ~100 µs) |
| start-up | peak 1.013 V at the handover; with the PI, 4.2 µs above 1 V (2.5 µs above 1.005 V); VRD 11.1's overshoot limits met (before: 1.277 V, then 0.903 V) |
| line steps ±10% | Vo within 18.5 mV; the series capacitors re-divide within 25 µs; **a +10% step over 1 µs peaks at 207 A (limit 200 A)**, over 10 µs at 171 A |
| high side | turns on at the valley, ~9 V of the 12 V rail (not zero voltage): central hard turn-on loss 9.3 W for four phases at 5% (D56/D57; the energy balance's minimum) |
| model agreement | D58/D59 against the co-simulation: start-up within 0.03 V; load steps within 7%; line steps not (the series-capacitor dynamics are not in the averaged model) |

## 3. Where the results differ from P24

1. **"1-2% negative current gives zero-voltage switching for all phases."**
   - With P24's own inductor values (Table I at 1, 5, 10 MHz and
     Eq. (4)'s 1.47 nH) and any of three node compositions, full
     high-side zero voltage needs at least **5.3%**, and 27% at this
     model's point.
   - At 2% the module runs soft (valley switching), with the high side
     turning on at ~9.9 V.
   - D57; A78-A86.
2. **The inductance.** Table I's 2.68 nH (5 MHz, 4 × 4) against Eq. (4)'s
   1.47 nH used here (the 2026-09-14 recheck).
3. **The start-up.** P24 describes none. A103's sequence is ours.

## 4. Choices for evaluation

Each choice is followed by the assumed value it rests on.

| choice | cases | rests on |
|---|---|---|
| negative-current target | 2%: soft, high side at 9.9 V. **5%** (chosen): 9.0 V, robust attractor. 7.5%: 8.0 V, +2% conduction | datasheet Coss(V) (typical); 25 C |
| phase 1's turn-off | comparator (I1): 0.63-0.72 A at 30 ps, 1.64-1.84 A at 100 ps. **Timed (I2):** 0.49-0.53 A and 1.04-1.19 A | edge jitter 30-100 ps (assumed; the 1EDB drivers state no jitter); **phase 1's turn-off-current limit is not set** |
| loop bandwidth | 60 kHz: ±2.6% on ±62.5 A, no spread cost. **100 kHz:** ±1.7%, +15% spread at light load. 150 kHz: ±1.1%, +40% | ideal ADC sample, 0.5 mV; Co 4.672 mF (every gain scales with it) |
| boot load during start-up | With mode S Ton 568 (this design), the full load: 1.013 V (co-simulation); 75%: ~1.10 V (D58, ±15 mV). With mode S Ton 533: ≥ ~70% keeps it within 50 mV (1.03 V at 75%). Lighter: a regulated start (RTL) and a light-load mode are needed | the processor's reset current (unknown) |
| fast rising line steps | bus slew ≤ ~0.5 V/µs: within limits. 4.8 V/µs: 207 A | the 48 V bus's slew; input feed-forward not built |

## 5. Not in this level

- **Multi-module assembly.**
- **Package and PCB parasitics.** Not in P24's published data.
- **Thermal.** 125 C appears only in the orbit model, D48.
- **Protection and light-load operation.**

## 6. A separate extension

Neither paper has this: an auxiliary commutation branch per phase (Lr and
a bidirectional switch to a self-balanced capacitor) for high-side zero
voltage.
- **Saving:** 2.6-5.2 W (1-2% of the output).
- **Area:** +10-12% dies, +3.6-3.8% inductor, +1-5.5% capacitors, and
  four floating drivers per module.
- It is kept apart from the reproduction:
  `extensions/aux_commutation_branch/README.md`, with its own cases.

## 7. Evidence

- **Experiments:** `experiments/track_A_periodic_steady_state/`
  (A92-A106).
- **Derivations:** `symbolic_derivations/03_P24_native/` (D43-D59).
- **Running status:** `reports/CURRENT_STATUS.md`.
- **Trade-offs:** `reports/TRADEOFF_SCORECARD.md`.

## 8. Addendum 2026-10-03: high-side zero voltage by the negative current (A110-A114)

The negative-current target (Section 4's first choice) was raised from
5% to 10-30% of the peak. Physical model and D62 middle-case loss model
as above.

| target | high-side turn-on | efficiency | steady state | fast line steps |
|---|---|---|---|---|
| 5% (Section 1) | 8.9-9.1 V | 87.9% | robust | 207 A at +4.8 V / 1 µs |
| **20%** | 2.2-3.0 V | **90.2%** | robust (A112) | timed turn-off: 199-204 A, −4.8 V / 1 µs settles in 75 µs |
| **25%** | **−0.16 to +0.88 V (practical zero voltage)** | **90.1%** | robust (A112) | timed: falling steps oscillate 160-180 µs; comparator (A114): rising steps run away to 246-290 A |
| 30% | partly zero voltage | 89.4% | the valley-based turn-on timing breaks down (A110, A111) | - |

- **Why 1-2% (P24) and 5% (this design) do not give zero voltage:**
  the node's capacitance needs ~27% at 1.47 nH (D57). Measured, zero
  voltage first appears at 25%.
- **The gain:** the high side's hard-turn-on loss (8.9 W) and part of the
  gate drive (lower frequency) outweigh the extra conduction.
- **The open limit:** fast input changes. The controller structure (phase
  1 at its boundary, phases 2-4 on slots) cannot follow a fast rail
  change with a large negative current. A per-phase boundary, or an
  input slew limit, is needed.
- **For evaluation:** whether the bus slew allows 20-25%.
  - **20%** is the robust choice today: load steps and slow inputs fine;
    line-step peaks at the limit.
  - **25%** needs either a slow bus or the controller change.

