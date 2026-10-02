# A102 / D57 - the auxiliary commutation branch over its assumed values (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Follows A101 / D56.

**Boundary:** `BOUNDARY.md`. It was committed with D57 and the
predictions (0b3eec7) before any run. The code is a7b5e23.

**Records:**
- `cosim/run_*.json` and `cfg_*.json`;
- `a102_summary.json` (`a102_analyze.py`);
- `d57_predictions.json`.

**Models:**
- **Physical:** Verilog RTL (unchanged) with A88's plant (kernel2) and the
  adopted design (A92's correctors, A97's slots), 25 C, ~250 A
  resistive load.
  - Branch per phase: Lr and a bidirectional switch (two dies of
    α × EPC2067) to Cm.
  - `valley_zero` 0; enabled at 200 µs (the handover is at 88.6 µs).
- **Mathematical:** D57 (`symbolic_derivations/03_P24_native/D57_P24_AUX_SCENARIOS.md`),
  on D56's single-phase model.

**Statistics:** over the last 200 periods unless stated.

**Approach.** The cases are built here instead of asking Mihai for the
values. They are for him to evaluate.

## 0. Verdict

1. **Is the branch worth it?** The sign rests on one value, the hard
   turn-on loss, and physics fixes it (D57 Section 3).
   - D56's central estimate is the circuit's energy balance: the high
     side's own Eoss, plus the other node capacitances' charge drawn
     through its channel. For identical devices this is the textbook
     Qoss·V.
   - A real turn-on can only lose more (current overlap, Coss
     hysteresis, ringing).
   - A91's lower bound (own Eoss only) assumes that charge comes in
     without loss. A hard-switched node cannot do that.
   - **Measured, central model:**

     | run | net, four phases |
     |---|---|
     | 1.25 nH (A101 p125) | −5.0 W |
     | Lr with P24 Table 2's air-core R (7.3 mΩ) | −4.2 W |
     | gate supply at 50% | −4.3 W |
     | 5 A residual at the opening | −4.8 W |
     | 0.75 nH (A101 dz_vz0) | −4.4 W |

   - D57's grid with all three of those penalties together: **−2.6 to
     −3.4 W**. So the saving is about 1-2% of the 250 W output.
2. **Does it fit?** Against the main stage of the same technology (D57):
   - the BDS dies are +10-12% of the switch area (P24 Table 3: 46.3 mm²
     per phase);
   - Lr is +3.6-3.8% of the inductor (by peak stored energy), 0.5% by
     L·I_rms²;
   - Cm (1 µF) is +4.6-5.5% of the series capacitors (by C·V²); with
     0.22 µF, about 1%;
   - plus four floating gate drivers per module (eight today; P24's
     estimate leaves drivers out).
3. **P24's 1-2%** cannot give zero voltage with any of P24's own
   inductor values or node compositions (D57 Section 2). The minimum is
   **5.3%**: 1 MHz (13.44 nH), counting only the high side's capacitance.
   That falls in P25's 5-10%. At 2% the high side turns on at the valley
   (9.9 V of 12.2 V), so 1-2% is at most a partial reduction.
4. **Enable after the handover** (Cm at 5 V, at D56's balance, or at
   0 V):
   - every run is stable, with no overlap;
   - Vm and the high side's V_DS settle in 24-32 µs;
   - the final state is A101's.
   - **New problem: Vo rises to 1.09-1.11 V** about 19 µs after the
     enable, and is back within 1% by 53 µs. This misses the ±5%
     criterion.
     - Cause: with the branch, the node's swing is paid by Cm, not by the
       filter inductor, so Ton drops by 16-19% (568 → 479 LSB at
       1.25 nH, 460 at 0.75 nH).
     - At the enable, the loop's gain jumps by that much until the
       voltage loop pulls Ton down.
     - A Ton feed-forward at the enable (≈ −90 to −110 LSB) is the
       obvious fix. **Not tested.**
   - **The precharge sets the current peak, not the Vo transient:**

     | precharge | peak branch current | against D57's first cycle |
     |---|---|---|
     | 0 V | 168 / 264 A | 173 / 277 A |
     | 5 V | 91 / 152 A | 82 / 137 A |
     | D56's balance | 43 / 62 A | 28 / 37 A |

     The balance case still exceeds 1.3 × the final peak, because the
     controller's timing has not yet adapted.
   - Against A101's start with the branch on from t = 0 (270-430 A
     until about 150 µs), enabling after the handover is much milder
     even without a precharge.
5. **Load steps of ±62.5 A:** all criteria met for both designs.
   - **Vo extremes** are slightly below A100's reference (+118 / −125 mV
     against +122 / −127 mV).
   - **The branch current is unchanged** across the step.
   - **The low side stays at zero voltage.**
   - **D57's load prediction holds within 0.1 V (Vm) and 0.15 V
     (V_DS).** The exception is s075_p62's V_DS, which turns on past the
     rail (Section 3).
     - At 1.25 nH: Vm 7.33 V (7.40), V_DS 2.94 V (3.07) after −62.5 A;
       Vm 8.88 V (8.92), V_DS 1.52 V (1.44) after +62.5 A.
     - At 0.75 nH, light load (−62.5 A) costs full zero voltage, as D57
       predicted: +0.31-0.41 V at turn-on (D57: +0.52).
6. **The 2% target:**
   - ref_2pct matches D51's 2% orbit within 0.05 V.
   - With the branch, D57 holds within 0.15 V (Vm) and 0.21 V (V_DS):
     - 1.25 nH meets every criterion;
     - 0.75 nH misses one, by 0.03 points (phase 4's ripple 3.03% below
       the reference; lower is not worse).
   - Net against the 2% design without a branch: −6.8 to −7.1 W.
   - **With a branch the target hardly matters:** 2% and 5% end within
     0.3 W of each other (Section 5). Without a branch, 2% loses about
     2.4 W against 5%.
7. **Realism:**
   - r125_lrair meets every criterion: −4.2 W against D57's −4.4 W.
   - c125_cm022 (0.22 µF) misses the Vm criterion on phases 2-4 (+0.45
     to 0.48 V against A101's 1 µF).
     - It is stable, its V_DS is better (1.83 against 2.15 V), and its
       net is the same (−5.0 W).
     - Likely cause: Vm is sampled once per period, at phase 1's
       turn-on, and with 0.22 µF Cm swings by ~0.9 V within a cycle
       (D57). **Not verified.**

## 1. Gates

| check | result |
|---|---|
| shared plant, enable off (default) | `--full` regression PASS; A101 dz_vz0 and p125 rerun to 100 µs: every section identical |
| enable / precharge in the plants | `tests/test_cosim_plants.py` `CosimPlantAuxEnable`: Fast and Kernel bit-identical with Reference; no branch current while disarmed |
| D57 | `tests/test_p24_aux_scenarios.py`, 5 of 5 |
| provenance | every run from committed code (`cosim_sources_modified` false) |
| enable runs' record length | the first runs kept the default 1000 records, which did not reach back to the enable. Rerun with 6000 (ffc36c3): sections, steps and the last 1000 turn-ons identical |

## 2. Enable (registered criteria, BOUNDARY 5.1)

| run | peak i_r (A) | Vo after the enable | Vm / V_DS settle (µs) | final state vs A101 | criteria missed |
|---|---|---|---|---|---|
| e125_5v | 91 (D57 82) | 0.983-1.091 | 28-30 / 24-28 | all ok | Vo ±5% |
| e075_5v | 152 (137) | 0.978-1.111 | 28-30 / 28-30 | Vo +1.4 mV | Vo ±5%; final Vo |
| e125_pc | 43 (≤ 35 allowed) | 0.983-1.092 | 27-29 / 24-28 | all ok | Vo ±5%; peak |
| e075_pc | 62 (≤ 47) | 0.978-1.111 | 28-29 / 28-32 | Vo +1.3 mV | Vo ±5%; peak; final Vo |
| e125_0v | 168 (≥ 121) | 0.983-1.091 | 27-32 / 25-31 | all ok | Vo ±5% |
| e075_0v | 264 (≥ 194) | 0.978-1.111 | 30-31 / 30-31 | Vo +1.3 mV | Vo ±5%; final Vo |

- **Final Vo.** The 0.75 nH runs end 1.3-1.4 mV above A101's dz_vz0
  (criterion ±1 mV). Over 300-500 µs, dz_vz0 itself wanders between
  0.998 and 1.002 V with a period of ~100 µs. The criterion was tighter
  than the loop's own wander.
- **Vm, V_DS and branch currents** of every run equal A101's final state
  (±0.1 V, ±0.2 V, ±5%).

## 3. Load steps (BOUNDARY 5.2): all met

| run | Vo extreme (A100 ref) | i_r peak before → after | after the step, phase 1 Vm / V_DS (D57) | low side |
|---|---|---|---|---|
| s125_m62 | +118 mV (+122) | 28 → 27 A | 7.33 V / +2.94 V (7.40 / +3.07) | −0.71 to −1.14 V |
| s125_p62 | −125 mV (−127) | 28 → 29 A | 8.88 V / +1.52 V (8.92 / +1.44) | −1.16 to −1.76 V |
| s075_m62 | +118 mV (+122) | 36 → 36 A | 8.12 V / +0.38 V (8.21 / +0.52) | −0.78 to −1.17 V |
| s075_p62 | −125 mV (−127) | 36 → 37 A | 9.68 V / −1.53 V (9.62 / 0) | −1.16 to −2.12 V |

- **Vo is settled after every step.** It is within 2.2 mV of 1.0 V over
  the last 200 periods.
- **s075_p62** turns on 1.5 V past the rail. This is A92's corrector
  aiming after the valley, as in A101 (dz_vz0, −0.7 V). It is below the
  reverse-conduction threshold (2.09 V).

## 4. The 2% target (BOUNDARY 5.3)

| run | Vm (V), phases 1-4 (D57) | high-side V_DS (D57) | i_r, phase 1 (D57) | result |
|---|---|---|---|---|
| ref_2pct | - | 9.93 / 9.87 / 9.87 / 10.26 (D51 9.93 / 9.86 / 9.86 / 10.21) | - | soft, matches |
| n125_2pct | 7.66 / 7.88 / 7.88 / 8.19 (7.80 / 7.97 / 7.98 / 8.18) | +2.89 to +2.93 (+2.72 to +2.83) | +23.4 / −29.6 A (+23.5 / −29.9) | all met |
| n075_2pct | 8.54 / 8.80 / 8.80 / 9.12 (8.69 / 8.85 / 8.86 / 9.07) | −0.01 to +0.07 (0) | +34.6 / −38.8 A (+34.4 / −39.3) | phase 4's ripple −3.03% (±3%) |

## 5. Losses on measured quantities (W, four phases; t_f 1 ns; negative = saving)

| run | A91 lower | **central** | A91 upper | gate supply 50% | residual 5 A |
|---|---|---|---|---|---|
| A101 p125 (1.25 nH) | +0.60 | **−5.04** | −11.74 | −4.28 | −4.76 |
| A101 dz_lr100 (1.0 nH) | +0.95 | **−4.95** | −12.08 | −4.19 | −4.73 |
| A101 dz_vz0 (0.75 nH) | +1.63 | **−4.37** | −11.65 | −3.45 | −4.20 |
| r125_lrair (Lr 7.3 mΩ) | +1.39 | **−4.22** | −10.88 | −3.46 | −3.94 |
| c125_cm022 (Cm 0.22 µF) | +0.70 | **−5.02** | −11.86 | −4.26 | −4.74 |
| n125_2pct (against ref_2pct) | +0.23 | **−7.09** | −15.25 | −6.29 | −6.80 |
| n075_2pct (against ref_2pct) | +1.19 | **−6.84** | −16.10 | −5.87 | −6.67 |

**2% against 5%:**
- **Main conduction** (triangle from the valley to the peak; Lf's R plus
  the duty-weighted switches): 22.39 W at 2% against 22.64 W at 5%.
- **Hard turn-on** (central): 11.46 W against 8.84 W.
- **Without a branch**, 2% loses about 2.4 W against 5%.
- **With the branch:**
  - 2% + 1.25 nH ≈ 33.85 − 7.09 = 26.8 W;
  - 5% + 1.25 nH ≈ 31.48 − 5.04 = 26.4 W;
  - at 0.75 nH, 27.0 against 27.1 W.
- **The difference is within these estimates' accuracy.**

## 6. What is not covered

- **The enable's Vo transient fix:** a Ton feed-forward at the enable,
  or running with the branch from the start with Cm precharged.
- **The bidirectional switch as a real device:**
  - a ~12 V die;
  - its floating gate supply (here only an efficiency);
  - its zero-current detection (ideal in the co-simulation, a residual
    current in D57 only).
- **Temperature, jitter with the enable, and P24's 1 MHz design point**
  (13.44 nH) in the co-simulation.
- **The c125_cm022 Vm sampling explanation.**
- **A measured hard turn-on loss.** The central model is the energy
  balance's minimum, so measurement can only raise the saving.
