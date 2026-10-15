# D83 - the inductor array and its core loss with the HBS1 units [10] actually measured

2026-10-15. Corrects D72 and D76. [10] = Alvarez Barros et al., IEEE TCPMT 11(12), 2021, pp. 2183-2192 (P24's ref. [10]);
pages are journal pages. D72's power law ran from IND046-HBS1 (20 nH / 13.6 mΩ) to "500 nH / 39.3 mΩ", which is
winding IND037 in material HPE1 ([10] Table II p. 2186, Fig. 7 p. 2187). The flake materials (HPE1 among them) saturate
from ~100 mA; "the low saturation point prevents any of these materials to be used in a buck converter" (p. 2187), and
"only HBS1 can actually be used in power conversion applications" (p. 2189). D76 priced the core with a discrete toroid
(Murali et al., ECTC 2022, Fig. 8(e)). Script: `scripts/p24_hbs1_units.py` → `diagnostics/D83_hbs1_units.json`. No new
co-simulation; D62 / D67 / D70 / D72 / D76 keep their text and carry an erratum pointing here.

## 0. Results

**Conditions for every number below.** 25 °C, 250 W per module, 4 phases, the design records of D72 / D76: 5 MHz =
A112 p20_n0 (measured 3.52 MHz, D 0.070, L 1.467 nH); 2.5 MHz = A124 p125_n0 (1.98 MHz, D 0.075, 2.933 nH); 1 MHz =
A118 f6_n0 (0.83 MHz, D 0.076, 7.333 nH). Per phase: 62.5-64.4 A DC, 154-178 A peak-to-peak ripple, steady peaks
141-153 A. All other loss terms are D73's middle scenario (R_on max, ESR 1 mΩ, Q_g 17.1 nC, t_f 0.75 ns), recomputed
from the records; the script asserts they match `diagnostics/D73_electrothermal.json`. Converter only (no package),
unless a line says otherwise.

**Unit and array.** Every design uses **IND048-HBS1**: 60.7 nH / 22.8 mΩ, 376 µΩ/nH, 5 A max ([10] Table VI p. 2190,
Table II). An array of s in series × p in parallel keeps its unit's R/L, so copper = R/L · L · I_rms² and the best unit
is the lowest-R/L one: IND048, with the next-best ≥ 1.47× worse (Section 1). Sizing rule: (a) p ≥ steady peak / 5 A,
where 5 A is Table VI's maximum, the test's limit, not a measured saturation (p. 2187); (b) p ≥ DC / 2 A, because [10]
reports R_DC and r_acx rising above 2 A DC (Joule heating, p. 2187) without giving the size of the rise, so the arrays stay
where [10]'s values hold; this binds, p ≥ 33; (c) s · 60.7 nH / p within 2 % of the record's L. D72's 200 A budget
(p ≥ 40) changes only the 1 MHz array.

| design | s × p (units / phase) | L | per unit DC / peak / half p-p | copper per module (D72, N 29-31 / 40) | area per phase, Fig. 5 drawn / Table VI cell | per module |
|---|---|---|---|---|---|---|
| 5 MHz | 1 × 41 (41) | 1.480 nH | 1.56 / 3.74 / 2.17 A | **14.7 W** (15.2 / 12.8) | 0.62 / 2.08 cm² | 2.5 / 8.3 cm² |
| 2.5 MHz | 2 × 41 (82) | 2.961 nH | 1.56 / 3.51 / 1.95 A | **27.3 W** (18.6 / 15.0) | 1.24 / 4.15 cm² | 5.0 / 16.6 cm² |
| 1 MHz | 4 × 33 (132); 200 A: 5 × 41 (205) | 7.358 / 7.402 nH | 1.95 / 4.29 / 2.33 A | **66.3 / 66.7 W** (24.5 / 19.8) | 2.00 / 6.68; 3.10 / 10.4 cm² | 8.0 / 26.7; 12.4 / 41.5 cm² |

**Area.** P24 gives a phase 0.25 cm² (one Fig. 5 column of a 1 cm² site), 0.5 cm² (D75: a 250 W module on two sites) or
0.625 cm² (25 × 40 mm over 16 phases). A single-layer array is 1-17× that at 5 and 2.5 MHz, and 3-42× at 1 MHz. P24
itself stacks 3 layers (p. 290: "4 arrays and 3 stacked layers"). At 0.5 cm² per phase the arrays need (drawn area to
cell area) 2-5 layers at 5 MHz, 3-9 at 2.5 MHz, 4-14 at 1 MHz (7-21 for the 200 A array).

**Core loss.** [10] Eq. (1) (p. 2184) gives P = κ r_acx(D, f) L Δi² per phase, with Δi **the half peak-to-peak
ripple** (p. 2188: "the current ripple is just the half peak-to-peak current"; Eq. (2) is normalised to it, Section 5).
D76 used Δi² = (peak − valley)² / 12, the rms², which is **one third** of Eq. (1)'s value. r_acx = the embedded HBS1
band of [10] Fig. 8 (p. 2187; small signal, zero DC, lowest to highest winding), read at the record's D, log-log in f
between the 2 and 5 MHz curves. κ = [10] Table V (p. 2189) at the nearest frequency, measured on IND037-HBS1 at D 0.5,
zero DC, ≤ 584 mA half p-p.

| design | r_acx, mΩ/nH (D76 toroid) | κ, Table V | core per module, κ 1 | core at Table V κ | D76, κ 1 / 4 |
|---|---|---|---|---|---|
| 5 MHz (3.52 MHz, D 0.070) | 0.94-1.09 (0.768) | 4.806 (4 MHz; 3 MHz: 4.134) | 43.5-50.2 W | 209-241 W | 11.8 / 47.2 W |
| 2.5 MHz (1.98 MHz, D 0.075) | 0.465-0.595 (0.302) | 3.074 (2 MHz) | **34.5-44.1 W** | **106-136 W** | 7.5 / 29.9 W |
| 1 MHz (0.83 MHz, D 0.076) | 0.167-0.251, extrapolated (0.077) | 3.074 (2 MHz; [10] has none below) | 29.0-43.5 W | 89-134 W | 4.5 / 17.9 W |

**Converter efficiency**, computed as D72 / D76 do: p_out / (p_out + p25 + core), 25 °C, no package.

| design | no core | κ 1 | Table V κ | same, D76's rms² convention (κ 1 / Table V) | D72 no core | D76 κ 1 | D76 κ 4 |
|---|---|---|---|---|---|---|---|
| 5 MHz | 86.53 % | 73.7-75.2 % | 47.2-50.2 % | 81.8-82.4 / 67.7-69.7 % | 86.38 / 87.10 % | 83.00 / 83.66 % | 74.27 / 74.80 % |
| 2.5 MHz | 84.01 % | **73.2-75.3 %** | **57.7-62.0 %** | 80.1-80.9 / 72.9-75.1 % | 86.56 / 87.65 % | 84.38 / 85.42 % | 78.44 / 79.34 % |
| 1 MHz | 74.97 % | 66.3-69.0 % | 53.5-59.2 % | 71.9-72.9 / 66.1-68.8 % | 85.71 / 87.13 % | 84.41 / 85.79 % | 80.75 / 82.01 % |

D75's package (20 mm module, 429 µm / 50 pH to 86 µm / 150 pH) costs 0.3-2.8 points more: for example 2.5 MHz falls to
70.5-74.6 % at κ 1 and 56.1-61.5 % at Table V κ. What moved the 2.5 MHz number, largest first: the Eq. (1)
normalisation (× 3 on the core loss), κ from Table V (3.07, where D76 used 1-4), the embedded r_acx (1.5-2.0 × the
toroid's), and a real unit's R/L (376 µΩ/nH, where D72's power law gave 208-258). **With HBS1 at this ripple the
converter is a 58-75 % design, not 84-88 %.**

## 1. The HBS1 units in [10]

L is from Fig. 7's HBS1 panel (measured, 1-2 MHz, digitised to ±0.5 nH), except IND048 from Table VI. R_DC is from
Table II (p. 2186). Footprints are from Fig. 5 (p. 2186).

| winding | L (nH) | R_DC (mΩ) | R/L (µΩ/nH) | footprint |
|---|---|---|---|---|
| IND034 | 18.8 | 14.3 | 761 | not fully dimensioned |
| IND046 | 19.8-19.9 | 13.6 | 684-687 | 1.75 × 0.5 mm |
| IND035 | 29.7-29.8 | 21.3 | 715-717 | 2.6 × 0.515 mm |
| IND036 | 43.1-43.3 | 24.9 | 575-578 | 1.84 × 1.06 mm |
| IND047 | 52.2-52.4 | 29.0 | 553-556 | 1.75 × 0.865 mm |
| **IND048** | 60.7 (Table VI) | 22.8 | **376** | 1.75 × 0.865 mm drawn; 2.25 × 2.25 mm "area" (Table VI), presumably the cell of its 16-element array (p. 2186) |
| IND037 | 70.6-71.0 | 39.3 | 553-563 | 2.91 × ~1.06 mm |

D72's 85-117 nH units (2.5 MHz) and 213-293 nH units (1 MHz) lie above every HBS1 unit here. Its 45-59 nH units (5 MHz)
lie inside the range, but at 331-392 µΩ/nH, where the measured units of 43-61 nH have 376-578. The JSON lists the
fewest-unit array for every winding (for example 5 MHz: IND047 1 × 36, at 555 µΩ/nH).

## 2. The frequency ranking

- **No core loss: 5 > 2.5 > 1 MHz (86.5 / 84.0 / 75.0 %).** With a fixed unit R/L, copper ∝ L ∝ 1/f: 14.7 / 27.3 /
  66.3 W. D72 put 2.5 MHz first only because its power law gave large units a low R/L (139 µΩ/nH at 1 MHz). No HBS1
  unit above 71 nH exists.
- **κ 1: 2.5 MHz and 5 MHz tie (73.2-75.3 / 73.7-75.2 %); 1 MHz is 4-9 points behind.** Between 2 and 5 MHz the
  embedded r_acx rises as f^1.0-1.2, where the toroid rose as f^1.55, so L r_acx Δi² is nearly flat in f:
  29-44 / 35-44 / 44-50 W at 1 / 2.5 / 5 MHz.
- **Table V κ: 2.5 MHz leads (57.7-62.0 %)**, then 1 MHz (53.5-59.2 %, κ unsourced below 2 MHz), then 5 MHz
  (47.2-50.2 %), because κ rises from 3.07 at 2 MHz to 5.07 at 5 MHz.
- **The choice does not change: 2.5 MHz leads or ties at every κ.** D76's "1 MHz ties or leads 2.5 MHz" (and D67
  Section 7) does not survive real units, because copper decides it. The 2.5 MHz design keeps its other reasons (3 ×
  the 1 MHz valley margin, the frozen controller).
- **The material is what fails.** [10] reaches the same conclusion for 12-1 V and asks for a new material (Sec. IX,
  p. 2190: μr 45-65, κ 4).

## 3. r_core of plant V7 with the embedded data

**A221's rule** sets r_core = (2π · 8 MHz)² L / r_acx(8 MHz, D 0.077). With the toroid's 2.557 mΩ/nH this gives 2.90 Ω
at L0 (2.933 nH) and 2.17 Ω at 0.75 L0.

**[10]'s value at 8 MHz.** Fig. 8 has curves at 2, 5 and 10 MHz only. At D 0.077 they read 1.38-1.49 mΩ/nH (5 MHz) and
3.51-3.83 mΩ/nH (10 MHz). Log-log interpolation (exponent 1.35-1.36) gives **2.60-2.83 mΩ/nH** at 8 MHz, 2-11 % above
the toroid's value. Uncertainty: ±0.04 mΩ/nH digitisation per curve edge gives 2.55-2.87; linear rather than log-log
interpolation in f gives 2.66-2.89.

**Result: r_core = 2.62-2.85 Ω at L0 and 1.97-2.14 Ω at 0.75 L0 (all readings: 2.56-2.90 Ω and 1.92-2.18 Ω),** i.e.
0 to −12 % under A221's rule. Fitting at [10]'s highest point instead (10 MHz, the one nearest the 20-25 MHz ring)
gives 3.02-3.30 Ω at L0.

**Under [10] Eq. (2) the rule books the wrong r_acx.** A parallel resistor's r_acx is 4 f² L / (D (1 − D) r_core), not
(2πf)² L / r_core (the script checks this against the harmonic sum).
- At the 2.5 MHz operating point (1.98 MHz, D 0.075), V7's 2.90 Ω books 0.229 mΩ/nH, i.e. 17.0 W per module on the A124
  waveform (V7's records: 15.5 W on N0, `reports/FINAL_SPEC_COVERAGE.md`). That is 0.38-0.49 × the embedded
  small-signal value and 0.13-0.16 × the Table V large-signal value.
- To book those values there, r_core would have to be 1.12-1.43 Ω (κ 1) or 0.36-0.47 Ω (κ 3.07) at L0. An
  Eq. (2)-consistent fit at 8 MHz gives 3.74-4.07 Ω.

A single resistor has r_acx ∝ f², while the embedded data rise as f^1.0-1.36, so no one value matches both the ~2 MHz
loss and the ring's damping. No source gives HBS1 above 10 MHz.

**Decision: V7 stays as it is, no rerun.** r_core's job in V7 is the damping of an idle phase's ring (A221), not the
loss figure. The fits above span 2.56-4.07 Ω at L0. The V7 conclusions were checked from 2.90 Ω to 5.80 Ω: A221's
skipping rows and A225's two-cycle orbit hold with half the core's damping (2 × r_core; A221 RESULTS rows rc2, A225
s rows rc2). The part below 2.90 Ω (to −12 %) is more damping of the same ring and is not run. What
changes is how V7's books are read: the core loss they carry (15.5 W per module on N0 at full load, 29.4 W on S75 at
125 °C) is a damping resistor's, not an efficiency figure; the core loss of the design is Section 0's.

## 4. P24's own sizing against [10]

P24 Table 3 and its text (p. 290) give 4 phases × 8 modules of 125 W, DCM, 62.5 A peak per phase, and **12 parallel
units per phase of 183 nH** (1 MHz), 36.7 nH (5 MHz) or 18.4 nH (10 MHz), 5 A each, naming "MPC core (HBS1) in [10]".
Against [10]:
- The largest HBS1 unit is IND037 at 70.6-71.0 nH; 183 nH is 2.6 × that. [10] Sec. IX (p. 2190) reaches 170 nH in
  IND048 only with a μr ~65 material, and HBS1 is μr 24 (Table VI). 36.7 nH lies inside the range, but no unit has it.
- With IND048-HBS1, P24's 15.25 nH per phase at 62.5 A takes 3 in series × 12 in parallel (36 units, 15.2 nH, 5.2 A
  per string): 3 × P24's count.
- P24's 5 A per unit is [10]'s test limit (Table VI), not a measured saturation. Its ripple per unit (5.2 A
  peak-to-peak, 2.6 A half p-p) is 4.5 × the ripple under which [10] measured κ.

## 5. Limits

- **κ.** Table V holds for D 0.5, zero DC and ≤ 584 mA half p-p on IND037-HBS1; here the units see D 0.070-0.076,
  1.6-2.0 A DC and 1.9-2.3 A half p-p. Table IV (5 MHz, 77-584 mA: κ 4.79-5.37) suggests κ grows with ripple. [10] has
  no κ below 2 MHz, so the 1 MHz design uses the 2 MHz value.
- **r_acx.** The band is ±0.04 mΩ/nH per edge. Fig. 8 does not label its lines, so the band is not tied to IND048. The
  1 MHz design is extrapolated below the 2 MHz curve with the 2-5 MHz exponent; with f^1 it reads 0.195-0.249 and the
  efficiency moves ≤ 0.9 points at κ 1 and ≤ 2.0 points at Table V κ.
- **DC.** The 1 MHz steady array runs at 1.95 A DC per unit, at the 2 A edge; above 2 A, [10] gives no size for the rise.
- **Copper and temperature.** R_DC only; winding AC loss is only what [10]'s measured R_ac (and so r_acx) contains. All
  at 25 °C: copper hot by D73's law would be × 1.24 at 85 °C; the core is held at its 25 °C value.
- **Waveforms.** The arrays match the record's L to +0.3 to +0.9 %. The ripple comes from the records (ideal-inductor
  co-simulations); at these losses Vo and Ton would shift, which is not modelled.
- **The × 3** rests on [10] Eq. (1)-(2) and p. 2188's definition. For a frequency-flat R, Eq. (2) gives r_acx = R / (3 L),
  so Eq. (1) with the half p-p ripple returns R · I_rms² exactly (the script checks it); with the rms or the peak-to-peak
  ripple it does not. D76's code (`phase_core_loss` in `src/scb_ivr/p24_core_loss.py`) is not changed here.
