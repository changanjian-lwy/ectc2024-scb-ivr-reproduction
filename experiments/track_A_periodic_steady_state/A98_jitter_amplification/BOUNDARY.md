# A98 / D53 - why gate-driver jitter is amplified, in both models (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`.
Written before any code or run of A98 and D53.

## 1. Question

Since A91, every gate edge carries independent Gaussian jitter of σ. The
co-simulation's response is much larger than σ alone explains.

**Co-simulation (A92 j30/j100, A97 j30/j100):**
- At 30 ps, the low-side turn-off current spread of phases 2-4 is
  0.52-0.66 A (deterministic runs: about 0.17 A).
- **20-27% of the high-side turn-ons of phases 2-4 come before the
  valley.**
  - D50's scalar corrector model predicted about 3%.
  - It assumes that the valley stays put, but the valley time itself
    varies by 0.098 ns per cycle (D50 Section 8.3).
- At 100 ps, the spread is 1.4-1.8 A, and 39-47% of the high-side
  turn-ons are early.
- From 30 to 100 ps (×3.3), the spread grows ×2.6-2.9. So the response is
  not linear in σ.

**Where does the amplification come from, and what in the controller
could reduce it?** Three candidates:
1. **The circuit:** a jittered edge changes a current, the current moves
   the next resonant transition (the valley), and the correctors follow.
2. **The correctors' gain:** the error-based update with gain 1/2.
3. **The early rule:**
   - a high-side turn-on before the valley adds a fixed
     dt_step = 0.2 ns, more than twice the 94 ps target;
   - a low-side turn-on before the crossing adds 0.05 ns.

## 2. Prior work

- **Peterchev, Sanders, IEEE TPEL 18(1):301-308, 2003, DOI
  10.1109/TPEL.2002.807092.** Limit cycles from quantisation in digital
  control loops. The trim's ±1 LSB alternation (D52) is of this kind.
- **Schirone, Macellari, Pellitteri, IET Power Electronics 10(4):421-428,
  2017, DOI 10.1049/iet-pel.2015.0551.** Predictive dead-time control for
  GaN converters. The trade-off is between small fixed steps (high
  resolution, slow) and fast response. Known from search results only.
- **Maksimovic, Zane, IEEE TPEL 22(6):2552-2556, 2007, DOI
  10.1109/TPEL.2007.909776.** Small-signal discrete-time modelling of
  digitally controlled converters, the class of model D53 uses.
- **D52:** the closed-loop linearisation with correctors, which D53
  extends with edge inputs.
- **D50 Section 4:** the scalar corrector model (σ_e = 49 ps at 30 ps).
  It is right for the low side and wrong for the high side.

The three papers have not been read in full; their DOIs go to the user.

## 3. Models

### 3.1 How jitter enters (from the bridge, `src/scb_ivr/cosim/bridge.py`)

**The jitter model.** Every commanded edge reaches the plant at
t_cmd + t_drv + m (low side only) + δ. Each δ is an independent N(0, σ).

**The jitter does not accumulate.** The RTL schedules each edge from the
previous **commanded** edge. The circuit therefore sees differences of
consecutive edge jitters:
- **phase k's high-side turn-on after its low-side turn-off:**
  d_k + δ_hon,k − δ_loff,k. For phase 1 the reference is the latch's
  commanded time.
- **on-time:** Ton + δ_hoff,k − δ_hon,k;
- **low-side turn-on after the high-side turn-off:**
  dl_k + δ_lon,k − δ_hoff,k;
- **slot of phases 2-4, after the actual phase-1 turn-on:**
  slot_k + δ_loff,k − δ_hon,1;
- **phase 1's low-side turn-off** (current comparator): a delay δ moves
  its current by −Vo/L·δ, the same as a threshold shift.

**The measurements include the jitter:**
- the high-side error is the actual turn-on minus the valley;
- the low-side error is the actual turn-on minus the crossing;
- the period measured for the slots is that of the commanded turn-ons.

### 3.2 D53 (mathematical model)

**The map.** D52's map is extended with per-phase on-time and slot
offsets, so that each edge has its own input. This needs an opt-in to
`ControlLP`: `ton_offset` and `slot_offset`, both zero by default.
- Adding 0.0 leaves every float unchanged.
- **Gate:** `scripts/p24_orbits.py --gate` (13 archived orbits) and D52
  recomputed, both bit-identical.

**Two calculations at D51's orbit (average slots) and D50's (fixed
slots):**
1. **Linear covariance.**
   - The closed loop of D52 with the 16 edge jitters per cycle as white
     inputs, with quantisation and the early rule left out.
   - The steady-state covariance comes from the discrete Lyapunov
     equation.
   - This is the amplification by the circuit and the correctors' gain
     alone (candidates 1 and 2).
2. **Monte Carlo: linear circuit, exact controller.**
   - The circuit is D52's linearised map.
   - The controller is the RTL's rules: commanded delays in LSB, error
     measurements rounded to 31.25 ps, the arithmetic-shift update, the
     early rules (+0.2 ns high, +0.05 ns low), clamps, the trim (±1 per
     cycle from the sign of the actual turn-off current), the voltage loop
     in integers, and the slot rule.
   - 20 000 cycles per case.
   - This adds candidate 3 and the quantisation.

**Outputs, per phase:**
- low-side turn-off current spread;
- early fractions (high and low side);
- high- and low-side error spread;
- valley-time spread;
- the windowed dither.

**What D53 cannot do.** The circuit is linear. A high-side turn-on well
before the valley (hard switching) changes the circuit beyond first
order. The Monte Carlo keeps the timing effect and not the loss.

### 3.3 A98 (physical model)

**Configuration.** The adopted design (preset: A92's correctors with A97's
slots), Verilog co-simulation, kernel2.

**One bridge opt-in:** `driver.jitter_edges` = `"all"` (absent: as now),
`"high"` or `"low"`. It restricts the jitter to the high-side or the
low-side gate edges.
- With the key absent, the random-number sequence and every result are
  unchanged.
- **Gate:** `--full` regression.

**Runs:**

| run | σ | jittered edges | purpose |
|---|---:|---|---|
| s10, s20, s50 | 10, 20, 50 ps | all | the σ sweep, with A97's j30 and j100 |
| h30, l30 | 30 ps | high only, low only | which edges drive the spread |
| one mitigation run | 30 or 100 ps | all | chosen from D53 **before** it runs, in an amendment to this file (Section 5) |

## 4. Predictions (before D53 is built and before A98 runs)

**D53 against the existing co-simulation runs (A92 and A97, j30 and
j100):**
1. **The linear covariance alone underestimates the 30 ps spread.**
   - It reproduces the valley-time spread within a factor of 2.
   - It underestimates the high-side early fraction (20-27%) by at least
     half.
   - The early rule (candidate 3) is the missing part.
2. **The Monte Carlo with the exact controller reproduces the 30 ps
   co-simulation:**
   - low-side turn-off current spread within ±30%;
   - high-side early fractions within ±10 percentage points.
3. **At 100 ps, the Monte Carlo reproduces the trend:** spread ×2.5-3 the
   30 ps value, and early fractions of 35-50%. The linear circuit is at
   its limit there, so this is a weaker check.
4. **Of the edge inputs, the on-time edges (high-side turn-off and
   turn-on) contribute most to the valley spread.** The phase current
   changes fastest during the on-time (about 11 V/1.47 nH ≈ 7.5 A/ns).

**A98:**
5. **σ sweep:** the turn-off current spread is close to linear in σ up to
   about 20 ps, and grows less than linearly from 50 ps. The early rule
   saturates the correctors.
6. **h30 against l30:** the high-side edges alone give at least 70% of the
   all-edge variance (spread²); the low-side edges alone at most 40%.
7. **No run cross-conducts.** Every peak current is ≤ 200 A.

## 5. Amendment (written after D53, before any A98 run; 2026-10-01)

### 5.1 What D53 found (details in D53)

**Against the existing runs:**
- At 30 and 100 ps, for all three slot rules, D53's Monte Carlo is within
  10-20% of the co-simulation in:
  - the turn-off current spread;
  - the high-side early fraction;
  - the high-side error spread;
  - the period spread;
  - the windowed dither.
- At 0 ps it is within 10%.

**Prediction 1 was wrong.** The linear covariance without the early rule
already gives 0.50-0.57 A of spread at 30 ps, and a high-side error
spread (0.17 ns) that puts about 25% of turn-ons before the valley.

**The amplifier is the circuit, not the early rule.**
- Phase 1's turn-off is decided by its current comparator. An on-time
  error of δ moves its peak current on the steep on-slope and is converted
  back to time on the shallow off-slope.
- So the period moves by 10.5·δ (∂T/∂ton_1 = +10.5 ns/ns).
- Phases 2-4's slots are referred to phase 1's turn-on, so they inherit
  that period error. Their turn-off current moves by −0.68 A/ns
  (∂i_off,k/∂slot_k), and their valley by −0.18 ns/ns.
- Variance shares at 30 ps (average rule, phase 4):
  - phase 1's on-time edges (η, hoff_1): 60%;
  - phases 2-4's on-time edges: 37%;
  - low-side edges: 3%.

**Controller variants (Monte Carlo, average slots):**
- **No corrector setting reduces the spread by more than 7%.**
- **Early fraction at 30 / 100 ps:**

  | variant | early at 30 ps | early at 100 ps |
  |---|---:|---:|
  | adopted | 25% | 47% |
  | gain 1/4 (`err_shift` 2) | 12-14% | 32-35% |
  | gain 1/4 with a 5 LSB target | 8-10% | 30-32% |
  | smaller early step (2 LSB) | 32-36% | 63-66% |

  The large early step pushes the edge back past the valley, so a smaller
  one makes things worse.

### 5.2 The mitigation runs

**Chosen: gain 1/4** (`err_shift` 2). This is the smallest change that
D53 predicts halves the turn-ons before the valley.

Runs **g4_j30** and **g4_j100**: the adopted preset with `err_shift` 2, at
30 and 100 ps. These are two runs instead of the one written in Section
3.3. The change is made here, before any A98 run.

A lower gain also slows the correctors' convergence. These runs do not
test start-up or handover. **Adoption would need the full A92 matrix in a
later experiment.**

### 5.3 D53's predictions for every A98 run

- Average slots, Monte Carlo of 40 000 cycles, seed 7.
- The band is the 5-95% range of the 200-cycle-window values, since the
  co-simulation's records hold its last 200 cycles.
- Phases 2-4 / 2-4.
- File: `d53_predictions.json`.

| run | turn-off current spread, median [5%, 95%] (A) | high-side early fraction, median [5%, 95%] | windowed dither (A) |
|---|---|---|---:|
| s10 | 0.29 / 0.29 / 0.30 [0.25-0.34] | 9 / 10 / 11% [6-14%] | 0.92 |
| s20 | 0.44 / 0.45 / 0.48 [0.38-0.53] | 18 / 19 / 21% [15-24%] | 1.47 |
| s50 | 0.91 / 0.95 / 1.00 [0.80-1.10] | 34 / 34 / 36% [30-39%] | 3.13 |
| h30 (high-side edges only) | 0.57 / 0.59 / 0.61 [0.51-0.68] | 24 / 25 / 26% [21-29%] | 1.95 |
| l30 (low-side edges only) | 0.25 / 0.27 / 0.28 [0.23-0.30] | 8 / 10 / 11% [5-14%] | 0.75 |
| g4_j30 | 0.56 / 0.58 / 0.63 [0.50-0.68] | 13 / 13 / 14% [10-17%] | 1.92 |
| g4_j100 | 1.67 / 1.76 / 1.87 [1.50-2.04] | 33 / 34 / 35% [29-38%] | 5.86 |

**Agreement criterion, per run:**
- each phase's spread is within ±20% of the median;
- each phase's early fraction is within ±8 percentage points of the
  median.
- This allows for the model error seen at 30 and 100 ps.

**Implications for Section 4's predictions:**
- Prediction 6 becomes: high-side edges alone give 89% of the all-edge
  jitter variance, low-side edges 14%.
- Prediction 5 becomes: the spread per ps of σ falls slowly from 10 ps on.
  The quantisation adds a floor at small σ.

## 6. Decides / does not decide

**Decides:**
- where the jitter amplification comes from: circuit, corrector gain or
  early rule, in both models;
- whether one controller change predicted by D53 reduces it.

**Does not decide:**
- the jitter's real statistics. Gaussian, independent edges are an
  idealisation: real drivers have correlated, supply-dependent delays;
- the loss of turn-ons before the valley;
- other loads.
