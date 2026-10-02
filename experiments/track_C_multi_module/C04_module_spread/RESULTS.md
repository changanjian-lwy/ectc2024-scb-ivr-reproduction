# C04 - module-to-module component spread (RESULTS)

Track C, the last experiment of the multi-module level.

**Boundary:** `BOUNDARY.md`, committed (fb09eb0) before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `c04_summary.json` (`c04_analyze.py`).

**Physical model:**
- Verilog RTL `scb_multi`: four modules of A105's I2 with `slot_lo`;
- four A88 plants (kernel2);
- 5%, 25 C.

**Reference:** C03.

## 0. Verdict

1. **The system holds under component spread.** In all four runs:
   - no overlap; peak ≤ 185 A (the start-up);
   - locked periods; gaps T/16 ± 0.05 ns; join ≤ 78 µV;
   - Vo 1.000 V ± 0.1 mV;
   - every valley ≤ −3.6 A and the low side at zero voltage.
2. **Cs ±20% hardly matters:**
   - currents within ±0.4%;
   - valleys within 0.35 A (registered ±0.3 A: a marginal miss);
   - start-up peak 176 A.
3. **R ±30% matters more than predicted.**
   - **Currents** −1.2% / +1.3% (registered ±0.5%: miss).
   - **Valleys** move ±1.7-2.2 A: −8.0 A in the high-R module, −3.65 A
     in the low-R module, with its high-side turn-on at 9.76 V.
   - **Cause:** the slaves run at the master's timing, so their valleys
     float (C01 Section 3). A module then behaves as a source with an
     output resistance of ~3.3 mΩ: ΔV = ΔR × I ≈ 10 mV gives
     ΔI ≈ 3.1 A.
   - My prediction counted only R's effect on the ripple.
4. **All spreads together** (module 1: L +5%, Cs −20%, R +30%; module 3
   the opposite):
   - currents −5.2% / +6.1%, within the registered −4.5 ± 1.5% and
     +4.7 ± 1.5%. The inductors dominate and R adds ~1%.
   - The +250 A step: −14.78 mV (C03 −14.74).

## 1. Results (last 200 master periods)

| run | currents (A), modules 0-3 | valleys range (A) | high-side turn-on (V) | peak (A) | late fires |
|---|---|---|---|---|---|
| cs20_n0 | 249.9 / 249.3 / 249.9 / 250.9 | −7.04 to −5.49 | 8.81-9.25 | 176 | 1 |
| r30_n0 | 249.9 / **246.9** / 250.0 / **253.2** | **−8.58 to −3.65** | 8.41-**9.76** | 175 | 0 |
| all_n0 | 249.5 / **236.5** / 249.5 / **264.6** | −7.36 to −5.07 | 8.80-9.32 | 185 | 3 |
| all_s_p62 | the same before the step | the same | the same | 185 | 3 |

## 2. Registered criteria (BOUNDARY Section 3)

| # | criterion | result |
|---|---|---|
| 1 | no overlap, locked, gaps, join, Vo (all runs) | pass |
| 2 | cs20: currents ±1%; valleys ±0.3 A; start-up ≤ 185 A | currents pass; valleys **0.35 A, miss**; 176 A pass |
| 3 | r30: currents ±0.5%; valleys ±0.3 A | **miss** (±1.3%, ±2.2 A). Mechanism in 0.3 |
| 4 | all: module 1 −4.5 ± 1.5%, module 3 +4.7 ± 1.5%; valleys ≤ −2.5 A; low side ≤ 0 | pass (−5.2%, +6.1%, −5.07 A) |
| 5 | all_s_p62: step ±10% of C03 | pass (−14.78 against −14.74 mV) |

## 3. Not done (BOUNDARY Section 2)

- **Coss spread.** It needs a scale on the datasheet curve, a plant
  change.
- **Per-module driver delay.** It needs a bridge key.
