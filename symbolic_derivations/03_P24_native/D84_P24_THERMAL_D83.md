# D84 - the thermal results rerun with D83's inductor losses (D73 / D74 / D77 / D78 / D80)

2026-10-16. D73 / D74 / D77 / D78 / D80 carry D83's erratum (inductor heat from D72's copper and D76's core: lower bounds, not
rerun). Their key cases are rerun here with D83's values, nothing else changed. Script: `scripts/p24_thermal_d83.py` →
`diagnostics/D84_thermal_d83.json`; no co-simulation, no existing file edited.

## 0. Results

**Conditions.** 2.5 MHz design, record A124 p125_n0 (1.98 MHz, D 0.075, 250 W per module, 4 phases); module on two
10 × 10 mm sites (D75: 2 cm², phase column 0.5 cm²); D74's stack; package 86 µm / 150 pH unless stated; D73's laws (switch
conduction +0.586 %/K, EPC2067 R_on chord 25-125 °C, A90; copper +0.393 %/K); core loss held at 25 °C; threshold 85 °C at
the hottest point (Choi et al., TCPMT 2025; Krishnakumar et al. 2026). **Changed (D83, 25 °C, per module):** copper 18.6 →
**27.3 W**; core at κ 1 7.5 → **34.5-44.1 W** ([10] Fig. 8 embedded r_acx band, edge lo-hi); D76's κ 4 (29.9 W) → [10]
Table V κ 3.074, **106.0-135.6 W**. Inductor heat 26.0 / 48.5 W → **61.8-71.4 / 133.3-162.9 W**. "Old" = published; the
Table V κ column compares with the old κ 4 (D76's upper bound).

**D73, lumped node** (method of D76's 85 °C table; switches and copper at 85 °C; R_th in K/W per module):

| quantity | old κ 1 / κ 4 | new κ 1 | new Table V κ |
|---|---|---|---|
| efficiency at 85 °C: converter / + 429 µm, 50 pH / + 86 µm, 150 pH | 81.9 / 81.0 / 78.2 %; 76.3 / 75.5 / 73.1 % | 70.9-72.9 / 70.2-72.2 / 68.1-69.9 % | 56.3-60.3 / 55.9-59.8 / 54.5-58.3 % |
| R_th max for 85 °C, converter, coolant 25 / 45 °C | 1.09 / 0.72; 0.77 / 0.51 | **0.58-0.64 / 0.39-0.43** | **0.31-0.36 / 0.21-0.24** |
| same, + 86 µm package | 0.86 / 0.57; 0.65 / 0.43 | 0.51-0.56 / 0.34-0.37 | 0.29-0.34 / 0.19-0.22 |
| module temperature at the old R_th (86 µm; coolant 25 / 45 °C) | 85 / 85 °C | **125-135 / 110-116 °C** | **151-173 / 127-141 °C** (κ 4's R_th) |

**D74, 3D stack** (h 2·10⁴ W/(m²K) on the spreader, °C; steps are column means, as D74 Section 3.1):

| case | old κ 1 (κ 4) | new κ 1 | new Table V κ |
|---|---|---|---|
| T_max / junction, coolant 25 °C, no vias (D74's headline) | 96.6 / 42.9 (145.1 / 50.7) | **184.5-206.8 / 56.9-60.4** | 350-419 / 83-94 |
| glass-1 step, inductor-body step (same case) | 34.7, 17.3 K | 80.5-92.1, 43.8-50.5 K | 167-203, 94-114 K |
| T_max, 2 % glass-1 fill, coolant 25 / 45 °C | 60.8 / 82.9 (82.5 / 104.5) | **97.5-107.1 / 120.3-129.9** | 168.6-198.1 / 191.4-220.9 |
| T_max, 19.6 % fill, coolant 25 / 45 °C | 53.9 / 75.6 (70.3 / 92.0) | 81.3-88.6 / 103.6-110.8 | 134.9-157.1 / 157.1-179.4 |
| junction, 2 % fill, coolant 25 / 45 °C | 42.0 / 63.0 (48.5 / 69.5) | 53.0-55.9 / 74.3-77.1 | 74.4-83.3 / **95.7-104.5** |

**Minimum glass-1 fill for 85 °C** (D74's bisection; "none" = 19.6 % is not enough, T_max at 19.6 % in brackets):

| coolant, h (W/(m²K)) | old κ 1 / κ 4 | new κ 1, edge lo / hi | new Table V κ |
|---|---|---|---|
| 25 °C, 2·10⁴ | 0.12 % / 1.53 % | **6.9 % / none (88.6)** | none (135-157) |
| 25 °C, 5·10⁴ | 0.01 % / 0.58 % | 1.5 % / 2.7 % | none (108-125) |
| 25 °C, 10⁵ | 0 / 0.45 % | 1.1 % / 1.8 % | none (99-115) |
| 45 °C, 2·10⁴ | 1.38 % / none | **none (104-111)** | none (157-179) |
| 45 °C, 5·10⁴ | 0.44 % / 3.78 % | none (88-93) | none (129-147) |
| 45 °C, 10⁵ | 0.32 % / 2.30 % | 8.3 % / none (87) | none (120-136) |

h 5·10³ / 10⁴: none in every new case (old κ 1, 25 °C: 0.62 % at 10⁴). 429 µm / 50 pH, κ 1, 25 °C: 4.4 % / none (86) at 2·10⁴,
1.3-2.4 % at 5·10⁴, 0.9-1.7 % at 10⁵; 45 °C: only lo at 10⁵ (7.8 %); Table V κ none (old κ 1: 0 / 0.17-0.73 % at 25 / 45 °C).

**D77, coolant** (cu_100_400 channels, face h ≈ 9·10⁴; flow per module for 85 °C; D77's sweep 0.4-4 g/s):

| case | old κ 1 / κ 4 | new κ 1 | new Table V κ |
|---|---|---|---|
| 2 % fill, inlet 25 / 45 °C | 0.44 / 1.12 g/s; 1.15 g/s / not within 4 | **3.39 g/s (lo), not within 4 (hi: 91.6 °C at 4 g/s) / not within 4 (106-114 °C)** | not within 4 (144-191 °C at 4 g/s) |
| 19.6 % fill, inlet 25 / 45 °C | ≤ 0.4 / 0.78 g/s; 0.73 / 2.28 g/s | 1.15-1.65 g/s / not within 4 (90-95 °C) | not within 4 (111-151 °C) |

**D78, processor side** (2 % fill; warmest processor side for 85 °C at R''_sub 12 / 3.3 / 1.2 K·cm²/W; adiabatic-top T_max in brackets):

| bottom h, coolant (all: to 95 °C; none: not at 45 °C) | old κ 1 | old κ 4 | new κ 1, lo; hi | new Table V κ |
|---|---|---|---|---|
| 2·10⁴, 25 °C | all / all / 94 (60.8) | 94 / 87 / 85 (82.5) | **none / 67 / 77; none / 53 / 71** (97.5-107.1) | none (169-198) |
| 2·10⁴, 45 °C | 93 / 87 / 85 (82.9) | none / 55 / 72 (104.5) | none / none / 61; none / none / 53 (120-130) | none (191-221) |
| 9·10⁴, 25 °C | all / all / all (48.9) | all / all / 94 (65.8) | all / all / 88; 86 / 85 / 84 (77.1-84.6) | none, except lo at R'' 1.2: 49 (133-156) |
| 9·10⁴, 45 °C | all / all / 92 (70.2) | 72 / 81 / 83 (87.1) | none / 61 / 75; none / 47 / 69 (99-107) | none (155-178) |

**D80, final spec** (A171 S50 gate-level edges, nominal devices, 50 pH damper; h 2·10⁴; fill interpolated over ≤ 10 % as D80):

| quantity | old κ 1 (κ 4) | new κ 1 | new Table V κ |
|---|---|---|---|
| T_max / junction, 25 °C, no vias | 95.3 / 42.0 | **183.1-205.4 / 56.0-59.6** | 348.6-417.2 / 82.5-93.4 |
| fill for 85 °C, coolant 25 / 45 °C | 0.14 / 1.22 % (κ 4, 25 °C: 1.48 %) | 5.95 % (lo), none ≤ 10 % (hi) / none | none / none |
| flow for 85 °C, 2 % fill, inlet 25 / 45 °C | 0.41 / 1.00 g/s (κ 4, 25 °C: 1.06) | 3.08 g/s (lo), not within 4 (hi) / not within 4 | not within 4 |

**Conclusions that flip.**
- D73 Section 4, "~84-86 % at 85 °C if the path to a 25 °C coolant is ≤ ~0.8-1.0": now 68-73 % (κ 1) / 54-60 % (Table V κ),
  with a path ≤ 0.51-0.64 / 0.29-0.36 K/W per module; at the old requirement the module sits at 125-173 °C.
- D74 Sections 0 / 4, "~2 % fill covers κ 1 up to a 45 °C coolant at h 2·10⁴": no fill holds κ 1 at 45 °C, at 25 °C only
  the lo edge (6.9 %); κ 1 needs h ≥ 5·10⁴ and 1.5-2.7 %; nothing (h ≤ 10⁵, fill ≤ 19.6 %) holds Table V κ, where the
  junctions alone reach 95-105 °C (h 2·10⁴, 2 %, 45 °C; old κ 4: 69.5): "the GaN does not set the cooling" flips. D83's copper without core gives
  104.7 / 86.0 °C (headline / 2 %, 45 °C; old κ 1: 96.6 / 82.9).
- D77, "0.44 / 1.12 g/s at κ 1; 1.6 g/s for the system is the edge": 3.4 g/s or not within 4 g/s (0.4 g/s: 88.5 → 145-159 °C;
  Table V κ 253-298 °C). No flow closes the cases D74 already fails at a uniform h 10⁵ (κ 1 hi at 45 °C, all Table V κ).
- D78, "at κ 1 the processor side does not bind": it binds (≤ 53-77 °C through R'' ≤ 3.3 at h 2·10⁴ / 25 °C; R'' 12 no
  longer suffices at h 2·10⁴); at Table V κ it rescues one case only (≤ 49 °C).
- D80, "the thermal conclusions stand for the final spec": they do not; its relative result stands (edges < 1 K, slow corner
  +0.6 K at every κ, against an inductor 127-324 K hotter than the junctions without vias). **Stays:** the inductor is the
  hottest point in every run; glass 1 is the largest step without vias (80-206 K); the lumped loop is stable (runaway
  4.8-5.4 K/W, old 5.7-6.7; ≥ 8 × the requirement). D83's copper without core: 81.0 % at 85 °C, R_th 1.02 / 0.68 K/W.

## 1. Method

- **D73**: `p24_electrothermal.p_at / dpdt / fixed_point` on D73's 2.5 MHz N29 split (other terms equal D73's, D83 asserts),
  copper replaced, core added to the constant part, D75's 20 mm lateral copper; reproduces D76's 85 °C table (N29) to 10⁻¹².
- **D74 / D77 / D78 / D80**: their job functions (`p24_thermal_stack.run / refine`, `p24_coolant.run`, `p24_processor_side.run`,
  `p24_thermal_gate.stack / coolant`) run unchanged and take all heat from `p24_thermal_stack.sources()`; each worker
  replaces it (monkeypatch) by `d83_sources()`: the original with the core at zero, then copper 27.3 W and core κ × 34.5 /
  44.1 W, split equally over the four phase columns as `coupled()` does (D83's per-phase DC 63.1-64.1 A: ±1 %). Copied:
  D78's 85 °C crossing (inline in its `main`). Checks: the original sources reproduce D74 (96.60), D77 (64.14), D78 (92.63),
  D80 gate_nom (95.31 °C) and D80's A171 edge powers to < 10⁻⁶ K; 1,154 solves plus bisections, ≤ 12 Picard iterations,
  energy balance ≤ 4·10⁻⁹.
- **Not rerun**: D74's ×2 density case, sensitivity (3.3), microvia table (3.4); D77's other coolers (2-13 % on its flows)
  and checks; D80's base / loop50 / gate_hot (base = the D74 / D77 inputs, rerun above).

## 2. Area and limits

- **Footprint.** All runs keep D74's 0.5 cm² column per phase and one 300 µm glass-2 body. One layer of IND048 needs
  1.24-4.15 cm² per phase (D83, drawn to Table VI cell), 2.5-8.3 × that (P24: 0.25-0.63 cm²). Inductor heat per footprint
  here: 31-36 W/cm² (κ 1), 67-81 W/cm² (Table V κ); old 13 / 24 W/cm². *Spread on one layer*, the flux falls 2.5-8.3 × and
  the glass and body steps roughly with it: the numbers above are conservative, but the module outgrows P24's and its
  cooled face must follow. *Stacked in P24's area* (P24: 3 layers; D83: 3-9), the flux per footprint is as modelled, but
  with uniform generation and one cooled face the body step is q'' t / (2 k_z): the 44-114 K body step grows roughly with
  the layer count, plus the dielectrics between layers, so the numbers are lower bounds. Neither case is computed.
- **Above ~150 °C the temperatures are not predictions** (core loss at 25 °C, linear copper law, constant conductivities,
  single-phase water whose mean outlet at 0.4 g/s reaches 112-120 °C at κ 1 / 45 °C and 138-184 °C at Table V κ): they
  measure the distance from 85 °C. κ and copper carry D83 Section 5's limits ([10] Table V on IND037-HBS1 at D 0.5, zero
  DC, ≤ 584 mA half p-p; here D 0.075, 1.56 A DC, 1.95 A half p-p per unit; copper R_DC, D73's law, × 1.24 at 85 °C).
- Waveforms are the ideal-inductor record's; with 36-137 W more inductor loss than D72 + D76 at κ 1, Vo and Ton would shift
  (D83). Stack values are scenarios (D74 Section 5); D74's levers (core k_z, glass-1 thickness, processor face) weigh more
  with a 44-114 K body step, not rerun. **For Mihai** (D74 Section 6, sharper): the cooled face and coolant, and the
  inductor's construction (layers, footprint, core conductivity).
