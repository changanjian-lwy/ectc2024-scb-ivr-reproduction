# D74 - the module stack as a 3D conduction model: the inductor layer and the via copper in glass 1

2026-10-07. D73 closed the electrothermal loop with one lumped node per module and named the inductor array (inside
glass 2, away from the dies' heat spreader) as the binding path, from a one-line estimate. This note replaces the
node with a steady 3D conduction model of the stack in Fig. 5c-d, verified against closed forms, with a convective
cooling face (heat transfer coefficient h) in place of a coolant model (D77 adds one). No co-simulation.
**Revised the same day** with D75's lateral copper (20 mm deep module) and D76's core loss in the inductor body (κ 1
baseline, κ 4 bound); the first version (no core loss, 10 mm copper) is commit 361115a and the row "no core loss" below.
Code: `src/scb_ivr/p24_thermal.py`; `scripts/p24_thermal_verify.py` → `diagnostics/D74_verification.json`;
`scripts/p24_thermal_stack.py` → `diagnostics/D74_thermal_stack.json`; `tests/test_p24_thermal.py`.

## 0. Answer

- **The inductor layer is the hottest part of the module in every case run (656 solves), and glass 1 is the barrier.**
  At h = 2·10⁴ W/(m²K) on the spreader, 25 °C coolant, core loss κ 1 and no via copper in glass 1, the inductor reaches
  96.6 °C while the hottest GaN junction is at 42.9 °C. Of the 72 K rise, glass 1 (300 µm, k 1.1) takes 35 K, the
  inductor's own body (copper + core loss in a spiral-in-paste core) 17 K, the cooling face 14 K; dies, solder and
  spreader 2.4 K.
- **A few per cent of copper in glass 1 under the phase columns removes the glass step.** 2 % fill brings it to 5 K
  (T_max 60.8 °C at a 25 °C coolant, 82.9 °C at 45 °C); 19.6 % (30 µm vias at 60 µm pitch, VPD Table III) to 0.6 K.
  The minimum for 85 °C at h 2·10⁴: **κ 1: 0.1 % / 1.4 % at a 25 / 45 °C coolant** (up to ~3,900 vias of 30 µm or ~350
  of 100 µm per 250 W module); **κ 4: 1.0-1.5 % at 25 °C**, and at 45 °C nothing works below h 5·10⁴ (then 3.2-3.8 %, ~9,000-
  10,700 vias of 30 µm; 2.1-2.3 % at 10⁵). Design point: **~2 % ≈ 5,700 vias of 30 µm (510 of 100 µm), 4 mm² of copper
  per module** covers κ 1 up to a 45 °C coolant at h 2·10⁴; κ 4 needs ~4 % and h ≥ 5·10⁴ (D77's microchannels give 9·10⁴).
- **Two conditions decide whether the vias work at all.** They must land on copper on both glass faces (bare glass: a
  resolved via field runs 1.6-2.8 × hotter than the effective medium, V6), and every ABF dielectric on the path needs
  ≥ ~1-2 % copper (1 % leaves 85.4 °C at the 45 °C baseline): with no microvias the four 30 µm ABF layers block more than the glass (135 °C at 19.6 %).
- **With the vias in, the inductor stays the hottest point by ~12 K over the junctions at κ 1** (core k_z 2 W/(m K);
  23 K at κ 4; 3-6 K with core k_z 5-20): the core material's loss and conduction are then the levers, with 1/h. The GaN
  junctions stay at 39-72 °C at h 2·10⁴: the GaN does not set the cooling.
- **The switch-node vias D65 assumed do not cover it:** 0.5-5 mm² of via-field footprint at fill π/16 is 0.1-1 mm²
  of copper, 0.05-0.5 % of the 200 mm² of columns. Dedicated thermal vias (or much larger switch-node fields) are needed.
- **Footprint:** 20 EPC2067 (185 mm²) do not fit P24's 10 × 10 mm site; a module takes two (10 × 20 mm, D75). D73's
  1 cm² density is the heat × 2 case.

## 1. Model

Half the central strip (2.5 mm) plus the module's four 2.5 mm phase columns (L1 inner) in x, half the module (10 mm)
in y with a mirror plane; sides adiabatic (identical neighbours, package edge). Stack (bottom to top), every value
not printed by P24 is a scenario:

| layer | thickness | conductivity W/(m K) | basis |
|---|---|---|---|
| Cu heat spreader, **cooled face below** | 200 µm | 390 | P24: dies on a spreader (0.5 mm with die); assumed |
| die attach (under dies) | 25 µm | 50 | assumed |
| EPC2067 dies, heat in the top 20 µm | 518 µm | Si 120 (mould 0.8 between) | datasheet thickness; R_θJC check V7 |
| solder bars + resist | 140 µm | under dies 55 % solder: k_z 32 | datasheet bars (120 µm) |
| lower build-up | ABF 30 / Cu GND 86 or 429 / ABF 30 / Cu 25 µm | ABF 0.4, Cu layers 70 % cover | D65 copper cases |
| glass 1 | 300 µm | 1.1 + via fill f (columns), 10 % (strip) | VPD Table III via height |
| middle build-up | Cu 25 / ABF 30 / Cu Vo 86 or 429 / ABF 30 / Cu 25 µm | as above | |
| glass 2: inductor body over the columns | 300 µm | k_xy 20, k_z 2 (MPC spiral) | P24 Table 2 [10]: spiral in a paste core |
| upper build-up, **processor face adiabatic** | Cu 25 / ABF 30 / Cu 25 / ABF 30 µm | | |

Glass-core convention: a metal layer on each glass face. Every ABF dielectric has 2 % microvias; over the glass vias
the ABF fill follows the glass fill (stacked thermal columns). Vias homogenised: k_z = f k_Cu + (1 − f) k_m, k_xy by
the cylinder (Rayleigh) formula. Dies: five per column (LS HS LS HS LS), drawn 2.5 × 3.705 mm (the die's area).

Heat (whole module; D73's split, 2.5 MHz, N = 29): each die from D73's die map (LS 0.98, HS 0.30 W at 25 °C), its
conduction part × (1 + 0.586 %/K (T_die − 25)) at its own mean junction temperature; inductor copper 18.6 W in glass 2,
per column × (1 + 0.393 %/K (T − 25)), plus the core loss (D76: 7.5 W at κ 1, 29.9 W at κ 4, held constant); lateral
copper 6.2 / 1.25 W at 86 / 429 µm (D75, 20 mm deep module) split between the GND and Vo copper, column weights
16 : 9 : 4 : 1 from L1 (D65), copper coefficient; gate drivers 3.4 W with the dies; Cs 2.7 W in glass 1; loop 6.6 / 1.7 W
in the GND copper. Fixed point: per-die / per-column Picard iteration to 10⁻³ K (≤ 16 iterations).

Solver: cell-centred finite volumes, harmonic face conductance, conjugate gradients with each z-column's tridiagonal
part as preconditioner (direct SuperLU agrees to round-off); 69k cells at 0.25 mm laterally, 32 layers of cells.

## 2. Verification (`D74_verification.json`)

| # | check | result |
|---|---|---|
| V1 | slab with uniform generation, convective face (exact quadratic) | error ÷ 4 per halving (order 2.00) |
| V2 | 1D stack of the module's layers, conductivity contrast 975, random non-uniform cells | exact to 4·10⁻¹⁴ |
| V3 | rectangular flux channel, 2 × 2 mm isoflux source, h 10⁴ (Muzychka et al. 2003 series) | +6.9 / 2.2 / 0.68 / 0.20 %, order 1.7; Richardson 0.000 % |
| V4 | compound channel: 200 µm Cu on 300 µm glass, die-size source (Yovanovich et al. 1999) | +0.94 / 0.26 / 0.07 % |
| V5 | orthotropic via-filled glass (5 %) against the orthotropic series | +8.0 / 2.9 / 0.89 %; treating it as isotropic k_z would give 22 K instead of 49 K |
| V6 | resolved copper pillars against the homogenised layer | bare glass: +57 to +176 %; 25 µm Cu on both faces: +3.1 / 1.4 / 0.0 % (pitch 240 / 120 / 60 µm) |
| V7 | EPC2067 junction-to-case, 518 µm Si | 0.38-0.47 K/W at k 148-120; datasheet 0.4 |
| V8 | module: energy balance; direct = CG; 0.25 → 0.0625 mm laterally; z cells × 4 | ≤ 3·10⁻¹² (sweep ≤ 4·10⁻¹¹); identical; ≤ 0.21 K; ≤ 0.07 K |

The series are written as a layer-by-layer impedance recursion, exact for any number of orthotropic layers over a
convective base. V6 is the condition behind every via number below: the effective medium holds when the vias end on
copper; the module has copper on both glass faces.

## 3. Results (`D74_thermal_stack.json`)

### 3.1 Where the temperature drops (K; column means, the last step to the inductor's hottest point; 2.5 MHz N29, 86 µm / 150 pH, κ 1, h 2·10⁴)

| coolant, fill | cooling face | spreader + die + bumps | lower build-up | glass 1 | middle build-up | inductor body | T_max / junction |
|---|---|---|---|---|---|---|---|
| 25 °C, 0 | 14.3 | 2.4 | 2.0 | **34.7** | 1.0 | 17.3 | 96.6 / 42.9 °C |
| 25 °C, 2 % | 14.0 | 2.3 | 2.0 | 5.0 | 1.1 | 11.5 | 60.8 / 42.0 °C |
| 25 °C, 19.6 % | 13.9 | 2.2 | 0.7 | 0.6 | 0.2 | 11.2 | 53.9 / 41.8 °C |
| 45 °C, 0 | 15.2 | 2.5 | 2.1 | **36.6** | 1.0 | 18.2 | 120.6 / 64.0 °C |
| 45 °C, 2 % | 14.9 | 2.4 | 2.1 | 5.3 | 1.1 | 12.1 | 82.9 / 63.0 °C |

With no via copper 28 % of the heat crossing glass 1 goes sideways in the Vo copper to the strip's vias; 10 % at 2 %.

### 3.2 Minimum glass-1 fill for T_max ≤ 85 °C (in brackets: T_max at fill 0 / 19.6 %, °C; h in W/(m²K))

**250 W on 2 cm², core κ 1, package 86 µm / 150 pH:**

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | none (152 / 103) | 0.62 % (114 / 69) | 0.12 % (97 / 54) | 0 (87 / 45) | 0 (83 / 42) |
| 45 °C | none (179 / 127) | none (139 / 92) | 1.38 % (121 / 76) | 0.44 % (110 / 66) | 0.32 % (107 / 63) |

**250 W on 2 cm², core κ 1, package 429 µm / 50 pH:**

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | none (124 / 90) | 0.20 % (95 / 64) | 0 (82 / 51) | 0 (74 / 44) | 0 (72 / 41) |
| 45 °C | none (150 / 114) | none (119 / 86) | 0.73 % (105 / 73) | 0.25 % (97 / 65) | 0.17 % (94 / 62) |

**250 W on 2 cm², core κ 4, package 86 µm / 150 pH:**

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | none (222 / 138) | none (169 / 92) | 1.53 % (145 / 70) | 0.58 % (131 / 58) | 0.45 % (127 / 53) |
| 45 °C | none (249 / 162) | none (194 / 114) | none (169 / 92) | 3.78 % (155 / 79) | 2.30 % (150 / 74) |

**250 W on 2 cm², core κ 4, package 429 µm / 50 pH:**

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | none (185 / 124) | none (142 / 86) | 1.02 % (123 / 68) | 0.42 % (112 / 57) | 0.32 % (108 / 53) |
| 45 °C | none (211 / 149) | none (166 / 108) | none (146 / 89) | 3.17 % (135 / 78) | 2.09 % (131 / 74) |

**D73's density (heat × 2), core κ 1, package 86 µm / 150 pH:**

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | none (378 / 218) | none (244 / 124) | none (194 / 87) | 1.47 % (168 / 66) | 0.92 % (159 / 60) |
| 45 °C | none (418 / 249) | none (277 / 150) | none (224 / 110) | none (196 / 89) | 7.11 % (187 / 82) |

**D73's density (heat × 2), core κ 1, package 429 µm / 50 pH:**

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | none (282 / 182) | none (191 / 110) | 5.39 % (155 / 81) | 1.02 % (135 / 64) | 0.69 % (129 / 58) |
| 45 °C | none (318 / 212) | none (220 / 135) | none (182 / 104) | none (161 / 86) | 5.31 % (155 / 80) |

Fill 1 % = 2,830 vias of 30 µm (255 of 100 µm) per module (200 mm² of columns); 19.6 % is the VPD framework's minimum pitch. "none": even 19.6 % stays above 85 °C, the cooling face decides. Bisection to 2 % of f.

### 3.3 One parameter at a time (250 W on 2 cm², 86 µm, κ 1, h 2·10⁴, 45 °C coolant)

| case | f* (85 °C) | T_max at fill 0 / 2 % / 19.6 % (°C) | inductor − junction at 19.6 % |
|---|---|---|---|
| baseline (glass 1.1, 300 µm; core k_z 2; ABF 2 % + stacked; κ 1) | 1.38 % | 120.6 / 82.9 / 75.6 | +12.7 K |
| glass k 0.9 | 1.44 % | 129.3 / 83.0 / 75.6 | +12.7 K |
| glass k 1.4 (fused silica) | 1.30 % | 111.9 / 82.7 / 75.6 | +12.7 K |
| glass 1 100 µm | 0.27 % | 92.2 / 79.1 / 75.2 | +12.3 K |
| glass 1 500 µm | 2.38 % | 146.3 / 86.6 / 76.0 | +13.1 K |
| inductor core k_z 1 | none | 132.1 / 94.1 / 86.6 | +23.7 K |
| inductor core k_z 5 | 0.59 % | 113.6 / 76.2 / 69.0 | +6.2 K |
| inductor core k_z 20 (Cu posts) | 0.42 % | 110.1 / 72.9 / 65.9 | +3.1 K |
| inductor k_xy 5 | 1.39 % | 121.3 / 82.9 / 75.6 | +12.8 K |
| ABF 2 %, not stacked over the glass vias | 1.39 % | 120.9 / 82.9 / 77.9 | +15.0 K |
| ABF without microvias | none | 187.1 / 141.2 / 135.3 | +71.0 K |
| strip without vias | 1.47 % | 126.5 / 83.2 / 75.6 | +12.7 K |
| strip 19.6 % vias | 1.38 % | 120.1 / 82.8 / 75.6 | +12.7 K |
| underfill / mould k 0.3 | 1.39 % | 121.0 / 82.9 / 75.6 | +12.7 K |
| solder bars 30 % of the die | 1.59 % | 121.7 / 83.7 / 76.4 | +13.5 K |
| copper layers 40 % cover | 1.52 % | 124.8 / 83.4 / 76.0 | +12.9 K |
| processor face cooled, h 10⁴ at 45 °C | 0.00 % | 66.0 / 61.3 / 59.4 | +2.1 K |
| spreader 1 mm | 1.31 % | 120.6 / 82.6 / 75.2 | +12.8 K |
| array N = 40 (D72) | 0.70 % | 110.4 / 78.7 / 72.5 | +10.8 K |
| no core loss | 0.43 % | 104.4 / 75.7 / 70.1 | +9.4 K |
| core κ 2 | 4.25 % | 136.8 / 90.1 / 81.1 | +16.1 K |
| core κ 4 | none | 169.1 / 104.5 / 92.0 | +22.7 K |

### 3.4 ABF microvias (every dielectric, not stacked over the glass vias; κ 1, h 2·10⁴, 45 °C)

| microvia fill per ABF dielectric | T_max at glass fill 2 % / 19.6 % | lower + middle build-up steps (2 %) |
|---|---|---|
| 0.00 % | 141.2 / 135.3 °C | 33.0 + 23.9 K |
| 0.25 % | 96.7 / 91.5 °C | 9.6 + 6.5 K |
| 0.50 % | 89.7 / 84.6 °C | 5.8 + 3.8 K |
| 1.00 % | 85.4 / 80.3 °C | 3.4 + 2.1 K |
| 2.00 % | 82.9 / 77.9 °C | 2.1 + 1.1 K |
| 5.00 % | 81.3 / 76.4 °C | 1.2 + 0.5 K |

## 4. What follows

- **Package requirements (thermal), for a 250 W module on 2 cm²:** copper via fill in glass 1 under the inductor
  columns of ~2 % at κ 1 (~4 % at κ 4), stacked through every build-up dielectric (≥ ~1-2 % each), landing on copper on both
  glass faces; cooling face h ≥ 2·10⁴ W/(m²K) at κ 1 for a 45 °C coolant, ≥ 5·10⁴ at κ 4. Then the inductor core's own
  loss (D76) and conduction (k_z ≥ 5 W/(m K) halves the excess over the junctions) are the levers.
- **The thermal design of this IVR is the inductor layer's,** unlike the team's DVPD where the switches dominate.
- **D77** replaces h with a microchannel coolant model (flow, pressure, coolant heating); **D78** opens the processor face.

## 5. Limits

- Every stack dimension and material value is assumed (P24 prints none); Section 3.3 gives the leverage of each.
- The processor face is adiabatic here (D78 opens it). The core loss is held constant with temperature and κ is a bound
  (D76). Not included: contact resistances (TIM, solder voids), k(T) of silicon and glass, transients.

## 6. Questions for Mihai

1. Which face of the IVR is cooled (the spreader under the GaN, as Fig. 5 suggests?), with what h or coolant and at
   what temperature?
2. Glass thicknesses and TGV diameter / pitch; are thermal vias under the inductor columns part of the plan?
3. The MPC spiral unit's construction (core conductivity, copper posts) and its large-signal core loss (D76).
4. How do P24's 12 EPC2067 (111 mm²) sit in a 10 × 10 mm module (D75)?
