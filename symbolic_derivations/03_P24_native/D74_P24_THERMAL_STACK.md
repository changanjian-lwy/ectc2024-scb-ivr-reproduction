# D74 - the module stack as a 3D conduction model: the inductor layer and the via copper in glass 1

2026-10-07. D73 closed the electrothermal loop with one lumped node per module and named the inductor array (inside
glass 2, away from the dies' heat spreader) as the binding path, from a one-line estimate. This note replaces the
node with a steady 3D conduction model of the stack in Fig. 5c-d, verified against closed forms, with a convective
cooling face (heat transfer coefficient h) in place of a coolant model. No co-simulation.
Code: `src/scb_ivr/p24_thermal.py`; `scripts/p24_thermal_verify.py` → `diagnostics/D74_verification.json`;
`scripts/p24_thermal_stack.py` → `diagnostics/D74_thermal_stack.json`; `tests/test_p24_thermal.py`.

## 0. Answer

- **The inductor layer is the hottest part of the module in every case with the processor face adiabatic (471 of 472
  solves), and glass 1 is the barrier.** At h = 2·10⁴ W/(m²K) on the spreader with no via copper in glass 1, the
  inductor reaches 85.5 °C while the hottest GaN junction is at 42.9 °C (25 °C coolant). Of the 60 K rise, glass 1 (300 µm, k 1.1) takes 30 K, the cooling face
  14 K and the inductor's own spiral-in-paste body 12 K; the dies, solder and spreader together take 2 K.
- **A few per cent of copper in glass 1 under the phase columns removes that step.** 2 % fill brings it from 30 to
  4-5 K (inductor 56 °C), 19.6 % (30 µm vias at 60 µm pitch, the VPD framework's Table III) to 0.5 K. The
  minimum for the 85 °C threshold is 0-0.7 % at h 2·10⁴ (25 / 45 °C coolant): up to ~1,900 vias of 30 µm, or ~170
  of 100 µm, per 250 W module. With h 5·10³-10⁴ it is 1.6-2.1 % (429 µm copper case), and at D73's density
  (250 W per cm²) 0.2-7.7 % with h ≥ 2·10⁴ (25 °C) / 5·10⁴ (45 °C). Suggested design point: **~2 % ≈ 5,700 vias
  of 30 µm (510 of 100 µm), 4 mm² of copper per module**; beyond it the gain is ≤ ~6 K.
- **Two conditions decide whether the vias work at all.** The vias must land on copper on both glass faces: on
  bare glass a resolved via field runs 1.6-2.8 × hotter than the effective medium (V6). And every ABF dielectric
  on the path needs ≥ ~0.5-1 % copper: with no microvias the four 30 µm ABF layers (3 K·cm²/W together) block more
  than the glass, and no glass fill reaches 85 °C (125 °C at 19.6 %).
- **With the vias in, the inductor stays the hottest point by ~9 K over the junctions** (core k_z 2 W/(m K); 17 K at
  k_z 1, 3 K at 20), and 1/h is the largest remaining term. Where no via fill meets 85 °C the cooling decides: h 5·10³ (all but
  one case), h 10⁴ at a 45 °C coolant with 86 µm copper, and at D73's density h < 2·10⁴ (25 °C) or < 5·10⁴ (45 °C).
  The GaN junctions stay at 37-66 °C at h 2·10⁴.
- **The switch-node vias D65 assumed do not cover it:** 0.5-5 mm² of via-field footprint at fill π/16 is 0.1-1 mm²
  of copper, 0.05-0.5 % of the 200 mm² of columns. Dedicated thermal vias (or much larger switch-node fields) are needed.
- **D73 cross-check.** The stack's hottest-point-to-coolant resistance is 1.9 K·cm²/W with no via copper, 1.0-1.1 at
  2 %, 0.8-0.9 at 19.6 % (h 2·10⁴, of which 1/h = 0.5). D73's requirement (≤ 0.8-1.0 per 1 cm² module at 25 °C) is
  reachable at that density only with ≥ 2 % fill and h ≥ 2·10⁴; on a 2 cm² module the same heat allows twice the value.

**Footprint (a finding on the way):** 20 EPC2067 per 250 W module (QH 2 / QL 3 per phase) need 185 mm², which does
not fit a 10 × 10 mm module (P24's own 12 dies per 125 W module need 111 mm²). Here a module takes two of P24's sites,
10 × 20 mm (die cover 93 %), as the 25 × 40 mm package would; D73's 1 cm² density is run as a heat × 2 case.

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
per column × (1 + 0.393 %/K (T − 25)); lateral copper 12.5 / 2.5 W split between the GND and Vo copper, column
weights 16 : 9 : 4 : 1 from L1 (D65), copper coefficient; gate drivers 3.4 W with the dies; Cs 2.7 W in glass 1; loop
6.6 / 1.7 W in the GND copper. D65's lateral loss was computed for a 10 mm deep module; it is kept although a 20 mm
module halves it (conservative). Fixed point: per-die / per-column Picard iteration to 10⁻³ K (≤ 18 iterations).

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
| V8 | module: energy balance; direct = CG; 0.25 → 0.0625 mm laterally; z cells × 4 | ≤ 3·10⁻¹² (sweep ≤ 5·10⁻¹¹); identical; ≤ 0.18 K; ≤ 0.05 K |

The series are written as a layer-by-layer impedance recursion, exact for any number of orthotropic layers over a
convective base. V6 is the condition behind every via number below: the effective medium holds when the vias end on
copper; the module has copper on both glass faces.

## 3. Results (`D74_thermal_stack.json`)

### 3.1 Where the temperature drops (K; column means, the last step to the inductor's hottest point; 2.5 MHz N29, 86 µm / 150 pH, h 2·10⁴)

| coolant, fill | cooling face | spreader + die + bumps | lower build-up | glass 1 | middle build-up | inductor body | T_max / junction |
|---|---|---|---|---|---|---|---|
| 25 °C, 0 | 14.1 | 2.3 | 1.9 | **29.8** | 0.8 | 11.7 | 85.5 / 42.9 °C |
| 25 °C, 2 % | 13.7 | 2.2 | 1.9 | 4.3 | 0.8 | 8.1 | 56.2 / 41.6 °C |
| 25 °C, 19.6 % | 13.6 | 2.2 | 0.7 | 0.5 | 0.1 | 8.0 | 50.2 / 41.5 °C |
| 45 °C, 0 | 15.0 | 2.5 | 2.0 | **32.0** | 0.8 | 12.6 | 109.9 / 64.2 °C |
| 45 °C, 2 % | 14.7 | 2.4 | 2.0 | 4.7 | 0.9 | 8.8 | 78.4 / 62.8 °C |

With no via copper 29 % of the heat crossing glass 1 goes sideways in the Vo copper to the strip's vias; 11 % at 2 %.

### 3.2 Minimum glass-1 fill for T_max ≤ 85 °C (in brackets: T_max at fill 0 / 19.6 %, °C)

**250 W on 2 cm², package 86 µm / 150 pH** (h in W/(m²K)):

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | none (141 / 98) | 0.29 % (103 / 65) | 0 (86 / 50) | 0 (76 / 42) | 0 (73 / 39) |
| 45 °C | none (170 / 123) | none (128 / 88) | 0.66 % (110 / 72) | 0.21 % (100 / 63) | 0.14 % (96 / 60) |

**250 W on 2 cm², package 429 µm / 50 pH** (h in W/(m²K)):

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | 2.09 % (106 / 80) | 0 (81 / 57) | 0 (69 / 46) | 0 (62 / 39) | 0 (60 / 37) |
| 45 °C | none (132 / 104) | 1.62 % (105 / 79) | 0.18 % (92 / 68) | 0 (85 / 61) | 0 (83 / 58) |

**D73's density (heat × 2), package 86 µm / 150 pH** (h in W/(m²K)):

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | none (372 / 214) | none (223 / 116) | 4.44 % (171 / 79) | 0.72 % (144 / 60) | 0.48 % (136 / 53) |
| 45 °C | none (416 / 248) | none (257 / 142) | none (202 / 103) | 7.73 % (173 / 82) | 2.84 % (164 / 75) |

**D73's density (heat × 2), package 429 µm / 50 pH** (h in W/(m²K)):

| coolant | h 5·10³ | h 10⁴ | h 2·10⁴ | h 5·10⁴ | h 10⁵ |
|---|---|---|---|---|---|
| 25 °C | none (239 / 159) | none (157 / 95) | 1.14 % (126 / 70) | 0.32 % (109 / 55) | 0.21 % (103 / 50) |
| 45 °C | none (274 / 189) | none (187 / 121) | none (153 / 93) | 2.84 % (135 / 77) | 1.56 % (129 / 72) |

Fill 0.66 % = 1,860 vias of 30 µm (167 of 100 µm) per module; 2 % = 5,660 (509); 19.6 % is the VPD framework's minimum pitch. "none": even 19.6 % stays above 85 °C, the cooling face decides. Bisection to 2 % of f.

### 3.3 One parameter at a time (250 W on 2 cm², 86 µm, h 2·10⁴, 45 °C coolant)

| case | f* (85 °C) | T_max at fill 0 / 2 % / 19.6 % (°C) | inductor − junction at 19.6 % |
|---|---|---|---|
| baseline (glass 1.1, 300 µm; core k_z 2; ABF 2 % + stacked) | 0.66 % | 109.9 / 78.4 / 72.1 | +9.3 K |
| glass k 0.9 | 0.71 % | 117.5 / 78.5 / 72.1 | +9.3 K |
| glass k 1.4 (fused silica) | 0.58 % | 102.4 / 78.3 / 72.0 | +9.3 K |
| glass 1 100 µm | 0.03 % | 86.0 / 75.2 / 71.7 | +9.0 K |
| glass 1 500 µm | 1.30 % | 132.4 / 81.6 / 72.4 | +9.7 K |
| inductor core k_z 1 | 2.42 % | 118.7 / 86.1 / 79.8 | +17.0 K |
| inductor core k_z 5 | 0.38 % | 104.6 / 74.0 / 67.7 | +5.0 K |
| inductor core k_z 20 (Cu posts) | 0.29 % | 101.8 / 71.9 / 65.5 | +2.8 K |
| inductor k_xy 5 | 0.67 % | 110.4 / 78.6 / 72.2 | +9.4 K |
| ABF 2 %, not stacked over the glass vias | 0.66 % | 110.3 / 78.5 / 74.2 | +11.4 K |
| ABF without microvias | none | 170.8 / 130.6 / 125.5 | +61.4 K |
| strip without vias | 0.83 % | 116.3 / 79.3 / 72.3 | +9.5 K |
| strip 19.6 % vias | 0.65 % | 109.5 / 78.3 / 72.0 | +9.3 K |
| underfill / mould k 0.3 | 0.67 % | 110.3 / 78.6 / 72.1 | +9.4 K |
| solder bars 30 % of the die | 0.74 % | 111.0 / 79.3 / 72.9 | +10.2 K |
| copper layers 40 % cover | 0.77 % | 113.0 / 79.3 / 72.6 | +9.7 K |
| processor face cooled, h 10⁴ at 45 °C | 0.00 % | 64.8 / 60.7 / 58.8 | +1.3 K |
| spreader 1 mm | 0.64 % | 110.0 / 78.1 / 71.6 | +9.6 K |
| array N = 40 (D72) | 0.31 % | 99.9 / 74.5 / 69.1 | +7.5 K |

### 3.4 ABF microvias (every dielectric, not stacked over the glass vias; h 2·10⁴, 45 °C)

| microvia fill per ABF dielectric | T_max at glass fill 2 % / 19.6 % | lower + middle build-up steps (2 %) |
|---|---|---|
| 0.00 % | 130.6 / 125.5 °C | 31.6 + 19.8 K |
| 0.25 % | 90.8 / 86.5 °C | 9.1 + 5.3 K |
| 0.50 % | 84.6 / 80.3 °C | 5.5 + 3.1 K |
| 1.00 % | 80.7 / 76.4 °C | 3.3 + 1.7 K |
| 2.00 % | 78.5 / 74.2 °C | 2.0 + 0.9 K |
| 5.00 % | 77.0 / 72.8 °C | 1.2 + 0.4 K |

## 4. What follows

- **Package requirements (thermal), for a 250 W module on 2 cm²:** copper via fill in glass 1 under the inductor
  columns of ~2 % (the 85 °C limit alone asks for 0-2 %, depending on h and coolant), stacked through every build-up
  dielectric (≥ 0.5-1 % each), landing on copper on both glass faces; cooling face h ≥ 2·10⁴ W/(m²K) for a 45 °C
  coolant (≥ 5·10⁴ at D73's density). Then the inductor core's own k_z is the next lever (≥ 5 W/(m K) halves the
  inductor's excess over the junctions).
- **The GaN does not set the cooling.** Junctions stay 31-46 K below the inductor without vias (h 2·10⁴) and ~9 K
  below with them; the thermal design of this IVR is the inductor layer's, unlike the team's DVPD where the switches dominate.
- **D73's hot efficiency stands** (83.9-86.3 % at 85 °C), now with a stack that reaches 85 °C under stated conditions.
- **Next step:** a coolant model in place of h (Choi et al.'s substrate microchannels next to the GaN layer, coolant
  heating along the channel), and the processor-side boundary.

## 5. Limits

- Every stack dimension and material value is assumed (P24 prints none); Section 3.3 gives the leverage of each.
- The processor face is adiabatic. The IVR sits on the back of the processor package (Fig. 6): a processor hotter
  than the inductor would add heat there; a cooler there (h 10⁴ at 45 °C) drops T_max to 65 °C without any via copper.
- Not included: contact resistances (TIM, solder voids), k(T) of silicon and glass, the MPC core loss (D72: open; it
  would add heat in glass 2), transients, coolant heating (h uniform).

## 6. Questions for Mihai

1. Which face of the IVR is cooled (the spreader under the GaN, as Fig. 5 suggests?), with what h or coolant and at
   what temperature? (D73's question 5, now with the h it needs.)
2. Glass thicknesses and TGV diameter / pitch; are thermal vias under the inductor columns part of the plan?
3. The MPC spiral unit's construction: core conductivity, copper posts or terminals through the core.
4. How do P24's 12 EPC2067 (111 mm²) sit in a 10 × 10 mm module?
