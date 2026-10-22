# D84 - the thermal results rerun with D83's inductor losses (D73 / D74 / D77 / D78 / D80)

**Note (2026-10-16, D85):** the die layer here carries D80's dies (V5 edges); the gate-level books (V6) put ~4.5 W more at the dies (conduction +2.5 W, low-side edges and reverse +2.1 W), small against the inductor's 52-154 W. Not rerun.

**Rerun 2026-10-23 (D85 Section 3 item 6):** the core term now leaves out the ripple at R_DC that the copper already
carries (9.38 W at 25 °C, counted twice before). Every number below is from that rerun; the inductor heat is 52.4-62.0 /
123.9-153.6 W instead of 61.8-71.4 / 133.3-162.9 W. The one verdict it flips: the 19.6 % fill at κ 1 with a 25 °C coolant
(h 2·10⁴) is now 74.3-81.5 °C, under 85 °C at both edges (was 81.3-88.6 °C). Every other verdict stays; the minimum fills
and flows fall (25 °C coolant, h 2·10⁴, κ 1: 2.6 / 7.1 % against 6.9 % / none).

2026-10-16. D73 / D74 / D77 / D78 / D80 carry D83's erratum (inductor heat from D72's copper and D76's core: lower bounds, not
rerun). Their key cases are rerun here with D83's values, nothing else changed. Script: `scripts/p24_thermal_d83.py` →
`diagnostics/D84_thermal_d83.json`; no co-simulation, no existing file edited.

## 0. Results

**Conditions.** 2.5 MHz design, record A124 p125_n0 (1.98 MHz, D 0.075, 250 W per module, 4 phases); module on two
10 × 10 mm sites (D75: 2 cm², phase column 0.5 cm²); D74's stack; package 86 µm / 150 pH unless stated; D73's laws (switch
conduction +0.586 %/K, EPC2067 R_on chord 25-125 °C, A90; copper +0.393 %/K); core loss held at 25 °C; threshold 85 °C at
the hottest point (Choi et al., TCPMT 2025; Krishnakumar et al. 2026). **Changed (D83, 25 °C, per module):** copper 18.6 →
**27.3 W**; core at κ 1 7.5 → 34.5-44.1 W ([10] Fig. 8 embedded r_acx band, edge lo-hi) less the 9.38 W the copper
carries: **25.1-34.7 W**; D76's κ 4 (29.9 W) → [10] Table V κ 3.074, **96.6-126.3 W**. Inductor heat 26.0 / 48.5 W →
**52.4-62.0 / 123.9-153.6 W**. "Old" = published; the Table V κ column compares with the old κ 4 (D76's upper bound).

**D73, lumped node** (method of D76's 85 °C table; switches and copper at 85 °C; R_th in K/W per module):

| quantity | old κ 1 / κ 4 | new κ 1 | new Table V κ |
|---|---|---|---|
| efficiency at 85 °C: converter / + 429 µm, 50 pH / + 86 µm, 150 pH | 81.9 / 81.0 / 78.2 %; 76.3 / 75.5 / 73.1 % | 72.8-74.9 / 72.1-74.2 / 69.9-71.8 % | 57.5-61.7 / 57.1-61.2 / 55.7-59.6 % |
| R_th max for 85 °C, converter, coolant 25 / 45 °C | 1.09 / 0.72; 0.77 / 0.51 | **0.64-0.72 / 0.43-0.48** | **0.32-0.39 / 0.22-0.26** |
| same, + 86 µm package | 0.86 / 0.57; 0.65 / 0.43 | 0.56-0.61 / 0.37-0.41 | 0.30-0.35 / 0.20-0.24 |
| module temperature at the old R_th (86 µm; coolant 25 / 45 °C) | 85 / 85 °C | **115-125 / 104-110 °C** | **144-166 / 122-136 °C** (κ 4's R_th) |

**D74, 3D stack** (h 2·10⁴ W/(m²K) on the spreader, °C; steps are column means, as D74 Section 3.1):

| case | old κ 1 (κ 4) | new κ 1 | new Table V κ |
|---|---|---|---|
| T_max / junction, coolant 25 °C, no vias (D74's headline) | 96.6 / 42.9 (145.1 / 50.7) | **162.8-185.1 / 53.4-57.0** | 328-397 / 80-91 |
| glass-1 step, inductor-body step (same case) | 34.7, 17.3 K | 69.1-80.8, 37.3-44.0 K | 156-191, 87-108 K |
| T_max, 2 % glass-1 fill, coolant 25 / 45 °C | 60.8 / 82.9 (82.5 / 104.5) | **88.2-97.7 / 110.9-120.5** | 159.3-188.8 / 182.1-211.6 |
| T_max, 19.6 % fill, coolant 25 / 45 °C | 53.9 / 75.6 (70.3 / 92.0) | **74.3-81.5** / 96.5-103.8 | 127.9-150.1 / 150.1-172.3 |
| junction, 2 % fill, coolant 25 / 45 °C | 42.0 / 63.0 (48.5 / 69.5) | 50.2-53.1 / 71.4-74.3 | 71.6-80.5 / **92.9-101.7** |

**Minimum glass-1 fill for 85 °C** (D74's bisection; "none" = 19.6 % is not enough, T_max at 19.6 % in brackets):

| coolant, h (W/(m²K)) | old κ 1 / κ 4 | new κ 1, edge lo / hi | new Table V κ |
|---|---|---|---|
| 25 °C, 2·10⁴ | 0.12 % / 1.53 % | **2.6 % / 7.1 %** | none (128-150) |
| 25 °C, 5·10⁴ | 0.01 % / 0.58 % | 0.8 % / 1.6 % | none (102-120) |
| 25 °C, 10⁵ | 0 / 0.45 % | 0.6 % / 1.1 % | none (94-110) |
| 45 °C, 2·10⁴ | 1.38 % / none | **none (97-104)** | none (150-172) |
| 45 °C, 5·10⁴ | 0.44 % / 3.78 % | 7.3 % / none (88) | none (124-141) |
| 45 °C, 10⁵ | 0.32 % / 2.30 % | 3.5 % / 8.4 % | none (115-131) |

h 5·10³ / 10⁴: none in every new case (old κ 1, 25 °C: 0.62 % at 10⁴). 429 µm / 50 pH, κ 1, 25 °C: 1.8 % / 4.5 % at 2·10⁴,
0.7-1.3 % at 5·10⁴, 0.5-0.9 % at 10⁵; 45 °C: none at 2·10⁴ (94-101), lo 5.9 % / hi none (87) at 5·10⁴, 3.2-8.1 % at 10⁵;
Table V κ none (old κ 1: 0 / 0.17-0.73 % at 25 / 45 °C).

**D77, coolant** (cu_100_400 channels, face h ≈ 9·10⁴; flow per module for 85 °C; D77's sweep 0.4-4 g/s):

| case | old κ 1 / κ 4 | new κ 1 | new Table V κ |
|---|---|---|---|
| 2 % fill, inlet 25 / 45 °C | 0.44 / 1.12 g/s; 1.15 g/s / not within 4 | **1.61 g/s (lo), 3.47 g/s (hi) / not within 4 (98-106 °C at 4 g/s)** | not within 4 (136-161 / 158-183 °C at 4 g/s) |
| 19.6 % fill, inlet 25 / 45 °C | ≤ 0.4 / 0.78 g/s; 0.73 / 2.28 g/s | 0.85-1.16 g/s / 3.50 g/s (lo), not within 4 (hi: 90 °C) | not within 4 (106-124 / 127-145 °C) |

**D78, processor side** (2 % fill; warmest processor side for 85 °C at R''_sub 12 / 3.3 / 1.2 K·cm²/W; adiabatic-top T_max in brackets):

| bottom h, coolant (all: to 95 °C; none: not at 45 °C) | old κ 1 | old κ 4 | new κ 1, lo; hi | new Table V κ |
|---|---|---|---|---|
| 2·10⁴, 25 °C | all / all / 94 (60.8) | 94 / 87 / 85 (82.5) | **69 / 79 / 82; none / 67 / 77** (88.2-97.7) | none (159-189) |
| 2·10⁴, 45 °C | 93 / 87 / 85 (82.9) | none / 55 / 72 (104.5) | none / 46 / 68; none / none / 61 (110.9-120.5) | none (182-212) |
| 9·10⁴, 25 °C | all / all / all (48.9) | all / all / 94 (65.8) | all / all / 92; all / all / 88 (69.8-77.3) | none, except lo at R'' 1.2: 55 (125-148) |
| 9·10⁴, 45 °C | all / all / 92 (70.2) | 72 / 81 / 83 (87.1) | 47 / 74 / 80; none / 61 / 74 (91.7-99.2) | none (147-170) |

**D80, final spec** (A171 S50 gate-level edges, nominal devices, 50 pH damper; h 2·10⁴; fill interpolated over ≤ 10 % as D80):

| quantity | old κ 1 (κ 4) | new κ 1 | new Table V κ |
|---|---|---|---|
| T_max / junction, 25 °C, no vias | 95.3 / 42.0 | **161.4-183.7 / 52.5-56.1** | 326.9-395.5 / 79.0-90.0 |
| fill for 85 °C, coolant 25 / 45 °C | 0.14 / 1.22 % (κ 4, 25 °C: 1.48 %) | 2.6 % (lo), 6.2 % (hi) / none | none / none |
| flow for 85 °C, 2 % fill, inlet 25 / 45 °C | 0.41 / 1.00 g/s (κ 4, 25 °C: 1.06) | 1.50 g/s (lo), 3.16 g/s (hi) / not within 4 | not within 4 |

**Conclusions that flip.**
- D73 Section 4, "~84-86 % at 85 °C if the path to a 25 °C coolant is ≤ ~0.8-1.0": now 70-75 % (κ 1) / 56-62 % (Table V κ),
  with a path ≤ 0.56-0.72 / 0.30-0.39 K/W per module; at the old requirement the module sits at 104-166 °C.
- D74 Sections 0 / 4, "~2 % fill covers κ 1 up to a 45 °C coolant at h 2·10⁴": no fill holds κ 1 at 45 °C there
  (19.6 %: 96.5-103.8 °C); at 25 °C κ 1 needs 2.6-7.1 %, at h ≥ 5·10⁴ 0.6-1.6 % (and 3.5-8.4 % at 10⁵ with 45 °C);
  nothing (h ≤ 10⁵, fill ≤ 19.6 %) holds Table V κ, where the junctions alone reach 93-102 °C (h 2·10⁴, 2 %, 45 °C;
  old κ 4: 69.5): "the GaN does not set the cooling" flips. D83's copper without core gives 104.7 / 86.0 °C (headline / 2 %,
  45 °C; old κ 1: 96.6 / 82.9).
- D77, "0.44 / 1.12 g/s at κ 1; 1.6 g/s for the system is the edge": 1.6-3.5 g/s at a 25 °C inlet, not within 4 g/s at
  45 °C (0.4 g/s, 25 °C: 88.5 → 131-145 °C; Table V κ 239-283 °C). No flow closes the cases D74 already fails at a uniform
  h 10⁵ (all Table V κ).
- D78, "at κ 1 the processor side does not bind": it binds (≤ 67-82 °C through R'' ≤ 3.3 at h 2·10⁴ / 25 °C; R'' 12 holds
  only the lo edge there, at ≤ 69 °C); at Table V κ it rescues one case only (≤ 55 °C).
- D80, "the thermal conclusions stand for the final spec": they do not; its relative result stands (edges < 1 K, slow corner
  +0.6 K at every κ, against an inductor 109-306 K hotter than the junctions without vias). **Stays:** the inductor is the
  hottest point in every run; glass 1 is the largest step without vias (69-194 K); the lumped loop is stable (runaway
  4.8-5.4 K/W, old 5.7-6.7; ≥ 7.5 × the requirement). D83's copper without core: 81.0 % at 85 °C, R_th 1.02 / 0.68 K/W.

## 1. Method

- **D73**: `p24_electrothermal.p_at / dpdt / fixed_point` on D73's 2.5 MHz N29 split (other terms equal D73's, D83 asserts),
  copper replaced, core added to the constant part, D75's 20 mm lateral copper; reproduces D76's 85 °C table (N29) to 10⁻¹².
- **D74 / D77 / D78 / D80**: their job functions (`p24_thermal_stack.run / refine`, `p24_coolant.run`, `p24_processor_side.run`,
  `p24_thermal_gate.stack / coolant`) run unchanged and take all heat from `p24_thermal_stack.sources()`; each worker
  replaces it (monkeypatch) by `d83_sources()`: the original with the core at zero, then copper 27.3 W and core κ × 34.5 /
  44.1 W less 9.38 W (`core_w`), split equally over the four phase columns as `coupled()` does (D83's per-phase DC
  63.1-64.1 A: ±1 %). Copied: D78's 85 °C crossing (inline in its `main`). Checks: the original sources reproduce D74
  (96.60), D77 (64.14), D78 (92.63), D80 gate_nom (95.31 °C) and D80's A171 edge powers to < 10⁻⁶ K; 1,154 solves plus
  bisections, ≤ 12 Picard iterations, energy balance ≤ 5·10⁻⁹.
- **Not rerun**: D74's ×2 density case, sensitivity (3.3), microvia table (3.4); D77's other coolers (2-13 % on its flows)
  and checks; D80's base / loop50 / gate_hot (base = the D74 / D77 inputs, rerun above).

## 2. Area and limits

- **Footprint.** All runs keep D74's 0.5 cm² column per phase and one 300 µm glass-2 body. One layer of IND048 needs
  1.24-4.15 cm² per phase (D83, drawn to Table VI cell), 2.5-8.3 × that (P24: 0.25-0.63 cm²). Inductor heat per footprint
  here: 26-31 W/cm² (κ 1), 62-77 W/cm² (Table V κ); old 13 / 24 W/cm². *Spread on one layer*, the flux falls 2.5-8.3 × and
  the glass and body steps roughly with it: the numbers above are conservative, but the module outgrows P24's and its
  cooled face must follow. *Stacked in P24's area* (P24: 3 layers; D83: 3-9), the flux per footprint is as modelled, but
  with uniform generation and one cooled face the body step is q'' t / (2 k_z): the 37-108 K body step grows roughly with
  the layer count, plus the dielectrics between layers, so the numbers are lower bounds. Neither case is computed.
- **Above ~150 °C the temperatures are not predictions** (core loss at 25 °C, linear copper law, constant conductivities,
  single-phase water whose mean outlet at 0.4 g/s exceeds 100 °C at κ 1 / 45 °C and 150 °C at Table V κ, from P / (ṁ c_p)
  with the rerun's module power): they measure the distance from 85 °C. κ and copper carry D83 Section 5's limits ([10]
  Table V on IND037-HBS1 at D 0.5, zero DC, ≤ 584 mA half p-p; here D 0.075, 1.56 A DC, 1.95 A half p-p per unit; copper
  R_DC, D73's law, × 1.24 at 85 °C).
- Waveforms are the ideal-inductor record's; with 26-128 W more inductor loss than D72 + D76 at κ 1, Vo and Ton would shift
  (D83). Stack values are scenarios (D74 Section 5); D74's levers (core k_z, glass-1 thickness, processor face) weigh more
  with a 37-108 K body step, not rerun. **For Mihai** (D74 Section 6, sharper): the cooled face and coolant, and the
  inductor's construction (layers, footprint, core conductivity).
