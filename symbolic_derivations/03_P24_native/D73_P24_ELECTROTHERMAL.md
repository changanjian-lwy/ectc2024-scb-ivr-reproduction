# D73 - an electrothermal closure of the module, in the team's framework form

2026-10-07. D72 left heat as a requirement (39-58 W per 10 × 10 mm module, no thermal path in P24) and the hot
efficiency at an assumed 125 °C. This note takes the method of the team's design framework: losses → temperature →
temperature-dependent losses, iterated to a fixed point (Krishnakumar et al. 2026, arXiv, with P24's first author
among the co-authors: "A Comprehensive Design Framework for Vertical Power Delivery in HPC", Fig. 4; Choi et al., TCPMT 2025, "Self-consistent electrothermal modeling of DVPD with
substrate-embedded microfluidic cooling", and its companion "Substrate-embedded microfluidic cooling of DVPD
for HPC processors"). It replaces their thermal-fluidic solver with one lumped node per module.
No new runs: `scripts/p24_electrothermal.py` → `diagnostics/D73_electrothermal.json`.

## 1. What the team's papers give

- **Same power class as P24's IVR.** 1 kW at 1 V from 48 V in one stage, GaN switches, 2 A/mm² (P24's four 1 cm²
  modules: 2.5 A/mm²). They report 185-231 W of loss end to end (delivery included); P24's IVR has 157-232 W at
  25 °C (4 × D72's 39-58 W, package included).
- **The design threshold is 85 °C**, not 125 °C (both Choi et al. papers; the IVR sits in the processor stack).
  Without embedded cooling the stacks exceed 110 °C (framework) to 145 °C (Choi et al., cooling paper); substrate-
  embedded microchannels next to the GaN layer hold ~85 °C at 1.4-1.6 g/s, with pumping power < 0.1 % of the load.
- **The coupling matters:** at ~85 °C the self-consistent loss is 13.5 % (framework: 185 → 210 W) to 15.8 % (Choi et
  al.: 200 → 231 W) above the uncoupled estimate.

## 2. The lumped loop

Per module, at 25 °C: D62's budget on the design records with D72's array R/L (Section 3's rows reproduce D72 to
0.01 point). Temperature: switch conduction × (1 + 0.586 %/K · ΔT) (EPC2067 R_on, chord of A90's ×1.586 at 125 °C; the
real curve is convex, so the chord overstates R_on below 125 °C), inductor and lateral copper × (1 + 0.393 %/K · ΔT);
Coss, turn-off overlap, gate charge, Cs ESR and the loop loss held constant. One node: T = T_in + R_th · P(T), R_th from
the hottest point to the coolant per 1 cm² module (K/W, numerically K·cm²/W). P is linear in T, so the fixed point is
closed-form and exists while R_th · dP/dT < 1.

**Coupling bounds at 85 °C:** P85 / P25 = 1.08-1.13 with only the switches hot, 1.20-1.25 with all copper at 85 °C too (all
three designs, with and without the package terms).
The team's 1.135-1.158 (non-uniform field, 85 °C at the hottest point) falls between them.

## 3. Results (per module, 250 W out; package rows add D70 Section 2.5's copper and loop)

| design (D72) | 25 °C | 85 °C (switches only hot) | 85 °C (all) | 125 °C (all) |
|---|---|---|---|---|
| 5 MHz, 31 / 40 units | 86.38 / 87.10 % | 84.92 / 85.62 % | 83.90 / 84.74 % | 82.32 / 83.23 % |
| **2.5 MHz, 29 / 40 units** | **86.56 / 87.65 %** | **85.19 / 86.25 %** | **83.94 / 85.22 %** | 82.28 / 83.66 % |
| 1 MHz, 29 / 40 units | 85.71 / 87.13 % | 84.40 / 85.78 % | 82.78 / 84.42 % | 80.94 / 82.71 % |
| 2.5 MHz + package (429 µm, 50 pH) | 85.3 / 86.4 % | | 82.6 / 83.8 % | 80.9 / 82.2 % |
| 2.5 MHz + package (86 µm, 150 pH) | 81.2 / 82.2 % | | 78.2 / 79.3 % | 76.3 / 77.4 % |

**Required R_th at 2.5 MHz** (largest value that keeps the module at T_max; T_in = coolant or sink temperature):

| losses counted | T ≤ 85 °C, T_in 25 / 45 °C | T ≤ 125 °C, T_in 25 / 45 °C | runaway above |
|---|---|---|---|
| converter | 1.25-1.38 / 0.84-0.92 K/W | 1.86-2.05 / 1.49-1.64 K/W | 6.7 K/W |
| + package (429 µm, 50 pH) | 1.14-1.25 / 0.76-0.83 | 1.69-1.85 / 1.36-1.48 | 6.3 |
| + package (86 µm, 150 pH) | 0.86-0.92 / 0.57-0.61 | 1.28-1.37 / 1.03-1.10 | 5.0 |
| hottest module (+5 % current, D66), with package | 0.79-1.05 / 0.53-0.70 | | |

**Where the heat is generated at 85 °C** (2.5 MHz; 29 / 40 units, the two package cases): GaN dies 18.7 W (27-39 %),
inductor array 18.5-22.9 W (28-44 %), lateral copper 3.1-15.4 W (6-24 %), loop 1.7-6.6 W, gate drivers 3.4 W, series
capacitors 2.7 W. Per die (phases 1-4): low side 1.31-1.34 W, high side 0.34-0.37 W; the hottest die is 15 W/cm² and
0.5 K above its case (EPC2067: 2.85 × 3.25 mm, R_θJC 0.4 K/W).

## 4. What follows

- **The hot design point is the team's 85 °C, and the converter is then ~84-86 %** (package-inclusive ~78-84 %), if
  every module's path to a 25 °C coolant is ≤ ~0.8-1.0 K·cm²/W (≤ ~0.5-0.7 at 45 °C). The 125 °C figures stay as a
  bound (EPC2067 is rated to 150 °C); they are not a design point.
- **The loop is stable.** The fixed point needs R_th < 5-6.7 K/W, ≥ ~5 × the requirement, so each iteration of the
  framework's loop shrinks the error ~4-10 ×. Between modules the coupling is stabilising: a hotter module's higher R_on
  lowers its own current slightly (D70 Section 2.2's droop, ~0.3 % at +60 K), so there is no current hogging; the
  hottest module is the one with the smallest inductance (D66), and the requirement is set by it.
- **2.5 MHz stays the choice.** Hot, its efficiency lead over 5 MHz is 0-0.5 points (a tie with the fewest units, as the
  switching terms do not grow with temperature and 5 MHz has less copper); 1 MHz falls further behind (copper-heavy).
  The valley margin and the frozen controller carry the choice, as in D72.
- **The binding layer is the inductor array, not the GaN.** In the team's DVPD the switches give > 50-70 % of the
  conversion loss and the microchannels sit next to the GaN layer. Here the array gives as much heat as the dies, and it
  is embedded in glass 2, with glass 1 between it and the dies' heat spreader (Fig. 5c-d). Glass conducts ~1 W/(m·K)
  (assumed; P24 gives no glass data): 0.1 mm costs ~0.9 K·cm²/W, so 18.5-22.9 W crossing ~0.3 mm of glass alone would
  use the whole 60 K budget. The array needs its own path (copper via fill or a cooler on its side); P24 gives neither
  the glass thicknesses nor the via counts nor which face of the IVR is cooled. *D74 checks this in 3D:* with no via
  copper glass 1 takes 30 of the 60 K at h 2·10⁴ W/(m²K) (inductor 85.5 °C, junction 42.9 °C); ~2 % copper fill under
  the columns takes it to 4-5 K.
- **Not covered:** the temperature field inside a module (one node), the core's loss and saturation at temperature,
  the processor's own heat next to the IVR, thermal transients.

## 5. For the team's thermal framework

The input Choi et al.'s solver takes, per component and position, is in `D73_electrothermal.json` (`die_map_2.5MHz`,
`designs.*.layers_85C`) with the temperature coefficients. A Mihai question follows: has P24's IVR been run through
that framework, and which face of the IVR is cooled, at what coolant temperature?
